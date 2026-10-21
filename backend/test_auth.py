"""
BudgetBuddy Authentication Test Script
Run this script to verify all authentication scenarios.
Usage: python test_auth.py
"""

import requests
import json
import sys

BASE_URL = 'http://localhost:8000/api'

# Test data
TEST_USER = {
    'username': 'authuser1',
    'email': 'authuser1@test.com',
    'password': 'SecurePass123!',
    'password_confirm': 'SecurePass123!',
    'first_name': 'Auth',
    'last_name': 'User'
}

TEST_USER_2 = {
    'username': 'authuser2',
    'email': 'authuser2@test.com',
    'password': 'SecurePass456!',
    'password_confirm': 'SecurePass456!',
    'first_name': 'Auth',
    'last_name': 'User2'
}


def print_test(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"       {details}")
    return passed


def test_registration():
    print("\n=== Testing User Registration ===")
    
    # Test 1: Successful registration
    response = requests.post(f"{BASE_URL}/auth/register/", json=TEST_USER)
    passed = response.status_code == 201
    if passed:
        data = response.json()
        print_test("Register new user", True, f"User ID: {data['user']['id']}")
    else:
        print_test("Register new user", False, f"Status: {response.status_code}, Error: {response.text}")
    
    # Test 2: Duplicate username
    response = requests.post(f"{BASE_URL}/auth/register/", json=TEST_USER)
    passed = response.status_code == 400
    print_test("Reject duplicate username", passed, f"Status: {response.status_code}")
    
    # Test 3: Password mismatch
    invalid_user = TEST_USER.copy()
    invalid_user['username'] = 'invaliduser'
    invalid_user['password_confirm'] = 'DifferentPass123!'
    response = requests.post(f"{BASE_URL}/auth/register/", json=invalid_user)
    passed = response.status_code == 400
    print_test("Reject password mismatch", passed, f"Status: {response.status_code}")
    
    # Test 4: Weak password
    weak_user = TEST_USER.copy()
    weak_user['username'] = 'weakuser'
    weak_user['password'] = '123'
    weak_user['password_confirm'] = '123'
    response = requests.post(f"{BASE_URL}/auth/register/", json=weak_user)
    passed = response.status_code == 400
    print_test("Reject weak password", passed, f"Status: {response.status_code}")
    
    # Register second user
    requests.post(f"{BASE_URL}/auth/register/", json=TEST_USER_2)


def test_login():
    print("\n=== Testing Login ===")
    
    # Test 1: Successful login
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        'username': TEST_USER['username'],
        'password': TEST_USER['password']
    })
    passed = response.status_code == 200
    if passed:
        data = response.json()
        print_test("Login successful", True, f"Token received")
        return data
    else:
        print_test("Login successful", False, f"Status: {response.status_code}, Error: {response.text}")
        return None


def test_protected_routes(tokens):
    print("\n=== Testing Protected Routes ===")
    
    headers = {'Authorization': f'Bearer {tokens["access"]}'}
    
    # Test 1: Access protected route with valid token
    response = requests.get(f"{BASE_URL}/auth/check/", headers=headers)
    passed = response.status_code == 200
    print_test("Access protected route with valid token", passed, f"Status: {response.status_code}")
    
    # Test 2: Access protected route without token
    response = requests.get(f"{BASE_URL}/auth/check/")
    passed = response.status_code == 401
    print_test("Reject request without token", passed, f"Status: {response.status_code}")
    
    # Test 3: Access protected route with invalid token
    response = requests.get(f"{BASE_URL}/auth/check/", headers={'Authorization': 'Bearer invalidtoken123'})
    passed = response.status_code == 401
    print_test("Reject invalid token", passed, f"Status: {response.status_code}")
    
    # Test 4: Access protected route with expired token (simulate)
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJqdGkiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0.invalid"
    response = requests.get(f"{BASE_URL}/auth/check/", headers={'Authorization': f'Bearer {expired_token}'})
    passed = response.status_code == 401
    print_test("Reject expired token", passed, f"Status: {response.status_code}")


