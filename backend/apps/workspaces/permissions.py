from rest_framework import permissions
from .models import WorkspaceMember, Workspace


def get_workspace_id_from_view(view):
    """Helper to extract workspace_id from URL kwargs (either 'ws' or 'workspace_id' or 'pk')."""
    return view.kwargs.get('ws') or view.kwargs.get('workspace_id') or view.kwargs.get('pk')


class IsWorkspaceMember(permissions.BasePermission):
    """
    Ensures that the requesting user is an active member of the target workspace.
    Guarantees strict tenant data isolation at the boundary.
    """
    message = "You do not have access to this workspace."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        ws_id = get_workspace_id_from_view(view)
        if not ws_id:
            return True

        # Fast indexed check using idx_ws_member_user_ws
        return WorkspaceMember.objects.filter(
            workspace_id=ws_id,
            user_id=request.user.id
        ).exists()

    def has_object_permission(self, request, view, obj):
        # If obj is a Workspace instance
        if isinstance(obj, Workspace):
            return WorkspaceMember.objects.filter(workspace=obj, user=request.user).exists()
        # If obj has a workspace attribute (e.g. Document, AskRequest)
        if hasattr(obj, 'workspace_id'):
            return WorkspaceMember.objects.filter(workspace_id=obj.workspace_id, user=request.user).exists()
        return False


class IsWorkspaceAdminOrOwner(permissions.BasePermission):
    """
    Allows access only to Workspace Owners or Admins (e.g. inviting/removing members).
    """
    message = "You must be an Owner or Admin of this workspace to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        ws_id = get_workspace_id_from_view(view)
        if not ws_id:
            return True

        return WorkspaceMember.objects.filter(
            workspace_id=ws_id,
            user_id=request.user.id,
            role__in=['owner', 'admin']
        ).exists()

    def has_object_permission(self, request, view, obj):
        ws_id = getattr(obj, 'workspace_id', getattr(obj, 'id', None))
        return WorkspaceMember.objects.filter(
            workspace_id=ws_id,
            user_id=request.user.id,
            role__in=['owner', 'admin']
        ).exists()


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Allows access strictly to the Workspace Owner (e.g. deleting the workspace).
    """
    message = "Only the workspace owner can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        ws_id = get_workspace_id_from_view(view)
        if not ws_id:
            return True

        return WorkspaceMember.objects.filter(
            workspace_id=ws_id,
            user_id=request.user.id,
            role='owner'
        ).exists()
