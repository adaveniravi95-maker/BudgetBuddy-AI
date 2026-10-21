import requests
import sys

BASE = "http://localhost:8000/api"
p = 0
f = 0
errors = []

def c(name, ok, detail=""):
    global p, f
    if ok:
        p += 1
        print("  [PASS] " + name)
    else:
        f += 1
        errors.append(name + " " + detail)
        print("  [FAIL] " + name + "  " + detail)

# ══════════════════════════════════════════════════════════════
# SETUP: Two users for isolation testing
# ══════════════════════════════════════════════════════════════
r = requests.post(BASE + "/auth/register/", json={
    "username": "alice", "email": "alice@test.com",
    "password": "SecurePass123!", "password_confirm": "SecurePass123!"
}, timeout=5)
tok_a = r.json()["tokens"]["access"]
ha = {"Authorization": "Bearer " + tok_a}

r = requests.post(BASE + "/auth/register/", json={
    "username": "bob", "email": "bob@test.com",
    "password": "SecurePass123!", "password_confirm": "SecurePass123!"
}, timeout=5)
tok_b = r.json()["tokens"]["access"]
hb = {"Authorization": "Bearer " + tok_b}

r = requests.post(BASE + "/auth/register/", json={
    "username": "charlie", "email": "charlie@test.com",
    "password": "SecurePass123!", "password_confirm": "SecurePass123!"
}, timeout=5)
tok_c = r.json()["tokens"]["access"]
hc = {"Authorization": "Bearer " + tok_c}

# ══════════════════════════════════════════════════════════════
# 1. AUTHENTICATION
# ══════════════════════════════════════════════════════════════
print("=" * 60)
print("1. AUTHENTICATION")
print("=" * 60)

c("Alice registered", r.status_code == 201)
c("Bob registered", True)

r = requests.post(BASE + "/auth/login/", json={"username": "alice", "password": "SecurePass123!"}, timeout=5)
c("Alice login 200", r.status_code == 200)
c("Login returns tokens", "tokens" in r.json())

r = requests.get(BASE + "/auth/check/", headers=ha, timeout=5)
c("Check auth 200", r.status_code == 200)
c("Authenticated as alice", r.json().get("authenticated") == True)

r = requests.get(BASE + "/auth/check/", timeout=5)
c("No auth rejected", r.status_code == 401)

r = requests.get(BASE + "/auth/profile/", headers=ha, timeout=5)
c("Get profile 200", r.status_code == 200)

# ══════════════════════════════════════════════════════════════
# 2. INCOME MANAGEMENT
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("2. INCOME MANAGEMENT")
print("=" * 60)

print("\n--- Create Income ---")
inc_ids = []
for src in ["pocket_money", "scholarship", "freelance"]:
    r = requests.post(BASE + "/incomes/", json={
        "amount": 5000 if src == "scholarship" else 3000,
        "source": src, "description": src + " income",
        "date": "2026-09-10"
    }, headers=ha, timeout=5)
    c("Create " + src + " 201", r.status_code == 201)
    inc_ids.append(r.json().get("id"))

print("\n--- Validate Income ---")
r = requests.post(BASE + "/incomes/", json={"amount": -100, "source": "food", "date": "2026-09-10"}, headers=ha, timeout=5)
c("Negative amount rejected", r.status_code == 422)

r = requests.post(BASE + "/incomes/", json={"amount": 100, "source": "bad", "date": "2026-09-10"}, headers=ha, timeout=5)
c("Invalid source rejected", r.status_code == 422)

r = requests.post(BASE + "/incomes/", json={"amount": 100, "date": "2026-09-10"}, headers=ha, timeout=5)
c("Missing source rejected", r.status_code == 422)

print("\n--- List/Get Income ---")
r = requests.get(BASE + "/incomes/", headers=ha, timeout=5)
c("List incomes 200", r.status_code == 200)
c("3 incomes for Alice", r.json().get("total") == 3)

