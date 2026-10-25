from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'title', 'start_date', 'end_date', 'format', 'generated_at')
    list_filter = ('report_type', 'format', 'generated_at')
    search_fields = ('title',)
