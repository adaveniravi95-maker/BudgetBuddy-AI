"""
Milestone 2 — Systematic Testing: Positive, Negative, Boundary & Regression
============================================================================
Run:  cd backend && python -m pytest test_systematic.py -v
"""

import json
import pytest
from datetime import date, datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models, auth

# ══════════════════════════════════════════════════════════════════
# TEST DATABASE
# ══════════════════════════════════════════════════════════════════
TEST_DB_URL = "sqlite:///./test_systematic.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db

# ─── Results Collector ───────────────────────────────────────────
RESULTS = []        # list of dicts
DEFECTS = []        # list of dicts
DEFECT_ID = [0]


def record(category, tc_id, description, input_data, expected, actual, status, defect=None):
    """Append to results. If defect provided, also log it."""
    row = {
        "category": category,
        "tc_id": tc_id,
        "description": description,
        "input": input_data,
        "expected": expected,
        "actual": actual,
        "status": status,
    }
    RESULTS.append(row)
    if defect:
        DEFECT_ID[0] += 1
        defect["id"] = f"DEF-{DEFECT_ID[0]:03d}"
        defect["tc_id"] = tc_id
        DEFECTS.append(defect)


# ══════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_teardown():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def reg(c, u, email=None):
    email = email or f"{u}@test.com"
    return c.post("/api/auth/register/", json={
        "username": u, "email": email,
        "password": "SecurePass123!", "password_confirm": "SecurePass123!",
    })


def tok(c, u, email=None):
    r = reg(c, u, email)
    if r.status_code == 201:
        return r.json()["tokens"]["access"]
    return c.post("/api/auth/login/", json={"username": u, "password": "SecurePass123!"}).json()["access"]


