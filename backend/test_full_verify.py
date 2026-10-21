import requests
import sys

BASE = "http://localhost:8000/api"
p = 0
f = 0

def c(name, ok, detail=""):
    global p, f
    if ok:
        p += 1
        print("  [PASS] " + name)
    else:
        f += 1
        print("  [FAIL] " + name + "  " + detail)

# ── Register ──
r = requests.post(BASE + "/auth/register/", json={"username": "fulltest", "email": "full@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
token = r.json()["tokens"]["access"]
h = {"Authorization": "Bearer " + token}

# ═══════════════════════════════════════════════════
print("=== EXPENSE CATEGORIZATION ===")
# ═══════════════════════════════════════════════════

print("\n--- Create with valid category ---")
r = requests.post(BASE + "/expenses/", json={"amount": 500, "category": "food", "description": "Lunch", "date": "2026-09-16"}, headers=h, timeout=5)
c("Create food expense 201", r.status_code == 201)
c("Category stored as food", r.json().get("category") == "food")
exp_id = r.json().get("id")

for cat in ["travel", "shopping", "education", "entertainment", "miscellaneous"]:
    r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": cat, "date": "2026-09-16"}, headers=h, timeout=5)
    c("Category " + cat + " accepted", r.status_code == 201)

print("\n--- Invalid category ---")
r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": "invalid_cat", "date": "2026-09-16"}, headers=h, timeout=5)
c("Invalid category rejected 422", r.status_code == 422)

print("\n--- Missing category ---")
r = requests.post(BASE + "/expenses/", json={"amount": 100, "date": "2026-09-16"}, headers=h, timeout=5)
c("Missing category rejected 422", r.status_code == 422)

print("\n--- Update category ---")
r = requests.put(BASE + "/expenses/" + str(exp_id) + "/", json={"category": "travel"}, headers=h, timeout=5)
c("Update category to travel 200", r.status_code == 200)
c("Category changed", r.json().get("category") == "travel")

r = requests.put(BASE + "/expenses/" + str(exp_id) + "/", json={"category": "bad"}, headers=h, timeout=5)
c("Invalid category update rejected", r.status_code == 422)

print("\n--- Retrieve with categories ---")
r = requests.get(BASE + "/expenses/", headers=h, timeout=5)
c("List expenses 200", r.status_code == 200)
all_cats = set(e["category"] for e in r.json()["expenses"])
c("All 6 categories present", len(all_cats) == 6, str(all_cats))

print("\n--- User ownership ---")
r2 = requests.post(BASE + "/auth/register/", json={"username": "fulltest2", "email": "full2@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
h2 = {"Authorization": "Bearer " + r2.json()["tokens"]["access"]}
r = requests.get(BASE + "/expenses/" + str(exp_id) + "/", headers=h2, timeout=5)
c("User2 cant see User1 expense", r.status_code == 404)

# ═══════════════════════════════════════════════════
print("\n=== BUDGET CREATION SYSTEM ===")
# ═══════════════════════════════════════════════════

allocs = [
    {"category": "food", "amount": 5000},
    {"category": "travel", "amount": 2000},
    {"category": "shopping", "amount": 3000},
    {"category": "education", "amount": 1500},
    {"category": "entertainment", "amount": 1000},
    {"category": "miscellaneous", "amount": 500},
]

print("\n--- Create monthly budget ---")
r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 13000, "allocations": allocs}, headers=h, timeout=5)
c("Create budget 201", r.status_code == 201)
bud = r.json()
c("Budget has id", bool(bud.get("id")))
c("Month 9", bud.get("month") == 9)
c("Year 2026", bud.get("year") == 2026)
c("Total 13000", bud.get("total_amount") == 13000.0)
c("6 allocations", len(bud.get("allocations", [])) == 6)
bud_id = bud.get("id")

print("\n--- Category-wise allocation ---")
alloc_map = {a["category"]: a["amount"] for a in bud["allocations"]}
c("Food allocated 5000", alloc_map.get("food") == 5000.0)
c("Travel allocated 2000", alloc_map.get("travel") == 2000.0)
c("Shopping allocated 3000", alloc_map.get("shopping") == 3000.0)
c("Education allocated 1500", alloc_map.get("education") == 1500.0)
c("Entertainment allocated 1000", alloc_map.get("entertainment") == 1000.0)
c("Miscellaneous allocated 500", alloc_map.get("miscellaneous") == 500.0)

print("\n--- Invalid budget data ---")
r = requests.post(BASE + "/budgets/", json={"month": 13, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=h, timeout=5)
c("Invalid month rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": -100, "allocations": [{"category": "food", "amount": 100}]}, headers=h, timeout=5)
c("Negative total rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "bad_cat", "amount": 1000}]}, headers=h, timeout=5)
c("Invalid category rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": -100}]}, headers=h, timeout=5)
c("Negative allocation rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=h, timeout=5)
c("Duplicate month rejected 400", r.status_code == 400)

print("\n--- View budget ---")
r = requests.get(BASE + "/budgets/", headers=h, timeout=5)
c("List budgets 200", r.status_code == 200)
c("1 budget", r.json().get("total") == 1)

r = requests.get(BASE + "/budgets/" + str(bud_id) + "/", headers=h, timeout=5)
c("Get single 200", r.status_code == 200)
c("Has allocations", len(r.json().get("allocations", [])) == 6)

print("\n--- User isolation ---")
r = requests.get(BASE + "/budgets/" + str(bud_id) + "/", headers=h2, timeout=5)
c("User2 cant get User1 budget", r.status_code == 404)

r = requests.get(BASE + "/budgets/", headers=h2, timeout=5)
c("User2 sees empty budgets", r.json().get("total") == 0)

# ═══════════════════════════════════════════════════
print("\n" + "=" * 50)
print("TOTAL: Passed=" + str(p) + ", Failed=" + str(f))
if f == 0:
    print("ALL " + str(p) + " TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(0 if f == 0 else 1)
