from django.urls import path
from . import views

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='budget_list'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('category-budgets/', views.CategoryBudgetListView.as_view(), name='category_budget_list'),
]
