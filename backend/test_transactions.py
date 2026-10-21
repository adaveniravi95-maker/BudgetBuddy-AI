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
r = requests.post(BASE + "/auth/register/", json={"username": "tx1", "email": "tx1@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
token = r.json()["tokens"]["access"]
h = {"Authorization": "Bearer " + token}

# Create income
requests.post(BASE + "/incomes/", json={"amount": 10000, "source": "scholarship", "description": "Fall scholarship", "date": "2026-09-01"}, headers=h, timeout=5)
requests.post(BASE + "/incomes/", json={"amount": 5000, "source": "freelance", "description": "Web project", "date": "2026-09-05"}, headers=h, timeout=5)
requests.post(BASE + "/incomes/", json={"amount": 2000, "source": "pocket_money", "description": "Monthly pocket", "date": "2026-09-10"}, headers=h, timeout=5)

# Create expenses
requests.post(BASE + "/expenses/", json={"amount": 1500, "category": "food", "description": "Groceries", "date": "2026-09-02"}, headers=h, timeout=5)
requests.post(BASE + "/expenses/", json={"amount": 800, "category": "travel", "description": "Bus pass", "date": "2026-09-06"}, headers=h, timeout=5)
requests.post(BASE + "/expenses/", json={"amount": 3000, "category": "shopping", "description": "Books", "date": "2026-09-12"}, headers=h, timeout=5)

print("=== TRANSACTION SUMMARY ===")
r = requests.get(BASE + "/transactions/summary/", headers=h, timeout=5)
c("Summary 200", r.status_code == 200)
d = r.json()
c("Total income 17000", d.get("total_income") == 17000.0, str(d.get("total_income")))
c("Total expenses 5300", d.get("total_expenses") == 5300.0, str(d.get("total_expenses")))
c("Balance 11700", d.get("balance") == 11700.0, str(d.get("balance")))
c("Income count 3", d.get("income_count") == 3)
c("Expense count 3", d.get("expense_count") == 3)

print("\n=== FORMULA CHECK ===")
calc = d["total_income"] - d["total_expenses"]
c("Income - Expenses = Balance", calc == d["balance"], str(calc) + " vs " + str(d["balance"]))

print("\n=== TRANSACTION HISTORY (all) ===")
r = requests.get(BASE + "/transactions/", headers=h, timeout=5)
c("List 200", r.status_code == 200)
tx = r.json()
c("6 transactions", tx.get("total") == 6, str(tx.get("total")))

# Check chronological order (newest first)
dates = [t["date"] for t in tx["transactions"]]
c("Chronological order", dates == sorted(dates, reverse=True))

# Check types
types_seen = set(t["type"] for t in tx["transactions"])
c("Has income type", "income" in types_seen)
c("Has expense type", "expense" in types_seen)

print("\n=== FILTER BY TYPE ===")
r = requests.get(BASE + "/transactions/?type=income", headers=h, timeout=5)
c("Income only", r.json().get("total") == 3, str(r.json().get("total")))

r = requests.get(BASE + "/transactions/?type=expense", headers=h, timeout=5)
c("Expense only", r.json().get("total") == 3, str(r.json().get("total")))

print("\n=== FILTER BY DATE ===")
r = requests.get(BASE + "/transactions/?start_date=2026-09-05&end_date=2026-09-10", headers=h, timeout=5)
c("Date range filter", r.json().get("total") == 3, str(r.json().get("total")))

print("\n=== RECENT ACTIVITY (top 3) ===")
r = requests.get(BASE + "/transactions/", headers=h, timeout=5)
top3 = r.json()["transactions"][:3]
c("3 recent items", len(top3) == 3)
c("Most recent is newest", top3[0]["date"] >= top3[1]["date"])

print("\n=== USER ISOLATION ===")
r2 = requests.post(BASE + "/auth/register/", json={"username": "tx2", "email": "tx2@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
h2 = {"Authorization": "Bearer " + r2.json()["tokens"]["access"]}

r = requests.get(BASE + "/transactions/summary/", headers=h2, timeout=5)
c("User2 summary empty", r.json().get("total_income") == 0 and r.json().get("total_expenses") == 0)

r = requests.get(BASE + "/transactions/", headers=h2, timeout=5)
c("User2 history empty", r.json().get("total") == 0)

print("\n" + "=" * 40)
print("Passed: " + str(p) + ", Failed: " + str(f))
if f == 0:
    print("ALL TRANSACTION TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(0 if f == 0 else 1)
