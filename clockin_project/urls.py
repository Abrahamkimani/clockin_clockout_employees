"""
URL configuration for clockin_project project.
Mental Health Wellness Center Employee Tracking System API
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# API version prefix
API_VERSION = 'v1'

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path(f'api/{API_VERSION}/auth/', include('authentication.urls')),
    path(f'api/{API_VERSION}/clients/', include('clients.urls')),
    path(f'api/{API_VERSION}/sessions/', include('clock_sessions.urls')),
    
    # Health check endpoint
    path('health/', lambda request: JsonResponse({'status': 'healthy'})),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
