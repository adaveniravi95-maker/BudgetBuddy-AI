from datetime import date
from decimal import Decimal
import io
import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Form,
)
from fastapi.responses import StreamingResponse

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import get_current_user
from .models import (
    User,
    Expense,
    Income,
    Budget,
    SavingsGoal,
    Notification,
    Report,
)

from .schemas import (
    RegisterIn,
    UserOut,
    LoginIn,
    TokenOut,
    ExpenseCreate,
    ExpenseOut,
    IncomeCreate,
    IncomeOut,
    BudgetCreate,
    BudgetOut,
    SavingsGoalCreate,
    SavingsGoalOut,
    DashboardOut,
    NotificationOut,
    ReportOut,
)

from .security import (
    hash_password,
    verify_password,
    create_access_token,
)

from .services import dashboard


# ============================================================
# MAIN API ROUTER
# ============================================================

router = APIRouter(
    prefix="/api"
)


# ============================================================
# AUTHENTICATION
# ============================================================

auth = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@auth.post(
    "/register",
    response_model=UserOut,
    status_code=201
)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db)
):
    email = data.email.lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    user = User(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role="student",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@auth.post(
    "/login",
    response_model=TokenOut
)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(
            User.email == username.lower()
        )
    )

    if not user or not verify_password(
        password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    return {
        "access_token": create_access_token(
            user.id,
            user.role
        ),
        "token_type": "bearer",
    }


@auth.get(
    "/me",
    response_model=UserOut
)
def me(
    user: User = Depends(get_current_user)
):
    return user


router.include_router(auth)


# ============================================================
# AUTOMATIC BUDGET ALERTS
# ============================================================

def create_budget_alerts(
    db: Session,
    user_id: int,
    month: str
):
    budgets = db.scalars(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.month == month
        )
    ).all()

    if not budgets:
        return

    try:
        start = date.fromisoformat(month + "-01")
    except ValueError:
        return

    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    for budget in budgets:
        total_spent = db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == user_id,
                Expense.category == budget.category,
                Expense.expense_date >= start,
                Expense.expense_date < end
            )
        ) or Decimal("0.00")

        allocated = Decimal(str(budget.allocated_amount))

        if allocated <= 0:
            continue

        percentage = (total_spent / allocated) * Decimal("100")

        if total_spent > allocated:
            title = "Budget Exceeded"
            level = "exceeded"
            message = (
                f"Your {budget.category} budget for {month} has been exceeded. "
                f"You have spent ₹{total_spent:.2f} against a budget of ₹{allocated:.2f}."
            )
        elif percentage >= Decimal("80"):
            title = "Budget Almost Exhausted"
            level = "warning"
            message = (
                f"Your {budget.category} budget for {month} is almost exhausted. "
                f"You have used {percentage:.0f}% of your ₹{allocated:.2f} budget."
            )
        else:
            continue

        # Only one notification is created for each alert level of a
        # category/month. Further expenses do not create duplicates.
        search_prefix = f"Your {budget.category} budget for {month}"
        duplicate = db.scalar(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.title == title,
                Notification.message.like(search_prefix + "%")
            )
        )

        if duplicate:
            continue

        db.add(
            Notification(
                user_id=user_id,
                title=title,
                message=message,
                is_read=False
            )
        )

    db.commit()


# ============================================================
# EXPENSES
# ============================================================

expenses = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@expenses.post(
    "",
    response_model=ExpenseOut,
    status_code=201
)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = Expense(
        user_id=user.id,
        **data.model_dump()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    create_budget_alerts(
        db,
        user.id,
        item.expense_date.strftime("%Y-%m")
    )

    return item


@expenses.get(
    "",
    response_model=list[ExpenseOut]
)
def list_expenses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Expense)
        .where(
            Expense.user_id == user.id
        )
        .order_by(
            Expense.expense_date.desc(),
            Expense.id.desc()
        )
    ).all()


@expenses.put(
    "/{expense_id}",
    response_model=ExpenseOut
)
def update_expense(
    expense_id: int,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    create_budget_alerts(
        db,
        user.id,
        item.expense_date.strftime("%Y-%m")
    )

    return item


@expenses.delete(
    "/{expense_id}",
    status_code=204
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db.delete(item)
    db.commit()


router.include_router(expenses)


# ============================================================
# INCOME
# ============================================================

incomes = APIRouter(
    prefix="/incomes",
    tags=["Income"]
)


@incomes.post(
    "",
    response_model=IncomeOut,
    status_code=201
)
def create_income(
    data: IncomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = Income(
        user_id=user.id,
        **data.model_dump()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@incomes.get(
    "",
    response_model=list[IncomeOut]
)
def list_incomes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Income)
        .where(
            Income.user_id == user.id
        )
        .order_by(
            Income.income_date.desc(),
            Income.id.desc()
        )
    ).all()


@incomes.put(
    "/{income_id}",
    response_model=IncomeOut
)
def update_income(
    income_id: int,
    data: IncomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Income).where(
            Income.id == income_id,
            Income.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Income not found"
        )

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item


@incomes.delete(
    "/{income_id}",
    status_code=204
)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Income).where(
            Income.id == income_id,
            Income.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Income not found"
        )

    db.delete(item)
    db.commit()


router.include_router(incomes)


# ============================================================
# BUDGETS
# ============================================================

budgets = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)


@budgets.post(
    "",
    response_model=list[BudgetOut],
    status_code=201
)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Check for duplicate categories inside the same request
    categories = [item.category.value for item in data.allocations]

    if len(categories) != len(set(categories)):
        raise HTTPException(
            status_code=409,
            detail="The same category cannot be added more than once."
        )

    # Check whether any of these categories already exist
    # for this user and month
    existing = db.scalars(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.month == data.month,
            Budget.category.in_(categories)
        )
    ).all()

    if existing:
        existing_categories = ", ".join(
            item.category for item in existing
        )

        raise HTTPException(
            status_code=409,
            detail=(
                f"Budget already exists for: {existing_categories} "
                f"in {data.month}. "
                "Choose another category or edit the existing budget."
            )
        )

    items = [
        Budget(
            user_id=user.id,
            month=data.month,
            category=item.category.value,
            allocated_amount=item.allocated_amount,
        )
        for item in data.allocations
    ]

    db.add_all(items)
    db.commit()

    for item in items:
        db.refresh(item)

    return items


@budgets.get(
    "",
    response_model=list[BudgetOut]
)
def list_budgets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Budget)
        .where(
            Budget.user_id == user.id
        )
        .order_by(
            Budget.month.desc(),
            Budget.category
        )
    ).all()


@budgets.get(
    "/{month}",
    response_model=list[BudgetOut]
)
def get_month_budget(
    month: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.month == month
        )
        .order_by(Budget.category)
    ).all()


@budgets.put(
    "/{budget_id}",
    response_model=BudgetOut
)
def update_budget(
    budget_id: int,
    data: BudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    if len(data.allocations) != 1:
        raise HTTPException(
            status_code=400,
            detail="Update requires exactly one allocation."
        )

    allocation = data.allocations[0]
    new_category = allocation.category.value

    # Check whether another budget already uses
    # the same month + category for this user
    duplicate = db.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.month == data.month,
            Budget.category == new_category,
            Budget.id != budget_id
        )
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A {new_category} budget already exists "
                f"for {data.month}."
            )
        )

    item.month = data.month
    item.category = new_category
    item.allocated_amount = allocation.allocated_amount

    db.commit()
    db.refresh(item)

    return item


@budgets.delete(
    "/{budget_id}",
    status_code=204
)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    db.delete(item)
    db.commit()


router.include_router(budgets)

# ============================================================
# SAVINGS GOALS
# ============================================================

savings_goals = APIRouter(
    prefix="/savings-goals",
    tags=["Savings Goals"]
)


