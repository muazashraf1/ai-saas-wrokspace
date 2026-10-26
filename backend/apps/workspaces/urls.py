from django.urls import path
from .views import (
    WorkspaceListCreateView,
    WorkspaceDetailView,
    WorkspaceMemberListCreateView,
    WorkspaceMemberDeleteView,
)

urlpatterns = [
    # Workspaces
    path('', WorkspaceListCreateView.as_view(), name='workspace_list_create'),
    path('<int:ws>/', WorkspaceDetailView.as_view(), name='workspace_detail'),

    # Workspace Members
    path('<int:ws>/members/', WorkspaceMemberListCreateView.as_view(), name='workspace_member_list_create'),
    path('<int:ws>/members/<int:id>/', WorkspaceMemberDeleteView.as_view(), name='workspace_member_delete'),
]
