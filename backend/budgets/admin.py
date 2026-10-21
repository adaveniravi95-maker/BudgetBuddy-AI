from django.contrib import admin
from .models import Budget, CategoryBudget


class CategoryBudgetInline(admin.TabularInline):
    model = CategoryBudget
    extra = 1


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'total_amount', 'month', 'year', 'is_active')
    list_filter = ('month', 'year', 'is_active')
    inlines = [CategoryBudgetInline]


@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'allocated_amount')
