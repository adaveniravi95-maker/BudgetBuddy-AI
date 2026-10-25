from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test users for authentication testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users...')

        # User 1 - Student
        user1, created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@budgetbuddy.com',
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'role': 'student',
                'phone_number': '+91-9876543210',
            }
        )
        if created:
            user1.set_password('Student123!')
            user1.save()
            Profile.objects.get_or_create(user=user1, defaults={'monthly_income': Decimal('15000.00')})
            self.stdout.write(self.style.SUCCESS(f'Created student1 (password: Student123!)'))

        # User 2 - Student
        user2, created = User.objects.get_or_create(
            username='student2',
            defaults={
                'email': 'student2@budgetbuddy.com',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'role': 'student',
                'phone_number': '+91-9876543211',
            }
        )
        if created:
            user2.set_password('Student456!')
            user2.save()
            Profile.objects.get_or_create(user=user2, defaults={'monthly_income': Decimal('12000.00')})
            self.stdout.write(self.style.SUCCESS(f'Created student2 (password: Student456!)'))

        # User 3 - Premium
        user3, created = User.objects.get_or_create(
            username='premium1',
            defaults={
                'email': 'premium1@budgetbuddy.com',
                'first_name': 'Amit',
                'last_name': 'Kumar',
                'role': 'premium',
                'phone_number': '+91-9876543212',
            }
        )
        if created:
            user3.set_password('Premium123!')
            user3.save()
            Profile.objects.get_or_create(user=user3, defaults={'monthly_income': Decimal('50000.00')})
            self.stdout.write(self.style.SUCCESS(f'Created premium1 (password: Premium123!)'))

        self.stdout.write(self.style.SUCCESS('\nTest users created successfully!'))