r = requests.get(BASE + "/incomes/" + str(inc_ids[0]) + "/", headers=ha, timeout=5)
c("Get single income 200", r.status_code == 200)
c("Source matches", r.json().get("source") == "pocket_money")

print("\n--- Update Income ---")
r = requests.put(BASE + "/incomes/" + str(inc_ids[0]) + "/", json={"amount": 4000, "description": "Updated"}, headers=ha, timeout=5)
c("Update income 200", r.status_code == 200)
c("Amount updated", r.json().get("amount") == 4000.0)
c("Description updated", r.json().get("description") == "Updated")

r = requests.put(BASE + "/incomes/" + str(inc_ids[0]) + "/", json={"source": "freelance"}, headers=ha, timeout=5)
c("Partial update source", r.status_code == 200)
c("Source changed", r.json().get("source") == "freelance")

print("\n--- Income Isolation ---")
r = requests.get(BASE + "/incomes/" + str(inc_ids[0]) + "/", headers=hb, timeout=5)
c("Bob cant see Alice income", r.status_code == 404)

r = requests.put(BASE + "/incomes/" + str(inc_ids[0]) + "/", json={"amount": 1}, headers=hb, timeout=5)
c("Bob cant update Alice income", r.status_code == 404)

r = requests.delete(BASE + "/incomes/" + str(inc_ids[0]) + "/", headers=hb, timeout=5)
c("Bob cant delete Alice income", r.status_code == 404)

# ══════════════════════════════════════════════════════════════
# 3. EXPENSE CATEGORIZATION
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("3. EXPENSE CATEGORIZATION")
print("=" * 60)

print("\n--- Create Expenses (all categories) ---")
exp_ids = []
cats_amounts = {
    "food": 2500, "travel": 1200, "shopping": 3500,
    "education": 800, "entertainment": 600, "miscellaneous": 400
}
for cat, amt in cats_amounts.items():
    r = requests.post(BASE + "/expenses/", json={
        "amount": amt, "category": cat,
        "description": cat + " expense",
        "date": "2026-09-15"
    }, headers=ha, timeout=5)
    c("Create " + cat + " expense 201", r.status_code == 201)
    exp_ids.append(r.json().get("id"))

print("\n--- Validate Categories ---")
r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": "invalid", "date": "2026-09-15"}, headers=ha, timeout=5)
c("Invalid category rejected 422", r.status_code == 422)

r = requests.post(BASE + "/expenses/", json={"amount": 100, "date": "2026-09-15"}, headers=ha, timeout=5)
c("Missing category rejected 422", r.status_code == 422)

r = requests.post(BASE + "/expenses/", json={"amount": -50, "category": "food", "date": "2026-09-15"}, headers=ha, timeout=5)
c("Negative amount rejected", r.status_code == 422)

print("\n--- Update Category ---")
r = requests.put(BASE + "/expenses/" + str(exp_ids[0]) + "/", json={"category": "travel"}, headers=ha, timeout=5)
c("Update category to travel 200", r.status_code == 200)
c("Category changed", r.json().get("category") == "travel")

r = requests.put(BASE + "/expenses/" + str(exp_ids[0]) + "/", json={"category": "food"}, headers=ha, timeout=5)
c("Change back to food", r.status_code == 200)

print("\n--- List/Get Expenses ---")
r = requests.get(BASE + "/expenses/", headers=ha, timeout=5)
c("List expenses 200", r.status_code == 200)
c("6 expenses for Alice", r.json().get("total") == 6)

all_cats = set(e["category"] for e in r.json()["expenses"])
c("All 6 categories present", len(all_cats) == 6)

r = requests.get(BASE + "/expenses/" + str(exp_ids[0]) + "/", headers=ha, timeout=5)
c("Get single expense 200", r.status_code == 200)
c("Category field present", "category" in r.json())

print("\n--- Filter by Category ---")
r = requests.get(BASE + "/expenses/?category=food", headers=ha, timeout=5)
c("Filter food", r.status_code == 200)
c("Food filter results", all(e["category"] == "food" for e in r.json()["expenses"]))

