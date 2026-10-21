from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Expense, 
    Income, 
    Budget, 
    CategoryBudget, 
    SavingsGoal,
    Notification,
    EXPENSE_CATEGORIES, 
    INCOME_SOURCES
)

# User Profile Serializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']


# Change Password Serializer
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("New password must be at least 6 characters long.")
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'category', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_category(self, value):
        valid_cats = [c[0] for c in EXPENSE_CATEGORIES]
        if value not in valid_cats:
            raise serializers.ValidationError(
                f"Invalid category '{value}'. Must be one of: {', '.join(valid_cats)}"
            )
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Expense amount must be greater than 0.")
        return value


class IncomeSerializer(serializers.ModelSerializer):
    source = serializers.CharField(required=False)
    income_type = serializers.CharField(required=False)

    class Meta:
        model = Income
        fields = ['id', 'source', 'income_type', 'amount', 'date', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        source_val = data.get('income_type') or data.get('source')
        if not source_val:
            raise serializers.ValidationError({"income_type": ["This field is required."]})
        
        valid_sources = [s[0] for s in INCOME_SOURCES]
        if source_val not in valid_sources:
            raise serializers.ValidationError(
                {"income_type": [f"Must be one of: {', '.join(valid_sources)}"]}
            )
        
        data['source'] = source_val
        data['income_type'] = source_val
        return data

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Income amount must be greater than 0.")
        return value

    def create(self, validated_data):
        model_fields = [f.name for f in Income._meta.get_fields()]
        val = validated_data.pop('income_type', None) or validated_data.pop('source', None)

        if 'income_type' in model_fields:
            validated_data['income_type'] = val
        elif 'source' in model_fields:
            validated_data['source'] = val

        clean_data = {k: v for k, v in validated_data.items() if k in model_fields}
        return Income.objects.create(**clean_data)

    def update(self, instance, validated_data):
        model_fields = [f.name for f in Income._meta.get_fields()]
        val = validated_data.pop('income_type', None) or validated_data.pop('source', None)

        if val:
            if 'income_type' in model_fields:
                validated_data['income_type'] = val
            elif 'source' in model_fields:
                validated_data['source'] = val

        clean_data = {k: v for k, v in validated_data.items() if k in model_fields}
        for attr, value in clean_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        val = getattr(instance, 'income_type', None) or getattr(instance, 'source', None)
        data['source'] = val
        data['income_type'] = val
        return data


class CategoryBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryBudget
        fields = ['id', 'category', 'allocated_amount']

    def validate_category(self, value):
        valid_cats = [c[0] for c in EXPENSE_CATEGORIES]
        if value not in valid_cats:
            raise serializers.ValidationError(f"Invalid category '{value}'.")
        return value

    def validate_allocated_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Allocated amount must be greater than 0.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    category_allocations = CategoryBudgetSerializer(many=True, required=False)

    class Meta:
        model = Budget
        fields = ['id', 'month', 'year', 'total_amount', 'category_allocations', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_month(self, value):
        if not (1 <= int(value) <= 12):
            raise serializers.ValidationError("Month must be between 1 and 12.")
        return value

    def validate_total_amount(self, value):
        if float(value) <= 0:
            raise serializers.ValidationError("Total budget must be greater than 0.")
        return value

    def create(self, validated_data):
        allocations_data = validated_data.pop('category_allocations', [])
        user = self.context['request'].user
        
        budget, _ = Budget.objects.update_or_create(
            user=user,
            month=validated_data['month'],
            year=validated_data['year'],
            defaults={'total_amount': validated_data['total_amount']}
        )
        
        budget.category_allocations.all().delete()
        for alloc in allocations_data:
            CategoryBudget.objects.create(
                budget=budget,
                category=alloc['category'],
                allocated_amount=alloc['allocated_amount']
            )

        return budget


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = ['id', 'name', 'target_amount', 'current_amount', 'is_completed', 'progress_percentage', 'created_at']
        read_only_fields = ['id', 'is_completed', 'progress_percentage', 'created_at']

    def get_progress_percentage(self, obj):
        if obj.target_amount and obj.target_amount > 0:
            percentage = (float(obj.current_amount) / float(obj.target_amount)) * 100
            return round(min(percentage, 100.0), 1)
        return 0.0

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Goal name cannot be empty.")
        return value.strip()

    def validate_target_amount(self, value):
        if float(value) <= 0:
            raise serializers.ValidationError("Target amount must be greater than 0.")
        return value

    def validate_current_amount(self, value):
        if float(value) < 0:
            raise serializers.ValidationError("Saved amount cannot be negative.")
        return value

    def create(self, validated_data):
        current = float(validated_data.get('current_amount', 0))
        target = float(validated_data.get('target_amount', 0))
        validated_data['is_completed'] = current >= target
        return super().create(validated_data)

    def update(self, instance, validated_data):
        current = float(validated_data.get('current_amount', instance.current_amount))
        target = float(validated_data.get('target_amount', instance.target_amount))
        validated_data['is_completed'] = current >= target
        return super().update(instance, validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']