def savings_goal_response(
    item: SavingsGoal
):
    """
    Convert a SavingsGoal database object into
    the API response including calculated progress.
    """

    target = Decimal(str(item.target_amount))
    saved = Decimal(str(item.amount_saved))

    if target > 0:
        progress = (
            saved / target * Decimal("100")
        ).quantize(Decimal("0.01"))
        progress = min(progress, Decimal("100.00"))
    else:
        progress = Decimal("0.00")

    is_completed = target > 0 and saved >= target

    return {
        "id": item.id,
        "user_id": item.user_id,
        "goal_name": item.goal_name,
        "target_amount": item.target_amount,
        "amount_saved": item.amount_saved,
"start_date": item.start_date,
"target_date": item.target_date,
"progress_percentage": progress,
        "is_completed": is_completed,
    }


def create_savings_goal_notifications(
    db: Session,
    goal: SavingsGoal
):
    """
    Create one notification for each savings milestone reached.

    Milestones:
    25%, 50%, 75%, and 100%.

    Duplicate prevention uses a stable goal ID + milestone marker,
    so changing the saved amount later does not create the same
    milestone notification again.
    """

    target = Decimal(str(goal.target_amount))
    saved = Decimal(str(goal.amount_saved))

    if target <= 0:
        return

    progress = saved / target * Decimal("100")

    milestones = [
        (Decimal("25"), "25%"),
        (Decimal("50"), "50%"),
        (Decimal("75"), "75%"),
        (Decimal("100"), "100%"),
    ]

    for milestone_value, milestone_label in milestones:
        if progress < milestone_value:
            continue

        marker = (
            f"[SavingsGoal:{goal.id}][Milestone:{milestone_label}]"
        )

        if milestone_value == Decimal("100"):
            title = "Savings Goal Completed"
            message = (
                f"{marker} You completed your savings goal "
                f"'{goal.goal_name}'. You saved ₹{saved:.2f} "
                f"toward your ₹{target:.2f} target."
            )
        else:
            title = "Savings Goal Milestone Reached"
            message = (
                f"{marker} You reached the {milestone_label} milestone "
                f"for '{goal.goal_name}'. You have saved "
                f"₹{saved:.2f} of ₹{target:.2f}."
            )

        duplicate = db.scalar(
            select(Notification).where(
                Notification.user_id == goal.user_id,
                Notification.title == title,
                Notification.message.contains(marker)
            )
        )

        if not duplicate:
            db.add(
                Notification(
                    user_id=goal.user_id,
                    title=title,
                    message=message,
                    is_read=False
                )
            )


