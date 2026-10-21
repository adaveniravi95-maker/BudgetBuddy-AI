# BudgetBuddy Model Structure & Relationships

## Entity Relationship Diagram

```
User (accounts.User)
 │
 ├── Profile (accounts.Profile)
 │   ├── user (OneToOne → User)
 │   ├── monthly_income
 │   ├── currency
 │   ├── budget_alerts
 │   ├── savings_reminders
 │   └── monthly_report_notifications
 │
 ├── Income (income.Income)
 │   ├── user (FK → User)
 │   ├── category (FK → IncomeCategory)
 │   ├── amount
 │   ├── description
 │   ├── source
 │   ├── date
 │   ├── is_recurring
 │   └── recurring_frequency
 │
 ├── Expense (expenses.Expense)
 │   ├── user (FK → User)
 │   ├── category (FK → ExpenseCategory)
 │   ├── amount
 │   ├── description
 │   ├── date
 │   ├── payment_method
 │   ├── receipt_image
 │   ├── notes
 │   └── is_recurring
 │
 ├── Budget (budgets.Budget)
 │   ├── user (FK → User)
 │   ├── name
 │   ├── total_amount
 │   ├── month
 │   ├── year
 │   ├── is_active
 │   └── CategoryBudget (1:N)
 │       ├── category (FK → ExpenseCategory)
 │       └── allocated_amount
 │
 ├── SavingsGoal (savings.SavingsGoal)
 │   ├── user (FK → User)
 │   ├── name
 │   ├── target_amount
 │   ├── current_amount
 │   ├── deadline
 │   ├── status
 │   ├── priority
 │   ├── notes
 │   └── SavingsTransaction (1:N)
 │       ├── amount
 │       ├── transaction_type
 │       ├── description
 │       └── date
 │
 ├── Notification (notifications.Notification)
 │   ├── user (FK → User)
 │   ├── notification_type
 │   ├── title
 │   ├── message
 │   └── is_read
 │
 └── Report (reports.Report)
     ├── user (FK → User)
     ├── report_type
     ├── title
     ├── start_date
     ├── end_date
     ├── format
     └── file
```

## Model Details

### 1. User (accounts.User)
**Purpose**: Central user entity with authentication and role-based access

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| username | CharField(150) | UNIQUE, NOT NULL | Login username |
| email | EmailField | UNIQUE | Email address |
| password | CharField(128) | NOT NULL | Hashed password |
| first_name | CharField(150) | | First name |
| last_name | CharField(150) | | Last name |
| role | CharField(20) | DEFAULT 'student' | student/premium/admin |
| phone_number | CharField(15) | NULLABLE | Contact number |
| date_of_birth | DateField | NULLABLE | Birth date |
| is_active | BooleanField | DEFAULT True | Account status |
| is_staff | BooleanField | DEFAULT False | Admin access |
| created_at | DateTimeField | AUTO_ADD | Registration time |
| updated_at | DateTimeField | AUTO | Last update time |

### 2. Profile (accounts.Profile)
**Purpose**: Extended user profile with financial preferences

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | OneToOneField | FK → User, CASCADE | Owner user |
| monthly_income | DecimalField(12,2) | DEFAULT 0, MIN 0 | Expected monthly income |
| currency | CharField(3) | DEFAULT 'INR' | Currency code |
| budget_alerts | BooleanField | DEFAULT True | Enable budget alerts |
| savings_reminders | BooleanField | DEFAULT True | Enable savings reminders |
| monthly_report_notifications | BooleanField | DEFAULT True | Enable monthly reports |
| created_at | DateTimeField | AUTO_ADD | Creation time |
| updated_at | DateTimeField | AUTO | Last update time |

### 3. IncomeCategory (income.IncomeCategory)
**Purpose**: Categories for income types

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| name | CharField(50) | UNIQUE, NOT NULL | Category name |
| description | TextField | BLANK | Category description |
| icon | CharField(50) | BLANK | UI icon identifier |

**Predefined Categories**: Pocket Money, Scholarship, Freelance, Part-time Job, Gift

### 4. Income (income.Income)
**Purpose**: Track all income sources

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| category | ForeignKey | FK → IncomeCategory, SET_NULL, NULLABLE | Income category |
| amount | DecimalField(12,2) | MIN 0.01 | Income amount |
| description | CharField(255) | NOT NULL | Income description |
| source | CharField(100) | BLANK | Income source |
| date | DateField | NOT NULL | Income date |
| is_recurring | BooleanField | DEFAULT False | Recurring income? |
| recurring_frequency | CharField(20) | NULLABLE | weekly/monthly/yearly |
| created_at | DateTimeField | AUTO_ADD | Creation time |
| updated_at | DateTimeField | AUTO | Last update time |

### 5. ExpenseCategory (expenses.ExpenseCategory)
**Purpose**: Categories for expenses

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| name | CharField(50) | UNIQUE, NOT NULL | Category name |
| description | TextField | BLANK | Category description |
| icon | CharField(50) | BLANK | UI icon identifier |
| color | CharField(7) | DEFAULT '#000000' | Category color (hex) |

**Predefined Categories**: Food, Travel, Shopping, Education, Entertainment, Miscellaneous

### 6. Expense (expenses.Expense)
**Purpose**: Track all expenses

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| category | ForeignKey | FK → ExpenseCategory, SET_NULL, NULLABLE | Expense category |
| amount | DecimalField(12,2) | MIN 0.01 | Expense amount |
| description | CharField(255) | NOT NULL | Expense description |
| date | DateField | NOT NULL | Expense date |
| payment_method | CharField(20) | DEFAULT 'cash' | cash/card/upi/bank_transfer |
| receipt_image | ImageField | BLANK, NULLABLE | Receipt photo |
| notes | TextField | BLANK | Additional notes |
| is_recurring | BooleanField | DEFAULT False | Recurring expense? |
| created_at | DateTimeField | AUTO_ADD | Creation time |
| updated_at | DateTimeField | AUTO | Last update time |

