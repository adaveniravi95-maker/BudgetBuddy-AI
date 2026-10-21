"""
Milestone 2 - Comprehensive Integration Tests
==============================================
Tests all cross-module flows, failure cases, data consistency, and user isolation.

Flows tested:
  1. React -> Expense API -> Database
  2. React -> Income API -> Database
  3. Expense -> Category -> Database
  4. Income/Expense -> Transaction Dashboard
  5. Expense Category -> Budget Category
  6. Authenticated User -> User-specific data across all modules

Run:  cd backend && python -m pytest test_integration.py -v
"""

import sys
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models, auth


# ─── Test Database Setup ───────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ─── Helpers ────────────────────────────────────────────────────

def register_user(client, username, email="test@test.com", password="SecurePass123!"):
    return client.post("/api/auth/register/", json={
        "username": username,
        "email": email,
        "password": password,
        "password_confirm": password,
    })


def login_user(client, username, password="SecurePass123!"):
    return client.post("/api/auth/login/", json={
        "username": username,
        "password": password,
    })


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_token(client, username, email=None):
    """Register or login and return the access token."""
    if email is None:
        email = f"{username}@test.com"
    r = register_user(client, username, email)
    if r.status_code == 201:
        return r.json()["tokens"]["access"]
    r = login_user(client, username)
    return r.json()["access"]


# ══════════════════════════════════════════════════════════════════
# FLOW 1: React -> Expense API -> Database
# ══════════════════════════════════════════════════════════════════

class TestFlowExpenseAPI:
    """Verify Expense CRUD goes through API -> Backend -> Database correctly."""

    def test_create_expense_persists_to_db(self, client, db):
        token = get_token(client, "exp_user1")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 1500.50,
            "category": "food",
            "description": "Groceries",
            "date": "2026-09-15",
        }, headers=headers)

        assert r.status_code == 201
        data = r.json()
        assert data["amount"] == 1500.50
        assert data["category"] == "food"
        assert data["description"] == "Groceries"
        assert data["date"] == "2026-09-15"
        assert "id" in data

        # Verify in database directly
        user = db.query(models.User).filter(models.User.username == "exp_user1").first()
        expense = db.query(models.Expense).filter(
            models.Expense.user_id == user.id,
            models.Expense.id == data["id"],
        ).first()
        assert expense is not None
        assert float(expense.amount) == 1500.50
        assert expense.category.value == "food"

    def test_read_expense_from_api(self, client):
        token = get_token(client, "exp_user2")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "travel", "date": "2026-09-10",
        }, headers=headers)
        exp_id = r.json()["id"]

        r = client.get(f"/api/expenses/{exp_id}/", headers=headers)
        assert r.status_code == 200
        assert r.json()["category"] == "travel"
        assert r.json()["amount"] == 500.0

    def test_update_expense_persists(self, client):
        token = get_token(client, "exp_user3")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 200, "category": "education", "date": "2026-09-10",
        }, headers=headers)
        exp_id = r.json()["id"]

        r = client.put(f"/api/expenses/{exp_id}/", json={
            "amount": 350, "description": "Updated book",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["amount"] == 350.0
        assert r.json()["description"] == "Updated book"

    def test_delete_expense_removes_from_db(self, client, db):
        token = get_token(client, "exp_user4")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "entertainment", "date": "2026-09-10",
        }, headers=headers)
        exp_id = r.json()["id"]

        r = client.delete(f"/api/expenses/{exp_id}/", headers=headers)
        assert r.status_code == 204

        # Verify gone from database
        user = db.query(models.User).filter(models.User.username == "exp_user4").first()
        expense = db.query(models.Expense).filter(
            models.Expense.id == exp_id,
            models.Expense.user_id == user.id,
        ).first()
        assert expense is None

    def test_list_expenses_returns_all(self, client):
        token = get_token(client, "exp_user5")
        headers = auth_header(token)

        for cat in ["food", "travel", "shopping"]:
            client.post("/api/expenses/", json={
                "amount": 100, "category": cat, "date": "2026-09-10",
            }, headers=headers)

        r = client.get("/api/expenses/", headers=headers)
        assert r.status_code == 200
        assert r.json()["total"] == 3

    def test_filter_expenses_by_category(self, client):
        token = get_token(client, "exp_user6")
        headers = auth_header(token)

        client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "date": "2026-09-10",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 200, "category": "travel", "date": "2026-09-10",
        }, headers=headers)

        r = client.get("/api/expenses/?category=food", headers=headers)
        assert r.json()["total"] == 1
        assert r.json()["expenses"][0]["category"] == "food"


# ══════════════════════════════════════════════════════════════════
# FLOW 2: React -> Income API -> Database
# ══════════════════════════════════════════════════════════════════

