"""
BudgetBuddy FastAPI Authentication Flow Test
"""
import requests
import sys
from datetime import datetime

BASE_URL = 'http://localhost:8000/api/auth'
ts = datetime.now().strftime("%H%M%S")
TEST_USER = {
    'username': f'testuser_{ts}',
    'email': f'test_{ts}@test.com',
    'password': 'SecurePass123!',
    'password_confirm': 'SecurePass123!',
    'first_name': 'Test',
    'last_name': 'User'
}

passed = 0
failed = 0

def check(name, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'[PASS] {name}')
    else:
        failed += 1
        print(f'[FAIL] {name}  {detail}')

def main():
    print('=== TASK 1: REGISTRATION ===')
    r = requests.post(f'{BASE_URL}/register/', json=TEST_USER)
    check('Register returns 201', r.status_code == 201, f'got {r.status_code}: {r.text[:120]}')
    d = r.json() if r.status_code == 201 else {}
    check('Response has user', 'user' in d)
    check('Response has tokens', 'tokens' in d)
    check('Password not leaked', 'password' not in d.get('user', {}))

    r = requests.post(f'{BASE_URL}/register/', json=TEST_USER)
    check('Duplicate username rejected (400)', r.status_code == 400, f'got {r.status_code}')

    bad_user = dict(TEST_USER, username='mismatch', password_confirm='DifferentPass!')
    r = requests.post(f'{BASE_URL}/register/', json=bad_user)
    check('Password mismatch rejected (422)', r.status_code == 422, f'got {r.status_code}')

    r = requests.post(f'{BASE_URL}/register/', json={})
    check('Missing fields rejected (422)', r.status_code == 422, f'got {r.status_code}')

    print()
    print('=== TASK 2: LOGIN ===')
    r = requests.post(f'{BASE_URL}/login/', json={'username': TEST_USER['username'], 'password': TEST_USER['password']})
    check('Login returns 200', r.status_code == 200, f'got {r.status_code}: {r.text[:120]}')
    tokens = r.json() if r.status_code == 200 else None
    if tokens:
        check('Login has access token', 'access' in tokens)
        check('Login has refresh token', 'refresh' in tokens)
        check('Login has user data', 'user' in tokens)

    r = requests.post(f'{BASE_URL}/login/', json={'username': TEST_USER['username'], 'password': 'wrong'})
    check('Wrong password rejected (401)', r.status_code == 401, f'got {r.status_code}')

    r = requests.post(f'{BASE_URL}/login/', json={'username': 'nobody', 'password': 'x'})
    check('Unknown user rejected (401)', r.status_code == 401, f'got {r.status_code}')

    r = requests.post(f'{BASE_URL}/login/', json={})
    check('Empty credentials rejected (4xx)', r.status_code >= 400, f'got {r.status_code}')

    print()
    print('=== TASK 3: PROTECTED ENDPOINT ===')
    if tokens:
        h = {'Authorization': f'Bearer {tokens["access"]}'}

        r = requests.get(f'{BASE_URL}/check/', headers=h)
        check('Valid JWT accepted (200)', r.status_code == 200, f'got {r.status_code}: {r.text[:120]}')
        if r.status_code == 200:
            d = r.json()
            check('authenticated=True', d.get('authenticated') is True)
            check('Correct user identified', d.get('user', {}).get('username') == TEST_USER['username'])

        r = requests.get(f'{BASE_URL}/check/')
        check('No auth rejected (401)', r.status_code == 401, f'got {r.status_code}')

        r = requests.get(f'{BASE_URL}/check/', headers={'Authorization': 'Bearer invalidtoken123'})
        check('Invalid JWT rejected (401)', r.status_code == 401, f'got {r.status_code}')

        r = requests.get(f'{BASE_URL}/check/', headers={'Authorization': 'InvalidFormat'})
        check('Malformed header rejected (4xx)', r.status_code >= 400, f'got {r.status_code}')

        r = requests.get(f'{BASE_URL}/profile/', headers=h)
        check('Profile returns 200', r.status_code == 200, f'got {r.status_code}')
        if r.status_code == 200:
            check('Profile shows correct user', r.json().get('username') == TEST_USER['username'])

    print()
    print('=== BONUS: TOKEN REFRESH ===')
    if tokens and 'refresh' in tokens:
        r = requests.post(f'{BASE_URL}/token/refresh/', json={'refresh': tokens['refresh']})
        check('Token refresh returns 200', r.status_code == 200, f'got {r.status_code}: {r.text[:120]}')

    print()
    print('=' * 50)
    print(f'Results: {passed} passed, {failed} failed')
    if failed == 0:
        print('ALL TESTS PASSED')
        print()
        print('Definition of Done:')
        print('  [x] Registration API works')
        print('  [x] Login API works')
        print('  [x] JWT authentication configured')
        print('  [x] Valid token issued after login')
        print('  [x] Protected endpoint works')
        print('  [x] Unauthenticated access rejected')
        print('  [x] Authenticated user identified')
        print('  [x] Success and failure cases tested')
    else:
        print('SOME TESTS FAILED')
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
