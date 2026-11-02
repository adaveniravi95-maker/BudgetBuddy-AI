from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed

from .models import Expense, Profile, Income, Budget, SavingsGoal, Notification, Report


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Allows login via:
    1. Exact username
    2. Case-insensitive username (e.g. 'ravi1' or 'Ravi1')
    3. User email address
    """
    def validate(self, attrs):
        username_or_email = attrs.get('username', '').strip()
        password = attrs.get('password', '')

        user = User.objects.filter(username__iexact=username_or_email).first()
        if not user:
            user = User.objects.filter(email__iexact=username_or_email).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise AuthenticationFailed("User account is disabled.")
            attrs['username'] = user.username
            return super().validate(attrs)

        return super().validate(attrs)


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        read_only=True,
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    email = serializers.EmailField(required=False, allow_blank=False)
    phone = serializers.CharField(
        source='profile.phone',
        max_length=15,
        required=False,
        allow_blank=True,
    )
    college = serializers.CharField(
        source='profile.college',
        max_length=150,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'college')
        read_only_fields = ('id', 'username', 'role')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        profile = instance.profile
        for field, value in profile_data.items():
            setattr(profile, field, value)
        if profile_data:
            profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                'current_password': 'Current password is incorrect.',
            })
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from the current password.',
            })
        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({'new_password': error.messages}) from error
        return attrs

class ExpenseSerializer(serializers.ModelSerializer):
    category = serializers.ChoiceField(choices=Expense.CATEGORY_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Expense
        fields = ('id', 'category', 'description', 'amount', 'date', 'upi_reference')
        read_only_fields = ('id', 'upi_reference')



class IncomeSerializer(serializers.ModelSerializer):
    source = serializers.ChoiceField(choices=Income.SOURCE_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Income
        fields = ('id', 'source', 'description', 'amount', 'date', 'upi_reference')
        read_only_fields = ('id', 'upi_reference')



class BudgetSerializer(serializers.ModelSerializer):
    category = serializers.ChoiceField(choices=Expense.CATEGORY_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

    class Meta:
        model = Budget
        fields = ('id', 'category', 'amount', 'month')
        read_only_fields = ('id',)



class SavingsGoalSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, min_length=1, allow_blank=False)
    target_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    current_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), default=Decimal('0.00'), required=False)
    progress_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = SavingsGoal
        fields = (
            'id',
            'name',
            'target_amount',
            'current_amount',
            'target_date',
            'progress_percentage',
            'is_completed',
            'remaining_amount',
        )
        read_only_fields = ('id', 'progress_percentage', 'is_completed', 'remaining_amount')

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Goal name cannot be empty.")
        return value.strip()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'related_context',
        )
        read_only_fields = ('id', 'created_at')


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'id',
            'title',
            'report_type',
            'month',
            'data',
            'generated_at',
        )
        read_only_fields = ('id', 'generated_at')