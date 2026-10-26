from django.urls import path
from .views import WorkspaceUsageView

urlpatterns = [
    path('usage/', WorkspaceUsageView.as_view(), name='workspace_usage'),
]
