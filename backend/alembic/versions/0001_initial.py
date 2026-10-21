"""initial BudgetBuddy schema"""
from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("full_name", sa.String(120), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", sa.String(30), nullable=False, server_default="student"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("email"), sa.CheckConstraint("role IN ('student','admin')", name="ck_users_role"))
    op.create_table("profiles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("monthly_income", sa.Numeric(12,2)), sa.Column("financial_preferences", sa.Text()), sa.UniqueConstraint("user_id"), sa.CheckConstraint("monthly_income IS NULL OR monthly_income >= 0", name="ck_profiles_income_nonnegative"))
    for name, cols, checks in [
        ("incomes", [("id",sa.Integer(),False),("user_id",sa.Integer(),False),("amount",sa.Numeric(12,2),False),("source",sa.String(50),False),("income_date",sa.Date(),False),("details",sa.String(255),True)], ["amount > 0","source IN ('Pocket Money','Scholarship','Freelance Income')"]),
        ("expenses", [("id",sa.Integer(),False),("user_id",sa.Integer(),False),("amount",sa.Numeric(12,2),False),("category",sa.String(30),False),("expense_date",sa.Date(),False),("description",sa.String(255),True)], ["amount > 0","category IN ('Food','Travel','Shopping','Education','Entertainment','Miscellaneous')"]),
        ("savings_goals", [("id",sa.Integer(),False),("user_id",sa.Integer(),False),("goal_name",sa.String(120),False),("target_amount",sa.Numeric(12,2),False),("amount_saved",sa.Numeric(12,2),False),("target_date",sa.Date(),True)], ["target_amount > 0","amount_saved >= 0","amount_saved <= target_amount"]),
        ("notifications", [("id",sa.Integer(),False),("user_id",sa.Integer(),False),("title",sa.String(120),False),("message",sa.Text(),False),("is_read",sa.Boolean(),False),("created_at",sa.DateTime(),False)], []),
        ("reports", [("id",sa.Integer(),False),("user_id",sa.Integer(),False),("report_type",sa.String(50),False),("period",sa.String(7),False),("generated_at",sa.DateTime(),False),("summary",sa.Text(),True)], []),
    ]:
        columns=[]
        for i,(c,t,n) in enumerate(cols):
            col=sa.Column(c,t,primary_key=(c=="id"),nullable=not n)
            if c=="user_id": col=sa.Column(c,t,sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
            columns.append(col)
        columns += [sa.CheckConstraint(x, name=f"ck_{name}_{i}") for i,x in enumerate(checks)]
        op.create_table(name,*columns)
    op.create_table("budgets", sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("month",sa.String(7),nullable=False),sa.Column("category",sa.String(30),nullable=False),sa.Column("allocated_amount",sa.Numeric(12,2),nullable=False),sa.UniqueConstraint("user_id","month","category",name="uq_budget_user_month_category"),sa.CheckConstraint("allocated_amount > 0",name="ck_budgets_amount_positive"),sa.CheckConstraint("category IN ('Food','Travel','Shopping','Education','Entertainment','Miscellaneous')",name="ck_budgets_category"))

def downgrade():
    for table in ["budgets","reports","notifications","savings_goals","expenses","incomes","profiles","users"]: op.drop_table(table)
