# BudgetBuddy Authentication System

## Setup Instructions

### 1. Install Dependencies
```bash
pip install django djangorestframework django-cors-headers python-decouple psycopg2-binary djangorestframework-simplejwt
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create Test Users
```bash
python manage.py create_test_users
```

### 4. Start Server
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Login and get tokens | No |
| POST | `/api/auth/logout/` | Logout (blacklist token) | Yes |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| POST | `/api/auth/change-password/` | Change password | Yes |
| GET | `/api/auth/check/` | Check authentication status | Yes |

### User Profile
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET/PUT | `/api/auth/profile/` | Get/Update user profile | Yes |
| GET/PUT | `/api/auth/profile/detail/` | Get/Update profile details | Yes |

### Financial Records (All require authentication)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/income/` | List/Create income |
| GET/PUT/DELETE | `/api/income/<id>/` | Get/Update/Delete income |
| GET/POST | `/api/expenses/` | List/Create expenses |
| GET/PUT/DELETE | `/api/expenses/<id>/` | Get/Update/Delete expense |
| GET/POST | `/api/budgets/` | List/Create budgets |
| GET/PUT/DELETE | `/api/budgets/<id>/` | Get/Update/Delete budget |
| GET/POST | `/api/savings/goals/` | List/Create savings goals |
| GET/PUT/DELETE | `/api/savings/goals/<id>/` | Get/Update/Delete savings goal |

## Test Users
| Username | Password | Role |
|----------|----------|------|
| student1 | Student123! | Student |
| student2 | Student456! | Student |
| premium1 | Premium123! | Premium |
| admin | admin123 | Admin |

## Test Script
Run the automated test script:
```bash
python test_auth.py
```

## Test Scenarios Covered
1. ✅ User registration with validation
2. ✅ Password handling (change, validation)
3. ✅ Login with JWT generation
4. ✅ JWT validation
5. ✅ Protected backend routes
6. ✅ Basic role representation
7. ✅ Authenticated user can access their records
8. ✅ Unauthenticated user cannot access protected endpoints
9. ✅ User A cannot access User B's records
10. ✅ Invalid/expired authentication is rejected
11. ✅ Role information is available to backend

## Example API Calls

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "new@test.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!", "first_name": "New", "last_name": "User"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "Student123!"}'
```

### Access Protected Route
```bash
curl -X GET http://localhost:8000/api/auth/check/ \
  -H "Authorization: Bearer <your_access_token>"
```

### Create Expense
```bash
curl -X POST http://localhost:8000/api/expenses/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"category": 1, "amount": "150.00", "description": "Lunch", "date": "2026-09-15"}'
```
