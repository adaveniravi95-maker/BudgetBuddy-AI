"""
Budget Alert Workflow Tests
===========================
Expense added -> utilization calculated -> threshold checked ->
alert generated -> Notification created.

Covers below-limit, near-limit (>=80%), exceeded (>=100%) cases,
category and total monthly conditions, duplicate prevention and
user isolation.

Run:  cd backend && python -m pytest test_budget_alerts.py -v
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models
from app.budget_alerts import (
    alert_phase,
    calculate_utilization,
    get_month_spent,
    month_bounds,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_budget_alerts.db"
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


def create_budget(client, headers, month=9, year=2026, total=10000, allocations=None):
    if allocations is None:
        allocations = [
            {"category": "food", "amount": 5000},
            {"category": "travel", "amount": 2000},
        ]
    r = client.post("/api/budgets/", json={
        "month": month, "year": year, "total_amount": total,
        "allocations": allocations,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def add_expense(client, headers, amount, category, date_str):
    r = client.post("/api/expenses/", json={
        "amount": amount, "category": category, "date": date_str,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def get_notifications(client, headers, params=None):
    r = client.get("/api/notifications/", headers=headers, params=params)
    assert r.status_code == 200
    return r.json()["notifications"]


def budget_alerts(client, headers):
    return [
        n for n in get_notifications(client, headers)
        if n["notification_type"] == "budget_limit"
    ]


# ─── Unit: utilization & phase helpers ───────────────────────

class TestUtilizationMath:

    def test_utilization_basic(self):
        assert calculate_utilization(3000, 5000) == 60.0
        assert calculate_utilization(4500, 5000) == 90.0
        assert calculate_utilization(5000, 5000) == 100.0
        assert calculate_utilization(5100, 5000) == 102.0

    def test_utilization_zero_budget(self):
        assert calculate_utilization(100, 0) == 0.0

    def test_utilization_zero_spent(self):
        assert calculate_utilization(0, 5000) == 0.0

    def test_phase_below_threshold(self):
        assert alert_phase(0.0) is None
        assert alert_phase(59.99) is None
        assert alert_phase(79.99) is None

    def test_phase_near_limit(self):
        assert alert_phase(80.0) == "near limit"
        assert alert_phase(90.0) == "near limit"
        assert alert_phase(99.99) == "near limit"

    def test_phase_exceeded(self):
        assert alert_phase(100.0) == "exceeded"
        assert alert_phase(150.0) == "exceeded"

    def test_month_bounds(self):
        start, end = month_bounds(2026, 2)
        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)
        start, end = month_bounds(2026, 9)
        assert end == date(2026, 9, 30)


# ─── Below / Near / Exceeded limit cases ─────────────────────

class TestThresholdCases:

    def test_below_limit_no_alert(self, client):
        headers = register(client, "alert_below")
        create_budget(client, headers, total=10000)
        # food 3000/5000 = 60%, total 3000/10000 = 30% -> both below 80%
        add_expense(client, headers, 3000, "food", "2026-09-05")
        assert budget_alerts(client, headers) == []

    def test_just_below_near_limit_no_alert(self, client):
        headers = register(client, "alert_justbelow")
        create_budget(client, headers, total=10000)
        # 3999/5000 = 79.98% -> below 80%
        add_expense(client, headers, 3999, "food", "2026-09-05")
        assert budget_alerts(client, headers) == []

    def test_near_limit_alert(self, client):
        headers = register(client, "alert_near")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 3000, "food", "2026-09-05")   # 60% no alert
        add_expense(client, headers, 1000, "food", "2026-09-06")   # 4000/5000 = 80%

        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "near limit" in alerts[0]["message"]
        assert "'food'" in alerts[0]["message"]
        assert alerts[0]["notification_type"] == "budget_limit"
        assert alerts[0]["is_read"] is False

    def test_exact_80_percent_triggers_near_limit(self, client):
        headers = register(client, "alert_exact80")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 4000, "food", "2026-09-05")
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "near limit" in alerts[0]["message"]

    def test_exceeded_alert(self, client):
        headers = register(client, "alert_exceeded")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 5200, "food", "2026-09-05")   # 104%

        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "exceeded" in alerts[0]["message"]
        assert "'food'" in alerts[0]["message"]

    def test_escalation_near_then_exceeded(self, client):
        headers = register(client, "alert_escalate")
        create_budget(client, headers, total=10000)

        add_expense(client, headers, 4500, "food", "2026-09-05")   # 90% near
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "near limit" in alerts[0]["message"]

        add_expense(client, headers, 700, "food", "2026-09-06")    # 5200 = 104% exceeded
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 2
        messages = " ".join(a["message"] for a in alerts)
        assert "near limit" in messages
        assert "exceeded" in messages

    def test_zero_budget_allocation_with_spending(self, client):
        headers = register(client, "alert_zerobud")
        # zero allocation not allowed by schema; use tiny allocation instead
        create_budget(
            client, headers, total=10000,
            allocations=[{"category": "food", "amount": 1}],
        )
        add_expense(client, headers, 100, "food", "2026-09-05")
        alerts = budget_alerts(client, headers)
        assert any("exceeded" in a["message"] for a in alerts)


# ─── Duplicate prevention ────────────────────────────────────

class TestDuplicatePrevention:

    def test_same_phase_not_duplicated(self, client):
        headers = register(client, "alert_dupe")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 5100, "food", "2026-09-05")   # exceeded
        assert len(budget_alerts(client, headers)) == 1

        # Further spending in same phase -> still one alert
        add_expense(client, headers, 200, "food", "2026-09-06")
        add_expense(client, headers, 300, "food", "2026-09-07")
        assert len(budget_alerts(client, headers)) == 1

    def test_near_limit_not_duplicated(self, client):
        headers = register(client, "alert_dupe_near")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 4100, "food", "2026-09-05")   # 82% near
        assert len(budget_alerts(client, headers)) == 1
        add_expense(client, headers, 100, "food", "2026-09-06")    # still near
        assert len(budget_alerts(client, headers)) == 1

    def test_escalation_creates_new_alert(self, client):
        headers = register(client, "alert_dupe_esc")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 4100, "food", "2026-09-05")   # near
        add_expense(client, headers, 1000, "food", "2026-09-06")   # exceeded
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 2

    def test_category_alerts_do_not_block_each_other(self, client):
        headers = register(client, "alert_cats")
        create_budget(client, headers, total=20000)
        # food near limit
        add_expense(client, headers, 4200, "food", "2026-09-05")
        # travel near limit (2000 * 0.8 = 1600)
        add_expense(client, headers, 1700, "travel", "2026-09-06")

        alerts = budget_alerts(client, headers)
        assert len(alerts) == 2
        joined = " ".join(a["message"] for a in alerts)
        assert "'food'" in joined
        assert "'travel'" in joined


# ─── Category-wise and total monthly conditions ──────────────

class TestCategoryAndTotalConditions:

    def test_total_budget_near_limit_alert(self, client):
        headers = register(client, "alert_total")
        # total 5000, food alloc 4000
        create_budget(
            client, headers, total=5000,
            allocations=[{"category": "food", "amount": 4000}],
        )
        # 4200: food 105% exceeded, total 84% near limit -> both
        add_expense(client, headers, 4200, "food", "2026-09-05")

        alerts = budget_alerts(client, headers)
        assert len(alerts) == 2
        joined = " ".join(a["message"] for a in alerts)
        assert "'food'" in joined
        assert "total spending" in joined

    def test_total_only_when_category_still_under(self, client):
        headers = register(client, "alert_total2")
        create_budget(
            client, headers, total=5000,
            allocations=[{"category": "food", "amount": 10000}],
        )
        # food under its allocation, but total at 84%
        add_expense(client, headers, 4200, "food", "2026-09-05")

        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "total spending" in alerts[0]["message"]

    def test_no_budget_no_alerts(self, client):
        headers = register(client, "alert_nobudget")
        add_expense(client, headers, 99999, "food", "2026-09-05")
        assert budget_alerts(client, headers) == []

    def test_alert_only_for_matching_month(self, client):
        headers = register(client, "alert_month")
        create_budget(client, headers, month=9, year=2026, total=5000,
                      allocations=[{"category": "food", "amount": 4000}])
        # Expense in October - no October budget
        add_expense(client, headers, 4200, "food", "2026-10-05")
        assert budget_alerts(client, headers) == []

        # Expense in September - alerts fire
        add_expense(client, headers, 4200, "food", "2026-09-05")
        assert len(budget_alerts(client, headers)) >= 1

    def test_expense_update_triggers_recheck(self, client):
        headers = register(client, "alert_update")
        create_budget(client, headers, total=10000)
        r = add_expense(client, headers, 100, "food", "2026-09-05")
        assert budget_alerts(client, headers) == []

        r2 = client.put(f"/api/expenses/{r['id']}/", json={
            "amount": 5200,
        }, headers=headers)
        assert r2.status_code == 200
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "exceeded" in alerts[0]["message"]

    def test_budget_create_evaluates_existing_expenses(self, client):
        headers = register(client, "alert_budlast")
        add_expense(client, headers, 5200, "food", "2026-09-05")
        assert budget_alerts(client, headers) == []

        create_budget(client, headers, total=10000)
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "exceeded" in alerts[0]["message"]

    def test_budget_update_allocations_reevaluate(self, client):
        headers = register(client, "alert_budupd")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 3000, "food", "2026-09-05")   # 60% of 5000
        assert budget_alerts(client, headers) == []

        # Tighten food allocation to 3500 -> 3000/3500 = 85.7% near
        budgets = client.get("/api/budgets/", headers=headers).json()["budgets"]
        bud_id = budgets[0]["id"]
        r = client.put(f"/api/budgets/{bud_id}/", json={
            "allocations": [
                {"category": "food", "amount": 3500},
                {"category": "travel", "amount": 2000},
            ],
        }, headers=headers)
        assert r.status_code == 200
        alerts = budget_alerts(client, headers)
        assert len(alerts) == 1
        assert "near limit" in alerts[0]["message"]


# ─── Notification integration & user isolation ───────────────

class TestNotificationAndIsolation:

    def test_alert_stored_as_budget_limit_notification(self, client, db):
        headers = register(client, "alert_store")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 5200, "food", "2026-09-05")

        user = db.query(models.User).filter(
            models.User.username == "alert_store",
        ).first()
        notif = db.query(models.Notification).filter(
            models.Notification.user_id == user.id,
            models.Notification.notification_type == models.NotificationType.budget_limit,
        ).all()
        assert len(notif) == 1
        assert notif[0].related_id is not None

        budget = db.query(models.Budget).filter(
            models.Budget.user_id == user.id,
        ).first()
        assert notif[0].related_id == budget.id

    def test_alerts_only_for_correct_user(self, client):
        ha = register(client, "alert_user_a")
        hb = register(client, "alert_user_b")

        create_budget(client, ha, total=10000)
        add_expense(client, ha, 5200, "food", "2026-09-05")

        assert len(budget_alerts(client, ha)) == 1
        # User B has no budget and no expenses -> no alerts
        assert budget_alerts(client, hb) == []

    def test_user_b_expenses_do_not_trigger_user_a_alerts_extra(self, client):
        ha = register(client, "alert_iso_a")
        hb = register(client, "alert_iso_b")

        create_budget(client, ha, total=10000)
        add_expense(client, ha, 3000, "food", "2026-09-05")   # 60%, no alert

        # User B spends a lot - must not affect A
        add_expense(client, hb, 99999, "food", "2026-09-05")
        assert budget_alerts(client, ha) == []
        assert budget_alerts(client, hb) == []  # B has no budget

    def test_user_b_own_budget_own_alerts(self, client):
        ha = register(client, "alert_iso2_a")
        hb = register(client, "alert_iso2_b")

        create_budget(client, ha, total=10000)
        add_expense(client, ha, 5200, "food", "2026-09-05")

        create_budget(client, hb, total=10000)
        add_expense(client, hb, 1000, "food", "2026-09-05")

        assert len(budget_alerts(client, ha)) == 1
        assert budget_alerts(client, hb) == []

    def test_alerts_appear_in_notifications_endpoint(self, client):
        headers = register(client, "alert_endpoint")
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 5200, "food", "2026-09-05")

        notifications = get_notifications(client, headers)
        budget_notifs = [
            n for n in notifications
            if n["notification_type"] == "budget_limit"
        ]
        assert len(budget_notifs) == 1
        assert "exceeded" in budget_notifs[0]["message"]

    def test_get_month_spent_is_user_scoped(self, client, db):
        ha = register(client, "spent_a")
        hb = register(client, "spent_b")
        add_expense(client, ha, 1000, "food", "2026-09-05")
        add_expense(client, hb, 2000, "food", "2026-09-05")

        user_a = db.query(models.User).filter(models.User.username == "spent_a").first()
        user_b = db.query(models.User).filter(models.User.username == "spent_b").first()

        assert get_month_spent(db, user_a.id, 2026, 9) == 1000.0
        assert get_month_spent(db, user_b.id, 2026, 9) == 2000.0
        assert get_month_spent(db, user_a.id, 2026, 9, models.ExpenseCategory.food) == 1000.0
        assert get_month_spent(db, user_a.id, 2026, 10) == 0.0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--tb=short"]))
