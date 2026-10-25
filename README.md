# BudgetBuddy

BudgetBuddy is a personal finance application for tracking income, expenses, budgets, savings goals, analytics, reports, and notifications.

## Technology

- **Backend:** Django 6.1, Django REST Framework, Simple JWT
- **Database:** SQLite for local development; PostgreSQL for deployment
- **Frontend:** React 19, Vite, React Router, Recharts, Axios
- **Deployment:** Render

The Django project is at the repository root. `manage.py`, `config.settings`, and `config.wsgi` are the supported backend entry points. The remaining Django files under `backend/` are an inactive earlier implementation and are not used by the active app or Render deployment.

## Run locally on Windows

Open PowerShell in the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If `.venv` already exists, activate it and continue from the `pip install` step. The local Django settings use SQLite and do not require a `.env` file.

The API health check is at http://127.0.0.1:8000/api/health/. The Django admin is at http://127.0.0.1:8000/admin/.

## Run the frontend

In a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally http://localhost:5173). The Vite development server proxies `/api` requests to the Django backend on port 8000.

## Tests and checks

From the repository root with the virtual environment active:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test core
```

For a production deployment, configure the `SECRET_KEY`, `DATABASE_URL`, and allowed host/origin environment variables. Render deployment is defined in `render.yaml` and runs Django through `config.wsgi:application`.
