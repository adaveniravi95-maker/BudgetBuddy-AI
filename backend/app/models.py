from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    savings_goals = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("role IN ('student','admin')", name="ck_users_role"),)

class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12,2), nullable=True)
    financial_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    user = relationship("User", back_populates="profile")
    __table_args__ = (CheckConstraint("monthly_income IS NULL OR monthly_income >= 0", name="ck_profiles_income_nonnegative"),)

class Income(Base):
    __tablename__ = "incomes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    income_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user = relationship("User", back_populates="incomes")
    __table_args__ = (CheckConstraint("amount > 0", name="ck_incomes_amount_positive"), CheckConstraint("source IN ('Pocket Money','Scholarship','Freelance Income')", name="ck_incomes_source"))

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user = relationship("User", back_populates="expenses")
    __table_args__ = (CheckConstraint("amount > 0", name="ck_expenses_amount_positive"), CheckConstraint("category IN ('Food','Travel','Shopping','Education','Entertainment','Miscellaneous')", name="ck_expenses_category"))

class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    user = relationship("User", back_populates="budgets")
    __table_args__ = (UniqueConstraint("user_id", "month", "category", name="uq_budget_user_month_category"), CheckConstraint("allocated_amount > 0", name="ck_budgets_amount_positive"), CheckConstraint("length(month) = 7", name="ck_budgets_month_format"), CheckConstraint("category IN ('Food','Travel','Shopping','Education','Entertainment','Miscellaneous')", name="ck_budgets_category"))

class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    amount_saved: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    start_date: Mapped[date | None] = mapped_column(
    Date,
    nullable=True,
    default=date.today
)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    user = relationship("User", back_populates="savings_goals")
    __table_args__ = (CheckConstraint("target_amount > 0", name="ck_goals_target_positive"), CheckConstraint("amount_saved >= 0", name="ck_goals_saved_nonnegative"), CheckConstraint("amount_saved <= target_amount", name="ck_goals_saved_not_over_target"))

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="notifications")

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user = relationship("User", back_populates="reports")
