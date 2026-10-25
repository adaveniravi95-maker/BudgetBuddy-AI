from rest_framework import generics, permissions
from .models import Budget, CategoryBudget
from .serializers import BudgetSerializer, CategoryBudgetSerializer


class BudgetListView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class CategoryBudgetListView(generics.ListCreateAPIView):
    serializer_class = CategoryBudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CategoryBudget.objects.filter(budget__user=self.request.user)
