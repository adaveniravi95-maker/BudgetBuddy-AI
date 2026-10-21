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

print("=== TASK 1: CREATE ===")
r = requests.post(BASE + "/auth/register/", json={"username": "et1", "email": "et1@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"})
token = r.json()["tokens"]["access"]
h = {"Authorization": "Bearer " + token}

r = requests.post(BASE + "/expenses/", json={"amount": 250.50, "category": "food", "description": "Lunch", "date": "2026-09-16"}, headers=h)
c("Create 201", r.status_code == 201)
d = r.json() if r.status_code == 201 else {}
c("Has id", bool(d.get("id")))
c("Amount", d.get("amount") == 250.50)
c("Category", d.get("category") == "food")
c("Description", d.get("description") == "Lunch")

r = requests.post(BASE + "/expenses/", json={"amount": -50, "category": "food", "date": "2026-09-16"}, headers=h)
c("Negative rejected", r.status_code == 422)

r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": "bad", "date": "2026-09-16"}, headers=h)
c("Bad category rejected", r.status_code == 422)

r = requests.post(BASE + "/expenses/", json={"amount": 100, "category": "food", "date": "2026-09-16"})
c("No auth rejected", r.status_code == 401)

# Create more for list test
for cat in ["travel", "shopping", "education", "entertainment", "miscellaneous"]:
    requests.post(BASE + "/expenses/", json={"amount": 100, "category": cat, "date": "2026-09-16"}, headers=h)

print()
print("=== TASK 2: RETRIEVE ===")
r = requests.get(BASE + "/expenses/", headers=h)
c("List 200", r.status_code == 200)
data = r.json()
c("Has total", "total" in data)
c("Multiple expenses", data.get("total", 0) >= 6)

r = requests.get(BASE + "/expenses/" + str(d["id"]), headers=h)
c("Get single 200", r.status_code == 200)

r = requests.get(BASE + "/expenses/99999", headers=h)
c("Not found 404", r.status_code == 404)

print()
print("=== TASK 3: UPDATE ===")
r = requests.put(BASE + "/expenses/" + str(d["id"]), json={"amount": 300, "description": "Updated"}, headers=h)
c("Update 200", r.status_code == 200)
c("Amount updated", r.json().get("amount") == 300)
c("Desc updated", r.json().get("description") == "Updated")

r = requests.put(BASE + "/expenses/" + str(d["id"]), json={"category": "shopping"}, headers=h)
c("Partial update", r.status_code == 200)
c("Category changed", r.json().get("category") == "shopping")

r = requests.put(BASE + "/expenses/" + str(d["id"]), json={"amount": -1}, headers=h)
c("Bad update rejected", r.status_code == 422)

print()
print("=== TASK 4: DELETE ===")
r = requests.post(BASE + "/expenses/", json={"amount": 99, "category": "food", "date": "2026-09-16"}, headers=h)
did = r.json().get("id")

r = requests.delete(BASE + "/expenses/" + str(did), headers=h)
c("Delete 204", r.status_code == 204)

r = requests.get(BASE + "/expenses/" + str(did), headers=h)
c("Deleted gone 404", r.status_code == 404)

r = requests.delete(BASE + "/expenses/99999", headers=h)
c("Delete nonexistent 404", r.status_code == 404)

print()
print("=== TASK 5: USER ISOLATION ===")
r2 = requests.post(BASE + "/auth/register/", json={"username": "et2", "email": "et2@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"})
h2 = {"Authorization": "Bearer " + r2.json()["tokens"]["access"]}

r = requests.post(BASE + "/expenses/", json={"amount": 500, "category": "food", "description": "Private", "date": "2026-09-16"}, headers=h)
pid = r.json().get("id")

r = requests.get(BASE + "/expenses/" + str(pid), headers=h2)
c("User2 cant get User1", r.status_code == 404)

r = requests.put(BASE + "/expenses/" + str(pid), json={"amount": 1}, headers=h2)
c("User2 cant update User1", r.status_code == 404)

r = requests.delete(BASE + "/expenses/" + str(pid), headers=h2)
c("User2 cant delete User1", r.status_code == 404)

r = requests.get(BASE + "/expenses/" + str(pid), headers=h)
c("User1 can get own", r.status_code == 200)

r = requests.get(BASE + "/expenses/", headers=h2)
u2_ids = [e["id"] for e in r.json().get("expenses", [])]
c("User2 list excludes User1", pid not in u2_ids)

print()
print("=" * 40)
print("Passed: " + str(p) + ", Failed: " + str(f))
if f == 0:
    print("ALL EXPENSE TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(0 if f == 0 else 1)
