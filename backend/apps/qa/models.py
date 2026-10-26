from django.db import models
from django.conf import settings
from django.utils import timezone


class AskRequest(models.Model):
    """
    Audit log and history record of every user question.
    Stores question, AI answer, latency, token metrics, failure details,
    and idempotency key to prevent double charging/processing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('unsupported', 'Unsupported'),
        ('failed', 'Failed'),
    ]

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='ask_requests',
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ask_requests',
        db_index=True
    )
    question = models.TextField()
    answer = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    failure_code = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text="e.g. provider_timeout, provider_error, threshold_miss, rate_limit"
    )
    provider = models.CharField(max_length=30, default='mock')
    model = models.CharField(max_length=60, blank=True, default='')
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    idempotency_key = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Client-supplied UUID to prevent duplicate executions on network retry"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ask_requests'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'idempotency_key'],
                name='unique_user_idempotency_key'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_req_user_created'),
            models.Index(fields=['workspace', '-created_at'], name='idx_req_ws_created'),
        ]

    def __str__(self):
        return f"Req #{self.id} ({self.status}) - {self.user.email} - '{self.question[:30]}...'"

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens


class RequestSource(models.Model):
    """
    Stores verifiable citations linked to an AskRequest.
    Preserves document_name as a snapshot so citations remain valid even if the document is deleted later.
    """
    request = models.ForeignKey(
        AskRequest,
        on_delete=models.CASCADE,
        related_name='sources'
    )
    chunk = models.ForeignKey(
        'documents.DocumentChunk',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cited_in'
    )
    document_name = models.CharField(
        max_length=255,
        help_text="Snapshot copy of document name at the time of query"
    )
    page_number = models.IntegerField(default=1)
    similarity_score = models.FloatField(default=0.0)
    rank = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'request_sources'
        ordering = ['rank']

    def __str__(self):
        return f"Source #{self.rank}: {self.document_name} p.{self.page_number} (score: {self.similarity_score:.2f})"
