from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .serializers import UsageSummarySerializer
from .services import get_user_workspace_usage_summary
from workspaces.models import Workspace, WorkspaceMember
from workspaces.permissions import IsWorkspaceMember


def get_workspace_for_user(user, ws_id):
    """Ensures user is an active member of the workspace."""
    return get_object_or_404(
        Workspace.objects.filter(memberships__user=user),
        id=ws_id
    )


from drf_spectacular.utils import extend_schema


class WorkspaceUsageView(APIView):
    """
    GET /api/v1/workspaces/{ws}/usage/
    Retrieve authenticated user's usage and plan limits in the specified workspace (Section 8.1 & 8.2).
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    @extend_schema(responses={200: UsageSummarySerializer})
    def get(self, request, ws):
        workspace = get_workspace_for_user(request.user, ws)
        summary_data = get_user_workspace_usage_summary(request.user, workspace)
        membership = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).first()
        if membership and membership.is_admin_or_owner:
            summary_data['member_usage'] = []
            for member in WorkspaceMember.objects.filter(workspace=workspace).select_related('user'):
                member_summary = get_user_workspace_usage_summary(member.user, workspace)
                summary_data['member_usage'].append({
                    'user_id': member.user_id,
                    'email': member.user.email,
                    'full_name': member.user.full_name,
                    'role': member.role,
                    'daily_questions_used': member_summary['daily_questions_used'],
                    'monthly_tokens_used': member_summary['monthly_tokens_used'],
                })
        serializer = UsageSummarySerializer(summary_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
