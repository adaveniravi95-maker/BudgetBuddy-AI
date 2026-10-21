from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class SavingsGoal(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    current_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100

    @property
    def remaining_amount(self):
        return self.target_amount - self.current_amount

    @property
    def is_completed(self):
        return self.current_amount >= self.target_amount


class SavingsTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    )

    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.goal.name} - {self.transaction_type} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.transaction_type == 'deposit':
            self.goal.current_amount += self.amount
        else:
            self.goal.current_amount -= self.amount

        if self.goal.current_amount >= self.goal.target_amount:
            self.goal.status = 'completed'
        self.goal.save()
        super().save(*args, **kwargs)
