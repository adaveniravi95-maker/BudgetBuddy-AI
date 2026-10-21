import requests
import sys

BASE = "http://localhost:8000/api"
s = requests.Session()
s.headers.update({"Content-Type": "application/json"})

p = f = 0
errors = []

def c(name, ok, detail=""):
    global p, f
    if ok:
        p += 1
        print("  [PASS] " + name)
    else:
        f += 1
        errors.append(name)
        print("  [FAIL] " + name + "  " + detail)
    sys.stdout.flush()

def reg(user):
    r = s.post(BASE + "/auth/register/", json={
        "username": user, "email": user + "@test.com",
        "password": "SecurePass123!", "password_confirm": "SecurePass123!"
    }, timeout=10)
    return {"Authorization": "Bearer " + r.json()["tokens"]["access"]}

# ═══ SETUP ═══
ha = reg("alice20")
hb = reg("bob20")
hc = reg("charlie20")

# ═══ 1. AUTH ═══
print("1. AUTH")
r = s.get(BASE + "/auth/check/", headers=ha, timeout=5)
c("Check auth", r.status_code == 200 and r.json()["authenticated"])
r = s.get(BASE + "/auth/profile/", headers=ha, timeout=5)
c("Get profile", r.status_code == 200)
r = s.get(BASE + "/auth/check/", timeout=5)
c("No auth 401", r.status_code == 401)

# ═══ 2. INCOME ═══
print("2. INCOME")
inc_ids = []
for src in ["pocket_money", "scholarship", "freelance"]:
    r = s.post(BASE + "/incomes/", json={"amount": 5000, "source": src, "date": "2026-09-10"}, headers=ha, timeout=5)
    c("Create " + src, r.status_code == 201)
    inc_ids.append(r.json()["id"])

r = s.post(BASE + "/incomes/", json={"amount": -1, "source": "food", "date": "2026-09-10"}, headers=ha, timeout=5)
c("Neg amount", r.status_code == 422)
r = s.post(BASE + "/incomes/", json={"amount": 100, "source": "bad", "date": "2026-09-10"}, headers=ha, timeout=5)
c("Bad source", r.status_code == 422)
r = s.post(BASE + "/incomes/", json={"amount": 100, "date": "2026-09-10"}, headers=ha, timeout=5)
c("Missing source", r.status_code == 422)

r = s.get(BASE + "/incomes/", headers=ha, timeout=5)
c("List 3 incomes", r.json()["total"] == 3)
r = s.get(BASE + "/incomes/" + str(inc_ids[0]) + "/", headers=ha, timeout=5)
c("Get income", r.status_code == 200)
r = s.put(BASE + "/incomes/" + str(inc_ids[0]) + "/", json={"amount": 4000}, headers=ha, timeout=5)
c("Update income", r.status_code == 200 and r.json()["amount"] == 4000.0)
r = s.get(BASE + "/incomes/" + str(inc_ids[0]) + "/", headers=hb, timeout=5)
c("Isolation income", r.status_code == 404)
print("3. EXPENSES")
exp_ids = []
for cat in ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]:
    r = s.post(BASE + "/expenses/", json={"amount": 500, "category": cat, "date": "2026-09-15"}, headers=ha, timeout=5)
    c("Create " + cat, r.status_code == 201)
    exp_ids.append(r.json()["id"])

r = s.post(BASE + "/expenses/", json={"amount": 100, "category": "bad", "date": "2026-09-15"}, headers=ha, timeout=5)
c("Bad category", r.status_code == 422)
r = s.post(BASE + "/expenses/", json={"amount": 100, "date": "2026-09-15"}, headers=ha, timeout=5)
c("Missing category", r.status_code == 422)
r = s.post(BASE + "/expenses/", json={"amount": -50, "category": "food", "date": "2026-09-15"}, headers=ha, timeout=5)
c("Neg amount", r.status_code == 422)

