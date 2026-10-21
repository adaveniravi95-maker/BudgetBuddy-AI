from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas, auth
from ..budget_alerts import evaluate_budget

router = APIRouter()


@router.post("/", response_model=schemas.BudgetResponse, status_code=201)
def create_budget(
    data: schemas.BudgetCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.month == data.month,
            models.Budget.year == data.year,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this month")

    budget = models.Budget(
        user_id=current_user.id,
        month=data.month,
        year=data.year,
        total_amount=data.total_amount,
    )
    db.add(budget)
    db.flush()

    for alloc in data.allocations:
        db.add(models.BudgetAllocation(budget_id=budget.id, category=alloc.category, amount=alloc.amount))

    db.commit()
    db.refresh(budget)
    evaluate_budget(db, current_user.id, budget.year, budget.month)
    return budget


@router.get("/", response_model=schemas.BudgetListResponse)
def list_budgets(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    year: Optional[int] = None,
):
    q = db.query(models.Budget).filter(models.Budget.user_id == current_user.id)
    if year:
        q = q.filter(models.Budget.year == year)
    budgets = q.order_by(models.Budget.year.desc(), models.Budget.month.desc()).all()
    return schemas.BudgetListResponse(budgets=budgets, total=len(budgets))


@router.get("/{budget_id}/", response_model=schemas.BudgetResponse)
def get_budget(
    budget_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id,
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.put("/{budget_id}/", response_model=schemas.BudgetResponse)
def update_budget(
    budget_id: int,
    data: schemas.BudgetUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id,
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if data.total_amount is not None:
        budget.total_amount = data.total_amount

    if data.allocations is not None:
        db.query(models.BudgetAllocation).filter(
            models.BudgetAllocation.budget_id == budget.id
        ).delete()
        for alloc in data.allocations:
            db.add(models.BudgetAllocation(budget_id=budget.id, category=alloc.category, amount=alloc.amount))

    db.commit()
    db.refresh(budget)
    evaluate_budget(db, current_user.id, budget.year, budget.month)
    return budget


@router.delete("/{budget_id}/", status_code=204)
def delete_budget(
    budget_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id,
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
