from django.urls import path

from .views import (
    RegisterView,

    MyExpensesView,
    ExpenseCreateView,
    ExpenseDetailView,

    MyIncomeView,
    IncomeCreateView,
    IncomeDetailView,

    MyBudgetsView,
    BudgetCreateView,
    BudgetDetailView,

    MySavingsGoalsView,
    SavingsGoalCreateView,
    SavingsGoalDetailView,

    MyNotificationsView,
    MyUnreadNotificationsView,
    NotificationMarkReadView,

    MyReportsView,
    ReportCreateView,
    GenerateMonthlyReportView,
    GeneratePDFReportView,
    GenerateExcelReportView,

    ProfileView,
    ChangePasswordView,

    # Analytics
    AnalyticsView,
)


urlpatterns = [

    # =====================================================
    # REGISTER
    # =====================================================

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),

    # =====================================================
    # EXPENSES
    # =====================================================

    path(
        "my-expenses/",
        MyExpensesView.as_view(),
        name="my-expenses"
    ),

    path(
        "expenses/",
        ExpenseCreateView.as_view(),
        name="expense-create"
    ),

    path(
        "expenses/<int:pk>/",
        ExpenseDetailView.as_view(),
        name="expense-detail"
    ),

    # =====================================================
    # INCOME
    # =====================================================

    path(
        "my-income/",
        MyIncomeView.as_view(),
        name="my-income"
    ),

    path(
        "income/",
        IncomeCreateView.as_view(),
        name="income-create"
    ),

    path(
        "income/<int:pk>/",
        IncomeDetailView.as_view(),
        name="income-detail"
    ),

    # =====================================================
    # BUDGETS
    # =====================================================

    path(
        "my-budgets/",
        MyBudgetsView.as_view(),
        name="my-budgets"
    ),

    path(
        "budgets/",
        BudgetCreateView.as_view(),
        name="budget-create"
    ),

    path(
        "budgets/<int:pk>/",
        BudgetDetailView.as_view(),
        name="budget-detail"
    ),

    # =====================================================
    # SAVINGS GOALS
    # =====================================================

    path(
        "my-savings-goals/",
        MySavingsGoalsView.as_view(),
        name="my-savings-goals"
    ),

    path(
        "savings-goals/",
        SavingsGoalCreateView.as_view(),
        name="savings-goal-create"
    ),

    path(
        "savings-goals/<int:pk>/",
        SavingsGoalDetailView.as_view(),
        name="savings-goal-detail"
    ),

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    path(
        "my-notifications/",
        MyNotificationsView.as_view(),
        name="my-notifications"
    ),

    path(
        "my-notifications/unread/",
        MyUnreadNotificationsView.as_view(),
        name="my-unread-notifications"
    ),

    path(
        "notifications/<int:pk>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read"
    ),

    # =====================================================
    # REPORTS
    # =====================================================

    path(
        "my-reports/",
        MyReportsView.as_view(),
        name="my-reports"
    ),

    path(
        "reports/",
        ReportCreateView.as_view(),
        name="report-create"
    ),

    # Generate Monthly JSON Report
    path(
        "reports/generate/",
        GenerateMonthlyReportView.as_view(),
        name="generate-monthly-report"
    ),

    # Generate PDF Report
    path(
        "reports/pdf/",
        GeneratePDFReportView.as_view(),
        name="generate-pdf-report"
    ),

    # Generate Excel Report
    path(
        "reports/excel/",
        GenerateExcelReportView.as_view(),
        name="generate-excel-report"
    ),

    # =====================================================
    # PROFILE
    # =====================================================

    path(
        "profile/",
        ProfileView.as_view(),
        name="profile"
    ),

    # =====================================================
    # CHANGE PASSWORD
    # =====================================================

    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),

    # =====================================================
    # ANALYTICS
    # =====================================================

    path(
        "analytics/",
        AnalyticsView.as_view(),
        name="analytics"
    ),
]