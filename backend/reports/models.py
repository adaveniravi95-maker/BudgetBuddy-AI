from django.db import models
from django.conf import settings


class Report(models.Model):
    REPORT_TYPES = (
        ('monthly', 'Monthly Report'),
        ('yearly', 'Yearly Report'),
        ('custom', 'Custom Report'),
    )

    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
