from rest_framework import generics, permissions
from .models import IncomeCategory, Income
from .serializers import IncomeCategorySerializer, IncomeSerializer


class IncomeCategoryListView(generics.ListAPIView):
    serializer_class = IncomeCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = IncomeCategory.objects.all()


class IncomeListView(generics.ListCreateAPIView):
    serializer_class = IncomeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IncomeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)
