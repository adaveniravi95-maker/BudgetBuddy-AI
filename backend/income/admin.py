from django.contrib import admin
from .models import IncomeCategory, Income


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'description', 'date', 'is_recurring')
    list_filter = ('category', 'is_recurring', 'date')
    search_fields = ('description', 'source')
