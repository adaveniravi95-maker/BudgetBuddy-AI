from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Expense, Income


class UPITransactionImportTests(APITestCase):
    url = '/api/transactions/import/'

    def setUp(self):
        self.user = User.objects.create_user(
            username='upi_user',
            email='upi@example.com',
            password='Password123!',
        )
        self.other_user = User.objects.create_user(
            username='other_upi_user',
            email='other-upi@example.com',
            password='Password123!',
        )
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def upload(self, csv_text, url=None):
        return self.client.post(
            url or self.url,
            {
                'file': SimpleUploadedFile(
                    'transactions.csv',
                    csv_text.encode('utf-8'),
                    content_type='text/csv',
                ),
            },
            format='multipart',
        )

    def test_import_creates_income_and_categorized_expenses_for_logged_in_user(self):
        response = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Monthly stipend,12000.00,Credit,upi-credit-1\n'
            '02/10/2026,Swiggy dinner,450.50,Debit,upi-debit-1\n'
            '2026-10-03,Unknown transfer,10,Debit,upi-debit-2\n'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 3)
        self.assertEqual(Income.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 2)
        income = Income.objects.get(user=self.user)
        self.assertEqual(income.source, 'Other')
        self.assertEqual(income.amount, Decimal('12000.00'))
        self.assertEqual(income.date, date(2026, 10, 1))
        self.assertEqual(income.upi_reference, 'upi-credit-1')
        self.assertEqual(
            Expense.objects.get(description='Swiggy dinner').category,
            'Food',
        )
        self.assertEqual(
            Expense.objects.get(description='Unknown transfer').category,
            'Miscellaneous',
        )
        self.assertEqual(Income.objects.filter(user=self.other_user).count(), 0)
        self.assertEqual(Expense.objects.filter(user=self.other_user).count(), 0)
        summary = self.client.get('/api/dashboard/summary/')
        self.assertEqual(summary.data['total_income'], '12000.00')
        self.assertEqual(summary.data['total_expenses'], '460.50')
        self.assertEqual(summary.data['remaining_amount'], '11539.50')
        self.assertEqual(len(summary.data['recent_transactions']), 3)
        self.assertEqual(
            summary.data['recent_transactions'][-1]['upi_reference'],
            'upi-credit-1',
        )

    def test_preview_does_not_create_transactions_and_reports_categories(self):
        response = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Uber ride,120,Debit,ref-1\n'
            '2026-10-02,Course fee,2000,Debit,ref-2\n',
            f'{self.url}?preview=true',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['transactions']), 2)
        self.assertEqual(response.data['transactions'][0]['category'], 'Travel')
        self.assertEqual(response.data['transactions'][1]['category'], 'Education')
        self.assertFalse(response.data['transactions'][0]['duplicate'])
        self.assertEqual(Income.objects.count(), 0)
        self.assertEqual(Expense.objects.count(), 0)

    def test_reimport_skips_existing_references_and_duplicate_rows(self):
        csv_text = (
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Amazon order,500,Debit,ref-duplicate\n'
            '2026-10-01,Amazon order,500,Debit,ref-duplicate\n'
        )
        first = self.upload(csv_text)
        second = self.upload(csv_text)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data['imported_count'], 1)
        self.assertEqual(first.data['duplicate_count'], 1)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data['imported_count'], 0)
        self.assertEqual(second.data['duplicate_count'], 2)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_invalid_rows_prevent_partial_import(self):
        response = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Valid income,100,Credit,ref-valid\n'
            'not-a-date,Invalid expense,10,Debit,ref-invalid\n'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertEqual(Income.objects.count(), 0)
        self.assertEqual(Expense.objects.count(), 0)

    def test_missing_required_columns_are_rejected(self):
        response = self.upload('Date,Description,Amount\n2026-10-01,Lunch,10\n')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Type', response.data['detail'])
        self.assertIn('Upi Reference', response.data['detail'])

    def test_phonepe_upi_reference_id_column_is_recognized(self):
        response = self.upload(
            'Transaction Date,Transaction Details,Amount,Type,UPI Reference ID\n'
            '2026-10-01,Swiggy order,250,DEBIT,phonepe-reference-1\n'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 1)
        expense = Expense.objects.get(user=self.user)
        self.assertEqual(expense.upi_reference, 'phonepe-reference-1')
        self.assertEqual(expense.category, 'Food')

    def test_import_requires_authentication(self):
        self.client.credentials()
        response = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Lunch,10,Debit,ref-unauth\n'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reference_deduplication_is_scoped_to_user(self):
        csv_text = (
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Amazon order,500,Debit,shared-reference\n'
        )
        self.assertEqual(self.upload(csv_text).status_code, status.HTTP_200_OK)
        token = RefreshToken.for_user(self.other_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.upload(csv_text)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(Expense.objects.filter(user=self.other_user).count(), 1)

    def test_expense_category_heuristics_cover_every_supported_category(self):
        self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Swiggy order,10,Debit,food-ref\n'
            '2026-10-02,Uber ride,10,Debit,travel-ref\n'
            '2026-10-03,Amazon order,10,Debit,shopping-ref\n'
            '2026-10-04,College tuition,10,Debit,education-ref\n'
            '2026-10-05,Netflix subscription,10,Debit,entertainment-ref\n'
            '2026-10-06,Scholarship transfer,10,Debit,misc-ref\n'
        )

        categories = {
            expense.upi_reference: expense.category
            for expense in Expense.objects.filter(user=self.user)
        }
        self.assertEqual(categories, {
            'food-ref': 'Food',
            'travel-ref': 'Travel',
            'shopping-ref': 'Shopping',
            'education-ref': 'Education',
            'entertainment-ref': 'Entertainment',
            'misc-ref': 'Miscellaneous',
        })

    def test_import_skips_a_matching_transaction_created_manually(self):
        Expense.objects.create(
            user=self.user,
            category='Shopping',
            description='Amazon order',
            amount='500.00',
            date=date(2026, 10, 1),
        )
        response = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Amazon order,500,Debit,manual-existing-reference\n'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 0)
        self.assertEqual(response.data['duplicate_count'], 1)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)
