from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    month = models.IntegerField()
    year = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.month}/{self.year})"

    @property
    def spent_amount(self):
        from expenses.models import Expense
        expenses = Expense.objects.filter(
            user=self.user,
            date__year=self.year,
            date__month=self.month
        )
        return sum(exp.amount for exp in expenses)

    @property
    def remaining_amount(self):
        return self.total_amount - self.spent_amount

    @property
    def utilization_percentage(self):
        if self.total_amount == 0:
            return 0
        return (self.spent_amount / self.total_amount) * 100


class CategoryBudget(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='category_budgets')
    category = models.ForeignKey('expenses.ExpenseCategory', on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('budget', 'category')

    def __str__(self):
        return f"{self.budget.name} - {self.category.name}"

    @property
    def spent_amount(self):
        from expenses.models import Expense
        expenses = Expense.objects.filter(
            user=self.budget.user,
            category=self.category,
            date__year=self.budget.year,
            date__month=self.budget.month
        )
        return sum(exp.amount for exp in expenses)

    @property
    def utilization_percentage(self):
        if self.allocated_amount == 0:
            return 0
        return (self.spent_amount / self.allocated_amount) * 100
