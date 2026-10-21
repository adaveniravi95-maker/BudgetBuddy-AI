
from datetime import date

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Income, Expense, SavingsGoal


class AnalyticsAPITest(APITestCase):

    def setUp(self):

        # =====================================================
        # CREATE TEST USERS
        # =====================================================

        self.user1 = User.objects.create_user(
            username="analytics_user1",
            password="TestPass123!"
        )

        self.user2 = User.objects.create_user(
            username="analytics_user2",
            password="TestPass123!"
        )

        # =====================================================
        # USER 1 INCOME
        # =====================================================

        Income.objects.create(
            user=self.user1,
            source="Salary",
            amount=5000,
            date=date(2026, 8, 10),
            description="August salary"
        )

        Income.objects.create(
            user=self.user1,
            source="Freelance",
            amount=2000,
            date=date(2026, 9, 10),
            description="September freelance"
        )

        # =====================================================
        # USER 1 EXPENSES
        # =====================================================

        Expense.objects.create(
            user=self.user1,
            category="Food",
            amount=1000,
            date=date(2026, 9, 5),
            description="Groceries"
        )

        Expense.objects.create(
            user=self.user1,
            category="Food",
            amount=500,
            date=date(2026, 9, 15),
            description="Lunch"
        )

        Expense.objects.create(
            user=self.user1,
            category="Travel",
            amount=300,
            date=date(2026, 9, 20),
            description="Bus travel"
        )

        Expense.objects.create(
            user=self.user1,
            category="Education",
            amount=200,
            date=date(2026, 8, 15),
            description="Books"
        )

        # =====================================================
        # USER 2 DATA
        # =====================================================

        Income.objects.create(
            user=self.user2,
            source="Salary",
            amount=10000,
            date=date(2026, 9, 10),
            description="Other user income"
        )

        Expense.objects.create(
            user=self.user2,
            category="Shopping",
            amount=9000,
            date=date(2026, 9, 10),
            description="Other user expense"
        )

        # =====================================================
        # SAVINGS GOAL
        # =====================================================

        SavingsGoal.objects.create(
            user=self.user1,
            name="Laptop",
            target_amount=50000,
            current_amount=20000,
            target_date=date(2027, 6, 30),
            status="active"
        )

        # =====================================================
        # LOGIN USER 1
        # =====================================================

        self.client.force_authenticate(
            user=self.user1
        )

    # =========================================================
    # TEST 1: ANALYTICS SUCCESS
    # =========================================================

    def test_analytics_success(self):

        response = self.client.get(
            "/api/analytics/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertTrue(
            response.data["success"]
        )

    # =========================================================
    # TEST 2: TOTAL INCOME
    # =========================================================

    def test_total_income(self):

        response = self.client.get(
            "/api/analytics/"
        )

        self.assertEqual(
            response.data["summary"]["total_income"],
            7000.0
        )

    # =========================================================
    # TEST 3: TOTAL EXPENSES
    # =========================================================

    def test_total_expenses(self):

        response = self.client.get(
            "/api/analytics/"
        )

        self.assertEqual(
            response.data["summary"]["total_expenses"],
            2000.0
        )

    # =========================================================
    # TEST 4: BALANCE
    # =========================================================

    def test_balance(self):

        response = self.client.get(
            "/api/analytics/"
        )

        self.assertEqual(
            response.data["summary"]["balance"],
            5000.0
        )

    # =========================================================
    # TEST 5: CATEGORY-WISE EXPENSES
    # =========================================================

    def test_category_wise_expenses(self):

        response = self.client.get(
            "/api/analytics/"
        )

        categories = response.data[
            "category_wise_expenses"
        ]

        category_data = {
            item["category"]: item["amount"]
            for item in categories
        }

        self.assertEqual(
            category_data["Food"],
            1500.0
        )

        self.assertEqual(
            category_data["Travel"],
            300.0
        )

        self.assertEqual(
            category_data["Education"],
            200.0
        )

    # =========================================================
    # TEST 6: MONTHLY TRENDS
    # =========================================================

    def test_monthly_trends(self):

        response = self.client.get(
            "/api/analytics/"
        )

        trends = response.data[
            "monthly_trends"
        ]

        self.assertEqual(
            len(trends),
            2
        )

        # -------------------------
        # AUGUST
        # -------------------------

        august = trends[0]

        self.assertEqual(
            august["month"],
            "2026-08"
        )

        self.assertEqual(
            august["income"],
            5000.0
        )

        self.assertEqual(
            august["expense"],
            200.0
        )

        self.assertEqual(
            august["balance"],
            4800.0
        )

        # -------------------------
        # SEPTEMBER
        # -------------------------

        september = trends[1]

        self.assertEqual(
            september["month"],
            "2026-09"
        )

        self.assertEqual(
            september["income"],
            2000.0
        )

        self.assertEqual(
            september["expense"],
            1800.0
        )

        self.assertEqual(
            september["balance"],
            200.0
        )

    # =========================================================
    # TEST 7: MONTH FILTER
    # =========================================================

    def test_month_filter(self):

        response = self.client.get(
            "/api/analytics/?month=2026-09"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["summary"]["total_income"],
            2000.0
        )

        self.assertEqual(
            response.data["summary"]["total_expenses"],
            1800.0
        )

    # =========================================================
    # TEST 8: INVALID MONTH
    # =========================================================

    def test_invalid_month(self):

        response = self.client.get(
            "/api/analytics/?month=2026-13"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertFalse(
            response.data["success"]
        )

    # =========================================================
    # TEST 9: INVALID DATE
    # =========================================================

    def test_invalid_date(self):

        response = self.client.get(
            "/api/analytics/?start_date=2026-02-30"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertFalse(
            response.data["success"]
        )

    # =========================================================
    # TEST 10: INVALID DATE RANGE
    # =========================================================

    def test_invalid_date_range(self):

        response = self.client.get(
            "/api/analytics/"
            "?start_date=2026-09-30"
            "&end_date=2026-09-01"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertFalse(
            response.data["success"]
        )

    # =========================================================
    # TEST 11: USER DATA ISOLATION
    # =========================================================

    def test_user_data_isolation(self):

        response = self.client.get(
            "/api/analytics/"
        )

        self.assertEqual(
            response.data["summary"]["total_income"],
            7000.0
        )

        self.assertEqual(
            response.data["summary"]["total_expenses"],
            2000.0
        )

        categories = response.data[
            "category_wise_expenses"
        ]

        category_data = {
            item["category"]: item["amount"]
            for item in categories
        }

        # User 2 has ₹9000 Shopping expense.
        # It must NOT be included in User 1 analytics.

        self.assertEqual(
            category_data["Shopping"],
            0.0
        )

    # =========================================================
    # TEST 12: SAVINGS SUMMARY
    # =========================================================

    def test_savings_summary(self):

        response = self.client.get(
            "/api/analytics/"
        )

        savings = response.data[
            "savings_summary"
        ]

        self.assertEqual(
            savings["total_target"],
            50000.0
        )

        self.assertEqual(
            savings["total_saved"],
            20000.0
        )

        self.assertEqual(
            savings["remaining"],
            30000.0
        )

    # =========================================================
    # TEST 13: EMPTY DATE RANGE
    # =========================================================

    def test_empty_date_range(self):

        response = self.client.get(
            "/api/analytics/"
            "?start_date=2025-01-01"
            "&end_date=2025-01-31"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["summary"]["total_income"],
            0.0
        )

        self.assertEqual(
            response.data["summary"]["total_expenses"],
            0.0
        )

        categories = response.data[
            "category_wise_expenses"
        ]

        self.assertTrue(
            all(
                item["amount"] == 0.0
                for item in categories
            )
        )

        # The current API returns the existing
        # monthly trends even when the selected
        # date range has no transactions.

        self.assertEqual(
            len(response.data["monthly_trends"]),
            2
        )