class TestFlowIncomeAPI:
    """Verify Income CRUD goes through API -> Backend -> Database correctly."""

    def test_create_income_persists_to_db(self, client, db):
        token = get_token(client, "inc_user1")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 25000,
            "source": "scholarship",
            "description": "Fall semester",
            "date": "2026-09-01",
        }, headers=headers)

        assert r.status_code == 201
        data = r.json()
        assert data["amount"] == 25000.0
        assert data["source"] == "scholarship"
        assert data["description"] == "Fall semester"

        # Verify in database
        user = db.query(models.User).filter(models.User.username == "inc_user1").first()
        income = db.query(models.Income).filter(
            models.Income.user_id == user.id,
            models.Income.id == data["id"],
        ).first()
        assert income is not None
        assert float(income.amount) == 25000.0
        assert income.source.value == "scholarship"

    def test_read_income_from_api(self, client):
        token = get_token(client, "inc_user2")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 5000, "source": "freelance", "date": "2026-09-05",
        }, headers=headers)
        inc_id = r.json()["id"]

        r = client.get(f"/api/incomes/{inc_id}/", headers=headers)
        assert r.status_code == 200
        assert r.json()["source"] == "freelance"

    def test_update_income_persists(self, client):
        token = get_token(client, "inc_user3")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 3000, "source": "pocket_money", "date": "2026-09-10",
        }, headers=headers)
        inc_id = r.json()["id"]

        r = client.put(f"/api/incomes/{inc_id}/", json={
            "amount": 4500, "description": "Extra allowance",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["amount"] == 4500.0

    def test_delete_income_removes_from_db(self, client, db):
        token = get_token(client, "inc_user4")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 1000, "source": "freelance", "date": "2026-09-10",
        }, headers=headers)
        inc_id = r.json()["id"]

        r = client.delete(f"/api/incomes/{inc_id}/", headers=headers)
        assert r.status_code == 204

        user = db.query(models.User).filter(models.User.username == "inc_user4").first()
        income = db.query(models.Income).filter(
            models.Income.id == inc_id,
            models.Income.user_id == user.id,
        ).first()
        assert income is None

    def test_list_incomes_returns_all(self, client):
        token = get_token(client, "inc_user5")
        headers = auth_header(token)

        for src in ["pocket_money", "scholarship", "freelance"]:
            client.post("/api/incomes/", json={
                "amount": 1000, "source": src, "date": "2026-09-10",
            }, headers=headers)

        r = client.get("/api/incomes/", headers=headers)
        assert r.status_code == 200
        assert r.json()["total"] == 3

    def test_filter_incomes_by_source(self, client):
        token = get_token(client, "inc_user6")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 100, "source": "pocket_money", "date": "2026-09-10",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 200, "source": "scholarship", "date": "2026-09-10",
        }, headers=headers)

        r = client.get("/api/incomes/?source=pocket_money", headers=headers)
        assert r.json()["total"] == 1
        assert r.json()["incomes"][0]["source"] == "pocket_money"


# ══════════════════════════════════════════════════════════════════
# FLOW 3: Expense -> Category -> Database
# ══════════════════════════════════════════════════════════════════

class TestFlowExpenseCategory:
    """Verify expense categories are properly stored and retrieved."""

    ALL_CATEGORIES = ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]

    def test_all_categories_create_and_persist(self, client, db):
        token = get_token(client, "cat_user1")
        headers = auth_header(token)
        user = db.query(models.User).filter(models.User.username == "cat_user1").first()

        for cat in self.ALL_CATEGORIES:
            r = client.post("/api/expenses/", json={
                "amount": 100, "category": cat, "date": "2026-09-15",
            }, headers=headers)
            assert r.status_code == 201
            assert r.json()["category"] == cat

        # Verify all 6 categories exist in DB
        expenses = db.query(models.Expense).filter(models.Expense.user_id == user.id).all()
        db_cats = set(e.category.value for e in expenses)
        assert db_cats == set(self.ALL_CATEGORIES)

    def test_category_roundtrip_via_api(self, client):
        token = get_token(client, "cat_user2")
        headers = auth_header(token)

        # Create with category, read back, update category, read again
        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=headers)
        exp_id = r.json()["id"]
        assert r.json()["category"] == "food"

        # Update category
        r = client.put(f"/api/expenses/{exp_id}/", json={"category": "travel"}, headers=headers)
        assert r.json()["category"] == "travel"

        # Read back and verify
        r = client.get(f"/api/expenses/{exp_id}/", headers=headers)
        assert r.json()["category"] == "travel"

    def test_invalid_category_rejected(self, client):
        token = get_token(client, "cat_user3")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "invalid_category", "date": "2026-09-10",
        }, headers=headers)
        assert r.status_code == 422

    def test_missing_category_rejected(self, client):
        token = get_token(client, "cat_user4")
        headers = auth_header(token)

        r = client.post("/api/expenses/", json={
            "amount": 100, "date": "2026-09-10",
        }, headers=headers)
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════
# FLOW 4: Income/Expense -> Transaction Dashboard
# ══════════════════════════════════════════════════════════════════