r = s.get(BASE + "/expenses/", headers=ha, timeout=5)
c("List 6 expenses", r.json()["total"] == 6)
cats = set(e["category"] for e in r.json()["expenses"])
c("All 6 categories", len(cats) == 6)
r = s.put(BASE + "/expenses/" + str(exp_ids[0]) + "/", json={"category": "travel"}, headers=ha, timeout=5)
c("Update category", r.status_code == 200 and r.json()["category"] == "travel")
r = s.get(BASE + "/expenses/?category=food", headers=ha, timeout=5)
c("Filter food (updated to travel)", r.json()["total"] == 0)
r = s.get(BASE + "/expenses/?category=travel", headers=ha, timeout=5)
c("Filter travel (has 2)", r.json()["total"] == 2)
r = s.get(BASE + "/expenses/" + str(exp_ids[0]) + "/", headers=hb, timeout=5)
c("Isolation expense", r.status_code == 404)

# ═══ 4. TRANSACTIONS ═══
print("4. TRANSACTIONS")
r = s.get(BASE + "/transactions/summary/", headers=ha, timeout=5)
c("Summary 200", r.status_code == 200)
sm = r.json()
# Income: 4000 (updated) + 5000 + 5000 = 14000
# Expenses: 500 * 6 = 3000
c("Income=14000", sm["total_income"] == 14000.0)
c("Expenses=3000", sm["total_expenses"] == 3000.0)
c("Balance=11000", sm["balance"] == 11000.0)
c("Income count=3", sm["income_count"] == 3)
c("Expense count=6", sm["expense_count"] == 6)
formula = sm["total_income"] - sm["total_expenses"] == sm["balance"]
c("Formula correct", formula)

r = s.get(BASE + "/transactions/", headers=ha, timeout=5)
c("9 transactions", r.json()["total"] == 9)
txs = r.json()["transactions"]
types = set(t["type"] for t in txs)
c("Has income", "income" in types)
c("Has expense", "expense" in types)
dates = [t["date"] for t in txs]
c("Sorted newest", dates == sorted(dates, reverse=True))
# After updating food→travel, 5 unique expense categories remain
ecats = set(t["category"] for t in txs if t["type"] == "expense")
c("5 expense cats (food updated to travel)", len(ecats) == 5)

r = s.get(BASE + "/transactions/?type=income", headers=ha, timeout=5)
c("Filter income", r.json()["total"] == 3)
r = s.get(BASE + "/transactions/?type=expense", headers=ha, timeout=5)
c("Filter expense", r.json()["total"] == 6)
r = s.get(BASE + "/transactions/summary/", headers=hb, timeout=5)
c("Isolation tx", r.json()["total_income"] == 0)

# ═══ 5. BUDGETS ═══
print("5. BUDGETS")
allocs = [
    {"category": "food", "amount": 3000}, {"category": "travel", "amount": 1500},
    {"category": "shopping", "amount": 2500}, {"category": "education", "amount": 1000},
    {"category": "entertainment", "amount": 800}, {"category": "miscellaneous", "amount": 500},
]
r = s.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 9300, "allocations": allocs}, headers=ha, timeout=5)
c("Create budget", r.status_code == 201)
bud = r.json()
bud_id = bud["id"]
c("6 allocations", len(bud["allocations"]) == 6)
amap = {a["category"]: a["amount"] for a in bud["allocations"]}
for cat, amt in [("food", 3000), ("travel", 1500), ("shopping", 2500), ("education", 1000), ("entertainment", 800), ("miscellaneous", 500)]:
    c("Alloc " + cat, amap.get(cat) == amt)

r = s.post(BASE + "/budgets/", json={"month": 13, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=ha, timeout=5)
c("Bad month", r.status_code == 422)
r = s.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": -1, "allocations": [{"category": "food", "amount": 100}]}, headers=ha, timeout=5)
c("Neg total", r.status_code == 422)
r = s.post(BASE + "/budgets/", json={"month": 1, "year": 2026, "total_amount": 1000, "allocations": [{"category": "bad", "amount": 1000}]}, headers=ha, timeout=5)
c("Bad cat budget", r.status_code == 422)
r = s.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=ha, timeout=5)
c("Dup month", r.status_code == 400)

