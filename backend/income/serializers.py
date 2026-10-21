from rest_framework import serializers
from .models import IncomeCategory, Income


class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = ('id', 'name', 'description', 'icon')


class IncomeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Income
        fields = ('id', 'user', 'category', 'category_name', 'amount', 'description', 'source', 'date', 'is_recurring', 'recurring_frequency', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
