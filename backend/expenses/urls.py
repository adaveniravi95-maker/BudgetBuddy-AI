from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.ExpenseCategoryListView.as_view(), name='expense_category_list'),
    path('', views.ExpenseListView.as_view(), name='expense_list'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
]
