from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Workspace, WorkspaceMember
from .serializers import (
    WorkspaceSerializer,
    WorkspaceCreateSerializer,
    WorkspaceMemberSerializer,
    AddMemberSerializer,
)
from .permissions import (
    IsWorkspaceMember,
    IsWorkspaceAdminOrOwner,
    IsWorkspaceOwner,
)


class WorkspaceListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/workspaces/
    List all workspaces where the current user is a member.
    Enforces strict tenant isolation: users never see workspaces they don't belong to.

    POST /api/v1/workspaces/
    Create a new workspace. The authenticated user automatically becomes the owner.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Strict isolation: Only return workspaces where user is an active member
        return Workspace.objects.filter(
            memberships__user=self.request.user
        ).distinct().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkspaceCreateSerializer
        return WorkspaceSerializer


class WorkspaceDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/v1/workspaces/{ws}/
    Retrieve workspace details. Member only.

    DELETE /api/v1/workspaces/{ws}/
    Delete workspace and cascade chunks/documents. Owner only.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    serializer_class = WorkspaceSerializer
    lookup_url_kwarg = 'ws'

    def get_queryset(self):
        return Workspace.objects.filter(memberships__user=self.request.user).distinct()

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [permissions.IsAuthenticated(), IsWorkspaceOwner()]
        return [permissions.IsAuthenticated(), IsWorkspaceMember()]


class WorkspaceMemberListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/workspaces/{ws}/members/
    List all members in the workspace. (Any workspace member can view).

    POST /api/v1/workspaces/{ws}/members/
    Invite/add a member to the workspace by email. (Owner or Admin only).
    """
    lookup_url_kwarg = 'ws'

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsWorkspaceAdminOrOwner()]
        return [permissions.IsAuthenticated(), IsWorkspaceMember()]

    def get_workspace(self):
        ws_id = self.kwargs.get('ws')
        return get_object_or_404(
            Workspace.objects.filter(memberships__user=self.request.user),
            id=ws_id
        )

    def get_queryset(self):
        workspace = self.get_workspace()
        return WorkspaceMember.objects.filter(workspace=workspace).select_related('user').order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddMemberSerializer
        return WorkspaceMemberSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace()
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        output_serializer = WorkspaceMemberSerializer(member)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class WorkspaceMemberDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/v1/workspaces/{ws}/members/{id}/
    Remove a member from the workspace. (Owner or Admin only).
    Owners cannot be removed.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceAdminOrOwner]
    serializer_class = WorkspaceMemberSerializer
    lookup_url_kwarg = 'id'

    def get_workspace(self):
        ws_id = self.kwargs.get('ws')
        return get_object_or_404(
            Workspace.objects.filter(memberships__user=self.request.user),
            id=ws_id
        )

    def get_queryset(self):
        workspace = self.get_workspace()
        return WorkspaceMember.objects.filter(workspace=workspace)

    def destroy(self, request, *args, **kwargs):
        member = self.get_object()
        if member.role == 'owner':
            return Response(
                {"detail": "Cannot remove the workspace owner."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Prevent non-owners from removing admins
        current_membership = WorkspaceMember.objects.filter(
            workspace=member.workspace,
            user=request.user
        ).first()
        if current_membership.role == 'admin' and member.role == 'admin':
            return Response(
                {"detail": "Admins cannot remove fellow admins. Only the owner can."},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(member)
        return Response(status=status.HTTP_204_NO_CONTENT)