def h(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════
# 1. POSITIVE TESTING
# ══════════════════════════════════════════════════════════════════

class TestPositive:
    """Valid operations that should succeed."""

    # ── Auth ──────────────────────────────────────────────────

    def test_register_new_user(self, client, db):
        r = client.post("/api/auth/register/", json={
            "username": "pos_reg1", "email": "pos1@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        ok = r.status_code == 201 and "tokens" in r.json()
        record("Positive/Auth", "P-AUTH-01", "Register new user with valid data",
               '{"username":"pos_reg1","email":"pos1@test.com","password":"SecurePass123!"}',
               "201 + tokens", f"{r.status_code} + {'tokens' in r.json()}", "PASS" if ok else "FAIL")
        assert ok

    def test_login_existing_user(self, client, db):
        reg(client, "pos_login1", "pos_login1@test.com")
        r = client.post("/api/auth/login/", json={"username": "pos_login1", "password": "SecurePass123!"})
        ok = r.status_code == 200 and "access" in r.json()
        record("Positive/Auth", "P-AUTH-02", "Login existing user with correct password",
               '{"username":"pos_login1","password":"SecurePass123!"}',
               "200 + access", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_check_auth_returns_user(self, client):
        t = tok(client, "pos_auth1")
        r = client.get("/api/auth/check/", headers=h(t))
        ok = r.status_code == 200 and r.json()["authenticated"] is True
        record("Positive/Auth", "P-AUTH-03", "Check auth with valid token",
               "GET /api/auth/check/ with Bearer token",
               "200 authenticated=true", f"{r.status_code} auth={r.json().get('authenticated')}", "PASS" if ok else "FAIL")
        assert ok

    def test_get_profile(self, client):
        t = tok(client, "pos_profile1")
        r = client.get("/api/auth/profile/", headers=h(t))
        ok = r.status_code == 200 and r.json()["username"] == "pos_profile1"
        record("Positive/Auth", "P-AUTH-04", "Get user profile",
               "GET /api/auth/profile/ with Bearer token",
               "200 + user data", f"{r.status_code} user={r.json().get('username')}", "PASS" if ok else "FAIL")
        assert ok

    def test_token_refresh(self, client):
        r = reg(client, "pos_refresh", "pos_refresh@test.com")
        refresh = r.json()["tokens"]["refresh"]
        r = client.post("/api/auth/token/refresh/", json={"refresh": refresh})
        ok = r.status_code == 200 and "access" in r.json()
        record("Positive/Auth", "P-AUTH-05", "Refresh token with valid refresh token",
               '{"refresh":"<valid_jwt>"}',
               "200 + new access", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Expense CRUD ──────────────────────────────────────────

    def test_create_expense(self, client, db):
        t = tok(client, "pos_exp1")
        r = client.post("/api/expenses/", json={
            "amount": 1500.75, "category": "food", "description": "Groceries", "date": "2026-09-15",
        }, headers=h(t))
        ok = r.status_code == 201 and r.json()["amount"] == 1500.75
        record("Positive/Expense", "P-EXP-01", "Create expense with valid data",
               '{"amount":1500.75,"category":"food","description":"Groceries","date":"2026-09-15"}',
               "201 + amount=1500.75", f"{r.status_code} amt={r.json().get('amount')}", "PASS" if ok else "FAIL")
        assert ok

    def test_read_expense(self, client):
        t = tok(client, "pos_exp2")
        rid = client.post("/api/expenses/", json={
            "amount": 200, "category": "travel", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.get(f"/api/expenses/{rid}/", headers=h(t))
        ok = r.status_code == 200 and r.json()["id"] == rid
        record("Positive/Expense", "P-EXP-02", "Read single expense by ID",
               f"GET /api/expenses/{rid}/",
               "200 + correct data", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_update_expense(self, client):
        t = tok(client, "pos_exp3")
        rid = client.post("/api/expenses/", json={
            "amount": 500, "category": "shopping", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.put(f"/api/expenses/{rid}/", json={"amount": 750, "description": "Updated"}, headers=h(t))
        ok = r.status_code == 200 and r.json()["amount"] == 750.0
        record("Positive/Expense", "P-EXP-03", "Update expense amount and description",
               '{"amount":750,"description":"Updated"}',
               "200 + amount=750", f"{r.status_code} amt={r.json().get('amount')}", "PASS" if ok else "FAIL")
        assert ok

    def test_delete_expense(self, client, db):
        t = tok(client, "pos_exp4")
        rid = client.post("/api/expenses/", json={
            "amount": 100, "category": "entertainment", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.delete(f"/api/expenses/{rid}/", headers=h(t))
        gone = client.get(f"/api/expenses/{rid}/", headers=h(t)).status_code == 404
        ok = r.status_code == 204 and gone
        record("Positive/Expense", "P-EXP-04", "Delete expense and verify removed",
               f"DELETE /api/expenses/{rid}/",
               "204 + 404 on re-read", f"{r.status_code} + gone={gone}", "PASS" if ok else "FAIL")
        assert ok

    def test_list_expenses(self, client):
        t = tok(client, "pos_exp5")
        for cat in ["food", "travel", "shopping"]:
            client.post("/api/expenses/", json={"amount": 100, "category": cat, "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/expenses/", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 3
        record("Positive/Expense", "P-EXP-05", "List all expenses",
               "GET /api/expenses/",
               "200 + total=3", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    def test_filter_expenses_by_category(self, client):
        t = tok(client, "pos_exp6")
        client.post("/api/expenses/", json={"amount": 100, "category": "food", "date": "2026-09-10"}, headers=h(t))
        client.post("/api/expenses/", json={"amount": 200, "category": "travel", "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/expenses/?category=food", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 1
        record("Positive/Expense", "P-EXP-06", "Filter expenses by category",
               "GET /api/expenses/?category=food",
               "200 + total=1 (food only)", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    def test_filter_expenses_by_date_range(self, client):
        t = tok(client, "pos_exp7")
        client.post("/api/expenses/", json={"amount": 100, "category": "food", "date": "2026-09-01"}, headers=h(t))
        client.post("/api/expenses/", json={"amount": 200, "category": "food", "date": "2026-09-20"}, headers=h(t))
        r = client.get("/api/expenses/?start_date=2026-09-10&end_date=2026-09-30", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 1
        record("Positive/Expense", "P-EXP-07", "Filter expenses by date range",
               "GET /api/expenses/?start_date=2026-09-10&end_date=2026-09-30",
               "200 + total=1", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    # ── Income CRUD ───────────────────────────────────────────

    def test_create_income(self, client, db):
        t = tok(client, "pos_inc1")
        r = client.post("/api/incomes/", json={
            "amount": 25000, "source": "scholarship", "description": "Fall grant", "date": "2026-09-01",
        }, headers=h(t))
        ok = r.status_code == 201 and r.json()["amount"] == 25000.0
        record("Positive/Income", "P-INC-01", "Create income with valid data",
               '{"amount":25000,"source":"scholarship","description":"Fall grant","date":"2026-09-01"}',
               "201 + amount=25000", f"{r.status_code} amt={r.json().get('amount')}", "PASS" if ok else "FAIL")
        assert ok

    def test_read_income(self, client):
        t = tok(client, "pos_inc2")
        rid = client.post("/api/incomes/", json={
            "amount": 5000, "source": "freelance", "date": "2026-09-05",
        }, headers=h(t)).json()["id"]
        r = client.get(f"/api/incomes/{rid}/", headers=h(t))
        ok = r.status_code == 200 and r.json()["id"] == rid
        record("Positive/Income", "P-INC-02", "Read single income by ID",
               f"GET /api/incomes/{rid}/",
               "200 + correct data", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_update_income(self, client):
        t = tok(client, "pos_inc3")
        rid = client.post("/api/incomes/", json={
            "amount": 3000, "source": "pocket_money", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.put(f"/api/incomes/{rid}/", json={"amount": 4500, "description": "Updated"}, headers=h(t))
        ok = r.status_code == 200 and r.json()["amount"] == 4500.0
        record("Positive/Income", "P-INC-03", "Update income amount and description",
               '{"amount":4500,"description":"Updated"}',
               "200 + amount=4500", f"{r.status_code} amt={r.json().get('amount')}", "PASS" if ok else "FAIL")
        assert ok

    def test_delete_income(self, client, db):
        t = tok(client, "pos_inc4")
        rid = client.post("/api/incomes/", json={
            "amount": 1000, "source": "freelance", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.delete(f"/api/incomes/{rid}/", headers=h(t))
        gone = client.get(f"/api/incomes/{rid}/", headers=h(t)).status_code == 404
        ok = r.status_code == 204 and gone
        record("Positive/Income", "P-INC-04", "Delete income and verify removed",
               f"DELETE /api/incomes/{rid}/",
               "204 + 404 on re-read", f"{r.status_code} + gone={gone}", "PASS" if ok else "FAIL")
        assert ok

    def test_list_incomes(self, client):
        t = tok(client, "pos_inc5")
        for src in ["pocket_money", "scholarship", "freelance"]:
            client.post("/api/incomes/", json={"amount": 1000, "source": src, "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/incomes/", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 3
        record("Positive/Income", "P-INC-05", "List all incomes",
               "GET /api/incomes/",
               "200 + total=3", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    def test_filter_incomes_by_source(self, client):
        t = tok(client, "pos_inc6")
        client.post("/api/incomes/", json={"amount": 100, "source": "pocket_money", "date": "2026-09-10"}, headers=h(t))
        client.post("/api/incomes/", json={"amount": 200, "source": "scholarship", "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/incomes/?source=pocket_money", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 1
        record("Positive/Income", "P-INC-06", "Filter incomes by source",
               "GET /api/incomes/?source=pocket_money",
               "200 + total=1", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    # ── Budget CRUD ───────────────────────────────────────────

    def test_create_budget(self, client, db):
        t = tok(client, "pos_bud1")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 10000,
            "allocations": [{"category": "food", "amount": 5000}, {"category": "travel", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 201 and len(r.json()["allocations"]) == 2
        record("Positive/Budget", "P-BUD-01", "Create budget with allocations",
               '{"month":9,"year":2026,"total_amount":10000,"allocations":[...]}',
               "201 + 2 allocations", f"{r.status_code} allocs={len(r.json().get('allocations', []))}", "PASS" if ok else "FAIL")
        assert ok

    def test_read_budget(self, client):
        t = tok(client, "pos_bud2")
        rid = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t)).json()["id"]
        r = client.get(f"/api/budgets/{rid}/", headers=h(t))
        ok = r.status_code == 200 and r.json()["id"] == rid
        record("Positive/Budget", "P-BUD-02", "Read single budget by ID",
               f"GET /api/budgets/{rid}/",
               "200 + correct data", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_update_budget_total_and_allocations(self, client):
        t = tok(client, "pos_bud3")
        rid = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t)).json()["id"]
        r = client.put(f"/api/budgets/{rid}/", json={
            "total_amount": 8000,
            "allocations": [{"category": "food", "amount": 4000}, {"category": "travel", "amount": 4000}],
        }, headers=h(t))
        ok = r.status_code == 200 and r.json()["total_amount"] == 8000.0 and len(r.json()["allocations"]) == 2
        record("Positive/Budget", "P-BUD-03", "Update budget total and allocations",
               '{"total_amount":8000,"allocations":[...]}',
               "200 + total=8000 + 2 allocs", f"{r.status_code} total={r.json().get('total_amount')}", "PASS" if ok else "FAIL")
        assert ok

    def test_delete_budget(self, client, db):
        t = tok(client, "pos_bud4")
        rid = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t)).json()["id"]
        r = client.delete(f"/api/budgets/{rid}/", headers=h(t))
        gone = client.get(f"/api/budgets/{rid}/", headers=h(t)).status_code == 404
        ok = r.status_code == 204 and gone
        record("Positive/Budget", "P-BUD-04", "Delete budget and verify removed",
               f"DELETE /api/budgets/{rid}/",
               "204 + 404 on re-read", f"{r.status_code} + gone={gone}", "PASS" if ok else "FAIL")
        assert ok

    def test_list_budgets(self, client):
        t = tok(client, "pos_bud5")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        client.post("/api/budgets/", json={
            "month": 10, "year": 2026, "total_amount": 6000,
            "allocations": [{"category": "travel", "amount": 6000}],
        }, headers=h(t))
        r = client.get("/api/budgets/", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 2
        record("Positive/Budget", "P-BUD-05", "List all budgets",
               "GET /api/budgets/",
               "200 + total=2", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    def test_filter_budgets_by_year(self, client):
        t = tok(client, "pos_bud6")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2025, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        r = client.get("/api/budgets/?year=2026", headers=h(t))
        ok = r.status_code == 200 and r.json()["total"] == 1
        record("Positive/Budget", "P-BUD-06", "Filter budgets by year",
               "GET /api/budgets/?year=2026",
               "200 + total=1", f"{r.status_code} total={r.json().get('total')}", "PASS" if ok else "FAIL")
        assert ok

    # ── Transaction Dashboard ─────────────────────────────────

    def test_dashboard_summary(self, client):
        t = tok(client, "pos_dash1")
        client.post("/api/incomes/", json={"amount": 10000, "source": "scholarship", "date": "2026-09-01"}, headers=h(t))
        client.post("/api/expenses/", json={"amount": 3000, "category": "food", "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/transactions/summary/", headers=h(t))
        s = r.json()
        ok = (r.status_code == 200 and s["total_income"] == 10000.0
              and s["total_expenses"] == 3000.0 and s["balance"] == 7000.0)
        record("Positive/Dashboard", "P-DASH-01", "Dashboard summary correct after income+expense",
               "1 income(10000) + 1 expense(3000)",
               "income=10000, expense=3000, balance=7000",
               f"income={s['total_income']}, expense={s['total_expenses']}, balance={s['balance']}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_dashboard_formula(self, client):
        t = tok(client, "pos_dash2")
        client.post("/api/incomes/", json={"amount": 5000, "source": "freelance", "date": "2026-09-01"}, headers=h(t))
        client.post("/api/expenses/", json={"amount": 2000, "category": "shopping", "date": "2026-09-10"}, headers=h(t))
        r = client.get("/api/transactions/summary/", headers=h(t))
        s = r.json()
        ok = s["balance"] == s["total_income"] - s["total_expenses"]
        record("Positive/Dashboard", "P-DASH-02", "Balance = Income - Expenses formula",
               "income=5000, expense=2000",
               "balance=3000", f"balance={s['balance']}", "PASS" if ok else "FAIL")
        assert ok

    def test_transaction_list_mixed(self, client):
        t = tok(client, "pos_dash3")
        client.post("/api/incomes/", json={"amount": 1000, "source": "pocket_money", "date": "2026-09-01"}, headers=h(t))
        client.post("/api/expenses/", json={"amount": 500, "category": "food", "date": "2026-09-15"}, headers=h(t))
        r = client.get("/api/transactions/", headers=h(t))
        types = {tx["type"] for tx in r.json()["transactions"]}
        ok = r.status_code == 200 and "income" in types and "expense" in types
        record("Positive/Dashboard", "P-DASH-03", "Transaction list contains both income and expense",
               "1 income + 1 expense",
               "both types present", f"types={types}", "PASS" if ok else "FAIL")
        assert ok

    def test_transaction_sorted_desc(self, client):
        t = tok(client, "pos_dash4")
        client.post("/api/incomes/", json={"amount": 100, "source": "pocket_money", "date": "2026-09-01"}, headers=h(t))
        client.post("/api/incomes/", json={"amount": 200, "source": "freelance", "date": "2026-09-15"}, headers=h(t))
        r = client.get("/api/transactions/", headers=h(t))
        dates = [tx["date"] for tx in r.json()["transactions"]]
        ok = dates == sorted(dates, reverse=True)
        record("Positive/Dashboard", "P-DASH-04", "Transactions sorted newest first",
               "2 incomes on different dates",
               "dates descending", f"dates={dates}", "PASS" if ok else "FAIL")
        assert ok

    # ── Category consistency ──────────────────────────────────

    def test_expense_categories_all_valid(self, client):
        t = tok(client, "pos_cat1")
        for cat in ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]:
            r = client.post("/api/expenses/", json={"amount": 100, "category": cat, "date": "2026-09-10"}, headers=h(t))
            assert r.status_code == 201
        r = client.get("/api/expenses/", headers=h(t))
        db_cats = {e["category"] for e in r.json()["expenses"]}
        ok = len(db_cats) == 6
        record("Positive/Category", "P-CAT-01", "All 6 expense categories accepted and stored",
               "Create expense for each category",
               "6 unique categories in list", f"found={len(db_cats)}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_sources_all_valid(self, client):
        t = tok(client, "pos_cat2")
        for src in ["pocket_money", "scholarship", "freelance"]:
            r = client.post("/api/incomes/", json={"amount": 100, "source": src, "date": "2026-09-10"}, headers=h(t))
            assert r.status_code == 201
        r = client.get("/api/incomes/", headers=h(t))
        db_srcs = {i["source"] for i in r.json()["incomes"]}
        ok = len(db_srcs) == 3
        record("Positive/Category", "P-CAT-02", "All 3 income sources accepted and stored",
               "Create income for each source",
               "3 unique sources in list", f"found={len(db_srcs)}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_alloc_uses_expense_categories(self, client):
        t = tok(client, "pos_cat3")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 6000,
            "allocations": [{"category": c, "amount": 1000} for c in
                            ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]],
        }, headers=h(t))
        alloc_cats = {a["category"] for a in r.json()["allocations"]}
        ok = len(alloc_cats) == 6
        record("Positive/Category", "P-CAT-03", "Budget allocations use same expense categories",
               "Create budget with all 6 categories",
               "6 alloc categories", f"found={len(alloc_cats)}", "PASS" if ok else "FAIL")
        assert ok


# ══════════════════════════════════════════════════════════════════
# 2. NEGATIVE TESTING
# ══════════════════════════════════════════════════════════════════

class TestNegative:
    """Invalid inputs, missing data, unauthorized access, cross-user access."""

    # ── Registration failures ─────────────────────────────────

    def test_register_duplicate_username(self, client):
        reg(client, "neg_dup1", "neg_dup1@test.com")
        r = reg(client, "neg_dup1", "neg_dup1_other@test.com")
        ok = r.status_code == 400
        record("Negative/Auth", "N-AUTH-01", "Register with existing username",
               '{"username":"neg_dup1",...}',
               "400 Username already exists", f"{r.status_code}: {r.json().get('detail','')}",
               "PASS" if ok else "FAIL",
               None if ok else {"issue": "Duplicate username accepted", "expected": "400", "actual": str(r.status_code)})
        assert ok

    def test_register_duplicate_email(self, client):
        reg(client, "neg_dup_email1", "same@test.com")
        r = reg(client, "neg_dup_email2", "same@test.com")
        ok = r.status_code == 400
        record("Negative/Auth", "N-AUTH-02", "Register with existing email",
               '{"email":"same@test.com",...}',
               "400 Email already exists", f"{r.status_code}: {r.json().get('detail','')}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_register_short_username(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "ab", "email": "short@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        ok = r.status_code == 422
        record("Negative/Auth", "N-AUTH-03", "Register with username < 3 chars",
               '{"username":"ab",...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_register_short_password(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "validuser", "email": "shortpw@test.com",
            "password": "short", "password_confirm": "short",
        })
        ok = r.status_code == 422
        record("Negative/Auth", "N-AUTH-04", "Register with password < 8 chars",
               '{"password":"short",...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_register_mismatched_passwords(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "mismatch1", "email": "mismatch1@test.com",
            "password": "SecurePass123!", "password_confirm": "DifferentPass!",
        })
        ok = r.status_code == 422
        record("Negative/Auth", "N-AUTH-05", "Register with mismatched passwords",
               '{"password":"SecurePass123!","password_confirm":"DifferentPass!"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_login_wrong_password(self, client):
        reg(client, "neg_login1", "neg_login1@test.com")
        r = client.post("/api/auth/login/", json={"username": "neg_login1", "password": "WrongPass123!"})
        ok = r.status_code == 401
        record("Negative/Auth", "N-AUTH-06", "Login with wrong password",
               '{"username":"neg_login1","password":"WrongPass123!"}',
               "401 Invalid credentials", f"{r.status_code}: {r.json().get('detail','')}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/auth/login/", json={"username": "ghost_xyz", "password": "Whatever123!"})
        ok = r.status_code == 401
        record("Negative/Auth", "N-AUTH-07", "Login with nonexistent username",
               '{"username":"ghost_xyz",...}',
               "401 Invalid credentials", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Expense failures ──────────────────────────────────────

    def test_expense_negative_amount(self, client):
        t = tok(client, "neg_exp1")
        r = client.post("/api/expenses/", json={
            "amount": -100, "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-01", "Create expense with negative amount",
               '{"amount":-100,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_zero_amount(self, client):
        t = tok(client, "neg_exp2")
        r = client.post("/api/expenses/", json={
            "amount": 0, "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-02", "Create expense with zero amount",
               '{"amount":0,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_invalid_category(self, client):
        t = tok(client, "neg_exp3")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "invalid_cat", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-03", "Create expense with invalid category",
               '{"category":"invalid_cat",...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_missing_category(self, client):
        t = tok(client, "neg_exp4")
        r = client.post("/api/expenses/", json={
            "amount": 100, "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-04", "Create expense without category",
               '{"amount":100,"date":"2026-09-10"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_missing_date(self, client):
        t = tok(client, "neg_exp5")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-05", "Create expense without date",
               '{"amount":100,"category":"food"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_missing_amount(self, client):
        t = tok(client, "neg_exp6")
        r = client.post("/api/expenses/", json={
            "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-06", "Create expense without amount",
               '{"category":"food","date":"2026-09-10"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_empty_body(self, client):
        t = tok(client, "neg_exp7")
        r = client.post("/api/expenses/", json={}, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-07", "Create expense with empty body",
               '{}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_get_nonexistent_expense(self, client):
        t = tok(client, "neg_exp8")
        r = client.get("/api/expenses/99999/", headers=h(t))
        ok = r.status_code == 404
        record("Negative/Expense", "N-EXP-08", "Get expense with non-existing ID",
               "GET /api/expenses/99999/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_update_nonexistent_expense(self, client):
        t = tok(client, "neg_exp9")
        r = client.put("/api/expenses/99999/", json={"amount": 100}, headers=h(t))
        ok = r.status_code == 404
        record("Negative/Expense", "N-EXP-09", "Update expense with non-existing ID",
               "PUT /api/expenses/99999/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_delete_nonexistent_expense(self, client):
        t = tok(client, "neg_exp10")
        r = client.delete("/api/expenses/99999/", headers=h(t))
        ok = r.status_code == 404
        record("Negative/Expense", "N-EXP-10", "Delete expense with non-existing ID",
               "DELETE /api/expenses/99999/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_update_negative_amount(self, client):
        t = tok(client, "neg_exp11")
        rid = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=h(t)).json()["id"]
        r = client.put(f"/api/expenses/{rid}/", json={"amount": -100}, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Expense", "N-EXP-11", "Update expense with negative amount",
               '{"amount":-100}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Income failures ───────────────────────────────────────

    def test_income_negative_amount(self, client):
        t = tok(client, "neg_inc1")
        r = client.post("/api/incomes/", json={
            "amount": -500, "source": "freelance", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-01", "Create income with negative amount",
               '{"amount":-500,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_zero_amount(self, client):
        t = tok(client, "neg_inc2")
        r = client.post("/api/incomes/", json={
            "amount": 0, "source": "freelance", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-02", "Create income with zero amount",
               '{"amount":0,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_invalid_source(self, client):
        t = tok(client, "neg_inc3")
        r = client.post("/api/incomes/", json={
            "amount": 100, "source": "bad_source", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-03", "Create income with invalid source",
               '{"source":"bad_source",...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_missing_source(self, client):
        t = tok(client, "neg_inc4")
        r = client.post("/api/incomes/", json={
            "amount": 100, "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-04", "Create income without source",
               '{"amount":100,"date":"2026-09-10"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_missing_amount(self, client):
        t = tok(client, "neg_inc5")
        r = client.post("/api/incomes/", json={
            "source": "freelance", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-05", "Create income without amount",
               '{"source":"freelance","date":"2026-09-10"}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_empty_body(self, client):
        t = tok(client, "neg_inc6")
        r = client.post("/api/incomes/", json={}, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Income", "N-INC-06", "Create income with empty body",
               '{}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_get_nonexistent_income(self, client):
        t = tok(client, "neg_inc7")
        r = client.get("/api/incomes/99999/", headers=h(t))
        ok = r.status_code == 404
        record("Negative/Income", "N-INC-07", "Get income with non-existing ID",
               "GET /api/incomes/99999/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Budget failures ───────────────────────────────────────

    def test_budget_invalid_month_too_high(self, client):
        t = tok(client, "neg_bud1")
        r = client.post("/api/budgets/", json={
            "month": 13, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": 1000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-01", "Create budget with month=13",
               '{"month":13,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_invalid_month_zero(self, client):
        t = tok(client, "neg_bud2")
        r = client.post("/api/budgets/", json={
            "month": 0, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": 1000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-02", "Create budget with month=0",
               '{"month":0,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_negative_total(self, client):
        t = tok(client, "neg_bud3")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": -500,
            "allocations": [{"category": "food", "amount": 500}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-03", "Create budget with negative total",
               '{"total_amount":-500,...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_negative_allocation(self, client):
        t = tok(client, "neg_bud4")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": -500}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-04", "Create budget with negative allocation",
               '{"allocations":[{"amount":-500}]}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_invalid_category(self, client):
        t = tok(client, "neg_bud5")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "bad_cat", "amount": 1000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-05", "Create budget with invalid allocation category",
               '{"category":"bad_cat",...}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_duplicate_month(self, client):
        t = tok(client, "neg_bud6")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 3000,
            "allocations": [{"category": "food", "amount": 3000}],
        }, headers=h(t))
        ok = r.status_code == 400
        record("Negative/Budget", "N-BUD-06", "Create budget for same month+year (duplicate)",
               "Two budgets for Sep 2026",
               "400 Budget already exists", f"{r.status_code}: {r.json().get('detail','')}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_get_nonexistent_budget(self, client):
        t = tok(client, "neg_bud7")
        r = client.get("/api/budgets/99999/", headers=h(t))
        ok = r.status_code == 404
        record("Negative/Budget", "N-BUD-07", "Get budget with non-existing ID",
               "GET /api/budgets/99999/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_update_negative_total(self, client):
        t = tok(client, "neg_bud8")
        rid = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t)).json()["id"]
        r = client.put(f"/api/budgets/{rid}/", json={"total_amount": -1}, headers=h(t))
        ok = r.status_code == 422
        record("Negative/Budget", "N-BUD-08", "Update budget with negative total",
               '{"total_amount":-1}',
               "422 validation error", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Unauthorized / Cross-user ─────────────────────────────

    def test_unauthenticated_expense_list(self, client):
        r = client.get("/api/expenses/")
        ok = r.status_code in (401, 403)
        record("Negative/Auth", "N-AUTH-08", "Access expenses without authentication",
               "GET /api/expenses/ (no token)",
               "401/403 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_unauthenticated_income_list(self, client):
        r = client.get("/api/incomes/")
        ok = r.status_code in (401, 403)
        record("Negative/Auth", "N-AUTH-09", "Access incomes without authentication",
               "GET /api/incomes/ (no token)",
               "401/403 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_unauthenticated_budget_list(self, client):
        r = client.get("/api/budgets/")
        ok = r.status_code in (401, 403)
        record("Negative/Auth", "N-AUTH-10", "Access budgets without authentication",
               "GET /api/budgets/ (no token)",
               "401/403 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_unauthenticated_transaction_summary(self, client):
        r = client.get("/api/transactions/summary/")
        ok = r.status_code in (401, 403)
        record("Negative/Auth", "N-AUTH-11", "Access transaction summary without authentication",
               "GET /api/transactions/summary/ (no token)",
               "401/403 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_cannot_see_expense(self, client):
        t1 = tok(client, "neg_xuser1", "neg_x1@test.com")
        t2 = tok(client, "neg_xuser2", "neg_x2@test.com")
        rid = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=h(t1)).json()["id"]
        r = client.get(f"/api/expenses/{rid}/", headers=h(t2))
        ok = r.status_code == 404
        record("Negative/Isolation", "N-ISO-01", "User B cannot read User A's expense",
               f"User B GET /api/expenses/{rid}/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_cannot_update_expense(self, client):
        t1 = tok(client, "neg_xuser3", "neg_x3@test.com")
        t2 = tok(client, "neg_xuser4", "neg_x4@test.com")
        rid = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=h(t1)).json()["id"]
        r = client.put(f"/api/expenses/{rid}/", json={"amount": 1}, headers=h(t2))
        ok = r.status_code == 404
        record("Negative/Isolation", "N-ISO-02", "User B cannot update User A's expense",
               f"User B PUT /api/expenses/{rid}/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_cannot_delete_expense(self, client):
        t1 = tok(client, "neg_xuser5", "neg_x5@test.com")
        t2 = tok(client, "neg_xuser6", "neg_x6@test.com")
        rid = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=h(t1)).json()["id"]
        r = client.delete(f"/api/expenses/{rid}/", headers=h(t2))
        ok = r.status_code == 404
        record("Negative/Isolation", "N-ISO-03", "User B cannot delete User A's expense",
               f"User B DELETE /api/expenses/{rid}/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_cannot_see_income(self, client):
        t1 = tok(client, "neg_xuser7", "neg_x7@test.com")
        t2 = tok(client, "neg_xuser8", "neg_x8@test.com")
        rid = client.post("/api/incomes/", json={
            "amount": 5000, "source": "scholarship", "date": "2026-09-01",
        }, headers=h(t1)).json()["id"]
        r = client.get(f"/api/incomes/{rid}/", headers=h(t2))
        ok = r.status_code == 404
        record("Negative/Isolation", "N-ISO-04", "User B cannot read User A's income",
               f"User B GET /api/incomes/{rid}/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_cannot_see_budget(self, client):
        t1 = tok(client, "neg_xuser9", "neg_x9@test.com")
        t2 = tok(client, "neg_xuser10", "neg_x10@test.com")
        rid = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t1)).json()["id"]
        r = client.get(f"/api/budgets/{rid}/", headers=h(t2))
        ok = r.status_code == 404
        record("Negative/Isolation", "N-ISO-05", "User B cannot read User A's budget",
               f"User B GET /api/budgets/{rid}/",
               "404 not found", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_cross_user_dashboard_empty(self, client):
        t1 = tok(client, "neg_xuser11", "neg_x11@test.com")
        t2 = tok(client, "neg_xuser12", "neg_x12@test.com")
        client.post("/api/incomes/", json={"amount": 10000, "source": "scholarship", "date": "2026-09-01"}, headers=h(t1))
        client.post("/api/expenses/", json={"amount": 3000, "category": "food", "date": "2026-09-10"}, headers=h(t1))
        r = client.get("/api/transactions/summary/", headers=h(t2))
        s = r.json()
        ok = s["total_income"] == 0 and s["total_expenses"] == 0
        record("Negative/Isolation", "N-ISO-06", "User B sees empty dashboard (not User A's data)",
               "User B GET /api/transactions/summary/",
               "income=0, expenses=0", f"income={s['total_income']}, expenses={s['total_expenses']}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_invalid_token_rejected(self, client):
        r = client.get("/api/expenses/", headers={"Authorization": "Bearer fake.jwt.token"})
        ok = r.status_code == 401
        record("Negative/Auth", "N-AUTH-12", "Access with invalid JWT token",
               "Bearer fake.jwt.token",
               "401 unauthorized", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok


# ══════════════════════════════════════════════════════════════════
# 3. BOUNDARY TESTING
# ══════════════════════════════════════════════════════════════════

class TestBoundary:
    """Test values at, below, and above defined limits."""

    # ── Amount boundaries ─────────────────────────────────────

    def test_expense_amount_at_minimum(self, client):
        """Amount just above 0 (0.01) should be accepted."""
        t = tok(client, "bnd_exp1")
        r = client.post("/api/expenses/", json={
            "amount": 0.01, "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Amount", "BND-AMT-01", "Expense amount = 0.01 (just above 0)",
               '{"amount":0.01,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_amount_at_zero(self, client):
        """Amount = 0 should be rejected."""
        t = tok(client, "bnd_exp2")
        r = client.post("/api/expenses/", json={
            "amount": 0, "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Amount", "BND-AMT-02", "Expense amount = 0 (at boundary)",
               '{"amount":0,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_amount_very_large(self, client):
        """Very large amount should be accepted."""
        t = tok(client, "bnd_exp3")
        r = client.post("/api/expenses/", json={
            "amount": 999999999.99, "category": "shopping", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201 and r.json()["amount"] == 999999999.99
        record("Boundary/Amount", "BND-AMT-03", "Expense amount = 999999999.99 (very large)",
               '{"amount":999999999.99,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_amount_at_minimum(self, client):
        """Income amount = 0.01 should be accepted."""
        t = tok(client, "bnd_inc1")
        r = client.post("/api/incomes/", json={
            "amount": 0.01, "source": "pocket_money", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Amount", "BND-AMT-04", "Income amount = 0.01 (just above 0)",
               '{"amount":0.01,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_amount_at_zero(self, client):
        """Income amount = 0 should be rejected."""
        t = tok(client, "bnd_inc2")
        r = client.post("/api/incomes/", json={
            "amount": 0, "source": "freelance", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Amount", "BND-AMT-05", "Income amount = 0 (at boundary)",
               '{"amount":0,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_income_amount_very_large(self, client):
        """Very large income amount should be accepted."""
        t = tok(client, "bnd_inc3")
        r = client.post("/api/incomes/", json={
            "amount": 999999999.99, "source": "scholarship", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Amount", "BND-AMT-06", "Income amount = 999999999.99 (very large)",
               '{"amount":999999999.99,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_total_at_minimum(self, client):
        """Budget total = 0.01 should be accepted."""
        t = tok(client, "bnd_bud1")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 0.01,
            "allocations": [{"category": "food", "amount": 0.01}],
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Amount", "BND-AMT-07", "Budget total = 0.01 (just above 0)",
               '{"total_amount":0.01,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_total_at_zero(self, client):
        """Budget total = 0 should be rejected."""
        t = tok(client, "bnd_bud2")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 0,
            "allocations": [{"category": "food", "amount": 1}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Amount", "BND-AMT-08", "Budget total = 0 (at boundary)",
               '{"total_amount":0,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Month boundaries ──────────────────────────────────────

    def test_budget_month_1_accepted(self, client):
        t = tok(client, "bnd_mon1")
        r = client.post("/api/budgets/", json={
            "month": 1, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Month", "BND-MON-01", "Budget month = 1 (lower bound)",
               '{"month":1,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_month_12_accepted(self, client):
        t = tok(client, "bnd_mon2")
        r = client.post("/api/budgets/", json={
            "month": 12, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Month", "BND-MON-02", "Budget month = 12 (upper bound)",
               '{"month":12,...}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_month_0_rejected(self, client):
        t = tok(client, "bnd_mon3")
        r = client.post("/api/budgets/", json={
            "month": 0, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Month", "BND-MON-03", "Budget month = 0 (below lower bound)",
               '{"month":0,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_month_13_rejected(self, client):
        t = tok(client, "bnd_mon4")
        r = client.post("/api/budgets/", json={
            "month": 13, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Month", "BND-MON-04", "Budget month = 13 (above upper bound)",
               '{"month":13,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_budget_month_negative_rejected(self, client):
        t = tok(client, "bnd_mon5")
        r = client.post("/api/budgets/", json={
            "month": -1, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h(t))
        ok = r.status_code == 422
        record("Boundary/Month", "BND-MON-05", "Budget month = -1 (negative)",
               '{"month":-1,...}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Username boundaries ───────────────────────────────────

    def test_username_at_min_length(self, client):
        """Username with exactly 3 chars should be accepted."""
        r = client.post("/api/auth/register/", json={
            "username": "abc", "email": "bnd@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        ok = r.status_code == 201
        record("Boundary/Username", "BND-USR-01", "Username = 3 chars (at minimum)",
               '{"username":"abc"}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_username_below_min_length(self, client):
        """Username with 2 chars should be rejected."""
        r = client.post("/api/auth/register/", json={
            "username": "ab", "email": "bnd2@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        ok = r.status_code == 422
        record("Boundary/Username", "BND-USR-02", "Username = 2 chars (below minimum)",
               '{"username":"ab"}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_username_long(self, client):
        """Very long username should be accepted."""
        long_name = "a" * 150
        r = client.post("/api/auth/register/", json={
            "username": long_name, "email": "bnd3@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        ok = r.status_code == 201
        record("Boundary/Username", "BND-USR-03", "Username = 150 chars (very long)",
               f'{{"username":"{"a"*150}"}}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Password boundaries ───────────────────────────────────

    def test_password_at_min_length(self, client):
        """Password with exactly 8 chars should be accepted."""
        r = client.post("/api/auth/register/", json={
            "username": "bnd_pw1", "email": "bndpw1@test.com",
            "password": "12345678", "password_confirm": "12345678",
        })
        ok = r.status_code == 201
        record("Boundary/Password", "BND-PW-01", "Password = 8 chars (at minimum)",
               '{"password":"12345678"}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_password_below_min_length(self, client):
        """Password with 7 chars should be rejected."""
        r = client.post("/api/auth/register/", json={
            "username": "bnd_pw2", "email": "bndpw2@test.com",
            "password": "1234567", "password_confirm": "1234567",
        })
        ok = r.status_code == 422
        record("Boundary/Password", "BND-PW-02", "Password = 7 chars (below minimum)",
               '{"password":"1234567"}',
               "422 rejected", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    # ── Description boundaries ────────────────────────────────

    def test_expense_empty_description(self, client):
        """Empty description should be accepted (optional field)."""
        t = tok(client, "bnd_desc1")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "description": "", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Description", "BND-DESC-01", "Expense with empty description",
               '{"description":""}',
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok

    def test_expense_no_description_field(self, client):
        """Omitting description should default to empty string."""
        t = tok(client, "bnd_desc2")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201 and r.json()["description"] == ""
        record("Boundary/Description", "BND-DESC-02", "Expense without description field (defaults empty)",
               "no description field",
               '201 + description=""', f"{r.status_code} desc='{r.json().get('description','')}'",
               "PASS" if ok else "FAIL")
        assert ok

    def test_expense_long_description(self, client):
        """Very long description should be accepted."""
        t = tok(client, "bnd_desc3")
        long_desc = "x" * 5000
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "description": long_desc, "date": "2026-09-10",
        }, headers=h(t))
        ok = r.status_code == 201
        record("Boundary/Description", "BND-DESC-03", "Expense with 5000-char description",
               f"description length = {len(long_desc)}",
               "201 accepted", f"{r.status_code}", "PASS" if ok else "FAIL")
        assert ok


# ══════════════════════════════════════════════════════════════════
# 4. REGRESSION TESTING
# ══════════════════════════════════════════════════════════════════

class TestRegression:
    """After each fix, confirm related functionality still works."""

    def test_auth_flow_after_fix(self, client):
        """Full auth flow: register -> login -> check -> refresh -> profile."""
        r = reg(client, "reg_flow1", "reg_flow1@test.com")
        assert r.status_code == 201
        token = r.json()["tokens"]["access"]
        refresh = r.json()["tokens"]["refresh"]

        # Login
        r = client.post("/api/auth/login/", json={"username": "reg_flow1", "password": "SecurePass123!"})
        assert r.status_code == 200
        token2 = r.json()["access"]

        # Check auth with both tokens
        r1 = client.get("/api/auth/check/", headers=h(token))
        r2 = client.get("/api/auth/check/", headers=h(token2))
        assert r1.status_code == 200 and r2.status_code == 200

        # Refresh
        r = client.post("/api/auth/token/refresh/", json={"refresh": refresh})
        assert r.status_code == 200

        # Profile
        r = client.get("/api/auth/profile/", headers=h(token))
        assert r.status_code == 200

        record("Regression", "REG-01", "Full auth flow still works after changes",
               "register -> login -> check -> refresh -> profile",
               "all return 200", "all passed", "PASS")

    def test_expense_crud_after_fix(self, client):
        """Full expense CRUD: create -> read -> update -> list -> filter -> delete."""
        t = tok(client, "reg_exp1")
        h_ = h(t)

        # Create
        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "description": "Test", "date": "2026-09-10",
        }, headers=h_)
        assert r.status_code == 201
        rid = r.json()["id"]

        # Read
        r = client.get(f"/api/expenses/{rid}/", headers=h_)
        assert r.status_code == 200

        # Update
        r = client.put(f"/api/expenses/{rid}/", json={"amount": 750}, headers=h_)
        assert r.status_code == 200 and r.json()["amount"] == 750.0

        # List
        r = client.get("/api/expenses/", headers=h_)
        assert r.status_code == 200 and r.json()["total"] >= 1

        # Filter
        r = client.get("/api/expenses/?category=food", headers=h_)
        assert r.status_code == 200

        # Delete
        r = client.delete(f"/api/expenses/{rid}/", headers=h_)
        assert r.status_code == 204

        # Confirm gone
        r = client.get(f"/api/expenses/{rid}/", headers=h_)
        assert r.status_code == 404

        record("Regression", "REG-02", "Full expense CRUD still works after changes",
               "C -> R -> U -> List -> Filter -> D -> Confirm gone",
               "all return expected status", "all passed", "PASS")

    def test_income_crud_after_fix(self, client):
        """Full income CRUD: create -> read -> update -> list -> filter -> delete."""
        t = tok(client, "reg_inc1")
        h_ = h(t)

        r = client.post("/api/incomes/", json={
            "amount": 5000, "source": "scholarship", "date": "2026-09-01",
        }, headers=h_)
        assert r.status_code == 201
        rid = r.json()["id"]

        r = client.get(f"/api/incomes/{rid}/", headers=h_)
        assert r.status_code == 200

        r = client.put(f"/api/incomes/{rid}/", json={"amount": 6000}, headers=h_)
        assert r.status_code == 200 and r.json()["amount"] == 6000.0

        r = client.get("/api/incomes/", headers=h_)
        assert r.status_code == 200

        r = client.get("/api/incomes/?source=scholarship", headers=h_)
        assert r.status_code == 200

        r = client.delete(f"/api/incomes/{rid}/", headers=h_)
        assert r.status_code == 204

        r = client.get(f"/api/incomes/{rid}/", headers=h_)
        assert r.status_code == 404

        record("Regression", "REG-03", "Full income CRUD still works after changes",
               "C -> R -> U -> List -> Filter -> D -> Confirm gone",
               "all return expected status", "all passed", "PASS")

    def test_budget_crud_after_fix(self, client):
        """Full budget CRUD: create -> read -> update -> list -> filter -> delete."""
        t = tok(client, "reg_bud1")
        h_ = h(t)

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=h_)
        assert r.status_code == 201
        rid = r.json()["id"]

        r = client.get(f"/api/budgets/{rid}/", headers=h_)
        assert r.status_code == 200

        r = client.put(f"/api/budgets/{rid}/", json={"total_amount": 8000}, headers=h_)
        assert r.status_code == 200 and r.json()["total_amount"] == 8000.0

        r = client.get("/api/budgets/", headers=h_)
        assert r.status_code == 200

        r = client.get("/api/budgets/?year=2026", headers=h_)
        assert r.status_code == 200

        r = client.delete(f"/api/budgets/{rid}/", headers=h_)
        assert r.status_code == 204

        r = client.get(f"/api/budgets/{rid}/", headers=h_)
        assert r.status_code == 404

        record("Regression", "REG-04", "Full budget CRUD still works after changes",
               "C -> R -> U -> List -> Filter -> D -> Confirm gone",
               "all return expected status", "all passed", "PASS")

    def test_dashboard_after_expense_delete(self, client):
        """Dashboard summary updates correctly after deleting an expense."""
        t = tok(client, "reg_dash1")
        h_ = h(t)

        client.post("/api/incomes/", json={"amount": 10000, "source": "scholarship", "date": "2026-09-01"}, headers=h_)
        r = client.post("/api/expenses/", json={"amount": 3000, "category": "food", "date": "2026-09-10"}, headers=h_)
        exp_id = r.json()["id"]

        s1 = client.get("/api/transactions/summary/", headers=h_).json()
        assert s1["total_expenses"] == 3000.0

        client.delete(f"/api/expenses/{exp_id}/", headers=h_)

        s2 = client.get("/api/transactions/summary/", headers=h_).json()
        ok = s2["total_expenses"] == 0.0 and s2["balance"] == 10000.0
        record("Regression", "REG-05", "Dashboard updates after expense delete",
               "Create income+expense, delete expense, check summary",
               "expenses=0, balance=10000", f"expenses={s2['total_expenses']}, balance={s2['balance']}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_dashboard_after_income_delete(self, client):
        """Dashboard summary updates correctly after deleting an income."""
        t = tok(client, "reg_dash2")
        h_ = h(t)

        r = client.post("/api/incomes/", json={"amount": 10000, "source": "freelance", "date": "2026-09-01"}, headers=h_)
        inc_id = r.json()["id"]
        client.post("/api/expenses/", json={"amount": 2000, "category": "shopping", "date": "2026-09-10"}, headers=h_)

        s1 = client.get("/api/transactions/summary/", headers=h_).json()
        assert s1["total_income"] == 10000.0

        client.delete(f"/api/incomes/{inc_id}/", headers=h_)

        s2 = client.get("/api/transactions/summary/", headers=h_).json()
        ok = s2["total_income"] == 0.0 and s2["balance"] == -2000.0
        record("Regression", "REG-06", "Dashboard updates after income delete",
               "Create income+expense, delete income, check summary",
               "income=0, balance=-2000", f"income={s2['total_income']}, balance={s2['balance']}",
               "PASS" if ok else "FAIL")
        assert ok

    def test_isolation_after_fix(self, client):
        """User isolation still works across all modules."""
        t1 = tok(client, "reg_iso1", "reg_iso1@test.com")
        t2 = tok(client, "reg_iso2", "reg_iso2@test.com")

        # User1 creates data
        e_id = client.post("/api/expenses/", json={"amount": 100, "category": "food", "date": "2026-09-10"}, headers=h(t1)).json()["id"]
        i_id = client.post("/api/incomes/", json={"amount": 500, "source": "freelance", "date": "2026-09-01"}, headers=h(t1)).json()["id"]
        b_id = client.post("/api/budgets/", json={"month": 9, "year": 2026, "total_amount": 5000, "allocations": [{"category": "food", "amount": 5000}]}, headers=h(t1)).json()["id"]

        # User2 cannot access any of User1's data
        checks = [
            client.get(f"/api/expenses/{e_id}/", headers=h(t2)).status_code == 404,
            client.put(f"/api/expenses/{e_id}/", json={"amount": 1}, headers=h(t2)).status_code == 404,
            client.delete(f"/api/expenses/{e_id}/", headers=h(t2)).status_code == 404,
            client.get(f"/api/incomes/{i_id}/", headers=h(t2)).status_code == 404,
            client.put(f"/api/incomes/{i_id}/", json={"amount": 1}, headers=h(t2)).status_code == 404,
            client.delete(f"/api/incomes/{i_id}/", headers=h(t2)).status_code == 404,
            client.get(f"/api/budgets/{b_id}/", headers=h(t2)).status_code == 404,
            client.put(f"/api/budgets/{b_id}/", json={"total_amount": 1}, headers=h(t2)).status_code == 404,
            client.delete(f"/api/budgets/{b_id}/", headers=h(t2)).status_code == 404,
            client.get("/api/expenses/", headers=h(t2)).json()["total"] == 0,
            client.get("/api/incomes/", headers=h(t2)).json()["total"] == 0,
            client.get("/api/budgets/", headers=h(t2)).json()["total"] == 0,
        ]
        ok = all(checks)
        record("Regression", "REG-07", "User isolation still works across all modules",
               "User1 creates data, User2 tries all operations",
               "all return 404/empty", f"all={all(checks)}", "PASS" if ok else "FAIL")
        assert ok


# ══════════════════════════════════════════════════════════════════
# 5. REPORT GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_report():
    """Print full test case report and defect log."""
    print("\n" + "=" * 80)
    print("TEST CASE REPORT — Milestone 2 Systematic Testing")
    print("=" * 80)

    # Group by category
    cats = {}
    for r in RESULTS:
        cats.setdefault(r["category"], []).append(r)

    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = total - passed

    for cat, rows in sorted(cats.items()):
        cat_pass = sum(1 for r in rows if r["status"] == "PASS")
        cat_fail = len(rows) - cat_pass
        print(f"\n--- {cat} ({cat_pass}/{len(rows)} PASS) ---")
        for r in rows:
            mark = "PASS" if r["status"] == "PASS" else "FAIL"
            print(f"  [{mark}] {r['tc_id']}: {r['description']}")
            if r["status"] == "FAIL":
                print(f"         Input:    {r['input']}")
                print(f"         Expected: {r['expected']}")
                print(f"         Actual:   {r['actual']}")

    print("\n" + "=" * 80)
    print(f"TOTAL: {total}  |  PASSED: {passed}  |  FAILED: {failed}")
    print("=" * 80)

    if DEFECTS:
        print("\n" + "=" * 80)
        print("DEFECT LOG")
        print("=" * 80)
        for d in DEFECTS:
            print(f"\n  {d['id']}: {d['issue']}")
            print(f"    Steps:     TC {d['tc_id']}")
            print(f"    Expected:  {d['expected']}")
            print(f"    Actual:    {d['actual']}")
            print(f"    Status:    OPEN")
    else:
        print("\nNo defects found.")

    return total, passed, failed


# ══════════════════════════════════════════════════════════════════
# PYTEST HOOK — print report after all tests
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def session_report(request):
    yield
    generate_report()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-q"])
