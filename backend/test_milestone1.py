"""
Milestone 1 - Full Integration Test
Tests frontend-backend connection, auth flow, and failure cases
"""
import requests
import sys
from datetime import datetime

BASE = 'http://localhost:8000/api/auth'
FRONTEND = 'http://localhost:3000'
ts = datetime.now().strftime("%H%M%S")

passed = 0
failed = 0

def check(name, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        print(f'  [FAIL] {name}  {detail}')

print('=' * 60)
print('TASK 1: BACKEND FOUNDATION')
print('=' * 60)
try:
    r = requests.get('http://localhost:8000/health', timeout=5)
    check('Backend running', r.status_code == 200)
except Exception as e:
    check('Backend running', False, str(e))

try:
    r = requests.get('http://localhost:8000/docs', timeout=5)
    check('API docs accessible', r.status_code == 200)
except Exception as e:
    check('API docs accessible', False, str(e))

try:
    r = requests.get('http://localhost:8000/', timeout=5)
    check('Root endpoint', r.status_code == 200)
except Exception as e:
    check('Root endpoint', False, str(e))

print()
print('=' * 60)
print('TASK 4: FRONTEND-BACKEND INTEGRATION')
print('=' * 60)
try:
    r = requests.get(FRONTEND, timeout=5)
    check('Frontend running', r.status_code == 200)
except Exception as e:
    check('Frontend running', False, str(e))

try:
    r = requests.options(
        'http://localhost:8000/api/auth/login/',
        headers={'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST'},
        timeout=5
    )
    check('CORS configured', 'access-control-allow-origin' in r.headers)
except Exception as e:
    check('CORS configured', False, str(e))

print()
print('=' * 60)
print('TASK 2: JWT AUTHENTICATION FLOW')
print('=' * 60)
user_data = {
    'username': f'milestone_{ts}',
    'email': f'milestone_{ts}@test.com',
    'password': 'SecurePass123!',
    'password_confirm': 'SecurePass123!',
    'first_name': 'Milestone',
    'last_name': 'User'
}
r = requests.post(f'{BASE}/register/', json=user_data)
check('Registration (201)', r.status_code == 201, f'{r.status_code} {r.text[:120]}')
reg_tokens = r.json().get('tokens', {}) if r.status_code == 201 else {}

r = requests.post(f'{BASE}/login/', json={'username': user_data['username'], 'password': user_data['password']})
check('Login (200)', r.status_code == 200, f'{r.status_code} {r.text[:120]}')
login_tokens = r.json() if r.status_code == 200 else {}

if login_tokens.get('access'):
    h = {'Authorization': 'Bearer ' + login_tokens['access']}
    r = requests.get(f'{BASE}/check/', headers=h)
    check('Protected endpoint with JWT (200)', r.status_code == 200, f'{r.status_code}')
    if r.status_code == 200:
        d = r.json()
        check('User identified', d.get('user', {}).get('username') == user_data['username'])
        check('authenticated=True', d.get('authenticated') is True)

if login_tokens.get('refresh'):
    r = requests.post(f'{BASE}/token/refresh/', json={'refresh': login_tokens['refresh']})
    check('Token refresh (200)', r.status_code == 200, f'{r.status_code}')

if login_tokens.get('access'):
    h = {'Authorization': 'Bearer ' + login_tokens['access']}
    r = requests.get(f'{BASE}/profile/', headers=h)
    check('Profile endpoint (200)', r.status_code == 200, f'{r.status_code}')

print()
print('=' * 60)
print('TASK 5: FAILURE CASES')
print('=' * 60)
r = requests.post(f'{BASE}/register/', json=user_data)
check('Duplicate username rejected (400)', r.status_code == 400, f'{r.status_code}')

bad_user = dict(user_data, username='dup_test_' + ts, password_confirm='DifferentPass!')
r = requests.post(f'{BASE}/register/', json=bad_user)
check('Password mismatch rejected (422)', r.status_code == 422, f'{r.status_code}')

weak_user = dict(user_data, username='weak_' + ts, password='123', password_confirm='123')
r = requests.post(f'{BASE}/register/', json=weak_user)
check('Weak password rejected (422)', r.status_code == 422, f'{r.status_code}')

r = requests.post(f'{BASE}/login/', json={'username': user_data['username'], 'password': 'wrong'})
check('Wrong password rejected (401)', r.status_code == 401, f'{r.status_code}')

r = requests.post(f'{BASE}/login/', json={'username': 'nobody', 'password': 'x'})
check('Unknown user rejected (401)', r.status_code == 401, f'{r.status_code}')

r = requests.get(f'{BASE}/check/')
check('No auth rejected (401)', r.status_code == 401, f'{r.status_code}')

r = requests.get(f'{BASE}/check/', headers={'Authorization': 'Bearer invalidtoken'})
check('Invalid JWT rejected (401)', r.status_code == 401, f'{r.status_code}')

r = requests.post(f'{BASE}/register/', json={})
check('Empty body rejected (422)', r.status_code == 422, f'{r.status_code}')

print()
print('=' * 60)
print('FINAL RESULTS')
print('=' * 60)
print(f'Passed: {passed}, Failed: {failed}')
if failed == 0:
    print()
    print('ALL TESTS PASSED!')
    print()
    print('MILESTONE 1 CHECKLIST:')
    print('  [x] Backend project runs correctly')
    print('  [x] Database connection works')
    print('  [x] Schema are applied')
    print('  [x] Core models present (User, Profile)')
    print('  [x] JWT authentication configured')
    print('  [x] Registration works')
    print('  [x] Login works')
    print('  [x] Protected endpoint works')
    print('  [x] Unauthenticated access rejected')
    print('  [x] React frontend skeleton complete')
    print('  [x] Frontend connected to backend')
    print('  [x] CORS working')
    print('  [x] Failure cases handled')
else:
    print('SOME TESTS FAILED')
sys.exit(0 if failed == 0 else 1)
