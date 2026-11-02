
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "message": "BudgetBuddy backend is working!"})

urlpatterns = [
    path('', health_check, name='health-check'),
    path('api/health/', health_check, name='api-health'),

    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/income/', include('income.urls')),
    path('api/expenses/', include('expenses.urls')),
    path('api/budgets/', include('budgets.urls')),
    path('api/savings/', include('savings.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