r = s.get(BASE + "/budgets/", headers=ha, timeout=5)
c("List budget", r.json()["total"] == 1)
r = s.get(BASE + "/budgets/" + str(bud_id) + "/", headers=ha, timeout=5)
c("Get budget", r.status_code == 200 and len(r.json()["allocations"]) == 6)
r = s.put(BASE + "/budgets/" + str(bud_id) + "/", json={"total_amount": 10000, "allocations": allocs[:3] + [{"category": "education", "amount": 1200}, {"category": "entertainment", "amount": 800}, {"category": "miscellaneous", "amount": 500}]}, headers=ha, timeout=5)
c("Update budget", r.status_code == 200 and r.json()["total_amount"] == 10000.0)
r = s.get(BASE + "/budgets/" + str(bud_id) + "/", headers=hb, timeout=5)
c("Isolation budget", r.status_code == 404)

# ═══ 6. DELETES ═══
print("6. DELETES")
r = s.post(BASE + "/incomes/", json={"amount": 100, "source": "pocket_money", "date": "2026-09-16"}, headers=ha, timeout=5)
did = r.json()["id"]
r = s.delete(BASE + "/incomes/" + str(did) + "/", headers=ha, timeout=5)
c("Del income", r.status_code == 204)
r = s.get(BASE + "/incomes/" + str(did) + "/", headers=ha, timeout=5)
c("Income gone", r.status_code == 404)

r = s.post(BASE + "/expenses/", json={"amount": 10, "category": "food", "date": "2026-09-16"}, headers=ha, timeout=5)
did = r.json()["id"]
r = s.delete(BASE + "/expenses/" + str(did) + "/", headers=ha, timeout=5)
c("Del expense", r.status_code == 204)
r = s.get(BASE + "/expenses/" + str(did) + "/", headers=ha, timeout=5)
c("Expense gone", r.status_code == 404)

r = s.post(BASE + "/budgets/", json={"month": 5, "year": 2026, "total_amount": 1000, "allocations": [{"category": "food", "amount": 1000}]}, headers=ha, timeout=5)
did = r.json()["id"]
r = s.delete(BASE + "/budgets/" + str(did) + "/", headers=ha, timeout=5)
c("Del budget", r.status_code == 204)
r = s.get(BASE + "/budgets/" + str(did) + "/", headers=ha, timeout=5)
c("Budget gone", r.status_code == 404)

# ═══ 7. E2E FLOW ═══
print("7. E2E FLOW")
r = s.post(BASE + "/incomes/", json={"amount": 20000, "source": "scholarship", "date": "2026-09-01"}, headers=hc, timeout=5)
c("Step1 income", r.status_code == 201)
for cat in ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]:
    r = s.post(BASE + "/expenses/", json={"amount": 1000, "category": cat, "date": "2026-09-15"}, headers=hc, timeout=5)
c("Step2 expenses", r.status_code == 201)
r = s.get(BASE + "/transactions/summary/", headers=hc, timeout=5)
sm = r.json()
c("Step3 dash income=20000", sm["total_income"] == 20000.0)
c("Step3 dash exp=6000", sm["total_expenses"] == 6000.0)
c("Step3 balance=14000", sm["balance"] == 14000.0)
r = s.get(BASE + "/transactions/", headers=hc, timeout=5)
c("Step4 7 txns", r.json()["total"] == 7)
r = s.post(BASE + "/budgets/", json={"month": 9, "year": 2026, "total_amount": 6000, "allocations": [{"category": c, "amount": 1000} for c in ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]]}, headers=hc, timeout=5)
c("Step5 budget", r.status_code == 201)
r = s.get(BASE + "/budgets/", headers=hc, timeout=5)
c("Step6 view budget", r.json()["total"] == 1 and len(r.json()["budgets"][0]["allocations"]) == 6)

# ═══ SUMMARY ═══
print("\n" + "=" * 60)
print("RESULT: Passed=" + str(p) + ", Failed=" + str(f))
if f == 0:
    print("*** ALL " + str(p) + " TESTS PASSED ***")
else:
    for e in errors:
        print("  FAILED: " + e)
sys.exit(0 if f == 0 else 1)
