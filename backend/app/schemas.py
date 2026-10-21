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