from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from ..database import get_db
from .. import models, schemas, auth
from ..budget_alerts import calculate_utilization, month_bounds

router = APIRouter()


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}. Expected format YYYY-MM-DD",
        )


def _validate_filters(
    start_date: Optional[str],
    end_date: Optional[str],
    month: Optional[int],
    year: Optional[int],
) -> Tuple[Optional[date], Optional[date], Optional[int], Optional[int]]:
    if month is not None and not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")
    if year is not None and not 1 <= year <= 9999:
        raise HTTPException(status_code=400, detail="year must be between 1 and 9999")
    if month is not None and year is None:
        raise HTTPException(status_code=400, detail="year is required when month is provided")

    parsed_start = _parse_date(start_date, "start_date") if start_date else None
    parsed_end = _parse_date(end_date, "end_date") if end_date else None

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be on or before end_date",
        )
    if (start_date or end_date) and (month is not None or year is not None):
        raise HTTPException(
            status_code=400,
            detail="Use either date range filters or month/year filters, not both",
        )

    period_start: Optional[date] = None
    period_end: Optional[date] = None
    if month is not None and year is not None:
        period_start, period_end = month_bounds(year, month)
    elif year is not None and month is None:
        period_start = date(year, 1, 1)
        period_end = date(year, 12, 31)
    else:
        period_start = parsed_start
        period_end = parsed_end

    return period_start, period_end, month, year


def _year_month(d: date) -> Tuple[int, int]:
    return d.year, d.month


def _build_category_summary(expenses: List[models.Expense]) -> List[schemas.AnalyticsCategoryItem]:
    by_category: dict = {}
    for e in expenses:
        key = e.category.value
        entry = by_category.setdefault(key, {"total": 0.0, "count": 0})
        entry["total"] += float(e.amount)
        entry["count"] += 1

    total_expenses = sum(v["total"] for v in by_category.values())
    items = []
    for category, values in by_category.items():
        percent = round((values["total"] / total_expenses) * 100.0, 2) if total_expenses > 0 else 0.0
        items.append(schemas.AnalyticsCategoryItem(
            category=category,
            total=round(values["total"], 2),
            count=values["count"],
            percent_of_expenses=percent,
        ))
    items.sort(key=lambda x: (-x.total, x.category))
    return items


def _build_monthly_trends(
    incomes: List[models.Income],
    expenses: List[models.Expense],
    period_start: Optional[date],
    period_end: Optional[date],
    month: Optional[int],
    year: Optional[int],
) -> List[schemas.AnalyticsMonthlyTrend]:
    income_by_month: dict = {}
    expense_by_month: dict = {}

    for i in incomes:
        key = _year_month(i.date)
        income_by_month[key] = income_by_month.get(key, 0.0) + float(i.amount)
    for e in expenses:
        key = _year_month(e.date)
        expense_by_month[key] = expense_by_month.get(key, 0.0) + float(e.amount)

    if month is not None and year is not None:
        keys = [(year, month)]
    elif period_start and period_end:
        activity = sorted(set(income_by_month) | set(expense_by_month))
        keys = [k for k in activity if _in_period(k, period_start, period_end)]
    else:
        keys = sorted(set(income_by_month) | set(expense_by_month))

    trends = []
    for y, m in keys:
        inc = round(income_by_month.get((y, m), 0.0), 2)
        exp = round(expense_by_month.get((y, m), 0.0), 2)
        trends.append(schemas.AnalyticsMonthlyTrend(
            year=y,
            month=m,
            income=inc,
            expenses=exp,
            net=round(inc - exp, 2),
        ))
    return trends


def _in_period(key: Tuple[int, int], period_start: date, period_end: date) -> bool:
    y, m = key
    start, end = month_bounds(y, m)
    return start <= period_end and end >= period_start


def _savings_summary(db: Session, user_id: int) -> schemas.AnalyticsSavingsSummary:
    goals = db.query(models.SavingsGoal).filter(
        models.SavingsGoal.user_id == user_id,
    ).all()
    total_target = sum(float(g.target_amount) for g in goals)
    total_saved = sum(float(g.current_saved) for g in goals)
    completed = sum(1 for g in goals if g.is_completed)
    overall = round((total_saved / total_target) * 100.0, 2) if total_target > 0 else 0.0
    return schemas.AnalyticsSavingsSummary(
        total_goals=len(goals),
        completed_goals=completed,
        total_target=round(total_target, 2),
        total_saved=round(total_saved, 2),
        overall_progress_percent=overall,
    )


def _budget_summary(
    db: Session,
    user_id: int,
    month: int,
    year: int,
) -> Optional[schemas.AnalyticsBudgetSummary]:
    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year,
    ).first()
    if not budget:
        return None

    start, end = month_bounds(year, month)
    month_expenses = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.date >= start,
        models.Expense.date <= end,
    ).all()
    spent_by_category: dict = {}
    for e in month_expenses:
        key = e.category.value
        spent_by_category[key] = spent_by_category.get(key, 0.0) + float(e.amount)

    allocations = []
    for alloc in budget.allocations:
        cat = alloc.category.value
        budgeted = float(alloc.amount)
        spent = spent_by_category.get(cat, 0.0)
        allocations.append(schemas.AnalyticsBudgetAllocation(
            category=cat,
            budgeted=budgeted,
            spent=round(spent, 2),
            utilization_percent=calculate_utilization(spent, budgeted),
        ))
    allocations.sort(key=lambda x: (-x.utilization_percent, x.category))

    total_budget = float(budget.total_amount)
    total_spent = sum(spent_by_category.values())
    return schemas.AnalyticsBudgetSummary(
        month=month,
        year=year,
        total_budget=total_budget,
        total_spent=round(total_spent, 2),
        remaining=round(total_budget - total_spent, 2),
        utilization_percent=calculate_utilization(total_spent, total_budget),
        allocations=allocations,
    )


@router.get("/", response_model=schemas.AnalyticsResponse)
def get_analytics(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
):
    period_start, period_end, month, year = _validate_filters(
        start_date, end_date, month, year,
    )

    income_query = db.query(models.Income).filter(
        models.Income.user_id == current_user.id,
    )
    expense_query = db.query(models.Expense).filter(
        models.Expense.user_id == current_user.id,
    )
    if period_start:
        income_query = income_query.filter(models.Income.date >= period_start)
        expense_query = expense_query.filter(models.Expense.date >= period_start)
    if period_end:
        income_query = income_query.filter(models.Income.date <= period_end)
        expense_query = expense_query.filter(models.Expense.date <= period_end)

    incomes = income_query.all()
    expenses = expense_query.all()

    total_income = sum(float(i.amount) for i in incomes)
    total_expenses = sum(float(e.amount) for e in expenses)
    net_savings = total_income - total_expenses
    savings_rate = round((net_savings / total_income) * 100.0, 2) if total_income > 0 else 0.0

    budget_summary = None
    if month is not None and year is not None:
        budget_summary = _budget_summary(db, current_user.id, month, year)

    return schemas.AnalyticsResponse(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_savings=round(net_savings, 2),
        savings_rate_percent=savings_rate,
        income_count=len(incomes),
        expense_count=len(expenses),
        has_data=bool(incomes or expenses),
        category_summary=_build_category_summary(expenses),
        monthly_trends=_build_monthly_trends(
            incomes, expenses, period_start, period_end, month, year,
        ),
        savings_summary=_savings_summary(db, current_user.id),
        budget_summary=budget_summary,
        filters=schemas.AnalyticsFilters(
            start_date=start_date,
            end_date=end_date,
            month=month,
            year=year,
        ),
    )
