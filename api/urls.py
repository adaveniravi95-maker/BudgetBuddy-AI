from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    ExpenseViewSet, 
    IncomeViewSet, 
    BudgetViewSet, 
    SavingsGoalViewSet,
    NotificationViewSet,
    AnalyticsSummaryView,
    ExportReportView,
    UserProfileView,
    ChangePasswordView,
    RegisterView
)

router = DefaultRouter()
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'incomes', IncomeViewSet, basename='income')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'savings-goals', SavingsGoalViewSet, basename='savings-goal')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Auth Endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile & Password Management
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Analytics & Reports
    path('analytics/', AnalyticsSummaryView.as_view(), name='analytics-summary'),
    path('export-report/', ExportReportView.as_view(), name='export-report'),

    path('', include(router.urls)),
]