class TestFlowTransactionDashboard:
    """Verify the transaction dashboard aggregates income + expense data correctly."""

    def test_summary_reflects_actual_records(self, client, db):
        token = get_token(client, "dash_user1")
        headers = auth_header(token)
        user = db.query(models.User).filter(models.User.username == "dash_user1").first()

        # Create 2 incomes, 3 expenses
        client.post("/api/incomes/", json={
            "amount": 10000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 5000, "source": "freelance", "date": "2026-09-05",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 2000, "category": "food", "date": "2026-09-10",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1500, "category": "travel", "date": "2026-09-12",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 500, "category": "entertainment", "date": "2026-09-14",
        }, headers=headers)

        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.status_code == 200
        s = r.json()
        assert s["total_income"] == 15000.0
        assert s["total_expenses"] == 4000.0
        assert s["balance"] == 11000.0
        assert s["income_count"] == 2
        assert s["expense_count"] == 3

    def test_summary_formula_consistency(self, client):
        token = get_token(client, "dash_user2")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 8000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 3000, "category": "food", "date": "2026-09-10",
        }, headers=headers)

        r = client.get("/api/transactions/summary/", headers=headers)
        s = r.json()
        assert s["balance"] == s["total_income"] - s["total_expenses"]

    def test_transaction_list_includes_both_types(self, client):
        token = get_token(client, "dash_user3")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 5000, "source": "freelance", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1000, "category": "shopping", "date": "2026-09-15",
        }, headers=headers)

        r = client.get("/api/transactions/", headers=headers)
        assert r.status_code == 200
        txs = r.json()["transactions"]
        types = {t["type"] for t in txs}
        assert "income" in types
        assert "expense" in types
        assert r.json()["total"] == 2

    def test_transactions_sorted_by_date_desc(self, client):
        token = get_token(client, "dash_user4")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 1000, "source": "pocket_money", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 2000, "source": "freelance", "date": "2026-09-15",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 3000, "source": "scholarship", "date": "2026-09-10",
        }, headers=headers)

        r = client.get("/api/transactions/", headers=headers)
        dates = [t["date"] for t in r.json()["transactions"]]
        assert dates == sorted(dates, reverse=True)

    def test_filter_transactions_by_type(self, client):
        token = get_token(client, "dash_user5")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 5000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1000, "category": "food", "date": "2026-09-10",
        }, headers=headers)

        r = client.get("/api/transactions/?type=income", headers=headers)
        assert r.json()["total"] == 1
        assert r.json()["transactions"][0]["type"] == "income"

        r = client.get("/api/transactions/?type=expense", headers=headers)
        assert r.json()["total"] == 1
        assert r.json()["transactions"][0]["type"] == "expense"

    def test_filter_transactions_by_date_range(self, client):
        token = get_token(client, "dash_user6")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 1000, "source": "pocket_money", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 2000, "source": "freelance", "date": "2026-09-15",
        }, headers=headers)

        r = client.get("/api/transactions/?start_date=2026-09-10&end_date=2026-09-30", headers=headers)
        assert r.json()["total"] == 1
        assert r.json()["transactions"][0]["date"] == "2026-09-15"

    def test_summary_updates_after_delete(self, client):
        token = get_token(client, "dash_user7")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 10000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        inc_id = r.json()["id"]

        client.post("/api/expenses/", json={
            "amount": 3000, "category": "food", "date": "2026-09-10",
        }, headers=headers)

        # Before delete
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 10000.0

        # Delete income
        client.delete(f"/api/incomes/{inc_id}/", headers=headers)

        # After delete - summary must update
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 0.0
        assert r.json()["balance"] == -3000.0


# ══════════════════════════════════════════════════════════════════
# FLOW 5: Expense Category -> Budget Category
# ══════════════════════════════════════════════════════════════════

