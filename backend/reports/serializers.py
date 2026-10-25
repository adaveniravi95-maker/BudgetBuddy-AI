from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'user', 'report_type', 'title', 'start_date', 'end_date', 'format', 'file', 'generated_at')
        read_only_fields = ('id', 'user', 'generated_at')
