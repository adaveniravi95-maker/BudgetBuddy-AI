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

# Register
r = requests.post(BASE + "/auth/register/", json={"username": "bud1", "email": "bud1@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
token = r.json()["tokens"]["access"]
h = {"Authorization": "Bearer " + token}

allocations = [
    {"category": "food", "amount": 5000},
    {"category": "travel", "amount": 2000},
    {"category": "shopping", "amount": 3000},
    {"category": "education", "amount": 1500},
    {"category": "entertainment", "amount": 1000},
    {"category": "miscellaneous", "amount": 500},
]

print("=== CREATE BUDGET ===")
r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 13000, "allocations": allocations}, headers=h, timeout=5)
c("Create budget 201", r.status_code == 201)
bud = r.json() if r.status_code == 201 else {}
c("Has id", bool(bud.get("id")))
c("Month 9", bud.get("month") == 9)
c("Year 2026", bud.get("year") == 2026)
c("Total 13000", bud.get("total_amount") == 13000.0)
c("6 allocations", len(bud.get("allocations", [])) == 6)

# Check allocation amounts
allocs = {a["category"]: a["amount"] for a in bud.get("allocations", [])}
c("Food 5000", allocs.get("food") == 5000.0)
c("Travel 2000", allocs.get("travel") == 2000.0)
c("Shopping 3000", allocs.get("shopping") == 3000.0)

# Validation
r = requests.post(BASE + "/budgets/", json={"month": 13, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=h, timeout=5)
c("Invalid month rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": -100, "allocations": [{"category": "food", "amount": 100}]}, headers=h, timeout=5)
c("Negative total rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": -100}]}, headers=h, timeout=5)
c("Negative alloc rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "bad", "amount": 100}]}, headers=h, timeout=5)
c("Bad category rejected", r.status_code == 422)

# Duplicate
r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=h, timeout=5)
c("Duplicate month rejected 400", r.status_code == 400)

# No auth
r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, timeout=5)
c("No auth rejected", r.status_code == 401)

print("\n=== LIST BUDGETS ===")
r = requests.get(BASE + "/budgets/", headers=h, timeout=5)
c("List 200", r.status_code == 200)
c("1 budget", r.json().get("total") == 1)

r = requests.get(BASE + "/budgets/?year=2026", headers=h, timeout=5)
c("Filter by year", r.json().get("total") == 1)

r = requests.get(BASE + "/budgets/?year=2025", headers=h, timeout=5)
c("Filter year no match", r.json().get("total") == 0)

print("\n=== GET SINGLE ===")
r = requests.get(BASE + "/budgets/" + str(bud["id"]) + "/", headers=h, timeout=5)
c("Get single 200", r.status_code == 200)
c("Has allocations", len(r.json().get("allocations", [])) == 6)

r = requests.get(BASE + "/budgets/99999/", headers=h, timeout=5)
c("Not found 404", r.status_code == 404)

print("\n=== UPDATE BUDGET ===")
r = requests.put(BASE + "/budgets/" + str(bud["id"]) + "/", json={"total_amount": 15000, "allocations": [{"category": "food", "amount": 6000}, {"category": "travel", "amount": 2500}, {"category": "shopping", "amount": 3500}, {"category": "education", "amount": 1500}, {"category": "entertainment", "amount": 1000}, {"category": "miscellaneous", "amount": 500}]}, headers=h, timeout=5)
c("Update 200", r.status_code == 200)
c("Total updated", r.json().get("total_amount") == 15000.0)
c("Allocations replaced", len(r.json().get("allocations", [])) == 6)

r = requests.put(BASE + "/budgets/" + str(bud["id"]) + "/", json={"total_amount": -1}, headers=h, timeout=5)
c("Bad update rejected", r.status_code == 422)

# Partial update (total only)
r = requests.put(BASE + "/budgets/" + str(bud["id"]) + "/", json={"total_amount": 16000}, headers=h, timeout=5)
c("Partial update total", r.status_code == 200)
c("Allocations preserved", len(r.json().get("allocations", [])) == 6)

print("\n=== DELETE BUDGET ===")
r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 5000, "allocations": [{"category": "food", "amount": 5000}]}, headers=h, timeout=5)
did = r.json().get("id")

r = requests.delete(BASE + "/budgets/" + str(did) + "/", headers=h, timeout=5)
c("Delete 204", r.status_code == 204)

r = requests.get(BASE + "/budgets/" + str(did) + "/", headers=h, timeout=5)
c("Deleted gone 404", r.status_code == 404)

print("\n=== USER ISOLATION ===")
r2 = requests.post(BASE + "/auth/register/", json={"username": "bud2", "email": "bud2@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
h2 = {"Authorization": "Bearer " + r2.json()["tokens"]["access"]}

r = requests.get(BASE + "/budgets/" + str(bud["id"]) + "/", headers=h2, timeout=5)
c("User2 cant get User1", r.status_code == 404)

r = requests.put(BASE + "/budgets/" + str(bud["id"]) + "/", json={"total_amount": 1}, headers=h2, timeout=5)
c("User2 cant update User1", r.status_code == 404)

r = requests.delete(BASE + "/budgets/" + str(bud["id"]) + "/", headers=h2, timeout=5)
c("User2 cant delete User1", r.status_code == 404)

r = requests.get(BASE + "/budgets/", headers=h2, timeout=5)
c("User2 sees only own budgets", r.json().get("total") == 0)

print("\n=== EXPENSE CATEGORIZATION CHECK ===")
r = requests.post(BASE + "/expenses/", json={"amount": 500, "category": "food", "description": "Test", "date": "2026-09-16"}, headers=h, timeout=5)
c("Expense with category 201", r.status_code == 201)
c("Category stored", r.json().get("category") == "food")

r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": "bad", "date": "2026-09-16"}, headers=h, timeout=5)
c("Invalid category rejected", r.status_code == 422)

print("\n" + "=" * 40)
print("Passed: " + str(p) + ", Failed: " + str(f))
if f == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(0 if f == 0 else 1)
