import csv
import datetime
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import Expense, Income, Budget, CategoryBudget, SavingsGoal, Notification, EXPENSE_CATEGORIES
from .serializers import (
    ExpenseSerializer, 
    IncomeSerializer, 
    BudgetSerializer,
    SavingsGoalSerializer,
    NotificationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

# Automated Notification Triggers
def check_and_create_budget_alert(user):
    budget = Budget.objects.filter(user=user).order_by('-year', '-month').first()
    if not budget or float(budget.total_amount) <= 0:
        return

    total_exp = sum(float(e.amount) for e in Expense.objects.filter(user=user))
    budget_limit = float(budget.total_amount)
    ratio = total_exp / budget_limit

    if ratio >= 1.0:
        exists = Notification.objects.filter(
            user=user,
            notification_type='BUDGET_ALERT',
            title='Budget Limit Exceeded!'
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                notification_type='BUDGET_ALERT',
                title='Budget Limit Exceeded!',
                message=f"Alert: You have crossed 100% of your budget limit (₹{total_exp:,.2f} spent of ₹{budget_limit:,.2f})."
            )
    elif ratio >= 0.8:
        exists = Notification.objects.filter(
            user=user,
            notification_type='BUDGET_ALERT',
            title='Budget Warning (80% Reached)'
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                notification_type='BUDGET_ALERT',
                title='Budget Warning (80% Reached)',
                message=f"Warning: You have reached 80% of your budget limit (₹{total_exp:,.2f} spent of ₹{budget_limit:,.2f})."
            )
    else:
        Notification.objects.filter(user=user, notification_type='BUDGET_ALERT').delete()

def check_and_create_savings_milestone(user, goal):
    if float(goal.target_amount) <= 0:
        return
    pct = (float(goal.current_amount) / float(goal.target_amount)) * 100
    if pct >= 100:
        exists = Notification.objects.filter(
            user=user,
            notification_type='SAVINGS_MILESTONE',
            title=f"Goal Achieved: {goal.name}"
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                notification_type='SAVINGS_MILESTONE',
                title=f"Goal Achieved: {goal.name}",
                message=f"Congratulations! You reached 100% of your target for '{goal.name}' (₹{float(goal.target_amount):,.2f})!"
            )
    elif pct >= 50:
        exists = Notification.objects.filter(
            user=user,
            notification_type='SAVINGS_MILESTONE',
            title=f"50% Milestone: {goal.name}"
        ).exists()
        if not exists:
            Notification.objects.create(
                user=user,
                notification_type='SAVINGS_MILESTONE',
                title=f"50% Milestone: {goal.name}",
                message=f"Great progress! You crossed the 50% halfway milestone for '{goal.name}' (₹{float(goal.current_amount):,.2f} / ₹{float(goal.target_amount):,.2f})."
            )


# User Profile & Password Change Views
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_pwd = serializer.validated_data['old_password']
            new_pwd = serializer.validated_data['new_password']

            if not user.check_password(old_pwd):
                return Response({'error': 'Incorrect current password.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_pwd)
            user.save()
            return Response({'message': 'Password updated successfully! Please login again if needed.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists. Please choose a different one.'}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(username=username, password=password, email=email)
        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user).order_by('-date', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        check_and_create_budget_alert(self.request.user)

    def perform_update(self, serializer):
        serializer.save()
        check_and_create_budget_alert(self.request.user)

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        check_and_create_budget_alert(user)


class IncomeViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user).order_by('-date', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-year', '-month')

    def create(self, request, *args, **kwargs):
        try:
            month = request.data.get('month')
            year = request.data.get('year')
            total_amount = request.data.get('total_amount')
            allocations = request.data.get('category_allocations', [])

            if not month or not year or not total_amount:
                return Response(
                    {'error': 'Month, year and total_amount are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            budget, _ = Budget.objects.update_or_create(
                user=request.user,
                month=int(month),
                year=int(year),
                defaults={'total_amount': float(total_amount)}
            )

            budget.category_allocations.all().delete()
            for alloc in allocations:
                cat = alloc.get('category')
                amt = alloc.get('allocated_amount')
                if cat and amt and float(amt) > 0:
                    CategoryBudget.objects.create(
                        budget=budget,
                        category=cat,
                        allocated_amount=float(amt)
                    )

            check_and_create_budget_alert(request.user)
            serializer = self.get_serializer(budget)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        goal = serializer.save(user=self.request.user)
        check_and_create_savings_milestone(self.request.user, goal)

    def perform_update(self, serializer):
        goal = serializer.save()
        check_and_create_savings_milestone(self.request.user, goal)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['patch', 'post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['patch', 'post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})

    @action(detail=False, methods=['delete', 'post'])
    def clear_all(self, request):
        Notification.objects.filter(user=request.user).delete()
        return Response({'status': 'all notifications cleared'})


class AnalyticsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        expenses = Expense.objects.filter(user=user)
        incomes = Income.objects.filter(user=user)
        goals = SavingsGoal.objects.filter(user=user)

        total_income = sum(float(i.amount) for i in incomes)
        total_expense = sum(float(e.amount) for e in expenses)
        net_savings = total_income - total_expense
        savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

        budget = Budget.objects.filter(user=user).order_by('-year', '-month').first()
        budget_limit = float(budget.total_amount) if budget else 0.0
        budget_utilization = round((total_expense / budget_limit * 100), 1) if budget_limit > 0 else 0.0

        return Response({
            'total_income': total_income,
            'total_expenses': total_expense,
            'net_savings': net_savings,
            'savings_rate': max(0.0, savings_rate),
            'budget_limit': budget_limit,
            'budget_utilization': budget_utilization,
            'active_savings_goals': goals.count(),
            'completed_savings_goals': goals.filter(is_completed=True).count()
        })


class ExportReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="BudgetBuddy_Financial_Report.csv"'

        writer = csv.writer(response)
        writer.writerow(['BudgetBuddy Financial Summary Report'])
        writer.writerow(['User', user.username])
        writer.writerow(['Date Generated', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])

        expenses = Expense.objects.filter(user=user)
        incomes = Income.objects.filter(user=user)
        tot_inc = sum(float(i.amount) for i in incomes)
        tot_exp = sum(float(e.amount) for e in expenses)

        writer.writerow(['METRICS', 'AMOUNT (INR)'])
        writer.writerow(['Total Income', f"{tot_inc:.2f}"])
        writer.writerow(['Total Expenses', f"{tot_exp:.2f}"])
        writer.writerow(['Net Balance', f"{(tot_inc - tot_exp):.2f}"])
        writer.writerow([])

        writer.writerow(['TRANSACTIONS LOG'])
        writer.writerow(['Date', 'Type', 'Title / Source', 'Category', 'Amount (INR)'])

        for inc in incomes.order_by('-date'):
            writer.writerow([inc.date, 'INCOME', inc.income_type or inc.source, 'Income', f"+{inc.amount}"])
        for exp in expenses.order_by('-date'):
            writer.writerow([exp.date, 'EXPENSE', exp.title, exp.category, f"-{exp.amount}"])

        return response