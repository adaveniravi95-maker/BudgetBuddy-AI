from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Profile,
    Income,
    Expense,
    Budget,
    SavingsGoal,
    Notification,
    Report,
)


# =========================
# PROFILE
# =========================

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = Profile
        fields = [
            'id',
            'username',
            'email',
            'phone',
            'date_of_birth',
            'bio',
            'role',
            'user',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'role',
            'user',
        ]


# =========================
# INCOME
# =========================

class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ['user']


# =========================
# EXPENSE
# =========================

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['user']

    def validate_category(self, value):
        valid_categories = [
            'Food',
            'Travel',
            'Shopping',
            'Education',
            'Entertainment',
            'Miscellaneous'
        ]

        if value not in valid_categories:
            raise serializers.ValidationError(
                "Invalid expense category."
            )

        return value


# =========================
# BUDGET
# =========================

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ['user']


# =========================
# SAVINGS GOAL
# =========================

class SavingsGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsGoal
        fields = '__all__'
        read_only_fields = ['user', 'status']

    def validate_target_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Target amount must be greater than zero."
            )

        return value

    def validate_current_amount(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Current amount cannot be negative."
            )

        if self.instance:

            if value > self.instance.target_amount:
                raise serializers.ValidationError(
                    "Current amount cannot exceed target amount."
                )

        return value


# =========================
# NOTIFICATION
# =========================

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification

        fields = [
            'id',
            'user',
            'notification_type',
            'title',
            'message',
            'related_id',
            'is_read',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'user',
            'notification_type',
            'title',
            'message',
            'related_id',
            'created_at',
        ]


# =========================
# REPORT
# =========================

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['user']


# =========================
# REGISTER
# =========================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password'
        ]

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        return user