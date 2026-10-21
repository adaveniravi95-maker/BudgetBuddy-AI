"""
REST API & Data Flow Verification — Milestone 2
================================================
Traces the complete flow for 3 APIs:
  1. Create Expense
  2. Create Income
  3. Create Budget

Each test proves a specific step in the request → backend → database → response → UI chain.

Run:  cd backend && python -m pytest test_dataflow.py -v
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models, auth

# ══════════════════════════════════════════════════════════════════
# TEST DB
# ══════════════════════════════════════════════════════════════════
engine = create_engine("sqlite:///./test_dataflow.db", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app.dependency_overrides[get_db] = lambda: (db := TestSession()) or None

# ─── Correction: proper db override ────────────────────────────
def _override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_db


@pytest.fixture(autouse=True)
def setup():
    app.dependency_overrides[get_db] = _override_db
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
    return c.post("/api/auth/register/", json={
        "username": u, "email": email or f"{u}@test.com",
        "password": "SecurePass123!", "password_confirm": "SecurePass123!",
    })


def tok(c, u, email=None):
    r = reg(c, u, email)
    return r.json()["tokens"]["access"]


def hd(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════
# API 1: CREATE EXPENSE — Full Flow Trace
# ══════════════════════════════════════════════════════════════════

class TestCreateExpenseFlow:
    """
    FLOW: React form → handleExpCreate() → expenseAPI.create() →
          Axios interceptor adds Bearer token → POST /api/expenses/ →
          auth.get_current_user() decodes JWT → create_expense() →
          Pydantic validation → DB insert → 201 response →
          frontend calls fetchExpenses() + fetchSummary() → UI updates
    """

    # ── Step 1: Frontend sends correct HTTP method and path ───

    def test_01_axios_sends_post_to_correct_path(self, client, db):
        """React calls expenseAPI.create() → api.post('/expenses/', data)
        This becomes: POST /api/expenses/ (baseURL='/api' + path='/expenses/')
        Verified by: creating expense via the correct endpoint."""
        token = tok(client, "flow_exp1")
        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "description": "Test", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 201, f"POST /api/expenses/ should return 201, got {r.status_code}"
        assert "id" in r.json(), "Response must contain 'id' field"

    # ── Step 2: JWT token attached by Axios interceptor ──────

    def test_02_request_requires_jwt_auth(self, client):
        """Axios request interceptor reads localStorage 'access_token' and
        sets header: Authorization: Bearer <token>.
        Without the header, the endpoint must reject."""
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "date": "2026-09-15",
        })
        assert r.status_code in (401, 403), f"Without token: expected 401/403, got {r.status_code}"

    def test_03_invalid_token_rejected(self, client):
        """If token is tampered or expired, decode_token() raises 401."""
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food", "date": "2026-09-15",
        }, headers={"Authorization": "Bearer invalid.jwt.here"})
        assert r.status_code == 401

    # ── Step 3: Backend validates input via Pydantic ──────────

    def test_04_validation_rejects_negative_amount(self, client):
        """ExpenseCreate schema: amount > 0 validator."""
        token = tok(client, "flow_exp4")
        r = client.post("/api/expenses/", json={
            "amount": -100, "category": "food", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 422
        assert "amount" in str(r.json())

    def test_05_validation_rejects_zero_amount(self, client):
        token = tok(client, "flow_exp5")
        r = client.post("/api/expenses/", json={
            "amount": 0, "category": "food", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_06_validation_rejects_invalid_category(self, client):
        """ExpenseCategory enum: food|travel|shopping|education|entertainment|miscellaneous"""
        token = tok(client, "flow_exp6")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "nonexistent", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_07_validation_rejects_missing_category(self, client):
        token = tok(client, "flow_exp7")
        r = client.post("/api/expenses/", json={
            "amount": 100, "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_08_validation_rejects_missing_date(self, client):
        token = tok(client, "flow_exp8")
        r = client.post("/api/expenses/", json={
            "amount": 100, "category": "food",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_09_validation_rejects_missing_amount(self, client):
        token = tok(client, "flow_exp9")
        r = client.post("/api/expenses/", json={
            "category": "food", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 422

    # ── Step 4: Backend creates DB record with user_id ────────

    def test_10_expense_saved_with_correct_user_id(self, client, db):
        """create_expense() sets expense.user_id = current_user.id before commit."""
        token = tok(client, "flow_exp10")
        user = db.query(models.User).filter(models.User.username == "flow_exp10").first()

        r = client.post("/api/expenses/", json={
            "amount": 1234.56, "category": "travel", "description": "Bus fare", "date": "2026-09-15",
        }, headers=hd(token))

        exp_id = r.json()["id"]
        expense_db = db.query(models.Expense).filter(models.Expense.id == exp_id).first()

        assert expense_db is not None, "Record must exist in DB"
        assert expense_db.user_id == user.id, f"user_id={expense_db.user_id}, expected {user.id}"
        assert float(expense_db.amount) == 1234.56
        assert expense_db.category.value == "travel"
        assert expense_db.description == "Bus fare"
        assert str(expense_db.date) == "2026-09-15"

    # ── Step 5: Response contains all expected fields ─────────

    def test_11_response_matches_expense_schema(self, client):
        """ExpenseResponse: id, user_id, amount, category, description, date, created_at"""
        token = tok(client, "flow_exp11")
        r = client.post("/api/expenses/", json={
            "amount": 99.99, "category": "entertainment", "description": "Movie", "date": "2026-09-15",
        }, headers=hd(token))

        data = r.json()
        assert "id" in data
        assert "user_id" in data
        assert data["amount"] == 99.99
        assert data["category"] == "entertainment"
        assert data["description"] == "Movie"
        assert data["date"] == "2026-09-15"
        assert "created_at" in data

    def test_12_status_code_is_201(self, client):
        """Router decorator: status_code=status.HTTP_201_CREATED"""
        token = tok(client, "flow_exp12")
        r = client.post("/api/expenses/", json={
            "amount": 50, "category": "food", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.status_code == 201

    # ── Step 6: Frontend refreshes list after create ──────────

    def test_13_list_endpoint_returns_new_expense(self, client, db):
        """After create, frontend calls fetchExpenses() → GET /api/expenses/
        The new expense must appear in the list."""
        token = tok(client, "flow_exp13")

        client.post("/api/expenses/", json={
            "amount": 250, "category": "shopping", "date": "2026-09-15",
        }, headers=hd(token))

        r = client.get("/api/expenses/", headers=hd(token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        amounts = [e["amount"] for e in r.json()["expenses"]]
        assert 250.0 in amounts

    # ── Step 7: Dashboard summary reflects new expense ────────

    def test_14_summary_updates_after_expense_create(self, client):
        """After create, frontend calls fetchSummary() → GET /api/transactions/summary/
        total_expenses must include the new amount."""
        token = tok(client, "flow_exp14")

        # Before
        s0 = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s0["total_expenses"] == 0.0

        # Create expense
        client.post("/api/expenses/", json={
            "amount": 750, "category": "education", "date": "2026-09-15",
        }, headers=hd(token))

        # After
        s1 = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s1["total_expenses"] == 750.0
        assert s1["expense_count"] == 1
        assert s1["balance"] == -750.0

    # ── Step 8: Data isolation — user can't see others' expenses ──

    def test_15_user_b_cannot_see_user_a_expense(self, client):
        tA = tok(client, "flow_exp15a", "a@test.com")
        tB = tok(client, "flow_exp15b", "b@test.com")

        r = client.post("/api/expenses/", json={
            "amount": 500, "category": "food", "date": "2026-09-15",
        }, headers=hd(tA))
        exp_id = r.json()["id"]

        # User B cannot read
        r = client.get(f"/api/expenses/{exp_id}/", headers=hd(tB))
        assert r.status_code == 404

        # User B's list is empty
        r = client.get("/api/expenses/", headers=hd(tB))
        assert r.json()["total"] == 0

    # ── Step 9: Description defaults to empty string ──────────

    def test_16_description_defaults_to_empty(self, client, db):
        """Dashboard sends description: '' when user leaves it blank."""
        token = tok(client, "flow_exp16")
        r = client.post("/api/expenses/", json={
            "amount": 10, "category": "miscellaneous", "description": "", "date": "2026-09-15",
        }, headers=hd(token))
        assert r.json()["description"] == ""

        exp_id = r.json()["id"]
        expense_db = db.query(models.Expense).filter(models.Expense.id == exp_id).first()
        assert expense_db.description == ""

    # ── Step 10: Expense appears in transaction list ──────────

    def test_17_expense_appears_in_transactions(self, client):
        """Transaction list merges incomes + expenses. Expense type='expense'."""
        token = tok(client, "flow_exp17")
        client.post("/api/expenses/", json={
            "amount": 300, "category": "travel", "date": "2026-09-15",
        }, headers=hd(token))

        r = client.get("/api/transactions/", headers=hd(token))
        txs = r.json()["transactions"]
        assert len(txs) == 1
        assert txs[0]["type"] == "expense"
        assert txs[0]["category"] == "travel"
        assert txs[0]["amount"] == 300.0


# ══════════════════════════════════════════════════════════════════
# API 2: CREATE INCOME — Full Flow Trace
# ══════════════════════════════════════════════════════════════════

class TestCreateIncomeFlow:
    """
    FLOW: React form → handleIncCreate() → incomeAPI.create() →
          Axios adds Bearer → POST /api/incomes/ → auth →
          create_income() → Pydantic validation → DB insert →
          201 response → fetchIncomes() + fetchSummary() → UI updates
    """

    # ── Step 1: Correct HTTP method and path ──────────────────

    def test_01_post_to_correct_path(self, client, db):
        """incomeAPI.create() → api.post('/incomes/', data) → POST /api/incomes/"""
        token = tok(client, "flow_inc1")
        r = client.post("/api/incomes/", json={
            "amount": 10000, "source": "scholarship", "description": "Grant", "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 201

    # ── Step 2: JWT required ──────────────────────────────────

    def test_02_requires_auth(self, client):
        r = client.post("/api/incomes/", json={
            "amount": 1000, "source": "freelance", "date": "2026-09-01",
        })
        assert r.status_code in (401, 403)

    # ── Step 3: Validation ────────────────────────────────────

    def test_03_rejects_negative_amount(self, client):
        token = tok(client, "flow_inc3")
        r = client.post("/api/incomes/", json={
            "amount": -500, "source": "freelance", "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_04_rejects_zero_amount(self, client):
        token = tok(client, "flow_inc4")
        r = client.post("/api/incomes/", json={
            "amount": 0, "source": "freelance", "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_05_rejects_invalid_source(self, client):
        """IncomeCategory enum: pocket_money|scholarship|freelance"""
        token = tok(client, "flow_inc5")
        r = client.post("/api/incomes/", json={
            "amount": 1000, "source": "invalid_src", "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_06_rejects_missing_source(self, client):
        token = tok(client, "flow_inc6")
        r = client.post("/api/incomes/", json={
            "amount": 1000, "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_07_rejects_missing_amount(self, client):
        token = tok(client, "flow_inc7")
        r = client.post("/api/incomes/", json={
            "source": "freelance", "date": "2026-09-01",
        }, headers=hd(token))
        assert r.status_code == 422

    def test_08_rejects_missing_date(self, client):
        token = tok(client, "flow_inc8")
        r = client.post("/api/incomes/", json={
            "amount": 1000, "source": "freelance",
        }, headers=hd(token))
        assert r.status_code == 422

    # ── Step 4: DB persistence with correct user_id ───────────

    def test_09_saved_with_correct_user_id(self, client, db):
        token = tok(client, "flow_inc9")
        user = db.query(models.User).filter(models.User.username == "flow_inc9").first()

        r = client.post("/api/incomes/", json={
            "amount": 25000, "source": "scholarship", "description": "Semester", "date": "2026-09-01",
        }, headers=hd(token))

        inc_id = r.json()["id"]
        income_db = db.query(models.Income).filter(models.Income.id == inc_id).first()

        assert income_db is not None
        assert income_db.user_id == user.id
        assert float(income_db.amount) == 25000.0
        assert income_db.source.value == "scholarship"
        assert income_db.description == "Semester"

    # ── Step 5: Response matches schema ───────────────────────

    def test_10_response_fields_correct(self, client):
        token = tok(client, "flow_inc10")
        r = client.post("/api/incomes/", json={
            "amount": 5000, "source": "freelance", "description": "Gig", "date": "2026-09-05",
        }, headers=hd(token))

        data = r.json()
        assert "id" in data
        assert "user_id" in data
        assert data["amount"] == 5000.0
        assert data["source"] == "freelance"
        assert data["description"] == "Gig"
        assert data["date"] == "2026-09-05"
        assert "created_at" in data

    # ── Step 6: List returns new income ───────────────────────

    def test_11_list_includes_new_income(self, client):
        token = tok(client, "flow_inc11")
        client.post("/api/incomes/", json={
            "amount": 8000, "source": "pocket_money", "date": "2026-09-01",
        }, headers=hd(token))

        r = client.get("/api/incomes/", headers=hd(token))
        assert r.json()["total"] >= 1
        assert any(i["amount"] == 8000.0 for i in r.json()["incomes"])

    # ── Step 7: Dashboard summary reflects income ─────────────

    def test_12_summary_updates_after_income_create(self, client):
        token = tok(client, "flow_inc12")

        client.post("/api/incomes/", json={
            "amount": 15000, "source": "scholarship", "date": "2026-09-01",
        }, headers=hd(token))

        s = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s["total_income"] == 15000.0
        assert s["income_count"] == 1
        assert s["balance"] == 15000.0

    # ── Step 8: Isolation ─────────────────────────────────────

    def test_13_user_b_cannot_see_user_a_income(self, client):
        tA = tok(client, "flow_inc13a", "inc_a@test.com")
        tB = tok(client, "flow_inc13b", "inc_b@test.com")

        r = client.post("/api/incomes/", json={
            "amount": 10000, "source": "freelance", "date": "2026-09-01",
        }, headers=hd(tA))
        inc_id = r.json()["id"]

        assert client.get(f"/api/incomes/{inc_id}/", headers=hd(tB)).status_code == 404
        assert client.get("/api/incomes/", headers=hd(tB)).json()["total"] == 0

    # ── Step 9: Income appears in transactions ────────────────

    def test_14_income_appears_in_transactions(self, client):
        token = tok(client, "flow_inc14")
        client.post("/api/incomes/", json={
            "amount": 7000, "source": "scholarship", "date": "2026-09-01",
        }, headers=hd(token))

        txs = client.get("/api/transactions/", headers=hd(token)).json()["transactions"]
        assert len(txs) == 1
        assert txs[0]["type"] == "income"
        assert txs[0]["category"] == "scholarship"

    # ── Step 10: Date stored correctly ────────────────────────

    def test_15_date_stored_correctly_in_db(self, client, db):
        token = tok(client, "flow_inc15")
        r = client.post("/api/incomes/", json={
            "amount": 3000, "source": "freelance", "date": "2026-12-25",
        }, headers=hd(token))

        inc_id = r.json()["id"]
        income_db = db.query(models.Income).filter(models.Income.id == inc_id).first()
        assert str(income_db.date) == "2026-12-25"
        assert r.json()["date"] == "2026-12-25"


# ══════════════════════════════════════════════════════════════════
# API 3: CREATE BUDGET — Full Flow Trace
# ══════════════════════════════════════════════════════════════════

class TestCreateBudgetFlow:
    """
    FLOW: React form → handleBudgetCreate() → budgetAPI.create() →
          Axios adds Bearer → POST /api/budgets/ → auth →
          create_budget() → Pydantic validation + duplicate check →
          DB insert (Budget + BudgetAllocations) → 201 →
          fetchBudgets() → UI updates
    """

    # ── Step 1: Correct HTTP method and path ──────────────────

    def test_01_post_to_correct_path(self, client, db):
        token = tok(client, "flow_bud1")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 10000,
            "allocations": [{"category": "food", "amount": 10000}],
        }, headers=hd(token))
        assert r.status_code == 201

    # ── Step 2: JWT required ──────────────────────────────────

    def test_02_requires_auth(self, client):
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        })
        assert r.status_code in (401, 403)

    # ── Step 3: Validation ────────────────────────────────────

    def test_03_rejects_month_0(self, client):
        token = tok(client, "flow_bud3")
        r = client.post("/api/budgets/", json={
            "month": 0, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(token))
        assert r.status_code == 422

    def test_04_rejects_month_13(self, client):
        token = tok(client, "flow_bud4")
        r = client.post("/api/budgets/", json={
            "month": 13, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(token))
        assert r.status_code == 422

    def test_05_rejects_negative_total(self, client):
        token = tok(client, "flow_bud5")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": -100,
            "allocations": [{"category": "food", "amount": 100}],
        }, headers=hd(token))
        assert r.status_code == 422

    def test_06_rejects_invalid_allocation_category(self, client):
        token = tok(client, "flow_bud6")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "bad", "amount": 1000}],
        }, headers=hd(token))
        assert r.status_code == 422

    def test_07_rejects_negative_allocation_amount(self, client):
        token = tok(client, "flow_bud7")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 1000,
            "allocations": [{"category": "food", "amount": -500}],
        }, headers=hd(token))
        assert r.status_code == 422

    # ── Step 4: Duplicate month+year rejected ─────────────────

    def test_08_duplicate_month_rejected(self, client):
        token = tok(client, "flow_bud8")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(token))

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 3000,
            "allocations": [{"category": "food", "amount": 3000}],
        }, headers=hd(token))
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]

    # ── Step 5: DB persistence — Budget + Allocations ─────────

    def test_09_saved_with_allocations_in_db(self, client, db):
        token = tok(client, "flow_bud9")
        user = db.query(models.User).filter(models.User.username == "flow_bud9").first()

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 8000,
            "allocations": [
                {"category": "food", "amount": 4000},
                {"category": "travel", "amount": 2000},
                {"category": "shopping", "amount": 2000},
            ],
        }, headers=hd(token))

        bud_id = r.json()["id"]
        bud_db = db.query(models.Budget).filter(models.Budget.id == bud_id).first()

        assert bud_db is not None
        assert bud_db.user_id == user.id
        assert bud_db.month == 9
        assert bud_db.year == 2026
        assert float(bud_db.total_amount) == 8000.0
        assert len(bud_db.allocations) == 3

        alloc_map = {a.category.value: float(a.amount) for a in bud_db.allocations}
        assert alloc_map["food"] == 4000.0
        assert alloc_map["travel"] == 2000.0
        assert alloc_map["shopping"] == 2000.0

    # ── Step 6: Response includes allocations ─────────────────

    def test_10_response_includes_allocations(self, client):
        token = tok(client, "flow_bud10")
        r = client.post("/api/budgets/", json={
            "month": 10, "year": 2026, "total_amount": 5000,
            "allocations": [
                {"category": "food", "amount": 3000},
                {"category": "entertainment", "amount": 2000},
            ],
        }, headers=hd(token))

        data = r.json()
        assert "id" in data
        assert data["month"] == 10
        assert data["year"] == 2026
        assert data["total_amount"] == 5000.0
        assert len(data["allocations"]) == 2
        assert "created_at" in data

        alloc_cats = {a["category"] for a in data["allocations"]}
        assert alloc_cats == {"food", "entertainment"}

    # ── Step 7: List returns new budget ───────────────────────

    def test_11_list_includes_new_budget(self, client):
        token = tok(client, "flow_bud11")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(token))

        r = client.get("/api/budgets/", headers=hd(token))
        assert r.json()["total"] >= 1

    # ── Step 8: Budget allocations use ExpenseCategory enum ───

    def test_12_allocations_use_expense_categories(self, client):
        """Budget allocations must use the same ExpenseCategory enum as expenses."""
        token = tok(client, "flow_bud12")
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 6000,
            "allocations": [
                {"category": "food", "amount": 1000},
                {"category": "travel", "amount": 1000},
                {"category": "shopping", "amount": 1000},
                {"category": "education", "amount": 1000},
                {"category": "entertainment", "amount": 1000},
                {"category": "miscellaneous", "amount": 1000},
            ],
        }, headers=hd(token))

        alloc_cats = {a["category"] for a in r.json()["allocations"]}
        assert alloc_cats == {"food", "travel", "shopping", "education", "entertainment", "miscellaneous"}

    # ── Step 9: Isolation ─────────────────────────────────────

    def test_13_user_b_cannot_see_user_a_budget(self, client):
        tA = tok(client, "flow_bud13a", "bud_a@test.com")
        tB = tok(client, "flow_bud13b", "bud_b@test.com")

        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(tA))
        bud_id = r.json()["id"]

        assert client.get(f"/api/budgets/{bud_id}/", headers=hd(tB)).status_code == 404
        assert client.get("/api/budgets/", headers=hd(tB)).json()["total"] == 0

    # ── Step 10: Budget does NOT affect transaction summary ────

    def test_14_budget_does_not_affect_dashboard(self, client):
        """Budgets are planning data. They should NOT appear in the transaction
        summary which tracks actual income/expenses."""
        token = tok(client, "flow_bud14")
        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 50000,
            "allocations": [{"category": "food", "amount": 50000}],
        }, headers=hd(token))

        s = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s["total_income"] == 0.0
        assert s["total_expenses"] == 0.0
        assert s["balance"] == 0.0


# ══════════════════════════════════════════════════════════════════
# CROSS-API VERIFICATION
# ══════════════════════════════════════════════════════════════════

class TestCrossAPIFlow:
    """Verify that multiple APIs interact correctly."""

    def test_income_plus_expense_dashboard_consistency(self, client):
        """Creating income then expense must produce correct dashboard values."""
        token = tok(client, "cross1")

        client.post("/api/incomes/", json={
            "amount": 20000, "source": "scholarship", "date": "2026-09-01",
        }, headers=hd(token))
        client.post("/api/expenses/", json={
            "amount": 5000, "category": "food", "date": "2026-09-10",
        }, headers=hd(token))
        client.post("/api/expenses/", json={
            "amount": 3000, "category": "travel", "date": "2026-09-15",
        }, headers=hd(token))

        s = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s["total_income"] == 20000.0
        assert s["total_expenses"] == 8000.0
        assert s["balance"] == 12000.0
        assert s["income_count"] == 1
        assert s["expense_count"] == 2

    def test_delete_expense_updates_dashboard(self, client):
        token = tok(client, "cross2")
        client.post("/api/incomes/", json={"amount": 10000, "source": "freelance", "date": "2026-09-01"}, headers=hd(token))
        r = client.post("/api/expenses/", json={"amount": 3000, "category": "food", "date": "2026-09-10"}, headers=hd(token))
        exp_id = r.json()["id"]

        client.delete(f"/api/expenses/{exp_id}/", headers=hd(token))
        s = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s["total_expenses"] == 0.0
        assert s["balance"] == 10000.0

    def test_delete_income_updates_dashboard(self, client):
        token = tok(client, "cross3")
        r = client.post("/api/incomes/", json={"amount": 15000, "source": "scholarship", "date": "2026-09-01"}, headers=hd(token))
        inc_id = r.json()["id"]
        client.post("/api/expenses/", json={"amount": 2000, "category": "food", "date": "2026-09-10"}, headers=hd(token))

        client.delete(f"/api/incomes/{inc_id}/", headers=hd(token))
        s = client.get("/api/transactions/summary/", headers=hd(token)).json()
        assert s["total_income"] == 0.0
        assert s["balance"] == -2000.0

    def test_budget_category_matches_expense_category(self, client, db):
        """Budget 'food' allocation should correspond to expense 'food' category."""
        token = tok(client, "cross4")
        user = db.query(models.User).filter(models.User.username == "cross4").first()

        client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 5000,
            "allocations": [{"category": "food", "amount": 5000}],
        }, headers=hd(token))

        client.post("/api/expenses/", json={
            "amount": 3000, "category": "food", "date": "2026-09-15",
        }, headers=hd(token))

        bud = db.query(models.Budget).filter(models.Budget.user_id == user.id).first()
        food_alloc = [a for a in bud.allocations if a.category.value == "food"][0]
        exp = db.query(models.Expense).filter(
            models.Expense.user_id == user.id,
            models.Expense.category == "food",
        ).first()

        assert food_alloc.category.value == exp.category.value == "food"
        assert float(food_alloc.amount) >= float(exp.amount)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
