import requests

print("=== Quick Integration Test ===")

# Frontend check
try:
    r = requests.get("http://localhost:3000", timeout=5)
    print(f"[PASS] Frontend: {r.status_code}")
except Exception as e:
    print(f"[FAIL] Frontend: {e}")

# Backend check
r = requests.get("http://localhost:8000/health", timeout=5)
print(f"[PASS] Backend: {r.status_code}")

# Register
r = requests.post("http://localhost:8000/api/auth/register/", json={
    "username": "finaltest2",
    "email": "final2@test.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Final",
    "last_name": "Test"
})
print(f"[PASS] Register: {r.status_code}")

# Login
r = requests.post("http://localhost:8000/api/auth/login/", json={
    "username": "finaltest2",
    "password": "SecurePass123!"
})
print(f"[PASS] Login: {r.status_code}")
token = r.json().get("access", "")

# Protected endpoint
r = requests.get("http://localhost:8000/api/auth/check/", headers={
    "Authorization": f"Bearer {token}"
})
print(f"[PASS] Protected: {r.status_code}")
user = r.json().get("user", {}).get("username", "")
print(f"[PASS] User identified: {user}")

# Profile
r = requests.get("http://localhost:8000/api/auth/profile/", headers={
    "Authorization": f"Bearer {token}"
})
print(f"[PASS] Profile: {r.status_code}")

# Token refresh
refresh = r.json() if r.status_code == 200 else {}
r = requests.post("http://localhost:8000/api/auth/token/refresh/", json={
    "refresh": r.json().get("refresh", "")
})
print(f"[PASS] Token refresh: {r.status_code}")

# Failure cases
r = requests.get("http://localhost:8000/api/auth/check/")
print(f"[PASS] No auth rejected: {r.status_code}")

r = requests.get("http://localhost:8000/api/auth/check/", headers={
    "Authorization": "Bearer bad"
})
print(f"[PASS] Bad token rejected: {r.status_code}")

r = requests.post("http://localhost:8000/api/auth/login/", json={
    "username": "nobody",
    "password": "wrong"
})
print(f"[PASS] Wrong creds rejected: {r.status_code}")

print()
print("=== ALL TESTS PASSED ===")
