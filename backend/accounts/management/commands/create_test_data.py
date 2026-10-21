from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile
from income.models import IncomeCategory, Income
from expenses.models import ExpenseCategory, Expense
from budgets.models import Budget, CategoryBudget
from savings.models import SavingsGoal, SavingsTransaction
from notifications.models import Notification
from datetime import date, timedelta
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates initial test data for BudgetBuddy'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')

        # Create test user
        user, created = User.objects.get_or_create(
            username='teststudent',
            defaults={
                'email': 'student@budgetbuddy.com',
                'first_name': 'Test',
                'last_name': 'Student',
                'role': 'student',
                'phone_number': '+91-9876543210',
                'date_of_birth': date(2000, 5, 15),
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))

        # Create profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'monthly_income': Decimal('15000.00'),
                'currency': 'INR',
            }
        )

        # Create income categories
        pocket_money_cat, _ = IncomeCategory.objects.get_or_create(name='Pocket Money')
        scholarship_cat, _ = IncomeCategory.objects.get_or_create(name='Scholarship')
        freelance_cat, _ = IncomeCategory.objects.get_or_create(name='Freelance')

        # Create incomes
        Income.objects.get_or_create(
            user=user,
            description='Monthly Pocket Money',
            defaults={
                'category': pocket_money_cat,
                'amount': Decimal('5000.00'),
                'source': 'Parents',
                'date': date.today().replace(day=1),
                'is_recurring': True,
                'recurring_frequency': 'monthly',
            }
        )
        Income.objects.get_or_create(
            user=user,
            description='Semester Scholarship',
            defaults={
                'category': scholarship_cat,
                'amount': Decimal('10000.00'),
                'source': 'University',
                'date': date.today() - timedelta(days=15),
            }
        )

        # Create expense categories
        food_cat, _ = ExpenseCategory.objects.get_or_create(name='Food', defaults={'color': '#FF6B6B'})
        travel_cat, _ = ExpenseCategory.objects.get_or_create(name='Travel', defaults={'color': '#4ECDC4'})
        education_cat, _ = ExpenseCategory.objects.get_or_create(name='Education', defaults={'color': '#45B7D1'})
        entertainment_cat, _ = ExpenseCategory.objects.get_or_create(name='Entertainment', defaults={'color': '#96CEB4'})
        shopping_cat, _ = ExpenseCategory.objects.get_or_create(name='Shopping', defaults={'color': '#FFEAA7'})
        misc_cat, _ = ExpenseCategory.objects.get_or_create(name='Miscellaneous', defaults={'color': '#DFE6E9'})

        # Create expenses
        Expense.objects.get_or_create(
            user=user,
            description='Lunch at cafeteria',
            defaults={
                'category': food_cat,
                'amount': Decimal('150.00'),
                'date': date.today(),
                'payment_method': 'upi',
            }
        )
        Expense.objects.get_or_create(
            user=user,
            description='Bus pass',
            defaults={
                'category': travel_cat,
                'amount': Decimal('500.00'),
                'date': date.today() - timedelta(days=5),
                'payment_method': 'cash',
            }
        )
        Expense.objects.get_or_create(
            user=user,
            description='Course materials',
            defaults={
                'category': education_cat,
                'amount': Decimal('800.00'),
                'date': date.today() - timedelta(days=10),
                'payment_method': 'card',
            }
        )
        Expense.objects.get_or_create(
            user=user,
            description='Movie tickets',
            defaults={
                'category': entertainment_cat,
                'amount': Decimal('300.00'),
                'date': date.today() - timedelta(days=3),
                'payment_method': 'upi',
            }
        )

        # Create budget
        budget, created = Budget.objects.get_or_create(
            user=user,
            month=date.today().month,
            year=date.today().year,
            defaults={
                'name': 'Monthly Budget',
                'total_amount': Decimal('12000.00'),
                'is_active': True,
            }
        )

        # Create category budgets
        if created:
            CategoryBudget.objects.get_or_create(
                budget=budget,
                category=food_cat,
                defaults={'allocated_amount': Decimal('4000.00')}
            )
            CategoryBudget.objects.get_or_create(
                budget=budget,
                category=travel_cat,
                defaults={'allocated_amount': Decimal('2000.00')}
            )
            CategoryBudget.objects.get_or_create(
                budget=budget,
                category=education_cat,
                defaults={'allocated_amount': Decimal('3000.00')}
            )
            CategoryBudget.objects.get_or_create(
                budget=budget,
                category=entertainment_cat,
                defaults={'allocated_amount': Decimal('2000.00')}
            )
            CategoryBudget.objects.get_or_create(
                budget=budget,
                category=shopping_cat,
                defaults={'allocated_amount': Decimal('1000.00')}
            )

        # Create savings goal
        goal, created = SavingsGoal.objects.get_or_create(
            user=user,
            name='New Laptop Fund',
            defaults={
                'target_amount': Decimal('60000.00'),
                'current_amount': Decimal('15000.00'),
                'deadline': date.today() + timedelta(days=180),
                'status': 'active',
                'priority': 1,
                'notes': 'Saving for a new laptop for programming',
            }
        )

        # Create savings transaction
        if created:
            SavingsTransaction.objects.get_or_create(
                goal=goal,
                amount=Decimal('5000.00'),
                transaction_type='deposit',
                date=date.today() - timedelta(days=30),
                defaults={'description': 'Monthly savings'}
            )

        # Create notification
        Notification.objects.get_or_create(
            user=user,
            notification_type='budget_alert',
            title='Budget Alert',
            defaults={
                'message': 'You have spent 75% of your food budget this month.',
                'is_read': False,
            }
        )

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