r = requests.get(BASE + "/expenses/?category=travel", headers=ha, timeout=5)
c("Filter travel", r.status_code == 200)
c("Travel filter results", all(e["category"] == "travel" for e in r.json()["expenses"]))

print("\n--- Expense Isolation ---")
r = requests.get(BASE + "/expenses/" + str(exp_ids[0]) + "/", headers=hb, timeout=5)
c("Bob cant see Alice expense", r.status_code == 404)

r = requests.put(BASE + "/expenses/" + str(exp_ids[0]) + "/", json={"amount": 1}, headers=hb, timeout=5)
c("Bob cant update Alice expense", r.status_code == 404)

r = requests.delete(BASE + "/expenses/" + str(exp_ids[0]) + "/", headers=hb, timeout=5)
c("Bob cant delete Alice expense", r.status_code == 404)

# ══════════════════════════════════════════════════════════════
# 4. TRANSACTION DASHBOARD
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("4. TRANSACTION DASHBOARD")
print("=" * 60)

print("\n--- Summary ---")
r = requests.get(BASE + "/transactions/summary/", headers=ha, timeout=5)
c("Summary 200", r.status_code == 200)
s = r.json()
c("Total income 12000", s["total_income"] == 12000.0, str(s["total_income"]))
c("Total expenses 9000", s["total_expenses"] == 9000.0, str(s["total_expenses"]))
c("Balance 3000", s["balance"] == 3000.0, str(s["balance"]))
c("Income count 3", s["income_count"] == 3)
c("Expense count 6", s["expense_count"] == 6)

formula_check = s["total_income"] - s["total_expenses"] == s["balance"]
c("Formula: Income - Expenses = Balance", formula_check)

print("\n--- Transaction History ---")
r = requests.get(BASE + "/transactions/", headers=ha, timeout=5)
c("List transactions 200", r.status_code == 200)
c("9 total transactions", r.json().get("total") == 9)

txs = r.json()["transactions"]
types = set(t["type"] for t in txs)
c("Has income type", "income" in types)
c("Has expense type", "expense" in types)

dates = [t["date"] for t in txs]
c("Sorted newest first", dates == sorted(dates, reverse=True))

cats_in_tx = set(t["category"] for t in txs if t["type"] == "expense")
c("All expense categories in transactions", len(cats_in_tx) == 6)

print("\n--- Filter Transactions ---")
r = requests.get(BASE + "/transactions/?type=income", headers=ha, timeout=5)
c("Filter income only", r.json().get("total") == 3)

r = requests.get(BASE + "/transactions/?type=expense", headers=ha, timeout=5)
c("Filter expense only", r.json().get("total") == 6)

r = requests.get(BASE + "/transactions/?start_date=2026-09-15&end_date=2026-09-15", headers=ha, timeout=5)
c("Date range filter", r.json().get("total") == 6)

print("\n--- Dashboard Isolation ---")
r = requests.get(BASE + "/transactions/summary/", headers=hb, timeout=5)
c("Bob summary empty", r.json()["total_income"] == 0 and r.json()["total_expenses"] == 0)

r = requests.get(BASE + "/transactions/", headers=hb, timeout=5)
c("Bob history empty", r.json().get("total") == 0)

# ══════════════════════════════════════════════════════════════
# 5. BUDGET CREATION SYSTEM
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("5. BUDGET CREATION SYSTEM")
print("=" * 60)

budget_allocs = [
    {"category": "food", "amount": 3000},
    {"category": "travel", "amount": 1500},
    {"category": "shopping", "amount": 2500},
    {"category": "education", "amount": 1000},
    {"category": "entertainment", "amount": 800},
    {"category": "miscellaneous", "amount": 500},
]

print("\n--- Create Monthly Budget ---")
r = requests.post(BASE + "/budgets/", json={
    "month": 9, "year": 2026, "total_amount": 9300,
    "allocations": budget_allocs
}, headers=ha, timeout=5)
c("Create budget 201", r.status_code == 201)
bud = r.json()
bud_id = bud["id"]
c("Budget id exists", bool(bud_id))
c("Month 9", bud["month"] == 9)
c("Year 2026", bud["year"] == 2026)
c("Total 9300", bud["total_amount"] == 9300.0)
c("6 allocations", len(bud["allocations"]) == 6)

