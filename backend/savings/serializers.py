from rest_framework import serializers
from .models import SavingsGoal, SavingsTransaction


class SavingsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsTransaction
        fields = ('id', 'goal', 'amount', 'transaction_type', 'description', 'date', 'created_at')
        read_only_fields = ('id', 'created_at')


class SavingsGoalSerializer(serializers.ModelSerializer):
    transactions = SavingsTransactionSerializer(many=True, read_only=True)
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = SavingsGoal
        fields = ('id', 'user', 'name', 'target_amount', 'current_amount', 'deadline', 'status', 'priority', 'notes', 'transactions', 'progress_percentage', 'remaining_amount', 'is_completed', 'created_at')
        read_only_fields = ('id', 'user', 'created_at', 'current_amount')
