import os
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .tasks import process_document_task
from workspaces.models import Workspace, WorkspaceMember
from workspaces.permissions import IsWorkspaceMember


def get_workspace_for_user(user, ws_id):
    """Ensures user is an active member of the workspace."""
    return get_object_or_404(
        Workspace.objects.filter(memberships__user=user),
        id=ws_id
    )


class DocumentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/workspaces/{ws}/documents/
    List all documents in the workspace with their ingestion status badges.

    POST /api/v1/workspaces/{ws}/documents/
    Upload a document (PDF or TXT).
    Returns 202 Accepted with status 'uploaded' and triggers background ingestion.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    lookup_url_kwarg = 'ws'

    def get_workspace(self):
        return get_workspace_for_user(self.request.user, self.kwargs.get('ws'))

    def get_queryset(self):
        workspace = self.get_workspace()
        # Tenant isolation: strictly return documents belonging to this workspace
        return Document.objects.filter(workspace=workspace).select_related('uploaded_by').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DocumentUploadSerializer
        return DocumentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace()
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            # Check for duplicate file error code and return HTTP 409 Conflict (Section 8.3 & 8.4)
            if 'duplicate_file' in getattr(e, 'get_codes', lambda: {})().get('file', []):
                return Response(e.detail, status=status.HTTP_409_CONFLICT)
            raise e

        document = serializer.save()

        # Trigger asynchronous Celery background ingestion task
        process_document_task.delay(document.id)

        # Return HTTP 202 Accepted as specified in Section 8.3
        return Response(
            {
                "id": document.id,
                "status": document.status,
                "original_name": document.original_name,
                "message": "File uploaded successfully. Processing started in background."
            },
            status=status.HTTP_202_ACCEPTED
        )


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/v1/workspaces/{ws}/documents/{id}/
    Retrieve document detail and chunk count. Member only.

    DELETE /api/v1/workspaces/{ws}/documents/{id}/
    Delete document, associated chunks, and stored physical file.
    Only the uploader (file owner) or workspace admin/owner can delete (Section 6.4).
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    serializer_class = DocumentSerializer
    lookup_url_kwarg = 'id'

    def get_workspace(self):
        return get_workspace_for_user(self.request.user, self.kwargs.get('ws'))

    def get_queryset(self):
        workspace = self.get_workspace()
        return Document.objects.filter(workspace=workspace)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        workspace = self.get_workspace()

        # File ownership authorization check: uploader or admin/owner
        user_membership = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user
        ).first()

        is_uploader = (document.uploaded_by_id == request.user.id)
        is_admin_or_owner = user_membership and user_membership.is_admin_or_owner

        if not (is_uploader or is_admin_or_owner):
            return Response(
                {"detail": "Only the document uploader or a workspace admin can delete this document."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Physically delete the file from storage if present
        if document.storage_key and os.path.exists(document.storage_key):
            try:
                os.remove(document.storage_key)
            except OSError:
                pass

        # Database deletion cascades to document_chunks automatically
        self.perform_destroy(document)
        return Response(status=status.HTTP_204_NO_CONTENT)


from drf_spectacular.utils import extend_schema


class DocumentRetryView(APIView):
    """
    POST /api/v1/workspaces/{ws}/documents/{id}/retry/
    Retry failed background processing for a document.
    Only uploader or workspace admin/owner can trigger retry.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
    serializer_class = DocumentSerializer

    @extend_schema(responses={200: DocumentSerializer})
    def post(self, request, ws, id):
        workspace = get_workspace_for_user(request.user, ws)
        document = get_object_or_404(Document, id=id, workspace=workspace)

        # File ownership check
        user_membership = WorkspaceMember.objects.filter(
            workspace=workspace,
            user=request.user
        ).first()

        is_uploader = (document.uploaded_by_id == request.user.id)
        is_admin_or_owner = user_membership and user_membership.is_admin_or_owner

        if not (is_uploader or is_admin_or_owner):
            return Response(
                {"detail": "Only the uploader or an admin can retry processing."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Reset document status and dispatch worker task again
        document.status = 'uploaded'
        document.failure_reason = None
        document.save(update_fields=['status', 'failure_reason', 'updated_at'])

        process_document_task.delay(document.id)

        return Response(
            {
                "id": document.id,
                "status": document.status,
                "message": "Document processing retry triggered."
            },
            status=status.HTTP_200_OK
        )
