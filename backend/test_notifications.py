"""
Notification Integration Tests
==============================
Notifications generated from actual system events:
  - Savings milestone (25/50/75/100%) from goal progress updates
  - Budget limit alerts from expense/budget activity
  - Monthly report notification from report generation
Unread/read behaviour, duplicate prevention, and user isolation.

Run:  cd backend && python -m pytest test_notifications.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models
from app.routers.savings import _check_savings_milestone

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notifications.db"
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


def create_goal(client, headers, name="Emergency fund", target=10000):
    r = client.post("/api/savings/", json={
        "name": name, "target_amount": target,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def set_progress(client, headers, goal_id, amount):
    return client.put(
        f"/api/savings/{goal_id}/progress/",
        json={"current_saved": amount},
        headers=headers,
    )


def add_expense(client, headers, amount, category, date_str):
    r = client.post("/api/expenses/", json={
        "amount": amount, "category": category, "date": date_str,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def create_budget(client, headers, month=9, year=2026, total=10000, allocations=None):
    if allocations is None:
        allocations = [{"category": "food", "amount": 5000}]
    r = client.post("/api/budgets/", json={
        "month": month, "year": year, "total_amount": total,
        "allocations": allocations,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def list_notifications(client, headers, path="/api/notifications/"):
    r = client.get(path, headers=headers)
    assert r.status_code == 200
    return r.json()


def notifs_of(payload, ntype):
    return [n for n in payload["notifications"] if n["notification_type"] == ntype]


# ─── Savings milestone notifications ─────────────────────────

class TestSavingsMilestoneNotifications:

    def test_below_first_milestone_no_notification(self, client):
        headers = register(client, "ms_below")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 1000)  # 10%

        payload = list_notifications(client, headers)
        assert payload["total"] == 0
        assert notifs_of(payload, "savings_milestone") == []

    def test_exact_25_percent_milestone(self, client, db):
        headers = register(client, "ms_25")
        goal = create_goal(client, headers, name="Laptop", target=10000)
        set_progress(client, headers, goal["id"], 2500)

        payload = list_notifications(client, headers)
        milestones = notifs_of(payload, "savings_milestone")
        assert len(milestones) == 1
        assert "25%" in milestones[0]["message"]
        assert "Laptop" in milestones[0]["message"]
        assert milestones[0]["is_read"] is False
        assert milestones[0]["related_id"] == goal["id"]

        user = db.query(models.User).filter(models.User.username == "ms_25").first()
        stored = db.query(models.Notification).filter(
            models.Notification.user_id == user.id,
            models.Notification.notification_type
            == models.NotificationType.savings_milestone,
        ).all()
        assert len(stored) == 1

    def test_50_percent_milestone(self, client):
        headers = register(client, "ms_50")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 5000)

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        # Jumping straight to 50% also back-fills the 25% milestone
        assert len(milestones) == 2
        joined = " ".join(n["message"] for n in milestones)
        assert "25%" in joined
        assert "50%" in joined
        assert any("50%" in n["message"] for n in milestones)

    def test_75_percent_milestone(self, client):
        headers = register(client, "ms_75")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 7500)

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        assert len(milestones) == 3
        joined = " ".join(n["message"] for n in milestones)
        assert "25%" in joined
        assert "50%" in joined
        assert "75%" in joined

    def test_100_percent_completion_milestone(self, client):
        headers = register(client, "ms_100")
        goal = create_goal(client, headers, target=10000)
        r = set_progress(client, headers, goal["id"], 10000)
        assert r.json()["is_completed"] is True

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        assert len(milestones) == 4
        completed = [n for n in milestones if "completed" in n["message"]]
        assert len(completed) == 1
        assert "100%" in completed[0]["message"]

    def test_jump_to_target_creates_all_missed_milestones(self, client):
        headers = register(client, "ms_jump")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 10000)

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        assert len(milestones) == 4
        joined = " ".join(n["message"] for n in milestones)
        assert "25%" in joined
        assert "50%" in joined
        assert "75%" in joined
        assert "100%" in joined
        assert all(n["related_id"] == goal["id"] for n in milestones)

    def test_milestone_not_duplicated_on_same_phase_updates(self, client):
        headers = register(client, "ms_dupe")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 3000)   # 30% -> 25%
        set_progress(client, headers, goal["id"], 4000)   # 40% -> still only 25%
        set_progress(client, headers, goal["id"], 4900)   # 49% -> still only 25%

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        assert len(milestones) == 1
        assert "25%" in milestones[0]["message"]

    def test_each_milestone_created_exactly_once_when_stepping(self, client):
        headers = register(client, "ms_steps")
        goal = create_goal(client, headers, target=100)
        for amount in (10, 25, 40, 50, 60, 75, 90, 100):
            set_progress(client, headers, goal["id"], amount)

        milestones = notifs_of(list_notifications(client, headers), "savings_milestone")
        assert len(milestones) == 4
        labels = sorted(
            m for m in ("25%", "50%", "75%", "100%")
            if any(m in n["message"] for n in milestones)
        )
        assert labels == ["100%", "25%", "50%", "75%"]

    def test_reinvoking_milestone_check_does_not_duplicate(self, client, db):
        """Dedupe must hold even if the milestone check runs again later."""
        headers = register(client, "ms_recheck")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 10000)

        user = db.query(models.User).filter(
            models.User.username == "ms_recheck",
        ).first()
        goal_row = db.query(models.SavingsGoal).filter(
            models.SavingsGoal.id == goal["id"],
        ).first()

        _check_savings_milestone(db, user.id, goal_row)
        _check_savings_milestone(db, user.id, goal_row)
        db.commit()

        stored = db.query(models.Notification).filter(
            models.Notification.user_id == user.id,
            models.Notification.notification_type
            == models.NotificationType.savings_milestone,
        ).all()
        assert len(stored) == 4  # 25/50/75/100, no extras
        completed_msgs = [n for n in stored if "completed" in n.message]
        assert len(completed_msgs) == 1

    def test_new_goal_milestone_notifications_start_unread(self, client):
        headers = register(client, "ms_unread")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 250)

        payload = list_notifications(client, headers)
        assert payload["unread_count"] == 1
        assert all(n["is_read"] is False for n in payload["notifications"])


# ─── Milestone user isolation ────────────────────────────────

class TestMilestoneIsolation:

    def test_user_b_does_not_receive_user_a_milestones(self, client):
        ha = register(client, "ms_iso_a")
        hb = register(client, "ms_iso_b")
        goal = create_goal(client, ha, target=10000)
        set_progress(client, ha, goal["id"], 5000)

        payload_a = list_notifications(client, ha)
        payload_b = list_notifications(client, hb)
        assert len(notifs_of(payload_a, "savings_milestone")) == 2  # 25% + 50%
        assert payload_b["total"] == 0
        assert payload_b["unread_count"] == 0

    def test_each_user_gets_own_milestone_notifications(self, client):
        ha = register(client, "ms_own_a")
        hb = register(client, "ms_own_b")
        goal_a = create_goal(client, ha, name="A goal", target=1000)
        goal_b = create_goal(client, hb, name="B goal", target=1000)
        set_progress(client, ha, goal_a["id"], 1000)
        set_progress(client, hb, goal_b["id"], 250)

        ma = notifs_of(list_notifications(client, ha), "savings_milestone")
        mb = notifs_of(list_notifications(client, hb), "savings_milestone")
        assert len(ma) == 4
        assert len(mb) == 1
        assert ma[0]["related_id"] == goal_a["id"]
        assert mb[0]["related_id"] == goal_b["id"]
        assert "A goal" in " ".join(n["message"] for n in ma)
        assert "B goal" in " ".join(n["message"] for n in mb)


# ─── Unread / read behaviour ─────────────────────────────────

class TestUnreadReadBehaviour:

    def test_empty_notifications_payload(self, client):
        headers = register(client, "nr_empty")
        payload = list_notifications(client, headers)
        assert payload == {"notifications": [], "total": 0, "unread_count": 0}

    def test_response_structure_keys(self, client):
        headers = register(client, "nr_shape")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 250)

        payload = list_notifications(client, headers)
        assert set(payload.keys()) == {"notifications", "total", "unread_count"}
        n = payload["notifications"][0]
        assert set(n.keys()) == {
            "id", "notification_type", "message", "is_read",
            "related_id", "created_at",
        }

    def test_new_event_notification_is_unread(self, client):
        headers = register(client, "nr_unread")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 250)

        payload = list_notifications(client, headers)
        assert payload["total"] == 1
        assert payload["unread_count"] == 1
        assert payload["notifications"][0]["is_read"] is False

    def test_unread_endpoint_returns_only_unread(self, client):
        headers = register(client, "nr_filter")
        goal = create_goal(client, headers, target=100)
        set_progress(client, headers, goal["id"], 25)   # 25% milestone
        set_progress(client, headers, goal["id"], 50)   # 50% milestone

        all_payload = list_notifications(client, headers)
        assert all_payload["total"] == 2

        first_id = all_payload["notifications"][0]["id"]
        r = client.put(f"/api/notifications/{first_id}/read/", headers=headers)
        assert r.status_code == 200

        unread_payload = list_notifications(
            client, headers, path="/api/notifications/unread/",
        )
        assert unread_payload["total"] == 1
        assert unread_payload["unread_count"] == 1
        remaining = unread_payload["notifications"]
        assert all(n["is_read"] is False for n in remaining)
        assert remaining[0]["id"] != first_id

        refreshed = list_notifications(client, headers)
        assert refreshed["unread_count"] == 1
        assert refreshed["total"] == 2
        read_items = [n for n in refreshed["notifications"] if n["id"] == first_id]
        assert read_items[0]["is_read"] is True

    def test_mark_all_read(self, client):
        headers = register(client, "nr_all")
        goal = create_goal(client, headers, target=100)
        set_progress(client, headers, goal["id"], 100)  # 4 milestones

        payload = list_notifications(client, headers)
        assert payload["unread_count"] == 4

        r = client.put("/api/notifications/read-all/", headers=headers)
        assert r.status_code == 200

        payload = list_notifications(client, headers)
        assert payload["total"] == 4
        assert payload["unread_count"] == 0
        assert all(n["is_read"] for n in payload["notifications"])

        unread_payload = list_notifications(
            client, headers, path="/api/notifications/unread/",
        )
        assert unread_payload["total"] == 0

    def test_mark_all_read_is_idempotent(self, client):
        headers = register(client, "nr_all_twice")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 250)

        assert client.put("/api/notifications/read-all/", headers=headers).status_code == 200
        assert client.put("/api/notifications/read-all/", headers=headers).status_code == 200

        payload = list_notifications(client, headers)
        assert payload["unread_count"] == 0
        assert payload["total"] == 1

    def test_mark_same_notification_read_twice(self, client):
        headers = register(client, "nr_twice")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 250)
        nid = list_notifications(client, headers)["notifications"][0]["id"]

        assert client.put(f"/api/notifications/{nid}/read/", headers=headers).status_code == 200
        assert client.put(f"/api/notifications/{nid}/read/", headers=headers).status_code == 200
        assert list_notifications(client, headers)["unread_count"] == 0

    def test_mark_nonexistent_notification_read(self, client):
        headers = register(client, "nr_404")
        r = client.put("/api/notifications/99999/read/", headers=headers)
        assert r.status_code == 404

    def test_mark_all_read_with_no_notifications(self, client):
        headers = register(client, "nr_all_empty")
        r = client.put("/api/notifications/read-all/", headers=headers)
        assert r.status_code == 200
        payload = list_notifications(client, headers)
        assert payload == {"notifications": [], "total": 0, "unread_count": 0}

    def test_requires_auth(self, client):
        assert client.get("/api/notifications/").status_code in (401, 403)
        assert client.get("/api/notifications/unread/").status_code in (401, 403)
        assert client.put("/api/notifications/1/read/").status_code in (401, 403)
        assert client.put("/api/notifications/read-all/").status_code in (401, 403)

    def test_invalid_token_rejected(self, client):
        bad = auth_header("bad.token.here")
        assert client.get("/api/notifications/", headers=bad).status_code in (401, 403)

    def test_cannot_mark_other_users_notification_read(self, client):
        ha = register(client, "nr_iso_a")
        hb = register(client, "nr_iso_b")
        goal = create_goal(client, ha, target=1000)
        set_progress(client, ha, goal["id"], 250)

        notif_a = list_notifications(client, ha)["notifications"][0]
        r = client.put(f"/api/notifications/{notif_a['id']}/read/", headers=hb)
        assert r.status_code == 404

        # A's notification remains unread
        assert list_notifications(client, ha)["unread_count"] == 1

    def test_read_all_only_affects_own_notifications(self, client):
        ha = register(client, "nr_ra_a")
        hb = register(client, "nr_ra_b")
        goal_a = create_goal(client, ha, target=1000)
        goal_b = create_goal(client, hb, target=1000)
        set_progress(client, ha, goal_a["id"], 250)
        set_progress(client, hb, goal_b["id"], 250)

        assert client.put("/api/notifications/read-all/", headers=ha).status_code == 200

        assert list_notifications(client, ha)["unread_count"] == 0
        assert list_notifications(client, hb)["unread_count"] == 1

    def test_users_separate_notification_lists(self, client):
        ha = register(client, "nr_list_a")
        hb = register(client, "nr_list_b")
        goal_a = create_goal(client, ha, target=100)
        set_progress(client, ha, goal_a["id"], 100)

        payload_a = list_notifications(client, ha)
        payload_b = list_notifications(client, hb)
        assert payload_a["total"] == 4
        assert payload_b["total"] == 0


# ─── Cross-event integration (budget + savings + report) ─────

class TestEventDrivenNotifications:

    def test_all_event_types_generate_notifications(self, client):
        headers = register(client, "ev_all")

        # Event 1: savings milestone
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 5000)  # 50%

        # Event 2: budget limit (expense crosses threshold)
        create_budget(client, headers, total=10000)
        add_expense(client, headers, 5200, "food", "2026-09-05")  # food 104%

        # Event 3: monthly report
        r = client.get(
            "/api/reports/monthly/",
            headers=headers,
            params={"month": 9, "year": 2026, "format": "json"},
        )
        assert r.status_code == 200

        payload = list_notifications(client, headers)
        types = {n["notification_type"] for n in payload["notifications"]}
        assert "savings_milestone" in types
        assert "budget_limit" in types
        assert "general" in types

        assert len(notifs_of(payload, "savings_milestone")) == 2  # 25% + 50%
        assert len(notifs_of(payload, "budget_limit")) >= 1
        report_notifs = [
            n for n in notifs_of(payload, "general")
            if "Monthly report" in n["message"]
        ]
        assert len(report_notifs) == 1
        assert payload["unread_count"] == payload["total"]

    def test_repeated_events_do_not_create_duplicates(self, client):
        headers = register(client, "ev_dupe")
        goal = create_goal(client, headers, target=10000)
        set_progress(client, headers, goal["id"], 5000)  # 50% milestone

        create_budget(client, headers, total=10000)
        add_expense(client, headers, 4100, "food", "2026-09-05")  # 82% near limit
        add_expense(client, headers, 100, "food", "2026-09-06")   # still near
        add_expense(client, headers, 100, "food", "2026-09-07")   # still near

        # Further progress below next milestone
        set_progress(client, headers, goal["id"], 6000)

        # Report generated repeatedly
        for fmt in ("json", "csv", "json"):
            client.get(
                "/api/reports/monthly/",
                headers=headers,
                params={"month": 9, "year": 2026, "format": fmt},
            )

        payload = list_notifications(client, headers)
        assert len(notifs_of(payload, "savings_milestone")) == 2  # 25% + 50%
        assert len(notifs_of(payload, "budget_limit")) == 1
        report_notifs = [
            n for n in notifs_of(payload, "general")
            if "Monthly report" in n["message"]
        ]
        assert len(report_notifs) == 1
        assert payload["total"] == 4
        assert payload["unread_count"] == 4

    def test_events_isolated_between_users(self, client):
        ha = register(client, "ev_iso_a")
        hb = register(client, "ev_iso_b")

        goal_a = create_goal(client, ha, target=1000)
        set_progress(client, ha, goal_a["id"], 1000)
        create_budget(client, ha, total=10000)
        add_expense(client, ha, 5200, "food", "2026-09-05")
        client.get(
            "/api/reports/monthly/",
            headers=ha,
            params={"month": 9, "year": 2026},
        )

        payload_a = list_notifications(client, ha)
        payload_b = list_notifications(client, hb)

        assert payload_a["total"] >= 6   # 4 milestones + budget + report
        assert payload_b["total"] == 0
        assert payload_b["unread_count"] == 0

        # B's read-all does not touch A's
        client.put("/api/notifications/read-all/", headers=hb)
        assert list_notifications(client, ha)["unread_count"] == payload_a["unread_count"]

    def test_mixed_read_states_across_event_types(self, client):
        headers = register(client, "ev_mixed")
        goal = create_goal(client, headers, target=1000)
        set_progress(client, headers, goal["id"], 1000)  # 4 milestones

        payload = list_notifications(client, headers)
        assert payload["unread_count"] == 4

        # Read one milestone
        target_id = payload["notifications"][0]["id"]
        client.put(f"/api/notifications/{target_id}/read/", headers=headers)

        payload = list_notifications(client, headers)
        assert payload["total"] == 4
        assert payload["unread_count"] == 3

        unread = list_notifications(client, headers, path="/api/notifications/unread/")
        assert unread["total"] == 3
        assert target_id not in [n["id"] for n in unread["notifications"]]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--tb=short"]))
