from django.urls import path
from . import views

urlpatterns = [
    path('goals/', views.SavingsGoalListView.as_view(), name='savings_goal_list'),
    path('goals/<int:pk>/', views.SavingsGoalDetailView.as_view(), name='savings_goal_detail'),
    path('transactions/', views.SavingsTransactionListView.as_view(), name='savings_transaction_list'),
]
