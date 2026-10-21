from rest_framework import serializers
from .models import Budget, CategoryBudget


class CategoryBudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = CategoryBudget
        fields = ('id', 'budget', 'category', 'category_name', 'allocated_amount', 'spent_amount', 'utilization_percentage')


class BudgetSerializer(serializers.ModelSerializer):
    category_budgets = CategoryBudgetSerializer(many=True, read_only=True)
    spent_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Budget
        fields = ('id', 'user', 'name', 'total_amount', 'month', 'year', 'is_active', 'category_budgets', 'spent_amount', 'remaining_amount', 'utilization_percentage', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