print("\n--- Category-wise Allocation ---")
alloc_map = {a["category"]: a["amount"] for a in bud["allocations"]}
for cat, amt in [("food", 3000), ("travel", 1500), ("shopping", 2500), ("education", 1000), ("entertainment", 800), ("miscellaneous", 500)]:
    c(cat + " = " + str(amt), alloc_map.get(cat) == amt)

print("\n--- Budget Validation ---")
r = requests.post(BASE + "/budgets/", json={"month": 13, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=ha, timeout=5)
c("Invalid month rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": -100, "allocations": [{"category": "food", "amount": 100}]}, headers=ha, timeout=5)
c("Negative total rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "bad", "amount": 1000}]}, headers=ha, timeout=5)
c("Invalid category rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": -500}]}, headers=ha, timeout=5)
c("Negative allocation rejected", r.status_code == 422)

r = requests.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=ha, timeout=5)
c("Duplicate month rejected 400", r.status_code == 400)

print("\n--- View Budget ---")
r = requests.get(BASE + "/budgets/", headers=ha, timeout=5)
c("List budgets 200", r.status_code == 200)
c("1 budget", r.json().get("total") == 1)

r = requests.get(BASE + "/budgets/" + str(bud_id) + "/", headers=ha, timeout=5)
c("Get budget with allocations 200", r.status_code == 200)
c("6 allocations in response", len(r.json()["allocations"]) == 6)

r = requests.get(BASE + "/budgets/?year=2026", headers=ha, timeout=5)
c("Filter by year 2026", r.json().get("total") == 1)

r = requests.get(BASE + "/budgets/?year=2025", headers=ha, timeout=5)
c("Filter year 2025 empty", r.json().get("total") == 0)

print("\n--- Update Budget ---")
r = requests.put(BASE + "/budgets/" + str(bud_id) + "/", json={
    "total_amount": 10000,
    "allocations": [
        {"category": "food", "amount": 3500},
        {"category": "travel", "amount": 2000},
        {"category": "shopping", "amount": 2500},
        {"category": "education", "amount": 1000},
        {"category": "entertainment", "amount": 500},
        {"category": "miscellaneous", "amount": 500},
    ]
}, headers=ha, timeout=5)
c("Update budget 200", r.status_code == 200)
c("Total updated", r.json().get("total_amount") == 10000.0)
new_allocs = {a["category"]: a["amount"] for a in r.json()["allocations"]}
c("Food updated to 3500", new_allocs.get("food") == 3500.0)
c("Travel updated to 2000", new_allocs.get("travel") == 2000.0)

r = requests.put(BASE + "/budgets/" + str(bud_id) + "/", json={"total_amount": -1}, headers=ha, timeout=5)
c("Bad update rejected", r.status_code == 422)

print("\n--- Budget Isolation ---")
r = requests.get(BASE + "/budgets/" + str(bud_id) + "/", headers=hb, timeout=5)
c("Bob cant get Alice budget", r.status_code == 404)

r = requests.put(BASE + "/budgets/" + str(bud_id) + "/", json={"total_amount": 1}, headers=hb, timeout=5)
c("Bob cant update Alice budget", r.status_code == 404)

r = requests.delete(BASE + "/budgets/" + str(bud_id) + "/", headers=hb, timeout=5)
c("Bob cant delete Alice budget", r.status_code == 404)

r = requests.get(BASE + "/budgets/", headers=hb, timeout=5)
c("Bob sees no budgets", r.json().get("total") == 0)

# ══════════════════════════════════════════════════════════════
# 6. DELETE OPERATIONS
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("6. DELETE OPERATIONS")
print("=" * 60)

