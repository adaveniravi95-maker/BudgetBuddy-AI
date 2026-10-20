import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Expense, ImportedTransactionIdentity, Income


class UPITransactionImportTests(APITestCase):
    url = '/api/transactions/import/'
    header = 'Date,Description,Amount,Type,UPI Reference,Status\n'

    def setUp(self):
        self.user = User.objects.create_user(
            username='upi_review_user',
            email='upi-review@example.com',
            password='Password123!',
        )
        self.other_user = User.objects.create_user(
            username='upi_other_user',
            email='upi-other@example.com',
            password='Password123!',
        )
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def upload_bytes(self, contents, url=None, filename='statement.csv', decisions=None):
        data = {
            'file': SimpleUploadedFile(filename, contents, content_type='text/csv'),
        }
        if decisions is not None:
            data['decisions'] = json.dumps(decisions)
        return self.client.post(url or self.url, data, format='multipart')

    def upload(self, csv_text, url=None, decisions=None, filename='statement.csv'):
        return self.upload_bytes(
            csv_text.encode('utf-8'),
            url=url,
            filename=filename,
            decisions=decisions,
        )

    def test_food_shopping_and_travel_are_categorized_and_dashboard_updates(self):
        response = self.upload(
            self.header
            + '2026-10-01,Paid to LAALUS CAFE AND FOOD COURT,250,Debit,food-ref,Completed\n'
            + '02/10/2026,Flipkart order,800,DEBIT,shop-ref,Success\n'
            + '03/10/2026,Metro travel card,100,DR,travel-ref,Paid\n'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 3)
        categories = {
            expense.upi_reference: expense.category
            for expense in Expense.objects.filter(user=self.user)
        }
        self.assertEqual(categories, {
            'food-ref': 'Food',
            'shop-ref': 'Shopping',
            'travel-ref': 'Travel',
        })
        summary = self.client.get('/api/dashboard/summary/')
        self.assertEqual(summary.data['total_expenses'], '1150.00')
        expense_api = self.client.get('/api/expenses/')
        self.assertEqual(len(expense_api.data), 3)

    def test_salary_and_scholarship_credit_are_saved_as_incomes(self):
        response = self.upload(
            self.header
            + '2026-10-01,Monthly Salary,50000,Credit,salary-ref,Completed\n'
            + '2026-10-02,College Scholarship,10000,CR,scholarship-ref,Success\n'
        )

        self.assertEqual(response.data['imported_count'], 2)
        self.assertEqual(Income.objects.filter(user=self.user).count(), 2)
        self.assertEqual(
            set(Income.objects.filter(user=self.user).values_list('source', flat=True)),
            {'Salary', 'Scholarship'},
        )
        self.assertEqual(Expense.objects.count(), 0)

    def test_refund_friend_transfer_own_transfer_and_unknown_are_held_for_review(self):
        response = self.upload(
            self.header
            + '2026-10-01,Swiggy refund,250,Credit,refund-ref,Completed\n'
            + '2026-10-02,Sent to my own account,300,Debit,self-ref,Completed\n'
            + '2026-10-03,Paid to Rohan,400,Debit,friend-ref,Completed\n'
            + '2026-10-04,Unknown merchant code ZX-92,50,Debit,unknown-ref,Completed\n'
            + '2026-10-05,Received from account transfer,700,Credit,transfer-ref,Completed\n'
        )

        self.assertEqual(response.data['imported_count'], 0)
        self.assertEqual(response.data['skipped_count'], 5)
        self.assertEqual(Expense.objects.count(), 0)
        self.assertEqual(Income.objects.count(), 0)
        rows = {
            item['row']: item
            for item in self.client.post(
                f'{self.url}?preview=true',
                {
                    'file': SimpleUploadedFile(
                        'preview.csv',
                        (
                            self.header
                            + '2026-10-01,Swiggy refund,250,Credit,refund-ref,Completed\n'
                            + '2026-10-02,Sent to my own account,300,Debit,self-ref,Completed\n'
                            + '2026-10-03,Paid to Rohan,400,Debit,friend-ref,Completed\n'
                            + '2026-10-04,Unknown merchant code ZX-92,50,Debit,unknown-ref,Completed\n'
                            + '2026-10-05,Received from account transfer,700,Credit,transfer-ref,Completed\n'
                        ).encode(),
                        content_type='text/csv',
                    ),
                },
                format='multipart',
            ).data['transactions']
        }
        self.assertEqual(rows[2]['transaction_type'], 'refund')
        self.assertEqual(rows[3]['transaction_type'], 'transfer')
        self.assertEqual(rows[4]['transaction_type'], 'needs_review')
        self.assertEqual(rows[5]['transaction_type'], 'needs_review')
        self.assertIsNone(rows[5]['category'])
        self.assertEqual(rows[6]['transaction_type'], 'transfer')

    def test_user_can_confirm_unknown_expense_as_uncategorized(self):
        decisions = {
            '2': {
                'transaction_type': 'expense',
                'category': 'Uncategorized',
                'income_source': None,
            },
        }
        response = self.upload(
            self.header + '2026-10-01,Unknown merchant,25,Debit,review-ref,Completed\n',
            decisions=decisions,
        )

        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(
            Expense.objects.get(user=self.user).category,
            'Uncategorized',
        )

    def test_refunds_are_not_income_without_user_override(self):
        response = self.upload(
            self.header + '2026-10-01,Refund from Zomato,250,Credit,refund-ref,Completed\n',
        )

        self.assertEqual(response.data['imported_count'], 0)
        self.assertEqual(response.data['skipped_count'], 1)
        self.assertEqual(Income.objects.count(), 0)

    def test_cp1252_legacy_phonepe_statement_imports_with_detected_encoding(self):
        csv_text = (
            'Transaction Date,Narration,Amount,Type,UPI Reference ID,Status\n'
            '16/10/2026 18:30:00,Paid to Laálus Café Food Court,250,DEBIT,phonepe-1,Completed\n'
        )
        response = self.upload_bytes(csv_text.encode('cp1252'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 1)
        expense = Expense.objects.get(user=self.user)
        self.assertEqual(expense.category, 'Food')
        self.assertEqual(expense.upi_reference, 'phonepe-1')

    def test_utf16_le_and_be_csv_without_bom_are_supported(self):
        for encoding in ('utf-16-le', 'utf-16-be'):
            with self.subTest(encoding=encoding):
                csv_text = (
                    'Transaction Date;Merchant;Debit Amount;Credit Amount;UTR;Status\n'
                    f'16-10-2026 19:00;Uber ride;120;0;{encoding}-ref;Success\n'
                )
                response = self.upload_bytes(csv_text.encode(encoding))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 2)
        self.assertEqual(
            set(Expense.objects.filter(user=self.user).values_list('category', flat=True)),
            {'Travel'},
        )

    def test_utf8_bom_and_failed_status_are_handled(self):
        contents = (
            '\ufeffDate,Description,Amount,Type,Reference,Transaction Status\n'
            '2026-10-01,Amazon order,100,Debit,success-ref,Completed\n'
            '2026-10-02,Amazon order,200,Debit,failed-ref,Failed\n'
            '2026-10-03,Amazon order,300,Debit,pending-ref,Pending\n'
        ).encode('utf-8')
        response = self.upload_bytes(contents)

        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(response.data['skipped_count'], 2)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_malformed_rows_are_reported_while_valid_rows_import(self):
        response = self.upload(
            self.header
            + '2026-10-01,Swiggy order,20,Debit,valid-ref,Completed\n'
            + 'not-a-date,Amazon order,25,Debit,bad-ref,Completed\n'
            + '2026-10-03,Amazon order,not-money,Debit,bad-amount,Completed\n'
        )

        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(response.data['failed_count'], 2)
        self.assertEqual(len(response.data['errors']), 2)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_directionless_amount_is_not_guessed_and_columns_are_validated(self):
        directionless = self.upload(
            'Date,Description,Amount,UPI Reference\n'
            '2026-10-01,Unknown transfer,50,ref-1\n'
        )
        self.assertEqual(directionless.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Type', directionless.data['detail'])

        missing = self.upload('Date,Amount,Type\n2026-10-01,50,Debit\n')
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Description', missing.data['detail'])

        unclear_type = self.upload(
            'Date,Description,Amount,Type,UPI Reference\n'
            '2026-10-01,Incoming payment,50,Other,unclear-type-ref\n',
            url=f'{self.url}?preview=true',
        )
        self.assertEqual(unclear_type.status_code, status.HTTP_200_OK)
        self.assertEqual(unclear_type.data['transactions'][0]['transaction_type'], 'needs_review')
        self.assertEqual(Income.objects.count(), 0)

    def test_repeated_reference_and_reference_free_rows_are_idempotent(self):
        with_reference = self.header + '2026-10-01,Amazon order,100,Debit,repeat-ref,Success\n'
        first = self.upload(with_reference)
        second = self.upload(with_reference)
        self.assertEqual(first.data['imported_count'], 1)
        self.assertEqual(second.data['duplicate_count'], 1)

        no_reference = (
            'Date,Description,Amount,Type\n'
            '2026-10-02,Uber ride,50,Debit\n'
        )
        third = self.upload(no_reference)
        fourth = self.upload(no_reference)
        self.assertEqual(third.data['imported_count'], 1)
        self.assertEqual(fourth.data['duplicate_count'], 1)
        self.assertEqual(ImportedTransactionIdentity.objects.filter(user=self.user).count(), 2)

    def test_imported_transactions_and_duplicate_keys_are_user_scoped(self):
        csv_text = self.header + '2026-10-01,Amazon order,100,Debit,shared-ref,Success\n'
        self.assertEqual(self.upload(csv_text).data['imported_count'], 1)

        other_token = RefreshToken.for_user(self.other_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        response = self.upload(csv_text)

        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(Expense.objects.filter(user=self.other_user).count(), 1)
        self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

    def test_import_requires_authentication(self):
        self.client.credentials()
        response = self.upload(self.header + '2026-10-01,Uber ride,50,Debit,ref,Success\n')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unsupported_extension_and_bad_decisions_return_errors(self):
        invalid_file = self.upload(
            self.header + '2026-10-01,Uber ride,50,Debit,ref,Success\n',
            filename='statement.txt',
        )
        self.assertEqual(invalid_file.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_decision = self.upload(
            self.header + '2026-10-01,Uber ride,50,Debit,ref-2,Success\n',
            decisions={'2': {'transaction_type': [], 'category': 'Travel'}},
        )
        self.assertEqual(invalid_decision.status_code, status.HTTP_200_OK)
        self.assertEqual(invalid_decision.data['failed_count'], 1)
        self.assertEqual(Expense.objects.count(), 0)
