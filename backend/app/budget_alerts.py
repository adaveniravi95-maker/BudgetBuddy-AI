from calendar import monthrange
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from . import models

NEAR_LIMIT_THRESHOLD = 80.0
EXCEEDED_THRESHOLD = 100.0


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def get_month_spent(
    db: Session,
    user_id: int,
    year: int,
    month: int,
    category: Optional[models.ExpenseCategory] = None,
) -> float:
    start, end = month_bounds(year, month)
    query = db.query(models.Expense).filter(
        models.Expense.user_id == user_id,
        models.Expense.date >= start,
        models.Expense.date <= end,
    )
    if category is not None:
        query = query.filter(models.Expense.category == category)
    return sum(float(e.amount) for e in query.all())


def calculate_utilization(spent: float, budgeted: float) -> float:
    if budgeted <= 0:
        return 0.0
    return round((spent / budgeted) * 100.0, 2)


def alert_phase(utilization_percent: float) -> Optional[str]:
    if utilization_percent >= EXCEEDED_THRESHOLD:
        return "exceeded"
    if utilization_percent >= NEAR_LIMIT_THRESHOLD:
        return "near limit"
    return None


def _already_alerted(
    db: Session,
    user_id: int,
    budget_id: int,
    scope_label: str,
    phase: str,
) -> bool:
    existing = db.query(models.Notification).filter(
        models.Notification.user_id == user_id,
        models.Notification.notification_type == models.NotificationType.budget_limit,
        models.Notification.related_id == budget_id,
        models.Notification.message.contains(phase, autoescape=True),
        models.Notification.message.contains(scope_label, autoescape=True),
    ).first()
    return existing is not None


def _create_alert(
    db: Session,
    user_id: int,
    budget_id: int,
    message: str,
) -> models.Notification:
    notification = models.Notification(
        user_id=user_id,
        notification_type=models.NotificationType.budget_limit,
        message=message,
        related_id=budget_id,
    )
    db.add(notification)
    return notification


def check_budget_alerts(
    db: Session,
    user_id: int,
    expense_date: date,
) -> List[models.Notification]:
    """Evaluate category and total budget utilization for the expense date's month.

    Creates budget_limit notifications (near limit / exceeded) when thresholds
    are crossed, skipping duplicates for the same budget, scope and phase.
    """
    budget = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == expense_date.month,
        models.Budget.year == expense_date.year,
    ).first()
    if not budget:
        return []

    created: List[models.Notification] = []
    year, month = budget.year, budget.month
    period_label = f"{year}-{month:02d}"

    for alloc in budget.allocations:
        category_label = alloc.category.value
        spent = get_month_spent(db, user_id, year, month, alloc.category)
        budgeted = float(alloc.amount)
        utilization = calculate_utilization(spent, budgeted)
        phase = alert_phase(utilization)
        if phase is None:
            continue
        if _already_alerted(db, user_id, budget.id, category_label, phase):
            continue
        message = (
            f"Budget alert ({phase}): '{category_label}' spent INR {spent:.2f} "
            f"of INR {budgeted:.2f} ({utilization:.1f}%) for {period_label}"
        )
        created.append(_create_alert(db, user_id, budget.id, message))

    total_spent = get_month_spent(db, user_id, year, month)
    total_budgeted = float(budget.total_amount)
    total_utilization = calculate_utilization(total_spent, total_budgeted)
    total_phase = alert_phase(total_utilization)
    if total_phase is not None and not _already_alerted(db, user_id, budget.id, "total", total_phase):
        message = (
            f"Budget alert ({total_phase}): total spending INR {total_spent:.2f} "
            f"of INR {total_budgeted:.2f} ({total_utilization:.1f}%) for {period_label}"
        )
        created.append(_create_alert(db, user_id, budget.id, message))

    if created:
        db.commit()
        for notification in created:
            db.refresh(notification)
    return created


def evaluate_budget(
    db: Session,
    user_id: int,
    year: int,
    month: int,
) -> List[models.Notification]:
    """Run alert checks for a specific budget month (used on budget create/update)."""
    return check_budget_alerts(db, user_id, date(year, month, 1))
