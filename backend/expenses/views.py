from rest_framework import generics, permissions
from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer


class ExpenseCategoryListView(generics.ListAPIView):
    serializer_class = ExpenseCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = ExpenseCategory.objects.all()


class ExpenseListView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)
