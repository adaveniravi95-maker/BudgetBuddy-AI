from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class IncomeCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = 'Income Categories'

    def __str__(self):
        return self.name


class Income(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incomes')
    category = models.ForeignKey(IncomeCategory, on_delete=models.SET_NULL, null=True, related_name='incomes')
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.CharField(max_length=255)
    source = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(
        max_length=20,
        choices=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.description} - {self.amount}"
