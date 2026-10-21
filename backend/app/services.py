from datetime import date
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import Expense, Income
from .schemas import CATEGORIES

def dashboard(db: Session, user_id: int, month: str):
    start = date.fromisoformat(month + "-01")
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)
    income_total = db.scalar(select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == user_id, Income.income_date >= start, Income.income_date < end)) or Decimal("0")
    expense_total = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == user_id, Expense.expense_date >= start, Expense.expense_date < end)) or Decimal("0")
    rows = db.execute(select(Expense.category, func.sum(Expense.amount)).where(Expense.user_id == user_id, Expense.expense_date >= start, Expense.expense_date < end).group_by(Expense.category)).all()
    category_expenses = {category: Decimal("0") for category in CATEGORIES}
    for category, total in rows:
        category_expenses[category] = total
    incomes = db.scalars(select(Income).where(Income.user_id == user_id, Income.income_date >= start, Income.income_date < end).order_by(Income.income_date.desc()).limit(10)).all()
    expenses = db.scalars(select(Expense).where(Expense.user_id == user_id, Expense.expense_date >= start, Expense.expense_date < end).order_by(Expense.expense_date.desc()).limit(10)).all()
    activity = ([{"type":"income","date":x.income_date.isoformat(),"amount":x.amount,"label":x.source} for x in incomes] + [{"type":"expense","date":x.expense_date.isoformat(),"amount":x.amount,"label":x.category} for x in expenses])
    activity.sort(key=lambda x: x["date"], reverse=True)
    return {"month": month, "total_income": income_total, "total_expenses": expense_total, "remaining_amount": income_total - expense_total, "category_expenses": category_expenses, "recent_activity": activity[:10]}
