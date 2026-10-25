from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'description', 'date', 'payment_method')
    list_filter = ('category', 'payment_method', 'date')
    search_fields = ('description', 'notes')
