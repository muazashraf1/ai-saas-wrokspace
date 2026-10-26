from django.db import models
from django.conf import settings
from django.utils import timezone
from pgvector.django import VectorField, HnswIndex


class Document(models.Model):
    """
    Represents an uploaded document (PDF, TXT) scoped strictly to a workspace.
    Tracks file metadata, hash (for duplicate upload detection), and processing status.
    """
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='documents',
        db_index=True
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_documents'
    )
    original_name = models.CharField(max_length=255)
    storage_key = models.CharField(
        max_length=500,
        help_text="Random UUID-based path on disk/storage to prevent path traversal and guessing"
    )
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()
    content_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of file content to prevent duplicate uploads in the same workspace"
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='uploaded',
        db_index=True
    )
    failure_reason = models.TextField(blank=True, null=True)
    page_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'content_hash'],
                name='unique_workspace_content_hash'
            )
        ]
        indexes = [
            models.Index(fields=['workspace', 'status'], name='idx_doc_ws_status'),
            models.Index(fields=['uploaded_by', 'created_at'], name='idx_doc_user_created'),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.workspace.name}) - {self.status}"


class DocumentChunk(models.Model):
    """
    Stores individual text chunks extracted from documents alongside their pgvector embeddings.
    Workspace ID is denormalized directly on this table for ultra-fast, zero-leak tenant filtering during RAG.
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='chunks',
        db_index=True,
        help_text="Denormalized tenant key for 100% isolated vector searches"
    )
    chunk_index = models.IntegerField(help_text="0-indexed order of the chunk in the document")
    page_number = models.IntegerField(default=1, help_text="Page number in original document for citations")
    content = models.TextField(help_text="The chunk text snippet (~300-500 tokens)")
    token_count = models.IntegerField(default=0)
    embedding = VectorField(
        dimensions=settings.EMBEDDING_DIMENSIONS,
        help_text="Vector embedding for semantic cosine similarity search"
    )

    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'chunk_index'],
                name='unique_doc_chunk_index'
            )
        ]
        indexes = [
            models.Index(fields=['workspace'], name='idx_chunk_workspace'),
        ] + ([HnswIndex(
                name='idx_chunk_embedding_hnsw',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops']
            )] if settings.DATABASES['default']['ENGINE'].endswith('postgresql') else [])

    def __str__(self):
        return f"Doc {self.document_id} Chunk {self.chunk_index} (p.{self.page_number})"
