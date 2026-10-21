from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ('id', 'name', 'description', 'icon', 'color')


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = ('id', 'user', 'category', 'category_name', 'amount', 'description', 'date', 'payment_method', 'receipt_image', 'notes', 'is_recurring', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