def test_user_isolation(tokens_user1, tokens_user2):
    print("\n=== Testing User Isolation ===")
    
    headers_user1 = {'Authorization': f'Bearer {tokens_user1["access"]}'}
    headers_user2 = {'Authorization': f'Bearer {tokens_user2["access"]}'}
    
    # User 1 creates an expense
    expense_data = {
        'category': 1,
        'amount': '100.00',
        'description': 'User1 private expense',
        'date': '2026-09-15'
    }
    response = requests.post(f"{BASE_URL}/expenses/", json=expense_data, headers=headers_user1)
    if response.status_code == 201:
        expense_id = response.json()['id']
        print_test("User1 creates expense", True, f"Expense ID: {expense_id}")
        
        # Test: User2 cannot access User1's expense
        response = requests.get(f"{BASE_URL}/expenses/{expense_id}/", headers=headers_user2)
        passed = response.status_code == 404
        print_test("User2 cannot access User1's expense", passed, f"Status: {response.status_code}")
        
        # Test: User1 can access their own expense
        response = requests.get(f"{BASE_URL}/expenses/{expense_id}/", headers=headers_user1)
        passed = response.status_code == 200
        print_test("User1 can access their own expense", passed, f"Status: {response.status_code}")
    else:
        print_test("User1 creates expense", False, f"Status: {response.status_code}")


def test_role_information(tokens):
    print("\n=== Testing Role Information ===")
    
    headers = {'Authorization': f'Bearer {tokens["access"]}'}
    
    # Test: Role is included in token response
    passed = 'user' in tokens and 'role' in tokens['user']
    print_test("Role information in login response", passed, f"Role: {tokens.get('user', {}).get('role', 'N/A')}")
    
    # Test: Role is accessible in profile
    response = requests.get(f"{BASE_URL}/auth/profile/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        passed = 'role' in data
        print_test("Role information in profile", passed, f"Role: {data.get('role', 'N/A')}")
    else:
        print_test("Role information in profile", False, f"Status: {response.status_code}")


def test_token_refresh(tokens):
    print("\n=== Testing Token Refresh ===")
    
    # Test: Refresh token
    response = requests.post(f"{BASE_URL}/auth/token/refresh/", json={
        'refresh': tokens['refresh']
    })
    passed = response.status_code == 200
    if passed:
        new_tokens = response.json()
        print_test("Token refresh successful", True, "New access token received")
        return new_tokens
    else:
        print_test("Token refresh successful", False, f"Status: {response.status_code}")
        return tokens


def test_logout(tokens):
    print("\n=== Testing Logout ===")
    
    headers = {'Authorization': f'Bearer {tokens["access"]}'}
    
    # Test: Logout
    response = requests.post(f"{BASE_URL}/auth/logout/", 
        json={'refresh': tokens['refresh']},
        headers=headers
    )
    passed = response.status_code == 200
    print_test("Logout successful", passed, f"Status: {response.status_code}")
    
    # Test: Token is blacklisted after logout
    response = requests.get(f"{BASE_URL}/auth/check/", headers=headers)
    passed = response.status_code == 401
    print_test("Token blacklisted after logout", passed, f"Status: {response.status_code}")


def test_password_change(tokens):
    print("\n=== Testing Password Change ===")
    
    headers = {'Authorization': f'Bearer {tokens["access"]}'}
    
    # Test: Change password with wrong old password
    response = requests.post(f"{BASE_URL}/auth/change-password/", 
        json={'old_password': 'WrongPass123!', 'new_password': 'NewSecurePass123!'},
        headers=headers
    )
    passed = response.status_code == 400
    print_test("Reject wrong old password", passed, f"Status: {response.status_code}")
    
    # Test: Change password with correct old password
    response = requests.post(f"{BASE_URL}/auth/change-password/", 
        json={'old_password': TEST_USER['password'], 'new_password': 'NewSecurePass123!'},
        headers=headers
    )
    passed = response.status_code == 200
    print_test("Password change successful", passed, f"Status: {response.status_code}")
    
    # Update password for further tests
    TEST_USER['password'] = 'NewSecurePass123!'


def main():
    print("=" * 60)
    print("BudgetBuddy Authentication Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        test_registration()
        tokens = test_login()
        
        if tokens:
            test_protected_routes(tokens)
            test_role_information(tokens)
            tokens = test_token_refresh(tokens)
            test_password_change(tokens)
            test_logout(tokens)
            
            # Login again for user isolation test
            tokens_user1 = test_login()
            
            # Login as user 2
            response = requests.post(f"{BASE_URL}/auth/login/", json={
                'username': TEST_USER_2['username'],
                'password': TEST_USER_2['password']
            })
            if response.status_code == 200:
                tokens_user2 = response.json()
                test_user_isolation(tokens_user1, tokens_user2)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server.")
        print("   Make sure the Django server is running:")
        print("   python manage.py runserver")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
