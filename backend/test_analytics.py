"""
Analytics API Tests
===================
Covers totals, category summary, monthly trends, savings/financial summary,
date/month filtering, user isolation, empty data, invalid input and zero values.

Run:  cd backend && python -m pytest test_analytics.py -v
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_analytics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if previous is not None:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register(client, username):
    r = client.post("/api/auth/register/", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
    })
    assert r.status_code == 201
    return auth_header(r.json()["tokens"]["access"])


def add_income(client, headers, amount, source, date):
    r = client.post("/api/incomes/", json={
        "amount": amount, "source": source, "date": date,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def add_expense(client, headers, amount, category, date):
    r = client.post("/api/expenses/", json={
        "amount": amount, "category": category, "date": date,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def seed_known_data(client, headers):
    """Known fixture records used for manual calculation verification."""
    add_income(client, headers, 10000, "scholarship", "2026-09-01")
    add_income(client, headers, 5000, "freelance", "2026-09-05")
    add_income(client, headers, 2000, "pocket_money", "2026-08-15")
    add_expense(client, headers, 1500, "food", "2026-09-02")
    add_expense(client, headers, 800, "food", "2026-09-06")
    add_expense(client, headers, 1200, "travel", "2026-09-12")
    add_expense(client, headers, 500, "shopping", "2026-08-20")


def get_analytics(client, headers, **params):
    return client.get("/api/analytics/", headers=headers, params=params)


# ─── Manual Calculation Verification ─────────────────────────

class TestKnownRecordCalculations:
    """Verify analytics against hand-computed expected values."""

    def test_totals_match_known_records(self, client):
        headers = register(client, "ana_known")
        seed_known_data(client, headers)

        r = get_analytics(client, headers)
        assert r.status_code == 200
        d = r.json()

        # Income: 10000 + 5000 + 2000 = 17000
        assert d["total_income"] == 17000.0
        # Expenses: 1500 + 800 + 1200 + 500 = 4000
        assert d["total_expenses"] == 4000.0
        # Net: 17000 - 4000 = 13000
        assert d["net_savings"] == 13000.0
        # Savings rate: 13000 / 17000 * 100 = 76.47
        assert d["savings_rate_percent"] == 76.47
        assert d["income_count"] == 3
        assert d["expense_count"] == 4
        assert d["has_data"] is True

    def test_formula_consistency(self, client):
        headers = register(client, "ana_formula")
        seed_known_data(client, headers)
        d = get_analytics(client, headers).json()
        assert d["net_savings"] == round(d["total_income"] - d["total_expenses"], 2)
        if d["total_income"] > 0:
            expected_rate = round(
                (d["net_savings"] / d["total_income"]) * 100, 2
            )
            assert d["savings_rate_percent"] == expected_rate

    def test_category_summary_known_values(self, client):
        headers = register(client, "ana_cats")
        seed_known_data(client, headers)
        d = get_analytics(client, headers).json()
        cats = {c["category"]: c for c in d["category_summary"]}

        # food: 1500 + 800 = 2300 (2 transactions), 2300/4000 = 57.5%
        assert cats["food"]["total"] == 2300.0
        assert cats["food"]["count"] == 2
        assert cats["food"]["percent_of_expenses"] == 57.5
        # travel: 1200, 1200/4000 = 30%
        assert cats["travel"]["total"] == 1200.0
        assert cats["travel"]["count"] == 1
        assert cats["travel"]["percent_of_expenses"] == 30.0
        # shopping: 500, 500/4000 = 12.5%
        assert cats["shopping"]["total"] == 500.0
        assert cats["shopping"]["percent_of_expenses"] == 12.5

        # Sorted by total descending
        totals = [c["total"] for c in d["category_summary"]]
        assert totals == sorted(totals, reverse=True)

        # Percents sum to 100
        assert round(sum(c["percent_of_expenses"] for c in d["category_summary"]), 2) == 100.0

    def test_monthly_trends_known_values(self, client):
        headers = register(client, "ana_trends")
        seed_known_data(client, headers)
        d = get_analytics(client, headers).json()
        trends = {(t["year"], t["month"]): t for t in d["monthly_trends"]}

        # Aug 2026: income 2000, expenses 500
        aug = trends[(2026, 8)]
        assert aug["income"] == 2000.0
        assert aug["expenses"] == 500.0
        assert aug["net"] == 1500.0

        # Sep 2026: income 10000+5000=15000, expenses 1500+800+1200=3500
        sep = trends[(2026, 9)]
        assert sep["income"] == 15000.0
        assert sep["expenses"] == 3500.0
        assert sep["net"] == 11500.0

        # Chronological order
        keys = [(t["year"], t["month"]) for t in d["monthly_trends"]]
        assert keys == sorted(keys)

    def test_multiple_same_category_aggregated(self, client):
        headers = register(client, "ana_multi")
        add_expense(client, headers, 100, "food", "2026-09-01")
        add_expense(client, headers, 200, "food", "2026-09-02")
        add_expense(client, headers, 300, "food", "2026-09-03")

        d = get_analytics(client, headers).json()
        assert d["total_expenses"] == 600.0
        assert len(d["category_summary"]) == 1
        assert d["category_summary"][0]["total"] == 600.0
        assert d["category_summary"][0]["count"] == 3


# ─── Date / Month Filtering ──────────────────────────────────

class TestFiltering:

    def test_month_filter(self, client):
        headers = register(client, "ana_month")
        seed_known_data(client, headers)

        d = get_analytics(client, headers, month=9, year=2026).json()
        # Sep only: income 15000, expenses 3500
        assert d["total_income"] == 15000.0
        assert d["total_expenses"] == 3500.0
        assert d["net_savings"] == 11500.0
        assert d["filters"]["month"] == 9
        assert d["filters"]["year"] == 2026
        # Single trend entry for Sep
        assert len(d["monthly_trends"]) == 1
        assert d["monthly_trends"][0]["month"] == 9
        # shopping (August) excluded from categories
        cats = {c["category"] for c in d["category_summary"]}
        assert cats == {"food", "travel"}

    def test_year_filter(self, client):
        headers = register(client, "ana_year")
        seed_known_data(client, headers)

        d = get_analytics(client, headers, year=2026).json()
        assert d["total_income"] == 17000.0
        assert d["total_expenses"] == 4000.0

    def test_date_range_filter(self, client):
        headers = register(client, "ana_range")
        seed_known_data(client, headers)

        d = get_analytics(
            client, headers, start_date="2026-08-01", end_date="2026-08-31",
        ).json()
        # August only: income 2000, expenses 500
        assert d["total_income"] == 2000.0
        assert d["total_expenses"] == 500.0
        assert d["income_count"] == 1
        assert d["expense_count"] == 1
        assert len(d["category_summary"]) == 1
        assert d["category_summary"][0]["category"] == "shopping"

    def test_open_ended_start_date(self, client):
        headers = register(client, "ana_open")
        seed_known_data(client, headers)

        d = get_analytics(client, headers, start_date="2026-09-01").json()
        assert d["total_income"] == 15000.0
        assert d["total_expenses"] == 3500.0

    def test_budget_summary_included_for_month(self, client):
        headers = register(client, "ana_budget_sum")
        seed_known_data(client, headers)
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 10000,
            "allocations": [
                {"category": "food", "amount": 5000},
                {"category": "travel", "amount": 2000},
            ],
        }, headers=headers)
        assert r.status_code == 201

        d = get_analytics(client, headers, month=9, year=2026).json()
        b = d["budget_summary"]
        assert b is not None
        assert b["total_budget"] == 10000.0
        assert b["total_spent"] == 3500.0
        assert b["remaining"] == 6500.0
        assert b["utilization_percent"] == 35.0

        allocs = {a["category"]: a for a in b["allocations"]}
        assert allocs["food"]["budgeted"] == 5000.0
        assert allocs["food"]["spent"] == 2300.0
        assert allocs["food"]["utilization_percent"] == 46.0
        assert allocs["travel"]["spent"] == 1200.0
        assert allocs["travel"]["utilization_percent"] == 60.0

    def test_budget_summary_null_without_month(self, client):
        headers = register(client, "ana_budget_null")
        seed_known_data(client, headers)
        d = get_analytics(client, headers).json()
        assert d["budget_summary"] is None


# ─── Savings / Financial Summary ─────────────────────────────

class TestSavingsSummary:

    def test_savings_goals_included(self, client):
        headers = register(client, "ana_savings")
        r = client.post("/api/savings/", json={
            "name": "Emergency fund", "target_amount": 50000,
        }, headers=headers)
        assert r.status_code == 201
        goal_id = r.json()["id"]
        client.put(f"/api/savings/{goal_id}/progress/", json={
            "current_saved": 10000,
        }, headers=headers)

        d = get_analytics(client, headers).json()
        s = d["savings_summary"]
        assert s["total_goals"] == 1
        assert s["total_target"] == 50000.0
        assert s["total_saved"] == 10000.0
        assert s["overall_progress_percent"] == 20.0
        assert s["completed_goals"] == 0

    def test_empty_savings_summary_values(self, client):
        headers = register(client, "ana_nosavings2")
        d = get_analytics(client, headers).json()
        s = d["savings_summary"]
        assert s["total_goals"] == 0
        assert s["total_target"] == 0.0
        assert s["total_saved"] == 0.0
        assert s["overall_progress_percent"] == 0.0


# ─── Empty Data / Zero Values ────────────────────────────────

class TestEmptyAndZero:

    def test_empty_account_returns_zeros(self, client):
        headers = register(client, "ana_empty")
        r = get_analytics(client, headers)
        assert r.status_code == 200
        d = r.json()
        assert d["total_income"] == 0.0
        assert d["total_expenses"] == 0.0
        assert d["net_savings"] == 0.0
        assert d["savings_rate_percent"] == 0.0
        assert d["income_count"] == 0
        assert d["expense_count"] == 0
        assert d["has_data"] is False
        assert d["category_summary"] == []
        assert d["monthly_trends"] == []
        assert d["budget_summary"] is None

    def test_no_data_for_selected_period(self, client):
        headers = register(client, "ana_noperiod")
        seed_known_data(client, headers)

        d = get_analytics(client, headers, month=1, year=2026).json()
        assert d["total_income"] == 0.0
        assert d["total_expenses"] == 0.0
        assert d["has_data"] is False
        # Selected month still appears as a zero trend entry
        assert d["monthly_trends"] == [{
            "year": 2026, "month": 1,
            "income": 0.0, "expenses": 0.0, "net": 0.0,
        }]

    def test_empty_date_range(self, client):
        headers = register(client, "ana_emptyrange")
        seed_known_data(client, headers)

        d = get_analytics(
            client, headers, start_date="2025-01-01", end_date="2025-12-31",
        ).json()
        assert d["total_income"] == 0.0
        assert d["total_expenses"] == 0.0
        assert d["category_summary"] == []
        assert d["monthly_trends"] == []
        assert d["has_data"] is False

    def test_expense_only_gives_negative_net_and_zero_rate(self, client):
        headers = register(client, "ana_negative")
        add_expense(client, headers, 500, "food", "2026-09-10")

        d = get_analytics(client, headers).json()
        assert d["total_income"] == 0.0
        assert d["total_expenses"] == 500.0
        assert d["net_savings"] == -500.0
        assert d["savings_rate_percent"] == 0.0  # no div-by-zero


# ─── Invalid Inputs ──────────────────────────────────────────

class TestInvalidInput:

    def test_invalid_start_date(self, client):
        headers = register(client, "ana_inv1")
        r = get_analytics(client, headers, start_date="not-a-date")
        assert r.status_code == 400
        assert "start_date" in r.json()["detail"]

    def test_invalid_end_date(self, client):
        headers = register(client, "ana_inv2")
        r = get_analytics(client, headers, end_date="2026-13-45")
        assert r.status_code == 400
        assert "end_date" in r.json()["detail"]

    def test_invalid_month_too_high(self, client):
        headers = register(client, "ana_inv3")
        r = get_analytics(client, headers, month=13, year=2026)
        assert r.status_code == 400
        assert "month" in r.json()["detail"]

    def test_invalid_month_zero(self, client):
        headers = register(client, "ana_inv4")
        r = get_analytics(client, headers, month=0, year=2026)
        assert r.status_code == 400

    def test_invalid_month_negative(self, client):
        headers = register(client, "ana_inv5")
        r = get_analytics(client, headers, month=-1, year=2026)
        assert r.status_code == 400

    def test_month_without_year(self, client):
        headers = register(client, "ana_inv6")
        r = get_analytics(client, headers, month=9)
        assert r.status_code == 400
        assert "year is required" in r.json()["detail"]

    def test_start_after_end(self, client):
        headers = register(client, "ana_inv7")
        r = get_analytics(
            client, headers, start_date="2026-09-30", end_date="2026-09-01",
        )
        assert r.status_code == 400

    def test_conflicting_filters(self, client):
        headers = register(client, "ana_inv8")
        r = get_analytics(
            client, headers, start_date="2026-09-01", month=9, year=2026,
        )
        assert r.status_code == 400

    def test_invalid_year(self, client):
        headers = register(client, "ana_inv9")
        r = get_analytics(client, headers, year=0)
        assert r.status_code == 400


# ─── Database Reconciliation ─────────────────────────────────

class TestDatabaseReconciliation:
    """Compare analytics API results directly against stored DB records."""

    def test_totals_match_database(self, client, db):
        headers = register(client, "ana_db_tot")
        seed_known_data(client, headers)

        user = db.query(models.User).filter(
            models.User.username == "ana_db_tot",
        ).first()
        db_income = sum(
            float(i.amount)
            for i in db.query(models.Income).filter(models.Income.user_id == user.id)
        )
        db_expenses = sum(
            float(e.amount)
            for e in db.query(models.Expense).filter(models.Expense.user_id == user.id)
        )

        d = get_analytics(client, headers).json()
        assert d["total_income"] == db_income
        assert d["total_expenses"] == db_expenses
        assert d["net_savings"] == round(db_income - db_expenses, 2)
        assert d["income_count"] == (
            db.query(models.Income).filter(models.Income.user_id == user.id).count()
        )
        assert d["expense_count"] == (
            db.query(models.Expense).filter(models.Expense.user_id == user.id).count()
        )

    def test_category_summary_matches_database(self, client, db):
        headers = register(client, "ana_db_cat")
        seed_known_data(client, headers)

        user = db.query(models.User).filter(
            models.User.username == "ana_db_cat",
        ).first()
        db_by_cat: dict = {}
        for e in db.query(models.Expense).filter(models.Expense.user_id == user.id):
            cat = e.category.value
            db_by_cat[cat] = db_by_cat.get(cat, 0.0) + float(e.amount)

        d = get_analytics(client, headers).json()
        api_by_cat = {c["category"]: c["total"] for c in d["category_summary"]}
        assert api_by_cat == db_by_cat
        assert round(sum(api_by_cat.values()), 2) == d["total_expenses"]

    def test_monthly_trends_match_database(self, client, db):
        headers = register(client, "ana_db_trend")
        seed_known_data(client, headers)

        user = db.query(models.User).filter(
            models.User.username == "ana_db_trend",
        ).first()
        db_trends: dict = {}
        for i in db.query(models.Income).filter(models.Income.user_id == user.id):
            key = (i.date.year, i.date.month)
            entry = db_trends.setdefault(key, {"income": 0.0, "expenses": 0.0})
            entry["income"] += float(i.amount)
        for e in db.query(models.Expense).filter(models.Expense.user_id == user.id):
            key = (e.date.year, e.date.month)
            entry = db_trends.setdefault(key, {"income": 0.0, "expenses": 0.0})
            entry["expenses"] += float(e.amount)

        d = get_analytics(client, headers).json()
        assert len(d["monthly_trends"]) == len(db_trends)
        for trend in d["monthly_trends"]:
            key = (trend["year"], trend["month"])
            assert key in db_trends
            assert trend["income"] == db_trends[key]["income"]
            assert trend["expenses"] == db_trends[key]["expenses"]
            assert trend["net"] == round(
                db_trends[key]["income"] - db_trends[key]["expenses"], 2
            )

    def test_savings_summary_matches_database(self, client, db):
        headers = register(client, "ana_db_sav")
        r = client.post("/api/savings/", json={
            "name": "Fund A", "target_amount": 50000,
        }, headers=headers)
        goal_a = r.json()["id"]
        client.put(f"/api/savings/{goal_a}/progress/", json={
            "current_saved": 10000,
        }, headers=headers)
        r = client.post("/api/savings/", json={
            "name": "Fund B", "target_amount": 20000,
        }, headers=headers)
        goal_b = r.json()["id"]
        client.put(f"/api/savings/{goal_b}/progress/", json={
            "current_saved": 20000,
        }, headers=headers)

        user = db.query(models.User).filter(
            models.User.username == "ana_db_sav",
        ).first()
        goals = db.query(models.SavingsGoal).filter(
            models.SavingsGoal.user_id == user.id,
        ).all()
        db_target = sum(float(g.target_amount) for g in goals)
        db_saved = sum(float(g.current_saved) for g in goals)
        db_completed = sum(1 for g in goals if g.is_completed)

        d = get_analytics(client, headers).json()
        s = d["savings_summary"]
        assert s["total_goals"] == len(goals)
        assert s["total_target"] == db_target
        assert s["total_saved"] == db_saved
        assert s["completed_goals"] == db_completed
        expected_pct = (
            round((db_saved / db_target) * 100, 2) if db_target > 0 else 0.0
        )
        assert s["overall_progress_percent"] == expected_pct

    def test_budget_summary_matches_database(self, client, db):
        headers = register(client, "ana_db_bud")
        seed_known_data(client, headers)
        r = client.post("/api/budgets/", json={
            "month": 9, "year": 2026, "total_amount": 10000,
            "allocations": [
                {"category": "food", "amount": 5000},
                {"category": "travel", "amount": 2000},
            ],
        }, headers=headers)
        assert r.status_code == 201

        user = db.query(models.User).filter(
            models.User.username == "ana_db_bud",
        ).first()
        budget = db.query(models.Budget).filter(
            models.Budget.user_id == user.id,
            models.Budget.month == 9,
            models.Budget.year == 2026,
        ).first()
        db_spent = sum(
            float(e.amount)
            for e in db.query(models.Expense).filter(
                models.Expense.user_id == user.id,
                models.Expense.date >= date(2026, 9, 1),
                models.Expense.date <= date(2026, 9, 30),
            )
        )

        d = get_analytics(client, headers, month=9, year=2026).json()
        b = d["budget_summary"]
        assert b["total_budget"] == float(budget.total_amount)
        assert b["total_spent"] == db_spent
        assert b["remaining"] == round(float(budget.total_amount) - db_spent, 2)
        assert b["utilization_percent"] == round(
            (db_spent / float(budget.total_amount)) * 100, 2
        )

        for alloc in b["allocations"]:
            db_alloc = next(
                a for a in budget.allocations if a.category.value == alloc["category"]
            )
            assert alloc["budgeted"] == float(db_alloc.amount)
            cat_spent = sum(
                float(e.amount)
                for e in db.query(models.Expense).filter(
                    models.Expense.user_id == user.id,
                    models.Expense.category == db_alloc.category,
                    models.Expense.date >= date(2026, 9, 1),
                    models.Expense.date <= date(2026, 9, 30),
                )
            )
            assert alloc["spent"] == cat_spent

    def test_filtered_totals_match_database(self, client, db):
        headers = register(client, "ana_db_filter")
        seed_known_data(client, headers)

        user = db.query(models.User).filter(
            models.User.username == "ana_db_filter",
        ).first()
        db_sep_income = sum(
            float(i.amount)
            for i in db.query(models.Income).filter(
                models.Income.user_id == user.id,
                models.Income.date >= date(2026, 9, 1),
                models.Income.date <= date(2026, 9, 30),
            )
        )
        db_sep_expenses = sum(
            float(e.amount)
            for e in db.query(models.Expense).filter(
                models.Expense.user_id == user.id,
                models.Expense.date >= date(2026, 9, 1),
                models.Expense.date <= date(2026, 9, 30),
            )
        )

        d = get_analytics(client, headers, month=9, year=2026).json()
        assert d["total_income"] == db_sep_income
        assert d["total_expenses"] == db_sep_expenses
        assert d["net_savings"] == round(db_sep_income - db_sep_expenses, 2)


# ─── Authentication & User Isolation ─────────────────────────

class TestAuthAndIsolation:

    def test_unauthenticated_rejected(self, client):
        r = client.get("/api/analytics/")
        assert r.status_code in (401, 403)

    def test_invalid_token_rejected(self, client):
        r = client.get("/api/analytics/", headers=auth_header("bad.token.here"))
        assert r.status_code in (401, 403)

    def test_user_sees_only_own_data(self, client):
        ha = register(client, "ana_iso_a")
        hb = register(client, "ana_iso_b")

        add_income(client, ha, 10000, "scholarship", "2026-09-01")
        add_expense(client, ha, 3000, "food", "2026-09-10")

        # User B adds different data
        add_income(client, hb, 500, "freelance", "2026-09-03")
        add_expense(client, hb, 100, "travel", "2026-09-04")

        da = get_analytics(client, ha).json()
        db_ = get_analytics(client, hb).json()

        assert da["total_income"] == 10000.0
        assert da["total_expenses"] == 3000.0
        assert db_["total_income"] == 500.0
        assert db_["total_expenses"] == 100.0

    def test_isolated_user_with_no_data(self, client):
        ha = register(client, "ana_iso2_a")
        hb = register(client, "ana_iso2_b")

        add_income(client, ha, 99999, "scholarship", "2026-09-01")
        add_expense(client, ha, 88888, "shopping", "2026-09-01")

        d = get_analytics(client, hb).json()
        assert d["total_income"] == 0.0
        assert d["total_expenses"] == 0.0
        assert d["has_data"] is False

    def test_response_structure_keys(self, client):
        headers = register(client, "ana_shape")
        d = get_analytics(client, headers).json()
        expected_keys = {
            "total_income", "total_expenses", "net_savings",
            "savings_rate_percent", "income_count", "expense_count",
            "has_data", "category_summary", "monthly_trends",
            "savings_summary", "budget_summary", "filters",
        }
        assert expected_keys == set(d.keys())
        assert set(d["filters"].keys()) == {"start_date", "end_date", "month", "year"}
        assert set(d["savings_summary"].keys()) == {
            "total_goals", "completed_goals", "total_target",
            "total_saved", "overall_progress_percent",
        }


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--tb=short"]))
