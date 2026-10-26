import os
import uuid
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from .models import Document
from .validators import validate_uploaded_file
from users.serializers import UserSerializer
from usage.services import get_plan_limits_for_workspace
from workspaces.models import Workspace


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for displaying document details and processing status."""
    uploaded_by = UserSerializer(read_only=True)
    chunks_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'workspace',
            'uploaded_by',
            'original_name',
            'mime_type',
            'size_bytes',
            'content_hash',
            'status',
            'failure_reason',
            'page_count',
            'chunks_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_chunks_count(self, obj):
        return obj.chunks.count()


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for handling multipart document upload.
    Validates file size, type, magic bytes, duplicate hash, and workspace document limits.
    """
    file = serializers.FileField(required=True, write_only=True)

    def validate_file(self, file_obj):
        workspace = self.context['workspace']
        limits = get_plan_limits_for_workspace(workspace)
        validation_result = validate_uploaded_file(file_obj, max_upload_mb=limits.max_file_mb)
        self.context['validation_result'] = validation_result
        self.context['plan_limits'] = limits
        return file_obj

    def validate(self, attrs):
        workspace = self.context['workspace']
        validation_result = self.context['validation_result']
        content_hash = validation_result['content_hash']
        limits = self.context['plan_limits']

        if Document.objects.filter(workspace=workspace).count() >= limits.max_documents:
            raise serializers.ValidationError({
                "file": f"Workspace document limit reached ({limits.max_documents} documents)."
            }, code='document_limit')

        # Duplicate upload detection in the same workspace (Section 8.3 & 6.4)
        if Document.objects.filter(workspace=workspace, content_hash=content_hash).exists():
            raise serializers.ValidationError({
                "file": "This document has already been uploaded to this workspace."
            }, code='duplicate_file')

        return attrs

    def create(self, validated_data):
        file_obj = validated_data['file']
        workspace = self.context['workspace']
        user = self.context['request'].user
        val_result = self.context['validation_result']

        limits = self.context['plan_limits']
        file_path = None

        try:
            with transaction.atomic():
                # Serialize uploads for a workspace so concurrent requests cannot
                # pass the document-count or duplicate checks together.
                locked_workspace = Workspace.objects.select_for_update().get(pk=workspace.pk)
                if Document.objects.filter(workspace=locked_workspace).count() >= limits.max_documents:
                    raise serializers.ValidationError({
                        "file": f"Workspace document limit reached ({limits.max_documents} documents)."
                    }, code='document_limit')
                if Document.objects.filter(
                    workspace=locked_workspace,
                    content_hash=val_result['content_hash'],
                ).exists():
                    raise serializers.ValidationError({
                        "file": "This document has already been uploaded to this workspace."
                    }, code='duplicate_file')

                ext = os.path.splitext(file_obj.name)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                storage_dir = getattr(settings, 'STORAGE_DIR', settings.BASE_DIR / 'storage/uploads')
                os.makedirs(storage_dir, exist_ok=True)
                file_path = os.path.join(storage_dir, unique_filename)

                file_obj.seek(0)
                with open(file_path, 'wb') as destination:
                    for chunk in file_obj.chunks():
                        destination.write(chunk)

                return Document.objects.create(
                    workspace=locked_workspace,
                    uploaded_by=user,
                    original_name=file_obj.name,
                    storage_key=file_path,
                    mime_type=val_result['mime_type'],
                    size_bytes=val_result['size_bytes'],
                    content_hash=val_result['content_hash'],
                    status='uploaded',
                )
        except Exception:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            raise
