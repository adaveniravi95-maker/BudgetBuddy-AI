from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from ..database import get_db
from .. import models, schemas, auth
from ..budget_alerts import check_budget_alerts

router = APIRouter()


@router.post("/", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    request: schemas.ExpenseCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expense = models.Expense(
        user_id=current_user.id,
        amount=request.amount,
        category=request.category,
        description=request.description,
        date=request.date,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    check_budget_alerts(db, current_user.id, request.date)
    return expense


@router.get("/", response_model=schemas.ExpenseListResponse)
def list_expenses(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    category: Optional[models.ExpenseCategory] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    query = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)

    if category:
        query = query.filter(models.Expense.category == category)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)

    expenses = query.order_by(desc(models.Expense.date), desc(models.Expense.created_at)).all()
    return schemas.ExpenseListResponse(expenses=expenses, total=len(expenses))


@router.get("/{expense_id}/", response_model=schemas.ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}/", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    request: schemas.ExpenseUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    check_budget_alerts(db, current_user.id, expense.date)
    return expense


@router.delete("/{expense_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id,
        models.Expense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return None