class TestFlowBudgetCategory:
    """Verify budget allocations use the same expense categories."""

    ALL_CATEGORIES = ["food", "travel", "shopping", "education", "entertainment", "miscellaneous"]

    def test_budget_allocations_match_expense_categories(self, client, db):
        token = get_token(client, "budcat_user1")
        headers = auth_header(token)
        user = db.query(models.User).filter(models.User.username == "budcat_user1").first()

        allocs = [{"category": cat, "amount": 1000} for cat in self.ALL_CATEGORIES]
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 6000,
            "allocations": allocs,
        }, headers=headers)
        assert r.status_code == 201
        bud = r.json()
        assert len(bud["allocations"]) == 6

        # Verify in DB
        budget_db = db.query(models.Budget).filter(
            models.Budget.id == bud["id"],
            models.Budget.user_id == user.id,
        ).first()
        assert budget_db is not None
        db_alloc_cats = set(a.category.value for a in budget_db.allocations)
        assert db_alloc_cats == set(self.ALL_CATEGORIES)

    def test_budget_category_matches_expense_category(self, client):
        """A budget for 'food' should correspond to expenses with category 'food'."""
        token = get_token(client, "budcat_user2")
        headers = auth_header(token)

        # Create budget for food = 5000
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=headers)
        assert r.status_code == 201

        # Create expense with category food = 3000
        client.post("/api/expenses/", json={
            "amount": 3000, "category": "food", "date": "2026-09-15",
        }, headers=headers)

        # Read budget back - food allocation should be 5000
        bud_id = r.json()["id"]
        r = client.get(f"/api/budgets/{bud_id}/", headers=headers)
        food_alloc = [a for a in r.json()["allocations"] if a["category"] == "food"]
        assert len(food_alloc) == 1
        assert food_alloc[0]["amount"] == 5000.0

    def test_budget_only_expense_categories_allowed(self, client):
        token = get_token(client, "budcat_user3")
        headers = auth_header(token)

        # Invalid category in budget allocation
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "invalid_cat", "amount": 1000}],
        }, headers=headers)
        assert r.status_code == 422

    def test_budget_update_allocations(self, client):
        token = get_token(client, "budcat_user4")
        headers = auth_header(token)

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [
                {"category": "food", "amount": 3000},
                {"category": "travel", "amount": 2000},
            ],
        }, headers=headers)
        bud_id = r.json()["id"]

        # Update allocations - replace entirely
        r = client.put(f"/api/budgets/{bud_id}/", json={
            "allocations": [
                {"category": "food", "amount": 2500},
                {"category": "shopping", "amount": 2500},
            ],
        }, headers=headers)
        assert r.status_code == 200
        alloc_map = {a["category"]: a["amount"] for a in r.json()["allocations"]}
        assert alloc_map["food"] == 2500.0
        assert alloc_map["shopping"] == 2500.0
        assert "travel" not in alloc_map


# ══════════════════════════════════════════════════════════════════
# FLOW 6: Authenticated User -> User-specific Data
# ══════════════════════════════════════════════════════════════════

class TestFlowUserIsolation:
    """Verify each user only sees their own data across all modules."""

    def test_expense_isolation(self, client):
        tok_a = get_token(client, "iso_user_a", "iso_a@test.com")
        tok_b = get_token(client, "iso_user_b", "iso_b@test.com")
        ha, hb = auth_header(tok_a), auth_header(tok_b)

        # Alice creates expense
        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-10",
        }, headers=ha)
        exp_id = r.json()["id"]

        # Bob cannot see Alice's expense
        r = client.get(f"/api/expenses/{exp_id}/", headers=hb)
        assert r.status_code == 404

        # Bob cannot update Alice's expense
        r = client.put(f"/api/expenses/{exp_id}/", json={"amount": 1}, headers=hb)
        assert r.status_code == 404

        # Bob cannot delete Alice's expense
        r = client.delete(f"/api/expenses/{exp_id}/", headers=hb)
        assert r.status_code == 404

        # Bob sees no expenses
        r = client.get("/api/expenses/", headers=hb)
        assert r.json()["total"] == 0

    def test_income_isolation(self, client):
        tok_a = get_token(client, "iso2_user_a", "iso2_a@test.com")
        tok_b = get_token(client, "iso2_user_b", "iso2_b@test.com")
        ha, hb = auth_header(tok_a), auth_header(tok_b)

        r = client.post("/api/incomes/", json={
            "amount": 5000, "source": "scholarship", "date": "2026-09-01",
        }, headers=ha)
        inc_id = r.json()["id"]

        r = client.get(f"/api/incomes/{inc_id}/", headers=hb)
        assert r.status_code == 404

        r = client.put(f"/api/incomes/{inc_id}/", json={"amount": 1}, headers=hb)
        assert r.status_code == 404

        r = client.delete(f"/api/incomes/{inc_id}/", headers=hb)
        assert r.status_code == 404

        r = client.get("/api/incomes/", headers=hb)
        assert r.json()["total"] == 0

    def test_budget_isolation(self, client):
        tok_a = get_token(client, "iso3_user_a", "iso3_a@test.com")
        tok_b = get_token(client, "iso3_user_b", "iso3_b@test.com")
        ha, hb = auth_header(tok_a), auth_header(tok_b)

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=ha)
        bud_id = r.json()["id"]

        r = client.get(f"/api/budgets/{bud_id}/", headers=hb)
        assert r.status_code == 404

        r = client.put(f"/api/budgets/{bud_id}/", json={"total_amount": 1}, headers=hb)
        assert r.status_code == 404

        r = client.delete(f"/api/budgets/{bud_id}/", headers=hb)
        assert r.status_code == 404

        r = client.get("/api/budgets/", headers=hb)
        assert r.json()["total"] == 0

    def test_transaction_dashboard_isolation(self, client):
        tok_a = get_token(client, "iso4_user_a", "iso4_a@test.com")
        tok_b = get_token(client, "iso4_user_b", "iso4_b@test.com")
        ha, hb = auth_header(tok_a), auth_header(tok_b)

        client.post("/api/incomes/", json={
            "amount": 10000, "source": "scholarship", "date": "2026-09-01",
        }, headers=ha)
        client.post("/api/expenses/", json={
            "amount": 2000, "category": "food", "date": "2026-09-10",
        }, headers=ha)

        # Bob's dashboard is empty
        r = client.get("/api/transactions/summary/", headers=hb)
        s = r.json()
        assert s["total_income"] == 0
        assert s["total_expenses"] == 0
        assert s["balance"] == 0

        r = client.get("/api/transactions/", headers=hb)
        assert r.json()["total"] == 0

    def test_unauthenticated_request_rejected(self, client):
        endpoints = [
            ("GET", "/api/expenses/"),
            ("POST", "/api/expenses/"),
            ("GET", "/api/incomes/"),
            ("POST", "/api/incomes/"),
            ("GET", "/api/transactions/summary/"),
            ("GET", "/api/transactions/"),
            ("GET", "/api/budgets/"),
            ("POST", "/api/budgets/"),
        ]
        for method, url in endpoints:
            if method == "GET":
                r = client.get(url)
            else:
                r = client.post(url, json={})
            assert r.status_code in (401, 403), f"{method} {url} should reject unauth: got {r.status_code}"


