from rest_framework import generics, permissions
from .models import SavingsGoal, SavingsTransaction
from .serializers import SavingsGoalSerializer, SavingsTransactionSerializer


class SavingsGoalListView(generics.ListCreateAPIView):
    serializer_class = SavingsGoalSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavingsGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavingsGoalSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SavingsGoal.objects.filter(user=self.request.user)


class SavingsTransactionListView(generics.ListCreateAPIView):
    serializer_class = SavingsTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SavingsTransaction.objects.filter(goal__user=self.request.user)