@savings_goals.post(
    "",
    response_model=SavingsGoalOut,
    status_code=201
)
def create_savings_goal(
    data: SavingsGoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    values = data.model_dump()
    target = Decimal(str(values.get("target_amount", 0)))
    saved = Decimal(str(values.get("amount_saved", 0)))

    if target <= 0:
        raise HTTPException(
            status_code=400,
            detail="Target amount must be greater than 0."
        )

    if saved < 0:
        raise HTTPException(
            status_code=400,
            detail="Amount saved cannot be negative."
        )

    item = SavingsGoal(
        user_id=user.id,
        **values
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    create_savings_goal_notifications(db, item)
    db.commit()
    db.refresh(item)

    return savings_goal_response(item)


@savings_goals.get(
    "",
    response_model=list[SavingsGoalOut]
)
def list_savings_goals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    items = db.scalars(
        select(SavingsGoal)
        .where(
            SavingsGoal.user_id == user.id
        )
        .order_by(
            SavingsGoal.id.desc()
        )
    ).all()

    return [
        savings_goal_response(item)
        for item in items
    ]


@savings_goals.put(
    "/{goal_id}",
    response_model=SavingsGoalOut
)
def update_savings_goal(
    goal_id: int,
    data: SavingsGoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Savings goal not found"
        )

    values = data.model_dump()
    target = Decimal(str(values.get("target_amount", 0)))
    saved = Decimal(str(values.get("amount_saved", 0)))

    if target <= 0:
        raise HTTPException(
            status_code=400,
            detail="Target amount must be greater than 0."
        )

    if saved < 0:
        raise HTTPException(
            status_code=400,
            detail="Amount saved cannot be negative."
        )

    for key, value in values.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    create_savings_goal_notifications(db, item)
    db.commit()
    db.refresh(item)

    return savings_goal_response(item)


@savings_goals.post(
    "/{goal_id}/complete",
    response_model=SavingsGoalOut
)
def complete_savings_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Explicitly mark a savings goal as completed.

    The current database model does not have a separate completed
    column, so completion is persisted by setting amount_saved to
    target_amount. The response then reports is_completed=True.
    """

    item = db.scalar(
        select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Savings goal not found"
        )

    target = Decimal(str(item.target_amount))

    if target <= 0:
        raise HTTPException(
            status_code=400,
            detail="Target amount must be greater than 0."
        )

    item.amount_saved = target

    db.commit()
    db.refresh(item)

    create_savings_goal_notifications(db, item)
    db.commit()
    db.refresh(item)

    return savings_goal_response(item)


@savings_goals.delete(
    "/{goal_id}",
    status_code=204
)
def delete_savings_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = db.scalar(
        select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user.id
        )
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Savings goal not found"
        )

    db.delete(item)
    db.commit()


router.include_router(savings_goals)


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "/dashboard/{month}",
    response_model=DashboardOut,
    tags=["Dashboard"]
)
def get_dashboard(
    month: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if len(month) != 7:
        raise HTTPException(
            status_code=400,
            detail="Month must be YYYY-MM"
        )

    try:
        date.fromisoformat(
            month + "-01"
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Month must be YYYY-MM"
        )

    return dashboard(
        db,
        user.id,
        month
    )
    
# ============================================================
# ANALYTICS
# ============================================================

@router.get(
    "/analytics/{month}",
    tags=["Analytics"]
)
def get_analytics(
    month: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Validate YYYY-MM format
    if len(month) != 7:
        raise HTTPException(
            status_code=400,
            detail="Month must be YYYY-MM"
        )

    try:
        start = date.fromisoformat(month + "-01")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Month must be YYYY-MM"
        )

    # Calculate next month
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    # Total income
    total_income = db.scalar(
        select(
            func.coalesce(func.sum(Income.amount), 0)
        ).where(
            Income.user_id == user.id,
            Income.income_date >= start,
            Income.income_date < end
        )
    ) or Decimal("0.00")

    total_income = Decimal(str(total_income))

    # Total expenses
    total_expenses = db.scalar(
        select(
            func.coalesce(func.sum(Expense.amount), 0)
        ).where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
    ) or Decimal("0.00")

    total_expenses = Decimal(str(total_expenses))
        # Monthly transaction counts
    income_transactions = db.scalar(
        select(func.count(Income.id)).where(
            Income.user_id == user.id,
            Income.income_date >= start,
            Income.income_date < end
        )
    ) or 0

    expense_transactions = db.scalar(
        select(func.count(Expense.id)).where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
    ) or 0

    total_transactions = income_transactions + expense_transactions
    balance = total_income - total_expenses

    # Savings rate
    if total_income > 0:
        savings_rate = (
            balance / total_income * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        savings_rate = Decimal("0.00")

    # Category-wise expenses
    rows = db.execute(
        select(
            Expense.category,
            func.sum(Expense.amount)
        ).where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        ).group_by(
            Expense.category
        ).order_by(
            Expense.category
        )
    ).all()

    category_expenses = [
        {
            "category": category,
            "amount": Decimal(str(amount))
        }
        for category, amount in rows
    ]

    # Monthly trend for the selected month
    monthly_trends = [{
        "month": month,
        "income": total_income,
        "expenses": total_expenses,
        "balance": balance
    }]

    # Budget summary
    budgets = db.scalars(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.month == month
        ).order_by(Budget.category)
    ).all()

    budget_summary = []

    for budget in budgets:
        allocated = Decimal(str(budget.allocated_amount))

        spent = db.scalar(
            select(
                func.coalesce(func.sum(Expense.amount), 0)
            ).where(
                Expense.user_id == user.id,
                Expense.category == budget.category,
                Expense.expense_date >= start,
                Expense.expense_date < end
            )
        ) or Decimal("0.00")

        spent = Decimal(str(spent))

        if allocated > 0:
            utilization = (
                spent / allocated * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            utilization = Decimal("0.00")

        budget_summary.append({
            "category": budget.category,
            "allocated": allocated,
            "spent": spent,
            "utilization_percentage": utilization
        })

    # Savings goals summary
    goals = db.scalars(
        select(SavingsGoal).where(
            SavingsGoal.user_id == user.id
        ).order_by(SavingsGoal.id)
    ).all()

    total_target = sum(
        (Decimal(str(goal.target_amount)) for goal in goals),
        Decimal("0.00")
    )

    total_saved = sum(
        (Decimal(str(goal.amount_saved)) for goal in goals),
        Decimal("0.00")
    )

    if total_target > 0:
        progress_percentage = (
            total_saved / total_target * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        progress_percentage = Decimal("0.00")

    completed_goals = sum(
        1 for goal in goals
        if goal.amount_saved == goal.target_amount
    )

    return {
        "month": month,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "savings_rate": savings_rate,
        "income_transactions": income_transactions,
        "expense_transactions": expense_transactions,
        "total_transactions": total_transactions,
        "category_expenses": category_expenses,
        "monthly_trends": monthly_trends,
        "budget_summary": budget_summary,
        "savings_summary": {
        "total_target": total_target,
        "total_saved": total_saved,
        "progress_percentage": progress_percentage,
        "completed_goals": completed_goals,
        "total_goals": len(goals)
        }
    }


# ============================================================
# NOTIFICATIONS
# ============================================================

notifications = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@notifications.get(
    "",
    response_model=list[NotificationOut]
)
def list_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Notification)
        .where(
            Notification.user_id == user.id
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc()
        )
    ).all()


@notifications.get(
    "/unread-count"
)
def unread_notification_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    count = db.scalar(
        select(func.count(Notification.id))
        .where(
            Notification.user_id == user.id,
            Notification.is_read == False
        )
    ) or 0

    return {
        "unread_count": count
    }


@notifications.delete(
    "/{notification_id}",
    status_code=204
)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    db.delete(notification)
    db.commit()


@notifications.put(
    "/{notification_id}/read",
    response_model=NotificationOut
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id
        )
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


router.include_router(notifications)

# ============================================================
# REPORTS
# ============================================================

reports = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@reports.get(
    "",
    response_model=list[ReportOut]
)
def list_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.scalars(
        select(Report)
        .where(
            Report.user_id == user.id
        )
        .order_by(
            Report.generated_at.desc(),
            Report.id.desc()
        )
    ).all()


@reports.get(
    "/pdf/{period}",
    tags=["Reports"]
)
def download_monthly_report_pdf(
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if len(period) != 7:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    try:
        date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    report = db.scalar(
        select(Report)
        .where(
            Report.user_id == user.id,
            Report.report_type == "Monthly Financial Report",
            Report.period == period
        )
        .order_by(Report.id.desc())
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Monthly report not found. Generate the report first."
        )

    try:
        summary = json.loads(report.summary or "{}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Stored report summary is invalid"
        )

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak
    )

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"BudgetBuddy Monthly Financial Report - {period}",
        author="BudgetBuddy"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BudgetBuddyTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=5 * mm
    )

    subtitle_style = ParagraphStyle(
        "BudgetBuddySubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
        spaceAfter=7 * mm
    )

    section_style = ParagraphStyle(
        "BudgetBuddySection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#3f3f46"),
        spaceBefore=5 * mm,
        spaceAfter=3 * mm
    )

    normal_style = ParagraphStyle(
        "BudgetBuddyNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12
    )

    small_style = ParagraphStyle(
        "BudgetBuddySmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#666666")
    )

    table_header = colors.HexColor("#6c5ce7")
    table_header_text = colors.white
    table_border = colors.HexColor("#dddddd")
    table_alt = colors.HexColor("#f7f7fb")
    summary_bg = colors.HexColor("#f5f3ff")

    def money(value):
        try:
            return f"₹{float(value):,.2f}"
        except (TypeError, ValueError):
            return "₹0.00"

    def percent(value):
        try:
            return f"{float(value):.2f}%"
        except (TypeError, ValueError):
            return "0.00%"

    def cell(value, style=normal_style):
        return Paragraph(str(value), style)

    def styled_table(data, widths, right_align_columns=None):
        table = Table(
            data,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT"
        )

        commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                table_header
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                table_header_text
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8.5
            ),
            (
                "LEADING",
                (0, 0),
                (-1, -1),
                11
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                table_border
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ]

        for row_index in range(1, len(data)):
            if row_index % 2 == 0:
                commands.append(
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (-1, row_index),
                        table_alt
                    )
                )

        if right_align_columns:
            for column in right_align_columns:
                commands.append(
                    (
                        "ALIGN",
                        (column, 1),
                        (column, -1),
                        "RIGHT"
                    )
                )

        table.setStyle(TableStyle(commands))
        return table

    story = []

    story.append(
        Paragraph(
            "BudgetBuddy",
            title_style
        )
    )
    story.append(
        Paragraph(
            "Monthly Financial Report",
            ParagraphStyle(
                "ReportHeading",
                parent=subtitle_style,
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=colors.HexColor("#333333"),
                spaceAfter=2 * mm
            )
        )
    )
    story.append(
        Paragraph(
            f"Report Period: {period}",
            subtitle_style
        )
    )

    financial = summary.get("financial_summary", {})

    story.append(
        Paragraph(
            "Financial Summary",
            section_style
        )
    )

    financial_data = [
        [
            cell("Metric", ParagraphStyle(
                "HeaderCell",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Value", ParagraphStyle(
                "HeaderCell2",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            ))
        ],
        [
            cell("Total Income"),
            cell(money(financial.get("total_income")))
        ],
        [
            cell("Total Expenses"),
            cell(money(financial.get("total_expenses")))
        ],
        [
            cell("Remaining Balance"),
            cell(money(financial.get("balance")))
        ],
        [
            cell("Savings Rate"),
            cell(percent(financial.get("savings_rate")))
        ]
    ]

    financial_table = styled_table(
        financial_data,
        [95 * mm, 80 * mm],
        [1]
    )
    financial_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    summary_bg
                )
            ]
        )
    )
    story.append(financial_table)

    transaction = summary.get("transaction_summary", {})

    story.append(
        Paragraph(
            "Transaction Summary",
            section_style
        )
    )

    transaction_data = [
        [
            cell("Metric", ParagraphStyle(
                "TransactionHeader",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Count", ParagraphStyle(
                "TransactionHeader2",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            ))
        ],
        [
            cell("Income Transactions"),
            cell(transaction.get("income_transactions", 0))
        ],
        [
            cell("Expense Transactions"),
            cell(transaction.get("expense_transactions", 0))
        ],
        [
            cell("Total Transactions"),
            cell(transaction.get("total_transactions", 0))
        ]
    ]

    story.append(
        styled_table(
            transaction_data,
            [95 * mm, 80 * mm],
            [1]
        )
    )

    categories = summary.get("category_expenses", {})

    story.append(
        Paragraph(
            "Category-wise Expenses",
            section_style
        )
    )

    category_data = [
        [
            cell("Category", ParagraphStyle(
                "CategoryHeader",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Amount", ParagraphStyle(
                "CategoryHeader2",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            ))
        ]
    ]

    if categories:
        for category, amount in categories.items():
            category_data.append(
                [
                    cell(category),
                    cell(money(amount))
                ]
            )
    else:
        category_data.append(
            [
                cell("No expenses recorded"),
                cell("₹0.00")
            ]
        )

    story.append(
        styled_table(
            category_data,
            [95 * mm, 80 * mm],
            [1]
        )
    )

    budget = summary.get("budget_summary", {})

    story.append(
        Paragraph(
            "Budget Summary",
            section_style
        )
    )

    budget_totals = [
        [
            cell("Total Allocated"),
            cell(money(budget.get("total_allocated")))
        ],
        [
            cell("Total Spent"),
            cell(money(budget.get("total_spent")))
        ]
    ]

    budget_total_table = Table(
        budget_totals,
        colWidths=[95 * mm, 80 * mm]
    )
    budget_total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), summary_bg),
                ("GRID", (0, 0), (-1, -1), 0.5, table_border),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]
        )
    )
    story.append(budget_total_table)
    story.append(Spacer(1, 3 * mm))

    budget_data = [
        [
            cell("Category", ParagraphStyle(
                "BudgetHeader",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Budget", ParagraphStyle(
                "BudgetHeader2",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Spent", ParagraphStyle(
                "BudgetHeader3",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            )),
            cell("Utilization", ParagraphStyle(
                "BudgetHeader4",
                parent=normal_style,
                textColor=colors.white,
                fontName="Helvetica-Bold"
            ))
        ]
    ]

    budget_categories = budget.get("categories", [])

    if budget_categories:
        for item in budget_categories:
            budget_data.append(
                [
                    cell(item.get("category", "")),
                    cell(money(item.get("allocated"))),
                    cell(money(item.get("spent"))),
                    cell(percent(item.get("utilization_percentage")))
                ]
            )
    else:
        budget_data.append(
            [
                cell("No budgets recorded"),
                cell("₹0.00"),
                cell("₹0.00"),
                cell("0.00%")
            ]
        )

    story.append(
        styled_table(
            budget_data,
            [50 * mm, 41 * mm, 41 * mm, 43 * mm],
            [1, 2, 3]
        )
    )

    savings = summary.get("savings_summary", {})

    story.append(
        Paragraph(
            "Savings Summary",
            section_style
        )
    )

    savings_totals = [
        [
            cell("Total Target"),
            cell(money(savings.get("total_target")))
        ],
        [
            cell("Total Saved"),
            cell(money(savings.get("total_saved")))
        ],
        [
            cell("Overall Progress"),
            cell(percent(savings.get("progress_percentage")))
        ],
        [
            cell("Completed Goals"),
            cell(
                f"{savings.get('completed_goals', 0)} / "
                f"{savings.get('total_goals', 0)}"
            )
        ]
    ]

    savings_total_table = Table(
        savings_totals,
        colWidths=[95 * mm, 80 * mm]
    )
    savings_total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), summary_bg),
                ("GRID", (0, 0), (-1, -1), 0.5, table_border),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]
        )
    )
    story.append(savings_total_table)

    goals = savings.get("goals", [])

    if goals:
        story.append(Spacer(1, 3 * mm))
        story.append(
            Paragraph(
                "Savings Goals",
                ParagraphStyle(
                    "GoalHeading",
                    parent=normal_style,
                    fontName="Helvetica-Bold",
                    fontSize=10
                )
            )
        )

        goal_data = [
            [
                cell("Goal", ParagraphStyle(
                    "GoalHeader",
                    parent=normal_style,
                    textColor=colors.white,
                    fontName="Helvetica-Bold"
                )),
                cell("Saved", ParagraphStyle(
                    "GoalHeader2",
                    parent=normal_style,
                    textColor=colors.white,
                    fontName="Helvetica-Bold"
                )),
                cell("Target", ParagraphStyle(
                    "GoalHeader3",
                    parent=normal_style,
                    textColor=colors.white,
                    fontName="Helvetica-Bold"
                )),
                cell("Progress", ParagraphStyle(
                    "GoalHeader4",
                    parent=normal_style,
                    textColor=colors.white,
                    fontName="Helvetica-Bold"
                ))
            ]
        ]

        for goal in goals:
            goal_data.append(
                [
                    cell(goal.get("goal_name", "")),
                    cell(money(goal.get("amount_saved"))),
                    cell(money(goal.get("target_amount"))),
                    cell(percent(goal.get("progress_percentage")))
                ]
            )

        story.append(
            styled_table(
                goal_data,
                [50 * mm, 41 * mm, 41 * mm, 43 * mm],
                [1, 2, 3]
            )
        )

    story.append(Spacer(1, 7 * mm))
    story.append(
        Paragraph(
            "Generated by BudgetBuddy",
            small_style
        )
    )

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawCentredString(
            A4[0] / 2,
            8 * mm,
            f"BudgetBuddy | Page {doc.page}"
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number
    )

    buffer.seek(0)

    filename = f"BudgetBuddy_Report_{period}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@reports.get(
    "/excel/{period}",
    tags=["Reports"]
)
def download_monthly_report_excel(
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if len(period) != 7:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    try:
        date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    report = db.scalar(
        select(Report)
        .where(
            Report.user_id == user.id,
            Report.report_type == "Monthly Financial Report",
            Report.period == period
        )
        .order_by(Report.id.desc())
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Monthly report not found. Generate the report first."
        )

    try:
        summary = json.loads(report.summary or "{}")
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Stored report summary is invalid"
        )

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel export requires openpyxl. Install it with pip install openpyxl."
        )

    workbook = Workbook()

    purple = "6C5CE7"
    light_purple = "F5F3FF"
    light_gray = "F4F4F5"
    border_color = "D9D9E2"
    dark_text = "30303A"
    white = "FFFFFF"
    green = "EAF7EE"
    red = "FDECEC"

    thin_side = Side(
        style="thin",
        color=border_color
    )

    table_border = Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side
    )

    title_font = Font(
        name="Calibri",
        size=18,
        bold=True,
        color=white
    )

    section_font = Font(
        name="Calibri",
        size=12,
        bold=True,
        color=dark_text
    )

    header_font = Font(
        name="Calibri",
        size=10,
        bold=True,
        color=white
    )

    normal_font = Font(
        name="Calibri",
        size=10,
        color=dark_text
    )

    bold_font = Font(
        name="Calibri",
        size=10,
        bold=True,
        color=dark_text
    )

    def money_value(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def percentage_value(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def setup_sheet(sheet, title, subtitle):
        sheet.sheet_view.showGridLines = False
        sheet.freeze_panes = "A5"

        sheet.merge_cells("A1:D1")
        sheet["A1"] = title
        sheet["A1"].font = title_font
        sheet["A1"].fill = PatternFill(
            "solid",
            fgColor=purple
        )
        sheet["A1"].alignment = Alignment(
            horizontal="left",
            vertical="center"
        )
        sheet.row_dimensions[1].height = 30

        sheet.merge_cells("A2:D2")
        sheet["A2"] = subtitle
        sheet["A2"].font = Font(
            name="Calibri",
            size=10,
            italic=True,
            color="666666"
        )
        sheet["A2"].alignment = Alignment(
            horizontal="left"
        )

        sheet["A3"] = "Report Period"
        sheet["B3"] = period
        sheet["A3"].font = bold_font
        sheet["B3"].font = normal_font

        for cell in ("A3", "B3"):
            sheet[cell].fill = PatternFill(
                "solid",
                fgColor=light_purple
            )

    def style_header_row(sheet, row, start_col, end_col):
        for column in range(start_col, end_col + 1):
            cell_obj = sheet.cell(
                row=row,
                column=column
            )
            cell_obj.font = header_font
            cell_obj.fill = PatternFill(
                "solid",
                fgColor=purple
            )
            cell_obj.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )
            cell_obj.border = table_border

    def style_data_rows(sheet, start_row, end_row, start_col, end_col):
        for row in range(start_row, end_row + 1):
            fill = (
                light_purple
                if row % 2 == 0
                else white
            )

            for column in range(start_col, end_col + 1):
                cell_obj = sheet.cell(
                    row=row,
                    column=column
                )
                cell_obj.font = normal_font
                cell_obj.fill = PatternFill(
                    "solid",
                    fgColor=fill
                )
                cell_obj.border = table_border
                cell_obj.alignment = Alignment(
                    vertical="center"
                )

    # =========================================================
    # 1. Financial Summary
    # =========================================================

    financial_sheet = workbook.active
    financial_sheet.title = "Financial Summary"

    setup_sheet(
        financial_sheet,
        "BudgetBuddy Monthly Financial Report",
        "Generated from your actual transactions"
    )

    financial_sheet.append([])
    financial_sheet.append([
        "Metric",
        "Value"
    ])

    financial = summary.get(
        "financial_summary",
        {}
    )

    financial_rows = [
        [
            "Total Income",
            money_value(
                financial.get("total_income")
            )
        ],
        [
            "Total Expenses",
            money_value(
                financial.get("total_expenses")
            )
        ],
        [
            "Remaining Balance",
            money_value(
                financial.get("balance")
            )
        ],
        [
            "Savings Rate",
            percentage_value(
                financial.get("savings_rate")
            )
        ]
    ]

    for row in financial_rows:
        financial_sheet.append(row)

    style_header_row(
        financial_sheet,
        5,
        1,
        2
    )

    style_data_rows(
        financial_sheet,
        6,
        9,
        1,
        2
    )

    for row in range(6, 9):
        financial_sheet.cell(
            row=row,
            column=2
        ).number_format = '₹#,##0.00'

    financial_sheet["B9"].number_format = '0.00%'

    financial_sheet.column_dimensions["A"].width = 28
    financial_sheet.column_dimensions["B"].width = 20

    # =========================================================
    # 2. Transactions
    # =========================================================

    transaction_sheet = workbook.create_sheet(
        "Transactions"
    )

    setup_sheet(
        transaction_sheet,
        "Transaction Summary",
        "Monthly transaction activity"
    )

    transaction_sheet.append([])
    transaction_sheet.append([
        "Metric",
        "Count"
    ])

    transaction = summary.get(
        "transaction_summary",
        {}
    )

    transaction_rows = [
        [
            "Income Transactions",
            int(
                transaction.get(
                    "income_transactions",
                    0
                )
            )
        ],
        [
            "Expense Transactions",
            int(
                transaction.get(
                    "expense_transactions",
                    0
                )
            )
        ],
        [
            "Total Transactions",
            int(
                transaction.get(
                    "total_transactions",
                    0
                )
            )
        ]
    ]

    for row in transaction_rows:
        transaction_sheet.append(row)

    style_header_row(
        transaction_sheet,
        5,
        1,
        2
    )

    style_data_rows(
        transaction_sheet,
        6,
        8,
        1,
        2
    )

    transaction_sheet.column_dimensions["A"].width = 28
    transaction_sheet.column_dimensions["B"].width = 16

    # =========================================================
    # 3. Category Expenses
    # =========================================================

    category_sheet = workbook.create_sheet(
        "Category Expenses"
    )

    setup_sheet(
        category_sheet,
        "Category-wise Expenses",
        "Expense distribution by category"
    )

    category_sheet.append([])
    category_sheet.append([
        "Category",
        "Amount"
    ])

    categories = summary.get(
        "category_expenses",
        {}
    )

    if categories:
        for category, amount in categories.items():
            category_sheet.append(
                [
                    category,
                    money_value(amount)
                ]
            )
    else:
        category_sheet.append(
            [
                "No expenses",
                0
            ]
        )

    category_end = category_sheet.max_row

    style_header_row(
        category_sheet,
        5,
        1,
        2
    )

    style_data_rows(
        category_sheet,
        6,
        category_end,
        1,
        2
    )

    for row in range(6, category_end + 1):
        category_sheet.cell(
            row=row,
            column=2
        ).number_format = '₹#,##0.00'

    category_sheet.column_dimensions["A"].width = 28
    category_sheet.column_dimensions["B"].width = 20

    # =========================================================
    # 4. Budget Summary
    # =========================================================

    budget_sheet = workbook.create_sheet(
        "Budget Summary"
    )

    setup_sheet(
        budget_sheet,
        "Budget Summary",
        "Budget allocation and monthly utilization"
    )

    budget = summary.get(
        "budget_summary",
        {}
    )

    budget_sheet["A4"] = "Total Allocated"
    budget_sheet["B4"] = money_value(
        budget.get("total_allocated")
    )
    budget_sheet["C4"] = "Total Spent"
    budget_sheet["D4"] = money_value(
        budget.get("total_spent")
    )

    for cell_ref in ("A4", "C4"):
        budget_sheet[cell_ref].font = bold_font
        budget_sheet[cell_ref].fill = PatternFill(
            "solid",
            fgColor=light_purple
        )

    for cell_ref in ("B4", "D4"):
        budget_sheet[cell_ref].font = bold_font
        budget_sheet[cell_ref].fill = PatternFill(
            "solid",
            fgColor=light_purple
        )
        budget_sheet[cell_ref].number_format = '₹#,##0.00'

    budget_sheet.append([])
    budget_sheet.append([
        "Category",
        "Budget",
        "Spent",
        "Utilization"
    ])

    budget_categories = budget.get(
        "categories",
        []
    )

    if budget_categories:
        for item in budget_categories:
            budget_sheet.append(
                [
                    item.get("category", ""),
                    money_value(
                        item.get("allocated")
                    ),
                    money_value(
                        item.get("spent")
                    ),
                    percentage_value(
                        item.get(
                            "utilization_percentage"
                        )
                    )
                ]
            )
    else:
        budget_sheet.append(
            [
                "No budgets",
                0,
                0,
                0
            ]
        )

    budget_end = budget_sheet.max_row

    style_header_row(
        budget_sheet,
        6,
        1,
        4
    )

    style_data_rows(
        budget_sheet,
        7,
        budget_end,
        1,
        4
    )

    for row in range(7, budget_end + 1):
        budget_sheet.cell(
            row=row,
            column=2
        ).number_format = '₹#,##0.00'

        budget_sheet.cell(
            row=row,
            column=3
        ).number_format = '₹#,##0.00'

        budget_sheet.cell(
            row=row,
            column=4
        ).number_format = '0.00%'

        utilization = percentage_value(
            budget_sheet.cell(
                row=row,
                column=4
            ).value
        )

        if utilization >= 100:
            budget_sheet.cell(
                row=row,
                column=4
            ).fill = PatternFill(
                "solid",
                fgColor=red
            )
        elif utilization >= 80:
            budget_sheet.cell(
                row=row,
                column=4
            ).fill = PatternFill(
                "solid",
                fgColor="FFF4D6"
            )
        else:
            budget_sheet.cell(
                row=row,
                column=4
            ).fill = PatternFill(
                "solid",
                fgColor=green
            )

    budget_sheet.column_dimensions["A"].width = 24
    budget_sheet.column_dimensions["B"].width = 18
    budget_sheet.column_dimensions["C"].width = 18
    budget_sheet.column_dimensions["D"].width = 18

    # =========================================================
    # 5. Savings Summary
    # =========================================================

    savings_sheet = workbook.create_sheet(
        "Savings Summary"
    )

    setup_sheet(
        savings_sheet,
        "Savings Summary",
        "Savings targets and goal progress"
    )

    savings = summary.get(
        "savings_summary",
        {}
    )

    savings_sheet.append([])
    savings_sheet.append([
        "Metric",
        "Value"
    ])

    savings_rows = [
        [
            "Total Target",
            money_value(
                savings.get("total_target")
            )
        ],
        [
            "Total Saved",
            money_value(
                savings.get("total_saved")
            )
        ],
        [
            "Overall Progress",
            percentage_value(
                savings.get("progress_percentage")
            )
        ],
        [
            "Completed Goals",
            f"{savings.get('completed_goals', 0)} / "
            f"{savings.get('total_goals', 0)}"
        ]
    ]

    for row in savings_rows:
        savings_sheet.append(row)

    style_header_row(
        savings_sheet,
        5,
        1,
        2
    )

    style_data_rows(
        savings_sheet,
        6,
        9,
        1,
        2
    )

    savings_sheet["B6"].number_format = '₹#,##0.00'
    savings_sheet["B7"].number_format = '₹#,##0.00'
    savings_sheet["B8"].number_format = '0.00%'

    savings_sheet.column_dimensions["A"].width = 28
    savings_sheet.column_dimensions["B"].width = 22

    # =========================================================
    # 6. Savings Goals
    # =========================================================

    goals_sheet = workbook.create_sheet(
        "Savings Goals"
    )

    setup_sheet(
        goals_sheet,
        "Savings Goals",
        "Individual savings goal progress"
    )

    goals_sheet.append([])
    goals_sheet.append([
        "Goal",
        "Saved",
        "Target",
        "Progress",
        "Target Date",
        "Status"
    ])

    goals = savings.get(
        "goals",
        []
    )

    if goals:
        for goal in goals:
            goals_sheet.append(
                [
                    goal.get("goal_name", ""),
                    money_value(
                        goal.get("amount_saved")
                    ),
                    money_value(
                        goal.get("target_amount")
                    ),
                    percentage_value(
                        goal.get(
                            "progress_percentage"
                        )
                    ),
                    goal.get("target_date") or "",
                    "Completed"
                    if goal.get("completed")
                    else "In Progress"
                ]
            )
    else:
        goals_sheet.append(
            [
                "No savings goals",
                0,
                0,
                0,
                "",
                "No Data"
            ]
        )

    goals_end = goals_sheet.max_row

    style_header_row(
        goals_sheet,
        5,
        1,
        6
    )

    style_data_rows(
        goals_sheet,
        6,
        goals_end,
        1,
        6
    )

    for row in range(6, goals_end + 1):
        goals_sheet.cell(
            row=row,
            column=2
        ).number_format = '₹#,##0.00'

        goals_sheet.cell(
            row=row,
            column=3
        ).number_format = '₹#,##0.00'

        goals_sheet.cell(
            row=row,
            column=4
        ).number_format = '0.00%'

        if goals_sheet.cell(
            row=row,
            column=6
        ).value == "Completed":
            goals_sheet.cell(
                row=row,
                column=6
            ).fill = PatternFill(
                "solid",
                fgColor=green
            )

    goals_sheet.column_dimensions["A"].width = 24
    goals_sheet.column_dimensions["B"].width = 16
    goals_sheet.column_dimensions["C"].width = 16
    goals_sheet.column_dimensions["D"].width = 16
    goals_sheet.column_dimensions["E"].width = 16
    goals_sheet.column_dimensions["F"].width = 18

    # Apply consistent row heights and alignment
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell_obj in row:
                cell_obj.alignment = Alignment(
                    vertical="center",
                    wrap_text=True,
                    horizontal=(
                        "right"
                        if isinstance(
                            cell_obj.value,
                            (int, float)
                        )
                        else "left"
                    )
                )

        sheet.row_dimensions[5].height = 24

        # Print settings for a clean exported workbook
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToWidth = 1
        sheet.page_setup.fitToHeight = 0
        sheet.page_setup.orientation = "portrait"
        sheet.page_margins.left = 0.25
        sheet.page_margins.right = 0.25
        sheet.page_margins.top = 0.5
        sheet.page_margins.bottom = 0.5
        sheet.oddFooter.center.text = (
            "BudgetBuddy | Monthly Financial Report"
        )

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    filename = f"BudgetBuddy_Report_{period}.xlsx"

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )




def _build_monthly_summary(
    period: str,
    db: Session,
    user: User
):
    """Build a fresh monthly report summary directly from transactions."""
    if len(period) != 7:
        raise HTTPException(status_code=400, detail="Period must be in YYYY-MM format")

    try:
        start = date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(status_code=400, detail="Period must be in YYYY-MM format")

    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    total_income = db.scalar(select(func.coalesce(func.sum(Income.amount), 0)).where(
        Income.user_id == user.id,
        Income.income_date >= start,
        Income.income_date < end
    )) or Decimal("0.00")
    total_income = Decimal(str(total_income))

    total_expenses = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.user_id == user.id,
        Expense.expense_date >= start,
        Expense.expense_date < end
    )) or Decimal("0.00")
    total_expenses = Decimal(str(total_expenses))
    balance = total_income - total_expenses

    rows = db.execute(select(Expense.category, func.sum(Expense.amount)).where(
        Expense.user_id == user.id,
        Expense.expense_date >= start,
        Expense.expense_date < end
    ).group_by(Expense.category).order_by(Expense.category)).all()
    category_expenses = {category: Decimal(str(amount)) for category, amount in rows}

    income_transaction_count = db.scalar(select(func.count(Income.id)).where(
        Income.user_id == user.id,
        Income.income_date >= start,
        Income.income_date < end
    )) or 0
    expense_transaction_count = db.scalar(select(func.count(Expense.id)).where(
        Expense.user_id == user.id,
        Expense.expense_date >= start,
        Expense.expense_date < end
    )) or 0

    budgets = db.scalars(select(Budget).where(
        Budget.user_id == user.id,
        Budget.month == period
    ).order_by(Budget.category)).all()
    budget_summary = []
    total_budget_allocated = Decimal("0.00")
    total_budget_spent = Decimal("0.00")

    for budget in budgets:
        allocated = Decimal(str(budget.allocated_amount))
        spent = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == user.id,
            Expense.category == budget.category,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )) or Decimal("0.00")
        spent = Decimal(str(spent))
        utilization = (spent / allocated * Decimal("100")).quantize(Decimal("0.01")) if allocated > 0 else Decimal("0.00")
        total_budget_allocated += allocated
        total_budget_spent += spent
        budget_summary.append({
            "category": budget.category,
            "allocated": allocated,
            "spent": spent,
            "utilization_percentage": utilization
        })

    goals = db.scalars(select(SavingsGoal).where(
        SavingsGoal.user_id == user.id
    ).order_by(SavingsGoal.id)).all()
    total_target = sum((Decimal(str(g.target_amount)) for g in goals), Decimal("0.00"))
    total_saved = sum((Decimal(str(g.amount_saved)) for g in goals), Decimal("0.00"))
    savings_progress = (total_saved / total_target * Decimal("100")).quantize(Decimal("0.01")) if total_target > 0 else Decimal("0.00")
    completed_goals = sum(1 for g in goals if Decimal(str(g.amount_saved)) == Decimal(str(g.target_amount)))
    savings_goals = []
    for goal in goals:
        target = Decimal(str(goal.target_amount))
        saved = Decimal(str(goal.amount_saved))
        progress = (saved / target * Decimal("100")).quantize(Decimal("0.01")) if target > 0 else Decimal("0.00")
        savings_goals.append({
            "goal_name": goal.goal_name,
            "target_amount": target,
            "amount_saved": saved,
            "progress_percentage": progress,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "completed": saved == target
        })

    savings_rate = (balance / total_income * Decimal("100")).quantize(Decimal("0.01")) if total_income > 0 else Decimal("0.00")
    return {
        "period": period,
        "financial_summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "savings_rate": savings_rate
        },
        "transaction_summary": {
            "income_transactions": int(income_transaction_count),
            "expense_transactions": int(expense_transaction_count),
            "total_transactions": int(income_transaction_count + expense_transaction_count)
        },
        "category_expenses": category_expenses,
        "budget_summary": {
            "total_allocated": total_budget_allocated,
            "total_spent": total_budget_spent,
            "categories": budget_summary
        },
        "savings_summary": {
            "total_target": total_target,
            "total_saved": total_saved,
            "progress_percentage": savings_progress,
            "completed_goals": completed_goals,
            "total_goals": len(goals),
            "goals": savings_goals
        }
    }


@reports.post("/generate/{period}", response_model=ReportOut)
def generate_monthly_report(
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    summary = _build_monthly_summary(period, db, user)
    summary_text = json.dumps(summary, default=str)

    existing_report = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Monthly Financial Report",
        Report.period == period
    ).order_by(Report.id.desc()))

    if existing_report:
        existing_report.summary = summary_text
        marker = f"[MonthlyReport:{period}]"
        duplicate_notification = db.scalar(select(Notification).where(
            Notification.user_id == user.id,
            Notification.title == "Monthly Report Generated",
            Notification.message.contains(marker)
        ))
        if not duplicate_notification:
            db.add(Notification(
                user_id=user.id,
                title="Monthly Report Generated",
                message=f"{marker} Your monthly financial report for {period} is ready. You can view, download as PDF, or export as Excel.",
                is_read=False
            ))
        db.commit()
        db.refresh(existing_report)
        return existing_report

    report = Report(
        user_id=user.id,
        report_type="Monthly Financial Report",
        period=period,
        summary=summary_text
    )
    db.add(report)
    db.flush()

    marker = f"[MonthlyReport:{period}]"
    duplicate_notification = db.scalar(select(Notification).where(
        Notification.user_id == user.id,
        Notification.title == "Monthly Report Generated",
        Notification.message.contains(marker)
    ))
    if not duplicate_notification:
        db.add(Notification(
            user_id=user.id,
            title="Monthly Report Generated",
            message=f"{marker} Your monthly financial report for {period} is ready. You can view, download as PDF, or export as Excel.",
            is_read=False
        ))
    db.commit()
    db.refresh(report)
    return report


@reports.post("/generate-year/{year}", response_model=ReportOut)
def generate_yearly_report(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2100")

    monthly_reports = db.scalars(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Monthly Financial Report",
        Report.period.like(f"{year}-%")
    ).order_by(Report.period)).all()

    # Always rebuild the monthly summaries from the real transaction data so an old
    # report cannot make the yearly report show stale/incorrect numbers.
    months = []
    total_income = Decimal("0.00")
    total_expenses = Decimal("0.00")
    total_income_transactions = 0
    total_expense_transactions = 0
    category_totals = {}

    for month in range(1, 13):
        period = f"{year}-{month:02d}"
        matching = next((r for r in monthly_reports if r.period == period), None)
        # Include only months that actually have a report or actual transactions.
        summary = None
        if matching:
            summary = _build_monthly_summary(period, db, user)
        else:
            candidate = _build_monthly_summary(period, db, user)
            fs = candidate["financial_summary"]
            ts = candidate["transaction_summary"]
            if fs["total_income"] != 0 or fs["total_expenses"] != 0 or ts["total_transactions"] != 0:
                summary = candidate

        if not summary:
            continue

        fs = summary["financial_summary"]
        ts = summary["transaction_summary"]
        income = Decimal(str(fs["total_income"]))
        expenses = Decimal(str(fs["total_expenses"]))
        balance = income - expenses
        total_income += income
        total_expenses += expenses
        total_income_transactions += int(ts["income_transactions"])
        total_expense_transactions += int(ts["expense_transactions"])
        for category, amount in summary.get("category_expenses", {}).items():
            category_totals[category] = category_totals.get(category, Decimal("0.00")) + Decimal(str(amount))

        months.append({
            "period": period,
            "month": date(year, month, 1).strftime("%B"),
            "total_income": income,
            "total_expenses": expenses,
            "balance": balance,
            "savings_rate": fs.get("savings_rate", Decimal("0.00")),
            "income_transactions": int(ts["income_transactions"]),
            "expense_transactions": int(ts["expense_transactions"]),
            "total_transactions": int(ts["total_transactions"])
        })

    total_balance = total_income - total_expenses
    yearly_savings_rate = (total_balance / total_income * Decimal("100")).quantize(Decimal("0.01")) if total_income > 0 else Decimal("0.00")

    summary = {
        "period": str(year),
        "report_scope": "yearly",
        "months_included": len(months),
        "financial_summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_balance,
            "savings_rate": yearly_savings_rate
        },
        "transaction_summary": {
            "income_transactions": total_income_transactions,
            "expense_transactions": total_expense_transactions,
            "total_transactions": total_income_transactions + total_expense_transactions
        },
        "category_expenses": category_totals,
        "monthly_breakdown": months
    }
    summary_text = json.dumps(summary, default=str)

    existing = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Yearly Financial Report",
        Report.period == str(year)
    ).order_by(Report.id.desc()))

    if existing:
        existing.summary = summary_text
        db.commit()
        db.refresh(existing)
        return existing

    report = Report(
        user_id=user.id,
        report_type="Yearly Financial Report",
        period=str(year),
        summary=summary_text
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@reports.get("/yearly/{year}", response_model=ReportOut)
def get_yearly_report(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Yearly Financial Report",
        Report.period == str(year)
    ).order_by(Report.id.desc()))
    if not report:
        raise HTTPException(status_code=404, detail="Yearly report not found. Generate the yearly report first.")
    return report


@reports.get("/yearly/pdf/{year}")
def download_yearly_report_pdf(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Yearly Financial Report",
        Report.period == str(year)
    ).order_by(Report.id.desc()))
    if not report:
        raise HTTPException(status_code=404, detail="Yearly report not found. Generate the yearly report first.")
    try:
        summary = json.loads(report.summary or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored yearly report summary is invalid")

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm, topMargin=14*mm, bottomMargin=14*mm,
                                 title=f"BudgetBuddy Yearly Financial Report - {year}", author="BudgetBuddy")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("YearTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=5*mm)
    section = ParagraphStyle("YearSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=5*mm, spaceAfter=3*mm)
    normal = ParagraphStyle("YearNormal", parent=styles["Normal"], fontSize=9, leading=12)
    story = [Paragraph(f"BudgetBuddy — {year} Yearly Financial Report", title),
             Paragraph(f"Months included: {summary.get('months_included', 0)}", normal), Spacer(1, 4*mm)]
    fs = summary.get("financial_summary", {})
    story += [Paragraph("Overall Financial Summary", section)]
    data = [["Metric", "Amount"], ["Total Income", f"₹{float(fs.get('total_income', 0)):,.2f}"], ["Total Expenses", f"₹{float(fs.get('total_expenses', 0)):,.2f}"], ["Balance", f"₹{abs(float(fs.get('balance', 0))):,.2f}"], ["Savings Rate", f"{float(fs.get('savings_rate', 0)):.2f}%"]]
    table = Table(data, colWidths=[90*mm, 70*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6C5CE7")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#D9D9E2")), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("PADDING", (0,0), (-1,-1), 7)]))
    story.append(table)
    story.append(Paragraph("Monthly Breakdown", section))
    rows = [["Month", "Income", "Expenses", "Balance", "Savings %"]]
    for item in summary.get("monthly_breakdown", []):
        rows.append([item.get("month"), f"₹{float(item.get('total_income',0)):,.2f}", f"₹{float(item.get('total_expenses',0)):,.2f}", f"₹{abs(float(item.get('balance',0))):,.2f}", f"{float(item.get('savings_rate',0)):.2f}%"])
    table2 = Table(rows, repeatRows=1, colWidths=[32*mm, 34*mm, 34*mm, 34*mm, 30*mm])
    table2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6C5CE7")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D9D9E2")), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 8), ("PADDING", (0,0), (-1,-1), 5)]))
    story.append(table2)
    document.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="BudgetBuddy_Yearly_Report_{year}.pdf"'})


@reports.get("/yearly/excel/{year}")
def download_yearly_report_excel(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Yearly Financial Report",
        Report.period == str(year)
    ).order_by(Report.id.desc()))
    if not report:
        raise HTTPException(status_code=404, detail="Yearly report not found. Generate the yearly report first.")
    try:
        summary = json.loads(report.summary or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored yearly report summary is invalid")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    except ImportError:
        raise HTTPException(status_code=500, detail="Excel export requires openpyxl. Install it with pip install openpyxl.")

    wb = Workbook()
    ws = wb.active
    ws.title = f"Year {year}"
    purple = "6C5CE7"
    white = "FFFFFF"
    border = Border(*(Side(style="thin", color="D9D9E2") for _ in range(4)))
    ws.merge_cells("A1:E1")
    ws["A1"] = f"BudgetBuddy — {year} Yearly Financial Report"
    ws["A1"].font = Font(size=18, bold=True, color=white)
    ws["A1"].fill = PatternFill("solid", fgColor=purple)
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.append([])
    ws.append(["Month", "Income", "Expenses", "Balance", "Savings Rate"])
    for cell in ws[3]:
        cell.font = Font(bold=True, color=white)
        cell.fill = PatternFill("solid", fgColor=purple)
        cell.border = border
    for item in summary.get("monthly_breakdown", []):
        ws.append([item.get("month"), float(item.get("total_income",0)), float(item.get("total_expenses",0)), abs(float(item.get("balance",0))), float(item.get("savings_rate",0))])
    for row in ws.iter_rows(min_row=4):
        for cell in row:
            cell.border = border
    ws.append([])
    fs = summary.get("financial_summary", {})
    ws.append(["Overall", float(fs.get("total_income",0)), float(fs.get("total_expenses",0)), abs(float(fs.get("balance",0))), float(fs.get("savings_rate",0))])
    for col, width in zip("ABCDE", [20,18,18,18,18]):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, (int,float)) and cell.column in (2,3,4):
                cell.number_format = '₹#,##0.00'
            elif isinstance(cell.value, (int,float)) and cell.column == 5:
                cell.number_format = '0.00%'
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="BudgetBuddy_Yearly_Report_{year}.xlsx"'})

@reports.get(
    "/{report_id}",
    response_model=ReportOut
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user.id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return report


@reports.post(
    "/generate/{period}",
    response_model=ReportOut
)
def generate_monthly_report(
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Validate YYYY-MM format
    if len(period) != 7:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    try:
        start = date.fromisoformat(period + "-01")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Period must be in YYYY-MM format"
        )

    # Calculate next month
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    # Total income
    total_income = db.scalar(
        select(
            func.coalesce(
                func.sum(Income.amount),
                0
            )
        ).where(
            Income.user_id == user.id,
            Income.income_date >= start,
            Income.income_date < end
        )
    ) or Decimal("0.00")

    total_income = Decimal(str(total_income))

    # Total expenses
    total_expenses = db.scalar(
        select(
            func.coalesce(
                func.sum(Expense.amount),
                0
            )
        ).where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
    ) or Decimal("0.00")

    total_expenses = Decimal(str(total_expenses))

    # Balance
    balance = total_income - total_expenses

    # Category-wise expenses
    rows = db.execute(
        select(
            Expense.category,
            func.sum(Expense.amount)
        )
        .where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
        .group_by(Expense.category)
        .order_by(Expense.category)
    ).all()

    category_expenses = {}

    for category, amount in rows:
        category_expenses[category] = Decimal(str(amount))

    # Transaction counts
    income_transaction_count = db.scalar(
        select(func.count(Income.id)).where(
            Income.user_id == user.id,
            Income.income_date >= start,
            Income.income_date < end
        )
    ) or 0

    expense_transaction_count = db.scalar(
        select(func.count(Expense.id)).where(
            Expense.user_id == user.id,
            Expense.expense_date >= start,
            Expense.expense_date < end
        )
    ) or 0

    # Budget summary
    budgets = db.scalars(
        select(Budget)
        .where(
            Budget.user_id == user.id,
            Budget.month == period
        )
        .order_by(Budget.category)
    ).all()

    budget_summary = []
    total_budget_allocated = Decimal("0.00")
    total_budget_spent = Decimal("0.00")

    for budget in budgets:
        allocated = Decimal(str(budget.allocated_amount))

        spent = db.scalar(
            select(
                func.coalesce(
                    func.sum(Expense.amount),
                    0
                )
            ).where(
                Expense.user_id == user.id,
                Expense.category == budget.category,
                Expense.expense_date >= start,
                Expense.expense_date < end
            )
        ) or Decimal("0.00")

        spent = Decimal(str(spent))

        if allocated > 0:
            utilization = (
                spent / allocated * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            utilization = Decimal("0.00")

        total_budget_allocated += allocated
        total_budget_spent += spent

        budget_summary.append({
            "category": budget.category,
            "allocated": allocated,
            "spent": spent,
            "utilization_percentage": utilization
        })

    # Savings goals summary
    goals = db.scalars(
        select(SavingsGoal)
        .where(
            SavingsGoal.user_id == user.id
        )
        .order_by(SavingsGoal.id)
    ).all()

    total_target = sum(
        (
            Decimal(str(goal.target_amount))
            for goal in goals
        ),
        Decimal("0.00")
    )

    total_saved = sum(
        (
            Decimal(str(goal.amount_saved))
            for goal in goals
        ),
        Decimal("0.00")
    )

    if total_target > 0:
        savings_progress = (
            total_saved / total_target * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        savings_progress = Decimal("0.00")

    completed_goals = sum(
        1
        for goal in goals
        if Decimal(str(goal.amount_saved))
        == Decimal(str(goal.target_amount))
    )

    savings_goals = []

    for goal in goals:
        target = Decimal(str(goal.target_amount))
        saved = Decimal(str(goal.amount_saved))

        if target > 0:
            progress = (
                saved / target * Decimal("100")
            ).quantize(Decimal("0.01"))
        else:
            progress = Decimal("0.00")

        savings_goals.append({
            "goal_name": goal.goal_name,
            "target_amount": target,
            "amount_saved": saved,
            "progress_percentage": progress,
            "target_date": (
                goal.target_date.isoformat()
                if goal.target_date
                else None
            ),
            "completed": saved == target
        })

    # Savings rate
    if total_income > 0:
        savings_rate = (
            balance / total_income * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        savings_rate = Decimal("0.00")

    # Complete report summary
    summary = {
        "period": period,
        "financial_summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "savings_rate": savings_rate
        },
        "transaction_summary": {
            "income_transactions": income_transaction_count,
            "expense_transactions": expense_transaction_count,
            "total_transactions": (
                income_transaction_count
                + expense_transaction_count
            )
        },
        "category_expenses": category_expenses,
        "budget_summary": {
            "total_allocated": total_budget_allocated,
            "total_spent": total_budget_spent,
            "categories": budget_summary
        },
        "savings_summary": {
            "total_target": total_target,
            "total_saved": total_saved,
            "progress_percentage": savings_progress,
            "completed_goals": completed_goals,
            "total_goals": len(goals),
            "goals": savings_goals
        }
    }

    import json

    summary_text = json.dumps(
        summary,
        default=str
    )

    # Check for an existing report for this user and month
    existing_report = db.scalar(
        select(Report)
        .where(
            Report.user_id == user.id,
            Report.report_type == "Monthly Financial Report",
            Report.period == period
        )
        .order_by(Report.id.desc())
    )

    # Update existing report
    

            # Update existing report
    if existing_report:
        existing_report.summary = summary_text

        marker = f"[MonthlyReport:{period}]"

        duplicate_notification = db.scalar(
            select(Notification).where(
                Notification.user_id == user.id,
                Notification.title == "Monthly Report Generated",
                Notification.message.contains(marker)
            )
        )

        if not duplicate_notification:
            db.add(
                Notification(
                    user_id=user.id,
                    title="Monthly Report Generated",
                    message=(
                        f"{marker} Your monthly financial report "
                        f"for {period} is ready. You can view, "
                        f"download as PDF, or export as Excel."
                    ),
                    is_read=False
                )
            )

        db.commit()
        db.refresh(existing_report)

        return existing_report

    # Create new report
    report = Report(
        user_id=user.id,
        report_type="Monthly Financial Report",
        period=period,
        summary=summary_text
    )

    db.add(report)
    db.flush()

    marker = f"[MonthlyReport:{period}]"

    duplicate_notification = db.scalar(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.title == "Monthly Report Generated",
            Notification.message.contains(marker)
        )
    )

    if not duplicate_notification:
        db.add(
            Notification(
                user_id=user.id,
                title="Monthly Report Generated",
                message=(
                    f"{marker} Your monthly financial report "
                    f"for {period} is ready. You can view, "
                    f"download as PDF, or export as Excel."
                ),
                is_read=False
            )
        )

    db.commit()
    db.refresh(report)

    return report


@reports.put(
    "/{report_id}",
    response_model=ReportOut
)
def update_report(
    report_id: int,
    period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(select(Report).where(
        Report.id == report_id,
        Report.user_id == user.id
    ))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.report_type != "Monthly Financial Report":
        raise HTTPException(status_code=400, detail="Only monthly reports can be updated with a month")

    # IMPORTANT: changing the period must also rebuild the summary from the
    # transactions in that month. This prevents September's data from being
    # displayed as November's data.
    summary = _build_monthly_summary(period, db, user)

    duplicate = db.scalar(select(Report).where(
        Report.user_id == user.id,
        Report.report_type == "Monthly Financial Report",
        Report.period == period,
        Report.id != report_id
    ))
    if duplicate:
        raise HTTPException(status_code=409, detail=f"A report already exists for {period}.")

    report.period = period
    report.summary = json.dumps(summary, default=str)
    db.commit()
    db.refresh(report)
    return report


@reports.delete(
    "/{report_id}",
    status_code=204
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    report = db.scalar(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == user.id
        )
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    db.delete(report)
    db.commit()


router.include_router(reports)