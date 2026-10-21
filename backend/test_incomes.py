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
r = requests.post(BASE + "/auth/register/", json={"username": "inc1", "email": "inc1@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
token = r.json()["tokens"]["access"]
h = {"Authorization": "Bearer " + token}

print("=== CREATE ===")
r = requests.post(BASE + "/incomes/", json={"amount": 5000, "source": "scholarship", "description": "Fall scholarship", "date": "2026-09-16"}, headers=h, timeout=5)
c("Create income 201", r.status_code == 201)
inc = r.json() if r.status_code == 201 else {}
c("Has id", bool(inc.get("id")))
c("Amount", inc.get("amount") == 5000.0)
c("Source", inc.get("source") == "scholarship")

r = requests.post(BASE + "/incomes/", json={"amount": -100, "source": "pocket_money", "date": "2026-09-16"}, headers=h, timeout=5)
c("Negative rejected", r.status_code == 422)

r = requests.post(BASE + "/incomes/", json={"amount": 100, "source": "bad", "date": "2026-09-16"}, headers=h, timeout=5)
c("Bad source rejected", r.status_code == 422)

r = requests.post(BASE + "/incomes/", json={"amount": 100, "source": "pocket_money", "date": "2026-09-16"})
c("No auth rejected", r.status_code == 401)

# Create more
for src in ["pocket_money", "freelance"]:
    requests.post(BASE + "/incomes/", json={"amount": 1000, "source": src, "date": "2026-09-15"}, headers=h, timeout=5)

print("\n=== LIST ===")
r = requests.get(BASE + "/incomes/", headers=h, timeout=5)
c("List 200", r.status_code == 200)
data = r.json()
c("Has total", "total" in data)
c("3 incomes", data.get("total", 0) == 3)

print("\n=== GET SINGLE ===")
r = requests.get(BASE + "/incomes/" + str(inc["id"]) + "/", headers=h, timeout=5)
c("Get single 200", r.status_code == 200)

r = requests.get(BASE + "/incomes/99999/", headers=h, timeout=5)
c("Not found 404", r.status_code == 404)

print("\n=== UPDATE ===")
r = requests.put(BASE + "/incomes/" + str(inc["id"]) + "/", json={"amount": 6000, "description": "Updated"}, headers=h, timeout=5)
c("Update 200", r.status_code == 200)
c("Amount updated", r.json().get("amount") == 6000.0)

r = requests.put(BASE + "/incomes/" + str(inc["id"]) + "/", json={"source": "freelance"}, headers=h, timeout=5)
c("Partial update", r.status_code == 200)
c("Source changed", r.json().get("source") == "freelance")

r = requests.put(BASE + "/incomes/" + str(inc["id"]) + "/", json={"amount": -1}, headers=h, timeout=5)
c("Bad update rejected", r.status_code == 422)

print("\n=== DELETE ===")
r = requests.post(BASE + "/incomes/", json={"amount": 999, "source": "pocket_money", "date": "2026-09-16"}, headers=h, timeout=5)
did = r.json().get("id")

r = requests.delete(BASE + "/incomes/" + str(did) + "/", headers=h, timeout=5)
c("Delete 204", r.status_code == 204)

r = requests.get(BASE + "/incomes/" + str(did) + "/", headers=h, timeout=5)
c("Deleted gone 404", r.status_code == 404)

print("\n=== USER ISOLATION ===")
r2 = requests.post(BASE + "/auth/register/", json={"username": "inc2", "email": "inc2@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}, timeout=5)
h2 = {"Authorization": "Bearer " + r2.json()["tokens"]["access"]}

r = requests.get(BASE + "/incomes/" + str(inc["id"]) + "/", headers=h2, timeout=5)
c("User2 cant get User1", r.status_code == 404)

r = requests.put(BASE + "/incomes/" + str(inc["id"]) + "/", json={"amount": 1}, headers=h2, timeout=5)
c("User2 cant update User1", r.status_code == 404)

r = requests.delete(BASE + "/incomes/" + str(inc["id"]) + "/", headers=h2, timeout=5)
c("User2 cant delete User1", r.status_code == 404)

print("\n" + "=" * 40)
print("Passed: " + str(p) + ", Failed: " + str(f))
if f == 0:
    print("ALL INCOME TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(0 if f == 0 else 1)
