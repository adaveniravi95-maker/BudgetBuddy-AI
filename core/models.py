from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# ============================================================
# User Profile
# ============================================================

class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    college = models.CharField(
        max_length=150,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ============================================================
# Income
# ============================================================

class Income(models.Model):
    SOURCE_CHOICES = [
        ('Pocket Money', 'Pocket Money'),
        ('Scholarship', 'Scholarship'),
        ('Freelance Income', 'Freelance Income'),
        ('Part-time Job', 'Part-time Job'),
        ('Salary', 'Salary'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="incomes"
    )

    source = models.CharField(
        max_length=100,
        choices=SOURCE_CHOICES,
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    upi_reference = models.CharField(
        max_length=150,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    date = models.DateField()

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.source} - {self.amount}"


# ============================================================
# Expense
# ============================================================

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Travel', 'Travel'),
        ('Shopping', 'Shopping'),
        ('Education', 'Education'),
        ('Entertainment', 'Entertainment'),
        ('Miscellaneous', 'Miscellaneous'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    upi_reference = models.CharField(
        max_length=150,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    date = models.DateField()

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.category} - {self.amount}"


class ImportedTransactionIdentity(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="imported_transaction_identities",
    )
    identity_key = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'identity_key'],
                name='unique_imported_transaction_identity',
            ),
        ]



# ============================================================
# Budget
# ============================================================

class Budget(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="budgets"
    )

    category = models.CharField(
        max_length=100,
        choices=Expense.CATEGORY_CHOICES,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    month = models.DateField()

    class Meta:
        ordering = ['-month', 'category']

    def __str__(self):
        return f"{self.category} ({self.month}) - {self.amount}"



# ============================================================
# Savings Goal
# ============================================================

class SavingsGoal(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="savings_goals"
    )

    name = models.CharField(
        max_length=150
    )

    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    target_date = models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-id']

    @property
    def progress_percentage(self):
        if not self.target_amount or self.target_amount <= Decimal('0.00'):
            return 0.0
        pct = (self.current_amount / self.target_amount) * Decimal('100')
        return round(float(pct), 2)

    @property
    def is_completed(self):
        if not self.target_amount or self.target_amount <= Decimal('0.00'):
            return False
        return self.current_amount >= self.target_amount

    @property
    def remaining_amount(self):
        if not self.target_amount:
            return Decimal('0.00')
        rem = self.target_amount - self.current_amount
        return max(Decimal('0.00'), rem)

    def __str__(self):
        return f"{self.name} ({self.current_amount}/{self.target_amount})"


# ============================================================
# Notification
# ============================================================

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('budget_alert', 'Budget Alert'),
        ('goal_milestone', 'Savings Goal Milestone'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='system'
    )

    title = models.CharField(
        max_length=150
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    related_context = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.user.username} - [{self.notification_type}] {self.title}"


# ============================================================
# Report
# ============================================================

class Report(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    title = models.CharField(
        max_length=200,
        default="Monthly Financial Report"
    )

    report_type = models.CharField(
        max_length=100,
        default="monthly_financial_summary"
    )

    month = models.DateField(
        null=True,
        blank=True
    )

    data = models.JSONField(
        default=dict,
        blank=True
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-generated_at', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'report_type', 'month'],
                name='unique_user_report_type_month',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.generated_at.strftime('%Y-%m-%d')})"