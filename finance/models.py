from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# =========================================================
# PROFILE
# =========================================================

class Profile(models.Model):

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    bio = models.TextField(
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    def __str__(self):
        return self.user.username


# =========================================================
# INCOME
# =========================================================

class Income(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incomes'
    )

    source = models.CharField(
        max_length=100
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    date = models.DateField()

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.source} - {self.amount}"


# =========================================================
# EXPENSE
# =========================================================

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
        related_name='expenses'
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    date = models.DateField()

    description = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.category} - {self.amount}"


# =========================================================
# BUDGET
# =========================================================

class Budget(models.Model):

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
        related_name='budgets'
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    start_date = models.DateField()

    end_date = models.DateField()

    def __str__(self):
        return f"{self.category} Budget - {self.amount}"


# =========================================================
# SAVINGS GOAL
# =========================================================

class SavingsGoal(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='savings_goals'
    )

    name = models.CharField(
        max_length=100
    )

    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    target_date = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    def __str__(self):
        return self.name



# =========================================================
# NOTIFICATION
# =========================================================

class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ('budget', 'Budget Limit Alert'),
        ('savings', 'Savings Goal Milestone'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='general'
    )

    title = models.CharField(
        max_length=150
    )

    message = models.TextField()

    # Stores the ID of the related Budget or SavingsGoal
    related_id = models.IntegerField(
        null=True,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title


# =========================================================
# REPORT
# =========================================================

class Report(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports'
    )

    title = models.CharField(
        max_length=150
    )

    report_type = models.CharField(
        max_length=50
    )

    start_date = models.DateField()

    end_date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title