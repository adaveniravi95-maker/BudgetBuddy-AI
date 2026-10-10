from django.contrib import admin
from django.urls import include, path
from core.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'api/auth/login/',
        CustomTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    path(
        'api/auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    path('api/', include('core.urls')),
]