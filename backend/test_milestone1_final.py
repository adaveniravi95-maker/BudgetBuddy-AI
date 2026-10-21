"""
Milestone 1 Final Verification
Complete test of all Milestone 1 requirements
"""
import requests
import sys
from datetime import datetime

BASE = 'http://localhost:8000/api/auth'
FRONTEND = 'http://localhost:3000'
ts = datetime.now().strftime("%H%M%S")

passed = 0
failed = 0
total = 0

def check(name, cond, detail=''):
    global passed, failed, total
    total += 1
    if cond:
        passed += 1
        print(f'  [{passed:2d}] PASS  {name}')
    else:
        failed += 1
        print(f'  [  ] FAIL  {name}  {detail}')

print()
print('=' * 60)
print('  MILESTONE 1 - FINAL VERIFICATION')
print('=' * 60)

# ── Backend Foundation ──────────────────────────────────────
print()
print('--- Backend Foundation ---')

try:
    r = requests.get('http://localhost:8000/health', timeout=5)
    check('Backend server running', r.status_code == 200)
except Exception as e:
    check('Backend server running', False, str(e))

try:
    r = requests.get('http://localhost:8000/', timeout=5)
    check('Root endpoint responds', r.status_code == 200)
except Exception as e:
    check('Root endpoint responds', False, str(e))

try:
    r = requests.get('http://localhost:8000/docs', timeout=5)
    check('API documentation accessible', r.status_code == 200)
except Exception as e:
    check('API documentation accessible', False, str(e))

# ── Database ────────────────────────────────────────────────
print()
print('--- Database ---')

from app.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
check('Users table exists', 'users' in tables)
check('Profiles table exists', 'profiles' in tables)

user_cols = [c['name'] for c in inspector.get_columns('users')]
check('User has username column', 'username' in user_cols)
check('User has email column', 'email' in user_cols)
check('User has hashed_password column', 'hashed_password' in user_cols)
check('User has role column', 'role' in user_cols)

# ── Frontend ────────────────────────────────────────────────
print()
print('--- Frontend ---')

try:
    r = requests.get(FRONTEND, timeout=5)
    check('React app running', r.status_code == 200)
    check('Serves HTML', 'html' in r.headers.get('content-type', ''))
except Exception as e:
    check('React app running', False, str(e))

# ── CORS ────────────────────────────────────────────────────
print()
print('--- CORS ---')

try:
    r = requests.options(
        'http://localhost:8000/api/auth/login/',
        headers={'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST'},
        timeout=5
    )
    check('CORS allows origin', 'access-control-allow-origin' in r.headers)
except Exception as e:
    check('CORS allows origin', False, str(e))

# ── Registration ────────────────────────────────────────────
print()
print('--- Registration API ---')

user1 = {
    'username': f'user1_{ts}',
    'email': f'user1_{ts}@test.com',
    'password': 'SecurePass123!',
    'password_confirm': 'SecurePass123!',
    'first_name': 'Test',
    'last_name': 'User1'
}
r = requests.post(f'{BASE}/register/', json=user1)
check('Register returns 201', r.status_code == 201)
data = r.json() if r.status_code == 201 else {}
check('Response has user object', 'user' in data)
check('Response has tokens', 'tokens' in data)
check('Password not leaked', 'password' not in str(data))
check('Username correct', data.get('user', {}).get('username') == user1['username'])
check('Email correct', data.get('user', {}).get('email') == user1['email'])
check('Role assigned', data.get('user', {}).get('role') == 'student')

# ── Login ───────────────────────────────────────────────────
print()
print('--- Login API ---')

r = requests.post(f'{BASE}/login/', json={'username': user1['username'], 'password': user1['password']})
check('Login returns 200', r.status_code == 200)
login_data = r.json() if r.status_code == 200 else {}
check('Access token issued', bool(login_data.get('access')))
check('Refresh token issued', bool(login_data.get('refresh')))
check('User data returned', 'user' in login_data)

# ── Protected Endpoints ─────────────────────────────────────
print()
print('--- Protected Endpoints ---')

token = login_data.get('access', '')
h = {'Authorization': f'Bearer {token}'}

r = requests.get(f'{BASE}/check/', headers=h)
check('Check endpoint accepts JWT', r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    check('authenticated flag True', d.get('authenticated') is True)
    check('User identified by backend', d.get('user', {}).get('username') == user1['username'])

r = requests.get(f'{BASE}/profile/', headers=h)
check('Profile endpoint works', r.status_code == 200)

r = requests.post(f'{BASE}/token/refresh/', json={'refresh': login_data.get('refresh', '')})
check('Token refresh works', r.status_code == 200)

# ── Unauthenticated Rejection ───────────────────────────────
print()
print('--- Unauthenticated Rejection ---')

r = requests.get(f'{BASE}/check/')
check('No token -> 401', r.status_code == 401)

r = requests.get(f'{BASE}/check/', headers={'Authorization': 'Bearer invalidtoken'})
check('Invalid token -> 401', r.status_code == 401)

r = requests.get(f'{BASE}/check/', headers={'Authorization': 'InvalidFormat'})
check('Malformed header -> 401/403', r.status_code in [401, 403])

r = requests.get(f'{BASE}/profile/')
check('Profile without auth -> 401', r.status_code == 401)

# ── Failure Cases ───────────────────────────────────────────
print()
print('--- Failure Cases ---')

r = requests.post(f'{BASE}/register/', json=user1)
check('Duplicate username rejected', r.status_code == 400)

r = requests.post(f'{BASE}/register/', json={})
check('Empty body rejected', r.status_code == 422)

bad = dict(user1, username='x', password='short', password_confirm='short')
r = requests.post(f'{BASE}/register/', json=bad)
check('Short password rejected', r.status_code == 422)

mismatch = dict(user1, username='mismatch_' + ts, password_confirm='DifferentPass!')
r = requests.post(f'{BASE}/register/', json=mismatch)
check('Password mismatch rejected', r.status_code == 422)

r = requests.post(f'{BASE}/login/', json={'username': user1['username'], 'password': 'wrong'})
check('Wrong password -> 401', r.status_code == 401)

r = requests.post(f'{BASE}/login/', json={'username': 'nobody', 'password': 'x'})
check('Unknown user -> 401', r.status_code == 401)

r = requests.post(f'{BASE}/login/', json={})
check('Empty login -> 400/422', r.status_code in [400, 422])

# ── Summary ─────────────────────────────────────────────────
print()
print('=' * 60)
print(f'  RESULTS: {passed}/{total} passed, {failed} failed')
print('=' * 60)

if failed == 0:
    print()
    print('  ALL TESTS PASSED!')
    print()
    print('  MILESTONE 1 CHECKLIST:')
    print('  [x] Backend project runs correctly')
    print('  [x] Database connection works')
    print('  [x] Schema applied (users, profiles)')
    print('  [x] Core models present (User, Profile)')
    print('  [x] JWT authentication configured')
    print('  [x] Registration works')
    print('  [x] Login works')
    print('  [x] Protected endpoint works')
    print('  [x] Unauthenticated access rejected')
    print('  [x] React frontend skeleton complete')
    print('  [x] Frontend connected to backend')
    print('  [x] Failure cases handled')
    print()
    print('  MILESTONE 1 COMPLETE!')
else:
    print()
    print('  SOME TESTS FAILED - Review above')

print('=' * 60)
sys.exit(0 if failed == 0 else 1)
