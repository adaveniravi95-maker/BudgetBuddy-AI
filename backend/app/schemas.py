from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import date, datetime
from typing import Optional, List
from .models import ExpenseCategory, IncomeCategory, NotificationType


# ─── User Schemas ────────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str = ""
    last_name: str = ""


class UserResponse(UserBase):
    id: int
    role: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Profile Schemas ─────────────────────────────────────────
class ProfileResponse(BaseModel):
    id: int
    user: UserResponse
    monthly_income: float
    currency: str
    budget_alerts: bool
    savings_reminders: bool
    monthly_report_notifications: bool

    model_config = {"from_attributes": True}


# ─── Registration ────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    password_confirm: str
    first_name: str = ""
    last_name: str = ""

    @field_validator("username")
    @classmethod
    def username_min_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class RegisterResponse(BaseModel):
    user: UserResponse
    tokens: dict


# ─── Login ───────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access: str
    refresh: str
    user: UserResponse


# ─── Token Refresh ───────────────────────────────────────────
class TokenRefreshRequest(BaseModel):
    refresh: str


class TokenRefreshResponse(BaseModel):
    access: str
    refresh: Optional[str] = None


# ─── Logout ──────────────────────────────────────────────────
class LogoutRequest(BaseModel):
    refresh: str


# ─── Check Auth ──────────────────────────────────────────────
class CheckAuthResponse(BaseModel):
    authenticated: bool
    user: UserResponse


# ─── Expense Schemas ───────────────────────────────────────
class ExpenseCreate(BaseModel):
    amount: float
    category: ExpenseCategory
    description: str = ""
    date: date

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    category: ExpenseCategory
    description: str
    date: date
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: int


# ─── Income Schemas ───────────────────────────────────────
class IncomeCreate(BaseModel):
    amount: float
    source: IncomeCategory
    description: str = ""
    date: date

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class IncomeUpdate(BaseModel):
    amount: Optional[float] = None
    source: Optional[IncomeCategory] = None
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class IncomeResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    source: IncomeCategory
    description: str
    date: date
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IncomeListResponse(BaseModel):
    incomes: List[IncomeResponse]
    total: int


# ─── Transaction Schemas ──────────────────────────────────
class TransactionItem(BaseModel):
    id: int
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: str
    date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionSummary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    income_count: int
    expense_count: int


class TransactionListResponse(BaseModel):
    transactions: List[TransactionItem]
    total: int


# ─── Budget Schemas ────────────────────────────────────────
class AllocationInput(BaseModel):
    category: ExpenseCategory
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class AllocationResponse(BaseModel):
    id: int
    category: ExpenseCategory
    amount: float

    model_config = {"from_attributes": True}