# ══════════════════════════════════════════════════════════════════
# FAILURE CASES
# ══════════════════════════════════════════════════════════════════

class TestFailureCases:
    """Test invalid inputs, missing data, non-existing records, etc."""

    # ── Invalid Input ──

    def test_expense_negative_amount_rejected(self, client):
        token = get_token(client, "fail_user1")
        r = client.post("/api/expenses/", json={
            "amount": -100, "category": "food", "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_expense_zero_amount_rejected(self, client):
        token = get_token(client, "fail_user2")
        r = client.post("/api/expenses/", json={
            "amount": 0, "category": "food", "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_income_negative_amount_rejected(self, client):
        token = get_token(client, "fail_user3")
        r = client.post("/api/incomes/", json={
            "amount": -500, "source": "freelance", "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_budget_invalid_month_rejected(self, client):
        token = get_token(client, "fail_user4")
        r = client.post("/api/budgets/", json={
            "month": 13, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": 1000}],
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_budget_month_zero_rejected(self, client):
        token = get_token(client, "fail_user5")
        r = client.post("/api/budgets/", json={
            "month": 0, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": 1000}],
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_budget_negative_total_rejected(self, client):
        token = get_token(client, "fail_user6")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": -500,
            "allocations": [{"category": "food", "amount": 500}],
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_budget_negative_allocation_rejected(self, client):
        token = get_token(client, "fail_user7")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": -500}],
        }, headers=auth_header(token))
        assert r.status_code == 422

    # ── Missing Required Data ──

    def test_expense_missing_category_rejected(self, client):
        token = get_token(client, "fail_user8")
        r = client.post("/api/expenses/", json={
            "amount": 100, "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_expense_missing_date_rejected(self, client):
        token = get_token(client, "fail_user9")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_income_missing_source_rejected(self, client):
        token = get_token(client, "fail_user10")
        r = client.post("/api/incomes/", json={
            "amount": 1000, "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    def test_income_missing_amount_rejected(self, client):
        token = get_token(client, "fail_user11")
        r = client.post("/api/incomes/", json={
            "source": "freelance", "date": "2026-09-10",
        }, headers=auth_header(token))
        assert r.status_code == 422

    # ── Non-existing Records ──

    def test_get_nonexistent_expense_returns_404(self, client):
        token = get_token(client, "fail_user12")
        r = client.get("/api/expenses/99999/", headers=auth_header(token))
        assert r.status_code == 404

    def test_update_nonexistent_expense_returns_404(self, client):
        token = get_token(client, "fail_user13")
        r = client.put("/api/expenses/99999/", json={"amount": 100}, headers=auth_header(token))
        assert r.status_code == 404

    def test_delete_nonexistent_expense_returns_404(self, client):
        token = get_token(client, "fail_user14")
        r = client.delete("/api/expenses/99999/", headers=auth_header(token))
        assert r.status_code == 404

    def test_get_nonexistent_income_returns_404(self, client):
        token = get_token(client, "fail_user15")
        r = client.get("/api/incomes/99999/", headers=auth_header(token))
        assert r.status_code == 404

    def test_get_nonexistent_budget_returns_404(self, client):
        token = get_token(client, "fail_user16")
        r = client.get("/api/budgets/99999/", headers=auth_header(token))
        assert r.status_code == 404

    def test_update_nonexistent_budget_returns_404(self, client):
        token = get_token(client, "fail_user17")
        r = client.put("/api/budgets/99999/", json={"total_amount": 100}, headers=auth_header(token))
        assert r.status_code == 404

    def test_delete_nonexistent_budget_returns_404(self, client):
        token = get_token(client, "fail_user18")
        r = client.delete("/api/budgets/99999/", headers=auth_header(token))
        assert r.status_code == 404

    # ── Duplicate Budget ──

    def test_duplicate_budget_month_rejected(self, client):
        token = get_token(client, "fail_user19")
        headers = auth_header(token)

        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=headers)

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 3000,
            "allocations": [{"category": "food", "amount": 3000}],
        }, headers=headers)
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]

    # ── Registration Failures ──

    def test_register_duplicate_username_rejected(self, client):
        client.post("/api/auth/register/", json={
            "username": "dup_user", "email": "dup1@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        r = client.post("/api/auth/register/", json={
            "username": "dup_user", "email": "dup2@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        assert r.status_code == 400
        assert "Username already exists" in r.json()["detail"]

    def test_register_duplicate_email_rejected(self, client):
        client.post("/api/auth/register/", json={
            "username": "dup_email1", "email": "same@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        r = client.post("/api/auth/register/", json={
            "username": "dup_email2", "email": "same@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        assert r.status_code == 400
        assert "Email already exists" in r.json()["detail"]

    def test_register_short_username_rejected(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "ab", "email": "short@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        assert r.status_code == 422

    def test_register_short_password_rejected(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "validuser", "email": "valid@test.com",
            "password": "short", "password_confirm": "short",
        })
        assert r.status_code == 422

    def test_register_mismatched_passwords_rejected(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "mismatch", "email": "mismatch@test.com",
            "password": "SecurePass123!", "password_confirm": "DifferentPass!",
        })
        assert r.status_code == 422

    def test_login_wrong_password_rejected(self, client):
        client.post("/api/auth/register/", json={
            "username": "login_fail", "email": "loginfail@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        r = client.post("/api/auth/login/", json={
            "username": "login_fail", "password": "WrongPassword!",
        })
        assert r.status_code == 401

    def test_login_nonexistent_user_rejected(self, client):
        r = client.post("/api/auth/login/", json={
            "username": "ghost_user", "password": "Whatever123!",
        })
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════
# DATA CONSISTENCY
# ══════════════════════════════════════════════════════════════════

class TestDataConsistency:
    """Verify cross-module data remains consistent after operations."""

    def test_add_income_updates_financial_info(self, client):
        token = get_token(client, "cons_user1")
        headers = auth_header(token)

        # Initial: zero
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 0

        # Add income
        client.post("/api/incomes/", json={
            "amount": 15000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)

        # Summary updates
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 15000.0
        assert r.json()["income_count"] == 1
        assert r.json()["balance"] == 15000.0

    def test_add_expense_updates_financial_info(self, client):
        token = get_token(client, "cons_user2")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 10000, "source": "freelance", "date": "2026-09-01",
        }, headers=headers)

        client.post("/api/expenses/", json={
            "amount": 3000, "category": "food", "date": "2026-09-15",
        }, headers=headers)

        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_expenses"] == 3000.0
        assert r.json()["expense_count"] == 1
        assert r.json()["balance"] == 7000.0

    def test_delete_expense_updates_financial_info(self, client):
        token = get_token(client, "cons_user3")
        headers = auth_header(token)

        client.post("/api/incomes/", json={
            "amount": 10000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)

        r = client.post("/api/expenses/", json={
            "amount": 5000, "category": "shopping", "date": "2026-09-10",
        }, headers=headers)
        exp_id = r.json()["id"]

        # Before delete
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_expenses"] == 5000.0

        # Delete expense
        client.delete(f"/api/expenses/{exp_id}/", headers=headers)

        # After delete
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_expenses"] == 0.0
        assert r.json()["balance"] == 10000.0
        assert r.json()["expense_count"] == 0

    def test_delete_income_updates_financial_info(self, client):
        token = get_token(client, "cons_user4")
        headers = auth_header(token)

        r = client.post("/api/incomes/", json={
            "amount": 20000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        inc_id = r.json()["id"]

        client.post("/api/expenses/", json={
            "amount": 5000, "category": "food", "date": "2026-09-10",
        }, headers=headers)

        # Before delete
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 20000.0
        assert r.json()["balance"] == 15000.0

        # Delete income
        client.delete(f"/api/incomes/{inc_id}/", headers=headers)

        # After delete
        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 0.0
        assert r.json()["balance"] == -5000.0
        assert r.json()["income_count"] == 0

    def test_categories_consistent_across_modules(self, client):
        """Same category strings used in expenses, budgets, and transactions."""
        token = get_token(client, "cons_user5")
        headers = auth_header(token)

        # Create expense with category
        client.post("/api/expenses/", json={
            "amount": 2000, "category": "food", "date": "2026-09-10",
        }, headers=headers)

        # Create budget with same category
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=headers)

        # Transaction list shows same category string
        r = client.get("/api/transactions/", headers=headers)
        tx_cats = [t["category"] for t in r.json()["transactions"]]
        assert "food" in tx_cats

    def test_dashboard_values_from_stored_records(self, client, db):
        """Dashboard values must be computed from actual stored records, not cached or fake."""
        token = get_token(client, "cons_user6")
        headers = auth_header(token)
        user = db.query(models.User).filter(models.User.username == "cons_user6").first()

        # Create known data
        client.post("/api/incomes/", json={
            "amount": 7500, "source": "freelance", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 2500, "source": "pocket_money", "date": "2026-09-05",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1500, "category": "education", "date": "2026-09-10",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 500, "category": "entertainment", "date": "2026-09-12",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 800, "category": "miscellaneous", "date": "2026-09-14",
        }, headers=headers)

        # Verify dashboard matches exactly
        r = client.get("/api/transactions/summary/", headers=headers)
        s = r.json()
        assert s["total_income"] == 10000.0
        assert s["total_expenses"] == 2800.0
        assert s["balance"] == 7200.0
        assert s["income_count"] == 2
        assert s["expense_count"] == 3

        # Cross-check with DB
        inc_db = db.query(models.Income).filter(models.Income.user_id == user.id).all()
        exp_db = db.query(models.Expense).filter(models.Expense.user_id == user.id).all()
        assert sum(float(i.amount) for i in inc_db) == 10000.0
        assert sum(float(e.amount) for e in exp_db) == 2800.0

    def test_budget_category_expense_category_correspondence(self, client, db):
        """Budget allocations for 'food' should match the expense category 'food'."""
        token = get_token(client, "cons_user7")
        headers = auth_header(token)
        user = db.query(models.User).filter(models.User.username == "cons_user7").first()

        # Budget: food=4000, travel=2000
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 6000,
            "allocations": [
                {"category": "food", "amount": 4000},
                {"category": "travel", "amount": 2000},
            ],
        }, headers=headers)

        # Expenses: food=3500, travel=1500, shopping=1000
        client.post("/api/expenses/", json={
            "amount": 3500, "category": "food", "date": "2026-09-10",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1500, "category": "travel", "date": "2026-09-12",
        }, headers=headers)
        client.post("/api/expenses/", json={
            "amount": 1000, "category": "shopping", "date": "2026-09-14",
        }, headers=headers)

        # Get budget back
        budgets = db.query(models.Budget).filter(models.Budget.user_id == user.id).all()
        assert len(budgets) == 1
        bud_allocs = {a.category.value: float(a.amount) for a in budgets[0].allocations}
        assert bud_allocs["food"] == 4000.0
        assert bud_allocs["travel"] == 2000.0

        # Get expenses back
        expenses = db.query(models.Expense).filter(models.Expense.user_id == user.id).all()
        exp_by_cat = {}
        for e in expenses:
            cat = e.category.value
            exp_by_cat[cat] = exp_by_cat.get(cat, 0) + float(e.amount)

        # Budget food (4000) >= actual food expenses (3500)
        assert bud_allocs["food"] >= exp_by_cat.get("food", 0)
        # Budget travel (2000) >= actual travel expenses (1500)
        assert bud_allocs["travel"] >= exp_by_cat.get("travel", 0)


# ══════════════════════════════════════════════════════════════════
# END-TO-END FULL FLOW
# ══════════════════════════════════════════════════════════════════

class TestEndToEndFlow:
    """Test a complete user journey: register -> add data -> view dashboard -> create budget -> verify consistency."""

    def test_complete_user_journey(self, client, db):
        # 1. Register
        r = client.post("/api/auth/register/", json={
            "username": "e2e_user",
            "email": "e2e@test.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        })
        assert r.status_code == 201
        token = r.json()["tokens"]["access"]
        headers = auth_header(token)
        user_id = r.json()["user"]["id"]

        # 2. Add incomes
        client.post("/api/incomes/", json={
            "amount": 25000, "source": "scholarship", "date": "2026-09-01",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 8000, "source": "freelance", "date": "2026-09-05",
        }, headers=headers)
        client.post("/api/incomes/", json={
            "amount": 3000, "source": "pocket_money", "date": "2026-09-10",
        }, headers=headers)

        # 3. Add expenses (all 6 categories)
        expense_data = [
            ("food", 4000), ("travel", 2000), ("shopping", 3500),
            ("education", 3000), ("entertainment", 1500), ("miscellaneous", 500),
        ]
        for cat, amt in expense_data:
            r = client.post("/api/expenses/", json={
                "amount": amt, "category": cat, "date": "2026-09-15",
            }, headers=headers)
            assert r.status_code == 201

        # 4. Verify dashboard
        r = client.get("/api/transactions/summary/", headers=headers)
        s = r.json()
        assert s["total_income"] == 36000.0
        assert s["total_expenses"] == 14500.0
        assert s["balance"] == 21500.0
        assert s["income_count"] == 3
        assert s["expense_count"] == 6

        # 5. Verify transaction list
        r = client.get("/api/transactions/", headers=headers)
        txs = r.json()["transactions"]
        assert r.json()["total"] == 9
        tx_types = {t["type"] for t in txs}
        assert "income" in tx_types
        assert "expense" in tx_types

        # 6. Create budget matching expense categories
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 14500,
            "allocations": [
                {"category": "food", "amount": 4000},
                {"category": "travel", "amount": 2000},
                {"category": "shopping", "amount": 3500},
                {"category": "education", "amount": 3000},
                {"category": "entertainment", "amount": 1500},
                {"category": "miscellaneous", "amount": 500},
            ],
        }, headers=headers)
        assert r.status_code == 201
        bud_id = r.json()["id"]

        # 7. Verify budget allocations match expense categories
        r = client.get(f"/api/budgets/{bud_id}/", headers=headers)
        alloc_cats = {a["category"] for a in r.json()["allocations"]}
        exp_cats = {cat for cat, _ in expense_data}
        assert alloc_cats == exp_cats

        # 8. Verify DB consistency
        user = db.query(models.User).filter(models.User.id == user_id).first()
        assert user is not None
        assert len(user.incomes) == 3
        assert len(user.expenses) == 6
        assert len(user.budgets) == 1
        assert len(user.budgets[0].allocations) == 6

        # 9. Update an expense and verify dashboard updates
        exp_to_update = db.query(models.Expense).filter(
            models.Expense.user_id == user_id,
            models.Expense.category == "food",
        ).first()
        r = client.put(f"/api/expenses/{exp_to_update.id}/", json={
            "amount": 5000, "description": "Updated food budget",
        }, headers=headers)
        assert r.status_code == 200

        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_expenses"] == 15500.0
        assert r.json()["balance"] == 20500.0

        # 10. Delete an income and verify
        inc_to_delete = db.query(models.Income).filter(
            models.Income.user_id == user_id,
            models.Income.source == "pocket_money",
        ).first()
        r = client.delete(f"/api/incomes/{inc_to_delete.id}/", headers=headers)
        assert r.status_code == 204

        r = client.get("/api/transactions/summary/", headers=headers)
        assert r.json()["total_income"] == 33000.0
        assert r.json()["income_count"] == 2
        assert r.json()["balance"] == 17500.0


# ══════════════════════════════════════════════════════════════════
# AUTH FLOW
# ══════════════════════════════════════════════════════════════════

class TestAuthFlow:
    """Test the authentication system end-to-end."""

    def test_register_returns_tokens(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "auth_reg", "email": "authreg@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        assert r.status_code == 201
        assert "tokens" in r.json()
        assert "access" in r.json()["tokens"]
        assert "refresh" in r.json()["tokens"]
        assert r.json()["user"]["username"] == "auth_reg"

    def test_login_returns_tokens(self, client):
        client.post("/api/auth/register/", json={
            "username": "auth_login", "email": "authlogin@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        r = client.post("/api/auth/login/", json={
            "username": "auth_login", "password": "SecurePass123!",
        })
        assert r.status_code == 200
        assert "access" in r.json()
        assert "refresh" in r.json()

    def test_check_auth_with_valid_token(self, client):
        token = get_token(client, "auth_check")
        r = client.get("/api/auth/check/", headers=auth_header(token))
        assert r.status_code == 200
        assert r.json()["authenticated"] is True
        assert r.json()["user"]["username"] == "auth_check"

    def test_check_auth_without_token(self, client):
        r = client.get("/api/auth/check/")
        assert r.status_code in (401, 403)

    def test_check_auth_with_invalid_token(self, client):
        r = client.get("/api/auth/check/", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_get_profile_with_valid_token(self, client):
        token = get_token(client, "auth_profile")
        r = client.get("/api/auth/profile/", headers=auth_header(token))
        assert r.status_code == 200
        assert r.json()["username"] == "auth_profile"

    def test_token_refresh(self, client):
        r = client.post("/api/auth/register/", json={
            "username": "auth_refresh", "email": "authrefresh@test.com",
            "password": "SecurePass123!", "password_confirm": "SecurePass123!",
        })
        refresh_token = r.json()["tokens"]["refresh"]

        r = client.post("/api/auth/token/refresh/", json={"refresh": refresh_token})
        assert r.status_code == 200
        assert "access" in r.json()

    def test_token_refresh_with_invalid_token(self, client):
        r = client.post("/api/auth/token/refresh/", json={"refresh": "invalid.refresh.token"})
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════
# REPORT SUMMARY
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
