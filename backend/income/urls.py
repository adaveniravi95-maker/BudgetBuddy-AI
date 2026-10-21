from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.IncomeCategoryListView.as_view(), name='income_category_list'),
    path('', views.IncomeListView.as_view(), name='income_list'),
    path('<int:pk>/', views.IncomeDetailView.as_view(), name='income_detail'),
]