### 7. Budget (budgets.Budget)
**Purpose**: Monthly budget planning

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| name | CharField(100) | NOT NULL | Budget name |
| total_amount | DecimalField(12,2) | MIN 0.01 | Total budget amount |
| month | IntegerField | NOT NULL | Month (1-12) |
| year | IntegerField | NOT NULL | Year |
| is_active | BooleanField | DEFAULT True | Active budget? |
| created_at | DateTimeField | AUTO_ADD | Creation time |
| updated_at | DateTimeField | AUTO | Last update time |

**Constraints**: UNIQUE(user, month, year) - One budget per user per month

### 8. CategoryBudget (budgets.CategoryBudget)
**Purpose**: Category-wise budget allocation

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| budget | ForeignKey | FK → Budget, CASCADE | Parent budget |
| category | ForeignKey | FK → ExpenseCategory, CASCADE | Expense category |
| allocated_amount | DecimalField(12,2) | MIN 0 | Allocated amount |

**Constraints**: UNIQUE(budget, category) - One allocation per category per budget

### 9. SavingsGoal (savings.SavingsGoal)
**Purpose**: Track savings goals

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| name | CharField(100) | NOT NULL | Goal name |
| target_amount | DecimalField(12,2) | MIN 0.01 | Target amount |
| current_amount | DecimalField(12,2) | DEFAULT 0, MIN 0 | Current savings |
| deadline | DateField | NULLABLE | Target date |
| status | CharField(20) | DEFAULT 'active' | active/completed/paused/cancelled |
| priority | IntegerField | DEFAULT 1 | Goal priority |
| notes | TextField | BLANK | Goal notes |
| created_at | DateTimeField | AUTO_ADD | Creation time |
| updated_at | DateTimeField | AUTO | Last update time |

### 10. SavingsTransaction (savings.SavingsTransaction)
**Purpose**: Track deposits and withdrawals for savings goals

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| goal | ForeignKey | FK → SavingsGoal, CASCADE | Parent goal |
| amount | DecimalField(12,2) | MIN 0.01 | Transaction amount |
| transaction_type | CharField(20) | NOT NULL | deposit/withdrawal |
| description | CharField(255) | BLANK | Transaction description |
| date | DateField | NOT NULL | Transaction date |
| created_at | DateTimeField | AUTO_ADD | Creation time |

### 11. Notification (notifications.Notification)
**Purpose**: User notifications and alerts

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| notification_type | CharField(20) | NOT NULL | Type of notification |
| title | CharField(200) | NOT NULL | Notification title |
| message | TextField | NOT NULL | Notification content |
| is_read | BooleanField | DEFAULT False | Read status |
| created_at | DateTimeField | AUTO_ADD | Creation time |

**Notification Types**: budget_alert, savings_reminder, goal_milestone, monthly_report, info

### 12. Report (reports.Report)
**Purpose**: Generated financial reports

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BigAutoField | PK | Unique identifier |
| user | ForeignKey | FK → User, CASCADE | Owner user |
| report_type | CharField(20) | NOT NULL | monthly/yearly/custom |
| title | CharField(200) | NOT NULL | Report title |
| start_date | DateField | NOT NULL | Report start date |
| end_date | DateField | NOT NULL | Report end date |
| format | CharField(10) | DEFAULT 'pdf' | pdf/excel/csv |
| file | FileField | BLANK, NULLABLE | Generated file |
| created_at | DateTimeField | AUTO_ADD | Generation time |

## Relationships Summary

### Ownership Relationships
All financial records are owned by a User through ForeignKey:

```
User (1) ──── (1) Profile
User (1) ──── (N) Income
User (1) ──── (N) Expense
User (1) ──── (N) Budget
User (1) ──── (N) SavingsGoal
User (1) ──── (N) Notification
User (1) ──── (N) Report
```

### Category Relationships
```
IncomeCategory (1) ──── (N) Income
ExpenseCategory (1) ──── (N) Expense
ExpenseCategory (1) ──── (N) CategoryBudget
```

### Budget Relationships
```
Budget (1) ──── (N) CategoryBudget
Budget (user, month, year) ──── UNIQUE
```

### Savings Relationships
```
SavingsGoal (1) ──── (N) SavingsTransaction
SavingsGoal (user) ──── (N) SavingsGoal
```

## Data Integrity Rules

### On Delete Behavior
- **CASCADE**: When User is deleted, all their data is deleted
- **SET_NULL**: When Category is deleted, records keep their data
- **CASCADE**: When Budget is deleted, CategoryBudgets are deleted
- **CASCADE**: When SavingsGoal is deleted, Transactions are deleted

### Validation Rules
- Amount fields: Must be > 0 (MinValueValidator)
- Monthly income: Must be >= 0
- Target amount: Must be > 0
- Current amount: Must be >= 0
- Required fields: Cannot be empty
- Unique constraints: Prevent duplicate entries

### User Isolation
- Each query filters by `user=self.request.user`
- Users can only see their own records
- API endpoints enforce ownership through queryset filtering

## Database Verification Commands

```bash
# Check model structure
python manage.py inspectdb

# Verify relationships
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
print(f'User: {user.username}')
print(f'Incomes: {user.incomes.count()}')
print(f'Expenses: {user.expenses.count()}')
print(f'Budgets: {user.budgets.count()}')
print(f'Savings Goals: {user.savings_goals.count()}')
print(f'Notifications: {user.notifications.count()}')
print(f'Reports: {user.reports.count()}')
"
```
