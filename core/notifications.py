from decimal import Decimal
from django.db.models import Sum
from .models import Notification, Budget, Expense, SavingsGoal


def create_notification(user, notification_type, title, message, related_context=None, prevent_duplicate=True):
    """
    Creates a user-specific notification with optional deduplication.
    If prevent_duplicate is True and related_context is specified,
    an existing notification with the same context will not be recreated.
    """
    if prevent_duplicate and related_context:
        existing = Notification.objects.filter(
            user=user,
            notification_type=notification_type,
            related_context=related_context
        ).first()
        if existing:
            return existing

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_context=related_context,
        is_read=False
    )


def check_and_trigger_budget_alert(user, category, expense_date):
    """
    Checks if spending in a category for the given month has reached or exceeded the allocated budget.
    If threshold is reached, triggers a user-specific budget_alert notification.
    """
    if not user or not category or not expense_date:
        return None

    # Look up budget allocated for this category in the expense's month
    budget = Budget.objects.filter(
        user=user,
        category=category,
        month__year=expense_date.year,
        month__month=expense_date.month
    ).first()

    if not budget or budget.amount <= Decimal('0.00'):
        return None

    # Calculate total expenses in this category for this month
    total_spent_agg = Expense.objects.filter(
        user=user,
        category=category,
        date__year=expense_date.year,
        date__month=expense_date.month
    ).aggregate(total=Sum('amount'))

    total_spent = total_spent_agg['total'] or Decimal('0.00')

    # Exceeded Limit condition (>= 100%)
    if total_spent >= budget.amount:
        related_context = f"budget:{budget.id}:{expense_date.year}-{expense_date.month:02d}"
        title = f"Budget Alert: {category} Exceeded"
        message = (
            f"You have spent ₹{total_spent:.2f} on {category} this month, "
            f"reaching or exceeding your budget limit of ₹{budget.amount:.2f}."
        )
        return create_notification(
            user=user,
            notification_type='budget_alert',
            title=title,
            message=message,
            related_context=related_context,
            prevent_duplicate=True
        )

    # Near Limit condition (>= 80% and < 100%)
    elif total_spent >= (budget.amount * Decimal('0.80')):
        utilization = (total_spent / budget.amount) * Decimal('100')
        related_context = f"budget:{budget.id}:{expense_date.year}-{expense_date.month:02d}:warning"
        title = f"Budget Warning: {category} Near Limit"
        message = (
            f"You have spent ₹{total_spent:.2f} on {category} this month, "
            f"reaching {utilization:.1f}% of your budget limit of ₹{budget.amount:.2f}."
        )
        return create_notification(
            user=user,
            notification_type='budget_alert',
            title=title,
            message=message,
            related_context=related_context,
            prevent_duplicate=True
        )

    return None


def check_and_trigger_goal_alert(goal):
    """
    Checks if a savings goal has reached a milestone (50%) or full completion (100%).
    Triggers a goal_milestone notification when condition is met.
    """
    if not goal or not goal.user or not goal.target_amount or goal.target_amount <= Decimal('0.00'):
        return None

    if goal.is_completed:
        related_context = f"goal:{goal.id}:completed"
        title = f"Savings Goal Achieved: {goal.name}! 🏆"
        message = (
            f"Congratulations! You have achieved your savings target of "
            f"₹{goal.target_amount:.2f} for '{goal.name}'."
        )
        return create_notification(
            user=goal.user,
            notification_type='goal_milestone',
            title=title,
            message=message,
            related_context=related_context,
            prevent_duplicate=True
        )

    elif goal.progress_percentage >= 50.0:
        related_context = f"goal:{goal.id}:50pct"
        title = f"Savings Milestone: {goal.name} (50%)"
        message = (
            f"Great job! You have reached {goal.progress_percentage:.1f}% "
            f"(₹{goal.current_amount:.2f} / ₹{goal.target_amount:.2f}) of your savings goal '{goal.name}'."
        )
        return create_notification(
            user=goal.user,
            notification_type='goal_milestone',
            title=title,
            message=message,
            related_context=related_context,
            prevent_duplicate=True
        )

    return None
