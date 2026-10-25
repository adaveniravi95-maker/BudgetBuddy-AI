# Backend setup

BudgetBuddy's supported backend is the Django project in the repository root. Run it from the root directory using `manage.py`; do not start `uvicorn` for the application.

```powershell
cd ..
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API health check is http://127.0.0.1:8000/api/health/. See the root [README](../README.md) for full setup and test instructions.

The remaining Django source under `backend/` is an earlier implementation and is not loaded by the active Django settings, URL configuration, or Render deployment.
