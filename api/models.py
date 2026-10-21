from django.db import models
from django.contrib.auth.models import User

# Strict 6 Expense Categories mandated by project rubric
EXPENSE_CATEGORIES = [
    ('Food', 'Food'),
    ('Travel', 'Travel'),
    ('Shopping', 'Shopping'),
    ('Education', 'Education'),
    ('Entertainment', 'Entertainment'),
    ('Miscellaneous', 'Miscellaneous'),
]

# Strict 3 Income Sources mandated by project rubric
INCOME_SOURCES = [
    ('Pocket Money', 'Pocket Money'),
    ('Scholarship', 'Scholarship'),
    ('Freelance Income', 'Freelance Income'),
]

# Notification Types
NOTIFICATION_TYPES = [
    ('BUDGET_ALERT', 'Budget Alert'),
    ('SAVINGS_MILESTONE', 'Savings Milestone'),
    ('SAVINGS_REMINDER', 'Savings Reminder'),
    ('MONTHLY_REPORT', 'Monthly Report'),
]

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.category})"


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    income_type = models.CharField(max_length=50, choices=INCOME_SOURCES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.income_type} - ₹{self.amount}"


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    month = models.IntegerField()
    year = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month', 'year')

    def __str__(self):
        return f"Budget {self.month}/{self.year} - ₹{self.total_amount}"


class CategoryBudget(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_allocations')
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('budget', 'category')

    def __str__(self):
        return f"{self.category}: ₹{self.allocated_amount}"


class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ₹{self.current_amount}/₹{self.target_amount} ({self.user.username})"


# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200, default='Alert')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.title}"