class BudgetCreate(BaseModel):
    month: int
    year: int
    total_amount: float
    allocations: List[AllocationInput]

    @field_validator("month")
    @classmethod
    def month_valid(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("total_amount")
    @classmethod
    def total_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Total amount must be greater than 0")
        return v


class BudgetUpdate(BaseModel):
    total_amount: Optional[float] = None
    allocations: Optional[List[AllocationInput]] = None

    @field_validator("total_amount")
    @classmethod
    def total_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Total amount must be greater than 0")
        return v


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    month: int
    year: int
    total_amount: float
    allocations: List[AllocationResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BudgetListResponse(BaseModel):
    budgets: List[BudgetResponse]
    total: int


# ─── Savings Goal Schemas ────────────────────────────────────
class SavingsGoalCreate(BaseModel):
    name: str
    target_amount: float

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Goal name cannot be empty")
        return v.strip()

    @field_validator("target_amount")
    @classmethod
    def target_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target amount must be greater than 0")
        return v


class SavingsGoalUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Goal name cannot be empty")
        return v.strip() if v else v

    @field_validator("target_amount")
    @classmethod
    def target_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Target amount must be greater than 0")
        return v


class SavingsGoalProgressUpdate(BaseModel):
    current_saved: float

    @field_validator("current_saved")
    @classmethod
    def saved_not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Saved amount cannot be negative")
        return v


class SavingsGoalResponse(BaseModel):
    id: int
    user_id: int
    name: str
    target_amount: float
    current_saved: float
    progress_percent: float
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SavingsGoalListResponse(BaseModel):
    goals: List[SavingsGoalResponse]
    total: int


# ─── Analytics Schemas ────────────────────────────────────────
class AnalyticsCategoryItem(BaseModel):
    category: str
    total: float
    count: int
    percent_of_expenses: float


class AnalyticsMonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expenses: float
    net: float


class AnalyticsSavingsSummary(BaseModel):
    total_goals: int
    completed_goals: int
    total_target: float
    total_saved: float
    overall_progress_percent: float


class AnalyticsBudgetAllocation(BaseModel):
    category: str
    budgeted: float
    spent: float
    utilization_percent: float


class AnalyticsBudgetSummary(BaseModel):
    month: int
    year: int
    total_budget: float
    total_spent: float
    remaining: float
    utilization_percent: float
    allocations: List[AnalyticsBudgetAllocation]


class AnalyticsFilters(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None


class AnalyticsResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate_percent: float
    income_count: int
    expense_count: int
    has_data: bool
    category_summary: List[AnalyticsCategoryItem]
    monthly_trends: List[AnalyticsMonthlyTrend]
    savings_summary: AnalyticsSavingsSummary
    budget_summary: Optional[AnalyticsBudgetSummary] = None
    filters: AnalyticsFilters


# ─── Report Schemas ───────────────────────────────────────────
class ReportBreakdownItem(BaseModel):
    label: str
    total: float
    count: int
    percent: float


class ReportSectionTotals(BaseModel):
    total: float
    count: int
    breakdown: List[ReportBreakdownItem]


class ReportBudgetAllocation(BaseModel):
    category: str
    budgeted: float
    spent: float
    remaining: float
    utilization_percent: float


class ReportBudgetSection(BaseModel):
    total_budget: float
    total_spent: float
    remaining: float
    utilization_percent: float
    allocations: List[ReportBudgetAllocation]


class ReportSavingsGoalItem(BaseModel):
    id: int
    name: str
    target_amount: float
    current_saved: float
    progress_percent: float
    is_completed: bool


class ReportSavingsSection(BaseModel):
    total_goals: int
    total_target: float
    total_saved: float
    overall_progress_percent: float
    goals: List[ReportSavingsGoalItem]


class MonthlyReportResponse(BaseModel):
    month: int
    year: int
    generated_at: datetime
    period_start: date
    period_end: date
    income: ReportSectionTotals
    expenses: ReportSectionTotals
    net_savings: float
    savings_rate_percent: float
    budget: Optional[ReportBudgetSection] = None
    savings: ReportSavingsSection
    transaction_count: int
    income_count: int
    expense_count: int


# ─── Notification Schemas ─────────────────────────────────────
class NotificationResponse(BaseModel):
    id: int
    notification_type: NotificationType
    message: str
    is_read: bool
    related_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# CONSTANTS
# ============================================================

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Entertainment",
    "Miscellaneous",
]

INCOME_SOURCES = [
    "Pocket Money",
    "Scholarship",
    "Freelance Income",
]


# ============================================================
# ENUMS
# ============================================================

class Category(str, Enum):
    Food = "Food"
    Travel = "Travel"
    Shopping = "Shopping"
    Education = "Education"
    Entertainment = "Entertainment"
    Miscellaneous = "Miscellaneous"


class IncomeSource(str, Enum):
    pocket_money = "Pocket Money"
    scholarship = "Scholarship"
    freelance_income = "Freelance Income"


# ============================================================
# AUTHENTICATION
# ============================================================

class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# EXPENSES
# ============================================================

class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category: Category
    expense_date: date
    description: str | None = Field(
        default=None,
        max_length=255
    )


class ExpenseOut(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


# ============================================================
# INCOME
# ============================================================

class IncomeCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    source: IncomeSource
    income_date: date
    details: str | None = Field(
        default=None,
        max_length=255
    )


class IncomeOut(IncomeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


# ============================================================
# BUDGET
# ============================================================

class BudgetItem(BaseModel):
    category: Category
    allocated_amount: Decimal = Field(gt=0)


class BudgetOut(BudgetItem):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    month: str


class BudgetCreate(BaseModel):
    month: str = Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    )

    allocations: list[BudgetItem] = Field(
        min_length=1
    )

    @field_validator("allocations")
    @classmethod
    def unique_categories(cls, value):
        categories = [item.category for item in value]

        if len(categories) != len(set(categories)):
            raise ValueError(
                "Each category can appear only once per monthly budget"
            )

        return value


# ============================================================
# SAVINGS GOALS
# ============================================================

class SavingsGoalCreate(BaseModel):
    goal_name: str = Field(
        min_length=2,
        max_length=120
    )

    target_amount: Decimal = Field(
        gt=0
    )

    amount_saved: Decimal = Field(
        default=Decimal("0.00"),
        ge=0
    )

    start_date: date | None = None

    target_date: date | None = None

    @field_validator("goal_name")
    @classmethod
    def validate_goal_name(cls, value):
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Goal name must contain at least 2 characters"
            )

        return value

    @model_validator(mode="after")
    def validate_goal_dates(self):
        if (
            self.start_date is not None
            and self.target_date is not None
            and self.target_date < self.start_date
        ):
            raise ValueError(
                "Target date cannot be earlier than start date"
            )

        if self.amount_saved > self.target_amount:
            raise ValueError(
                "Amount saved cannot be greater than target amount"
            )

        return self


class SavingsGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    goal_name: str
    target_amount: Decimal
    amount_saved: Decimal
    start_date: date | None
    target_date: date | None

    # Calculated fields
    progress_percentage: Decimal
    is_completed: bool

# ============================================================
# DASHBOARD
# ============================================================

class DashboardOut(BaseModel):
    month: str

    total_income: Decimal
    total_expenses: Decimal
    remaining_amount: Decimal

    category_expenses: dict[str, Decimal]

    recent_activity: list[dict]
    
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    
class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    report_type: str
    period: str
    generated_at: datetime
    summary: str | None
