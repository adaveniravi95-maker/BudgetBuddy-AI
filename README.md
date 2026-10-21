# BudgetBuddy

Personal budget planning and expense management platform. Track income and expenses, set monthly budgets with per-category allocations, monitor savings goals, and visualize your financial health from a single dashboard.

# Live Demo 
https://budgetbuddy-frontend-seven.vercel.app

## Features

- **Authentication** — JWT based register / login / logout with access + refresh token rotation, protected routes on the frontend.
- **Income & Expense tracking** — CRUD for income and expenses with categories, payment methods, recurrence flags and filters.
- **Transactions** — unified transaction feed with a summary endpoint (income, expense, net balance).
- **Budgets** — monthly budgets with per-category allocations, utilization tracking and CRUD.
- **Budget alerts** — automatic near-limit (80%) and exceeded (100%) alert phases computed from current month spending.
- **Savings goals** — goals with target amounts, deadlines, priority/status, progress updates and goal transactions.
- **Analytics** — financial summary, category spending, monthly trends, budget utilization and savings progress.
- **Reports** — monthly report export as JSON, CSV, XLSX or PDF, plus in-app notifications on generation.
- **Notifications** — unread list, mark-as-read and mark-all-as-read endpoints surfaced in the dashboard.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, Pydantic, SQLite |
| Auth | JWT (`python-jose`), bcrypt via `passlib` |
| Frontend | React 19, Vite, React Router 7, Recharts, Axios |
| Linting | oxlint |
| Testing | pytest |

## Project Structure

```
BudgetBuddy/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, router mounting
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── auth.py          # JWT helpers
│   │   ├── budget_alerts.py # Budget utilization / alert logic
│   │   └── routers/         # auth, expenses, incomes, transactions,
│   │                        # budgets, savings, notifications, analytics, reports
│   ├── requirements.txt
│   └── test_*.py            # pytest suites
└── frontend/
    ├── src/
    │   ├── pages/           # Login, Register, Dashboard
    │   ├── components/      # ProtectedRoute, analytics widgets
    │   ├── contexts/        # AuthContext
    │   ├── services/api.js  # Axios instance with JWT interceptors
    │   └── constants/
    └── vite.config.js       # dev server on :3000, proxies /api -> :8000
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows:  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs (Swagger UI): http://localhost:8000/docs
Health check: http://localhost:8000/health

Configuration lives in `backend/.env`:

```
DATABASE_URL=sqlite:///./db.sqlite3
SECRET_KEY=<your-secret>
```

Tables are created automatically on startup.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000 — the Vite dev server proxies `/api` requests to `http://localhost:8000`.

### Useful scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Production build |
| `npm run lint` | Run oxlint |

## API Overview

Base URL: `http://localhost:8000`

| Group | Prefix | Endpoints |
|-------|--------|-----------|
| Auth | `/api/auth` | `POST /register/`, `POST /login/`, `POST /logout/`, `POST /token/refresh/`, `GET /check/`, `GET/PUT /profile/` |
| Expenses | `/api/expenses` | `GET/POST /`, `GET/PUT/DELETE /{id}/` |
| Incomes | `/api/incomes` | `GET/POST /`, `GET/PUT/DELETE /{id}/` |
| Transactions | `/api/transactions` | `GET /`, `GET /summary/` |
| Budgets | `/api/budgets` | `GET/POST /`, `GET/PUT/DELETE /{id}/` |
| Savings Goals | `/api/savings` | `GET/POST /`, `GET/PUT/DELETE /{id}/`, `PUT /{id}/progress/` |
| Notifications | `/api/notifications` | `GET /`, `GET /unread/`, `PUT /{id}/read/`, `PUT /read-all/` |
| Analytics | `/api/analytics` | `GET /` (supports date-range filters) |
| Reports | `/api/reports` | `GET /monthly/?month=&year=&format=json\|csv\|xlsx\|pdf` |

All endpoints except registration, login and token refresh require an `Authorization: Bearer <access_token>` header.

## Testing

```bash
cd backend
pytest
```

Some `test_*.py` scripts are live-server integration scripts that require the API running on `localhost:8000`; they are excluded from automatic collection via `conftest.py` and can be run manually with `python test_<name>.py`.

## License

See repository for license details.
> **A Personal Finance Management Platform for Students**

BudgetBuddy is a full-stack personal finance management platform designed to help students manage their income, expenses, budgets, savings goals, and financial activities in one place.

---

## Live Application

**Frontend:**  
https://budgetbuddy-frontend-h3zw.onrender.com/

**Backend API Health Check:**  
https://budgetbuddy-student-finance-platform.onrender.com/health

---

## Features

- User Registration and Secure Login
- Income and Expense Management
- Budget Tracking
- Savings Goals
- Financial Analytics
- PDF and Excel Reports
- Notifications
- BudgetBuddy Assistant

---

## Technology

| Component | Technology |
|---|---|
| Frontend | React, Vite, Recharts |
| Backend | FastAPI, Python, SQLAlchemy |
| Database | PostgreSQL (Supabase) |
| Authentication | JWT |
| Deployment | Render |

---

## Overview

BudgetBuddy provides a simple and user-friendly platform for students to track their finances, monitor spending, manage budgets, and work towards their savings goals.

---

**BudgetBuddy**  
*Simple. Smart. Financially Organized.*
