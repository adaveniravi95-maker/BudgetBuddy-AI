import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

print("GET  /           ->", client.get("/").status_code)
print("GET  /health     ->", client.get("/health").status_code)

username = f"smoke{uuid.uuid4().hex[:8]}"
password = "SmokeTest123!"

reg = client.post(
    "/api/auth/register/",
    json={
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
        "password_confirm": password,
        "first_name": "Smoke",
        "last_name": "Test",
    },
)
print("POST /api/auth/register/ ->", reg.status_code)
if reg.status_code >= 400:
    print("  body:", reg.text[:400])
    sys.exit(1)

login = client.post("/api/auth/login/", json={"username": username, "password": password})
print("POST /api/auth/login/    ->", login.status_code)
if login.status_code != 200:
    print("  body:", login.text[:600])
    sys.exit(1)

body = login.json()
print("  token keys:", sorted(body.keys()))

headers = {"Authorization": f"Bearer {body['access']}"}

print("GET  /api/auth/check/    ->", client.get("/api/auth/check/", headers=headers).status_code)

protected = [
    "/api/expenses/",
    "/api/incomes/",
    "/api/transactions/",
    "/api/transactions/summary/",
    "/api/budgets/",
    "/api/savings/",
    "/api/notifications/",
    "/api/notifications/unread/",
    "/api/analytics/",
]
monthly = "/api/reports/monthly/?month=10&year=2026"
print(f"GET  {monthly:32} -> {client.get(monthly, headers=headers).status_code}")

failures = []
for path in protected:
    status_code = client.get(path, headers=headers).status_code
    print(f"GET  {path:32} -> {status_code}")
    if status_code >= 400:
        failures.append(path)

unauth = client.get("/api/expenses/")
print("GET  /api/expenses/ (no auth) ->", unauth.status_code)
if unauth.status_code != 401:
    failures.append("unauthenticated request was not rejected")

print("\nFAILURES:", failures or "none")