r = requests.post(BASE + "/incomes/", json={"amount": 500, "source": "pocket_money", "date": "2026-09-16"}, headers=ha, timeout=5)
del_inc = r.json().get("id")
r = requests.delete(BASE + "/incomes/" + str(del_inc) + "/", headers=ha, timeout=5)
c("Delete income 204", r.status_code == 204)
r = requests.get(BASE + "/incomes/" + str(del_inc) + "/", headers=ha, timeout=5)
c("Deleted income gone 404", r.status_code == 404)

r = requests.post(BASE + "/expenses/", json={"amount": 50, "category": "food", "date": "2026-09-16"}, headers=ha, timeout=5)
del_exp = r.json().get("id")
r = requests.delete(BASE + "/expenses/" + str(del_exp) + "/", headers=ha, timeout=5)
c("Delete expense 204", r.status_code == 204)
r = requests.get(BASE + "/expenses/" + str(del_exp) + "/", headers=ha, timeout=5)
c("Deleted expense gone 404", r.status_code == 404)

r = requests.post(BASE + "/budgets/", json={"month": 3, "year": 2026, "total_amount": 5000, "allocations": [{"category": "food", "amount": 5000}]}, headers=ha, timeout=5)
del_bud = r.json().get("id")
r = requests.delete(BASE + "/budgets/" + str(del_bud) + "/", headers=ha, timeout=5)
c("Delete budget 204", r.status_code == 204)
r = requests.get(BASE + "/budgets/" + str(del_bud) + "/", headers=ha, timeout=5)
c("Deleted budget gone 404", r.status_code == 404)

# ══════════════════════════════════════════════════════════════
# 7. END-TO-END FLOW
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("7. END-TO-END FLOW")
print("=" * 60)

print("\n--- Charlie: Fresh user full flow ---")
r = requests.post(BASE + "/incomes/", json={"amount": 20000, "source": "scholarship", "date": "2026-09-01"}, headers=hc, timeout=5)
c("Step 1: Add income", r.status_code == 201)

for cat, amt in [("food", 4000), ("travel", 1500), ("shopping", 2000), ("education", 3000), ("entertainment", 1000), ("miscellaneous", 500)]:
    r = requests.post(BASE + "/expenses/", json={"amount": amt, "category": cat, "date": "2026-09-15"}, headers=hc, timeout=5)
c("Step 2: Add expenses (6 categories)", True)

r = requests.get(BASE + "/transactions/summary/", headers=hc, timeout=5)
s = r.json()
c("Step 3: Dashboard shows income=20000", s["total_income"] == 20000.0)
c("Step 3: Dashboard shows expenses=12000", s["total_expenses"] == 12000.0)
c("Step 3: Balance=8000", s["balance"] == 8000.0)

r = requests.get(BASE + "/transactions/", headers=hc, timeout=5)
c("Step 4: 7 transactions (1 income + 6 expense)", r.json()["total"] == 7)

r = requests.post(BASE + "/budgets/", json={
    "month": 9, "year": 2026, "total_amount": 12000,
    "allocations": [
        {"category": "food", "amount": 4000},
        {"category": "travel", "amount": 1500},
        {"category": "shopping", "amount": 2000},
        {"category": "education", "amount": 3000},
        {"category": "entertainment", "amount": 1000},
        {"category": "miscellaneous", "amount": 500},
    ]
}, headers=hc, timeout=5)
c("Step 5: Create budget 201", r.status_code == 201)

r = requests.get(BASE + "/budgets/", headers=hc, timeout=5)
c("Step 6: View budget", r.json()["total"] == 1)
c("Step 6: Budget has allocations", len(r.json()["budgets"][0]["allocations"]) == 6)

# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY: Passed=" + str(p) + ", Failed=" + str(f))
print("=" * 60)
if f == 0:
    print("\n*** ALL " + str(p) + " TESTS PASSED ***")
    print("Milestone 2 is fully integrated and verified.")
else:
    print("\nFAILED TESTS:")
    for e in errors:
        print("  - " + e)
sys.exit(0 if f == 0 else 1)
