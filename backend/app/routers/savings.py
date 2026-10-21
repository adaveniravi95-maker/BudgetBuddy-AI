from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()

MILESTONES = [25, 50, 75, 100]


def _check_savings_milestone(db: Session, user_id: int, goal: models.SavingsGoal):
    if goal.target_amount <= 0:
        return
    pct = (float(goal.current_saved) / float(goal.target_amount)) * 100
    for m in MILESTONES:
        if pct >= m:
            existing = db.query(models.Notification).filter(
                models.Notification.user_id == user_id,
                models.Notification.notification_type == models.NotificationType.savings_milestone,
                models.Notification.related_id == goal.id,
                models.Notification.message.contains(f"{m}%", autoescape=True),
            ).first()
            if not existing:
                label = "completed (100%)" if m == 100 else f"reached {m}%"
                db.add(models.Notification(
                    user_id=user_id,
                    notification_type=models.NotificationType.savings_milestone,
                    message=f"Savings goal '{goal.name}' {label}! INR {float(goal.current_saved):.2f} / INR {float(goal.target_amount):.2f}",
                    related_id=goal.id,
                ))
                db.commit()


def calc_progress(current_saved: float, target_amount: float) -> float:
    if target_amount <= 0:
        return 0.0
    pct = (current_saved / target_amount) * 100
    return round(min(pct, 100.0), 2)


def goal_to_response(goal: models.SavingsGoal) -> schemas.SavingsGoalResponse:
    return schemas.SavingsGoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        name=goal.name,
        target_amount=float(goal.target_amount),
        current_saved=float(goal.current_saved),
        progress_percent=calc_progress(float(goal.current_saved), float(goal.target_amount)),
        is_completed=goal.is_completed,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


@router.post("/", response_model=schemas.SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_savings_goal(
    data: schemas.SavingsGoalCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goal = models.SavingsGoal(
        user_id=current_user.id,
        name=data.name,
        target_amount=data.target_amount,
        current_saved=0,
        is_completed=False,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    _check_savings_milestone(db, current_user.id, goal)
    return goal_to_response(goal)


@router.get("/", response_model=schemas.SavingsGoalListResponse)
def list_savings_goals(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goals = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.user_id == current_user.id,
    ).order_by(models.SavingsGoal.created_at.desc()).all()
    return schemas.SavingsGoalListResponse(
        goals=[goal_to_response(g) for g in goals],
        total=len(goals),
    )


@router.get("/{goal_id}/", response_model=schemas.SavingsGoalResponse)
def get_savings_goal(
    goal_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.id == goal_id,
        models.SavingsGoal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    return goal_to_response(goal)


@router.put("/{goal_id}/", response_model=schemas.SavingsGoalResponse)
def update_savings_goal(
    goal_id: int,
    data: schemas.SavingsGoalUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.id == goal_id,
        models.SavingsGoal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")

    if goal.is_completed:
        raise HTTPException(status_code=400, detail="Cannot update a completed goal")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    if float(goal.current_saved) >= float(goal.target_amount):
        goal.is_completed = True

    db.commit()
    db.refresh(goal)
    _check_savings_milestone(db, current_user.id, goal)
    return goal_to_response(goal)


@router.put("/{goal_id}/progress/", response_model=schemas.SavingsGoalResponse)
def update_savings_progress(
    goal_id: int,
    data: schemas.SavingsGoalProgressUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.id == goal_id,
        models.SavingsGoal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")

    if goal.is_completed:
        raise HTTPException(status_code=400, detail="Goal is already completed")

    goal.current_saved = data.current_saved

    if float(goal.current_saved) >= float(goal.target_amount):
        goal.current_saved = goal.target_amount
        goal.is_completed = True

    db.commit()
    db.refresh(goal)
    _check_savings_milestone(db, current_user.id, goal)
    return goal_to_response(goal)


@router.delete("/{goal_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_savings_goal(
    goal_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.id == goal_id,
        models.SavingsGoal.user_id == current_user.id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    db.delete(goal)
    db.commit()
    return None
