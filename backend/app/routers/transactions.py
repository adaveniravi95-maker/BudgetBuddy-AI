from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()


@router.get("/summary/", response_model=schemas.TransactionSummary)
def get_summary(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    incomes = db.query(models.Income).filter(models.Income.user_id == current_user.id).all()
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()

    total_income = sum(float(i.amount) for i in incomes)
    total_expenses = sum(float(e.amount) for e in expenses)

    return schemas.TransactionSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=total_income - total_expenses,
        income_count=len(incomes),
        expense_count=len(expenses),
    )


@router.get("/", response_model=schemas.TransactionListResponse)
def list_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    items = []

    if type != "expense":
        incomes = db.query(models.Income).filter(models.Income.user_id == current_user.id)
        if start_date:
            incomes = incomes.filter(models.Income.date >= start_date)
        if end_date:
            incomes = incomes.filter(models.Income.date <= end_date)
        for i in incomes.all():
            items.append(schemas.TransactionItem(
                id=i.id, type="income", amount=float(i.amount),
                category=i.source.value, description=i.description or "",
                date=i.date, created_at=i.created_at,
            ))

    if type != "income":
        expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)
        if start_date:
            expenses = expenses.filter(models.Expense.date >= start_date)
        if end_date:
            expenses = expenses.filter(models.Expense.date <= end_date)
        for e in expenses.all():
            items.append(schemas.TransactionItem(
                id=e.id, type="expense", amount=float(e.amount),
                category=e.category.value, description=e.description or "",
                date=e.date, created_at=e.created_at,
            ))

    items.sort(key=lambda x: (x.date, x.created_at), reverse=True)
    return schemas.TransactionListResponse(transactions=items, total=len(items))
