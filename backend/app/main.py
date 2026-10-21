from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import (
    accounts, expenses, incomes, transactions, budgets, savings,
    notifications, analytics, reports,
)
from .config import get_settings

settings = get_settings()
settings.check_production_safety()

# Create database tables

from .database import Base, engine
from .config import settings
from .routers import router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BudgetBuddy API",
    description="Personal Budget Planning and Expense Management Platform",
    version="1.0.0",
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(accounts.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(incomes.router, prefix="/api/incomes", tags=["Incomes"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(savings.router, prefix="/api/savings", tags=["Savings Goals"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "BudgetBuddy API is running"}
    return {"message": "BudgetBuddy Backend is Running"}


@app.get("/health")
def health():
    return {"status": "ok"}
    return {"status": "ok"}
