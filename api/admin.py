from django.contrib import admin
from .models import Expense, Income, Budget, CategoryBudget

# Register models in Django Admin
admin.site.register(Expense)
admin.site.register(Income)
admin.site.register(Budget)
admin.site.register(CategoryBudget)