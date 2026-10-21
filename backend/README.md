# BudgetBuddy Backend

FastAPI + SQLAlchemy + SQLite for local development, PostgreSQL-ready for production.

## Run

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python seed_data.py
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

Test account after seeding:
`student@example.com` / `Password123`

## Core API

- POST `/api/auth/register`
- POST `/api/auth/login`
- GET `/api/auth/me`
- POST/GET/PUT/DELETE `/api/expenses`
- POST/GET/PUT/DELETE `/api/incomes`
- POST/GET `/api/budgets`
- GET `/api/budgets/{month}`
- GET `/api/dashboard/{month}`

All financial routes require `Authorization: Bearer <JWT>` and filter records by the authenticated user's ID.
