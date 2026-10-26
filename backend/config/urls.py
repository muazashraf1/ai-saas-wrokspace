from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def health_check(request):
    """Health check endpoint to verify backend status."""
    return JsonResponse({
        "status": "healthy",
        "service": "AI SaaS Workspace Backend",
        "version": "1.0.0"
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health_check, name='health_check'),

    # Auth routes
    path('api/v1/auth/', include('users.urls')),

    # Workspaces & Members routes
    path('api/v1/workspaces/', include('workspaces.urls')),

    # Documents routes scoped by workspace
    path('api/v1/workspaces/<int:ws>/documents/', include('documents.urls')),

    # QA & Request History routes scoped by workspace
    path('api/v1/workspaces/<int:ws>/', include('qa.urls')),

    # Usage limits routes scoped by workspace
    path('api/v1/workspaces/<int:ws>/', include('usage.urls')),

    # OpenAPI schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
