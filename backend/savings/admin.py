from django.contrib import admin
from .models import SavingsGoal, SavingsTransaction


class SavingsTransactionInline(admin.TabularInline):
    model = SavingsTransaction
    extra = 0


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'target_amount', 'current_amount', 'status', 'deadline')
    list_filter = ('status', 'deadline')
    inlines = [SavingsTransactionInline]


@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = ('goal', 'amount', 'transaction_type', 'date')
    list_filter = ('transaction_type', 'date')
