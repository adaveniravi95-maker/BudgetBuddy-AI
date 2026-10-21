"""
Savings Goal Management — Tests
================================
Tests: CRUD, validation, ownership, progress calculation, completion detection.

Run:  cd backend && python -m pytest test_savings.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models, auth

# ══════════════════════════════════════════════════════════════════
# TEST DB
# ══════════════════════════════════════════════════════════════════
engine = create_engine("sqlite:///./test_savings.db", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
# 1. CREATE SAVINGS GOAL
# ══════════════════════════════════════════════════════════════════

class TestCreateGoal:

    def test_create_goal_success(self, client, db):
        token = tok(client, "sav1")
        r = client.post("/api/savings/", json={
            "name": "New Laptop", "target_amount": 50000,
        }, headers=hd(token))
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "New Laptop"
        assert data["target_amount"] == 50000.0
        assert data["current_saved"] == 0.0
        assert data["progress_percent"] == 0.0
        assert data["is_completed"] is False

    def test_create_goal_persists_in_db(self, client, db):
        token = tok(client, "sav2")
        user = db.query(models.User).filter(models.User.username == "sav2").first()
        r = client.post("/api/savings/", json={
            "name": "Emergency Fund", "target_amount": 100000,
        }, headers=hd(token))
        goal_id = r.json()["id"]
        goal_db = db.query(models.SavingsGoal).filter(models.SavingsGoal.id == goal_id).first()
        assert goal_db is not None
        assert goal_db.user_id == user.id
        assert goal_db.name == "Emergency Fund"
        assert float(goal_db.target_amount) == 100000.0
        assert float(goal_db.current_saved) == 0.0
        assert goal_db.is_completed is False

    def test_create_goal_requires_auth(self, client):
        r = client.post("/api/savings/", json={"name": "Test", "target_amount": 1000})
        assert r.status_code in (401, 403)

    def test_create_goal_empty_name_rejected(self, client):
        token = tok(client, "sav3")
        r = client.post("/api/savings/", json={"name": "", "target_amount": 5000}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_whitespace_name_rejected(self, client):
        token = tok(client, "sav4")
        r = client.post("/api/savings/", json={"name": "   ", "target_amount": 5000}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_missing_name_rejected(self, client):
        token = tok(client, "sav5")
        r = client.post("/api/savings/", json={"target_amount": 5000}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_zero_target_rejected(self, client):
        token = tok(client, "sav6")
        r = client.post("/api/savings/", json={"name": "Goal", "target_amount": 0}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_negative_target_rejected(self, client):
        token = tok(client, "sav7")
        r = client.post("/api/savings/", json={"name": "Goal", "target_amount": -1000}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_missing_target_rejected(self, client):
        token = tok(client, "sav8")
        r = client.post("/api/savings/", json={"name": "Goal"}, headers=hd(token))
        assert r.status_code == 422

    def test_create_goal_empty_body_rejected(self, client):
        token = tok(client, "sav9")
        r = client.post("/api/savings/", json={}, headers=hd(token))
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════
# 2. LIST / GET SAVINGS GOALS
# ══════════════════════════════════════════════════════════════════

class TestListGoals:

    def test_list_empty(self, client):
        token = tok(client, "list1")
        r = client.get("/api/savings/", headers=hd(token))
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert r.json()["goals"] == []

    def test_list_returns_all_goals(self, client):
        token = tok(client, "list2")
        client.post("/api/savings/", json={"name": "Goal A", "target_amount": 10000}, headers=hd(token))
        client.post("/api/savings/", json={"name": "Goal B", "target_amount": 20000}, headers=hd(token))
        r = client.get("/api/savings/", headers=hd(token))
        assert r.json()["total"] == 2

    def test_get_single_goal(self, client):
        token = tok(client, "list3")
        rid = client.post("/api/savings/", json={"name": "My Goal", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.get(f"/api/savings/{rid}/", headers=hd(token))
        assert r.status_code == 200
        assert r.json()["name"] == "My Goal"

    def test_get_nonexistent_goal(self, client):
        token = tok(client, "list4")
        r = client.get("/api/savings/99999/", headers=hd(token))
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════
# 3. UPDATE SAVINGS GOAL
# ══════════════════════════════════════════════════════════════════

class TestUpdateGoal:

    def test_update_name(self, client):
        token = tok(client, "upd1")
        rid = client.post("/api/savings/", json={"name": "Old Name", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/", json={"name": "New Name"}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_update_target_amount(self, client):
        token = tok(client, "upd2")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/", json={"target_amount": 10000}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["target_amount"] == 10000.0

    def test_update_empty_name_rejected(self, client):
        token = tok(client, "upd3")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/", json={"name": ""}, headers=hd(token))
        assert r.status_code == 422

    def test_update_zero_target_rejected(self, client):
        token = tok(client, "upd4")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/", json={"target_amount": 0}, headers=hd(token))
        assert r.status_code == 422

    def test_update_nonexistent_goal(self, client):
        token = tok(client, "upd5")
        r = client.put("/api/savings/99999/", json={"name": "X"}, headers=hd(token))
        assert r.status_code == 404

    def test_update_completed_goal_rejected(self, client, db):
        token = tok(client, "upd6")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 100}, headers=hd(token)).json()["id"]
        # Complete the goal
        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 100}, headers=hd(token))
        # Try to update
        r = client.put(f"/api/savings/{rid}/", json={"name": "Changed"}, headers=hd(token))
        assert r.status_code == 400
        assert "completed" in r.json()["detail"]


# ══════════════════════════════════════════════════════════════════
# 4. PROGRESS TRACKING
# ══════════════════════════════════════════════════════════════════

class TestProgress:

    def test_progress_basic(self, client):
        token = tok(client, "prog1")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 50000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 15000}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["current_saved"] == 15000.0
        assert r.json()["progress_percent"] == 30.0
        assert r.json()["is_completed"] is False

    def test_progress_zero(self, client):
        token = tok(client, "prog2")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 0}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["progress_percent"] == 0.0

    def test_progress_at_target_marks_completed(self, client):
        token = tok(client, "prog3")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 10000}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["is_completed"] is True
        assert r.json()["progress_percent"] == 100.0
        assert r.json()["current_saved"] == 10000.0

    def test_progress_exceeds_target_caps_at_100(self, client):
        """If saved exceeds target, cap at target and mark completed."""
        token = tok(client, "prog4")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 15000}, headers=hd(token))
        assert r.status_code == 200
        assert r.json()["is_completed"] is True
        assert r.json()["current_saved"] == 10000.0  # capped
        assert r.json()["progress_percent"] == 100.0

    def test_progress_negative_rejected(self, client):
        token = tok(client, "prog5")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": -500}, headers=hd(token))
        assert r.status_code == 422

    def test_progress_on_completed_goal_rejected(self, client):
        token = tok(client, "prog6")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 100}, headers=hd(token)).json()["id"]
        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 100}, headers=hd(token))
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 200}, headers=hd(token))
        assert r.status_code == 400
        assert "completed" in r.json()["detail"]

    def test_progress_nonexistent_goal(self, client):
        token = tok(client, "prog7")
        r = client.put("/api/savings/99999/progress/", json={"current_saved": 100}, headers=hd(token))
        assert r.status_code == 404

    def test_progress_requires_auth(self, client):
        r = client.put("/api/savings/1/progress/", json={"current_saved": 100})
        assert r.status_code in (401, 403)

    def test_progress_incremental(self, client):
        """Multiple progress updates should accumulate correctly."""
        token = tok(client, "prog8")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]

        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 2000}, headers=hd(token))
        r1 = client.get(f"/api/savings/{rid}/", headers=hd(token))
        assert r1.json()["progress_percent"] == 20.0

        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 5000}, headers=hd(token))
        r2 = client.get(f"/api/savings/{rid}/", headers=hd(token))
        assert r2.json()["progress_percent"] == 50.0

        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 8000}, headers=hd(token))
        r3 = client.get(f"/api/savings/{rid}/", headers=hd(token))
        assert r3.json()["progress_percent"] == 80.0


# ══════════════════════════════════════════════════════════════════
# 5. USER OWNERSHIP / ISOLATION
# ══════════════════════════════════════════════════════════════════

class TestOwnership:

    def test_user_b_cannot_see_user_a_goal(self, client):
        tA = tok(client, "own1a", "own1a@test.com")
        tB = tok(client, "own1b", "own1b@test.com")
        rid = client.post("/api/savings/", json={"name": "A's Goal", "target_amount": 5000}, headers=hd(tA)).json()["id"]
        r = client.get(f"/api/savings/{rid}/", headers=hd(tB))
        assert r.status_code == 404

    def test_user_b_cannot_update_user_a_goal(self, client):
        tA = tok(client, "own2a", "own2a@test.com")
        tB = tok(client, "own2b", "own2b@test.com")
        rid = client.post("/api/savings/", json={"name": "A's Goal", "target_amount": 5000}, headers=hd(tA)).json()["id"]
        r = client.put(f"/api/savings/{rid}/", json={"name": "Hacked"}, headers=hd(tB))
        assert r.status_code == 404

    def test_user_b_cannot_update_progress_on_user_a_goal(self, client):
        tA = tok(client, "own3a", "own3a@test.com")
        tB = tok(client, "own3b", "own3b@test.com")
        rid = client.post("/api/savings/", json={"name": "A's Goal", "target_amount": 5000}, headers=hd(tA)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 999}, headers=hd(tB))
        assert r.status_code == 404

    def test_user_b_cannot_delete_user_a_goal(self, client):
        tA = tok(client, "own4a", "own4a@test.com")
        tB = tok(client, "own4b", "own4b@test.com")
        rid = client.post("/api/savings/", json={"name": "A's Goal", "target_amount": 5000}, headers=hd(tA)).json()["id"]
        r = client.delete(f"/api/savings/{rid}/", headers=hd(tB))
        assert r.status_code == 404

    def test_user_list_only_own_goals(self, client):
        tA = tok(client, "own5a", "own5a@test.com")
        tB = tok(client, "own5b", "own5b@test.com")
        client.post("/api/savings/", json={"name": "A1", "target_amount": 1000}, headers=hd(tA))
        client.post("/api/savings/", json={"name": "A2", "target_amount": 2000}, headers=hd(tA))
        client.post("/api/savings/", json={"name": "B1", "target_amount": 3000}, headers=hd(tB))

        rA = client.get("/api/savings/", headers=hd(tA))
        rB = client.get("/api/savings/", headers=hd(tB))
        assert rA.json()["total"] == 2
        assert rB.json()["total"] == 1
        assert rB.json()["goals"][0]["name"] == "B1"


# ══════════════════════════════════════════════════════════════════
# 6. DELETE
# ══════════════════════════════════════════════════════════════════

class TestDelete:

    def test_delete_goal(self, client, db):
        token = tok(client, "del1")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 5000}, headers=hd(token)).json()["id"]
        r = client.delete(f"/api/savings/{rid}/", headers=hd(token))
        assert r.status_code == 204
        # Confirm gone
        r = client.get(f"/api/savings/{rid}/", headers=hd(token))
        assert r.status_code == 404

    def test_delete_nonexistent_goal(self, client):
        token = tok(client, "del2")
        r = client.delete("/api/savings/99999/", headers=hd(token))
        assert r.status_code == 404

    def test_delete_completed_goal(self, client):
        token = tok(client, "del3")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 100}, headers=hd(token)).json()["id"]
        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 100}, headers=hd(token))
        r = client.delete(f"/api/savings/{rid}/", headers=hd(token))
        assert r.status_code == 204


# ══════════════════════════════════════════════════════════════════
# 7. PROGRESS PERCENTAGE EDGE CASES
# ══════════════════════════════════════════════════════════════════

class TestProgressEdgeCases:

    def test_very_small_target(self, client):
        """Target = 0.01, saved = 0.01 → 100%"""
        token = tok(client, "edge1")
        rid = client.post("/api/savings/", json={"name": "Tiny", "target_amount": 0.01}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 0.01}, headers=hd(token))
        assert r.json()["progress_percent"] == 100.0
        assert r.json()["is_completed"] is True

    def test_large_amounts(self, client):
        """Target = 999999999.99, saved = 500000000 → 50%"""
        token = tok(client, "edge2")
        rid = client.post("/api/savings/", json={"name": "Big", "target_amount": 999999999.99}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 500000000}, headers=hd(token))
        assert r.json()["progress_percent"] == 50.0

    def test_progress_rounded_to_2_decimals(self, client):
        """1/3 = 33.33%"""
        token = tok(client, "edge3")
        rid = client.post("/api/savings/", json={"name": "Third", "target_amount": 300}, headers=hd(token)).json()["id"]
        r = client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 100}, headers=hd(token))
        assert r.json()["progress_percent"] == 33.33

    def test_update_target_after_partial_progress(self, client):
        """Changing target recalculates progress correctly."""
        token = tok(client, "edge4")
        rid = client.post("/api/savings/", json={"name": "Goal", "target_amount": 10000}, headers=hd(token)).json()["id"]
        client.put(f"/api/savings/{rid}/progress/", json={"current_saved": 5000}, headers=hd(token))
        # Change target to 20000 → 5000/20000 = 25%
        r = client.put(f"/api/savings/{rid}/", json={"target_amount": 20000}, headers=hd(token))
        assert r.json()["progress_percent"] == 25.0
        assert r.json()["is_completed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
