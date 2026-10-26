from django.db import models
from django.conf import settings
from django.utils import timezone


class PlanLimit(models.Model):
    """
    Defines per-plan usage ceilings (Section 6.1 & Section 7.8).
    Controls daily questions, monthly tokens, max documents, and file size.
    """
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]

    plan = models.CharField(
        max_length=20,
        primary_key=True,
        choices=PLAN_CHOICES,
        default='free'
    )
    daily_questions = models.IntegerField(default=20, help_text="Maximum allowed questions per user per day")
    monthly_tokens = models.IntegerField(default=100000, help_text="Monthly token budget per user")
    max_documents = models.IntegerField(default=10, help_text="Maximum documents allowed per workspace")
    max_file_mb = models.IntegerField(default=10, help_text="Maximum single file upload size in MB")

    class Meta:
        db_table = 'plan_limits'
        verbose_name = 'Plan Limit'
        verbose_name_plural = 'Plan Limits'

    def __str__(self):
        return f"Plan '{self.plan}': {self.daily_questions} Q/day, {self.monthly_tokens} tokens/mo"


class UsageRecord(models.Model):
    """
    Financial and audit accounting table for every token-consuming operation.
    Enforces 1-to-1 link with AskRequest (Section 6.4: 'unique request_id so a retry can never create a second charge').
    """
    KIND_CHOICES = [
        ('question', 'Question'),
        ('embedding', 'Embedding'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_records',
        db_index=True
    )
    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='usage_records',
        db_index=True
    )
    request = models.OneToOneField(
        'qa.AskRequest',
        on_delete=models.CASCADE,
        related_name='usage_record',
        null=True,
        blank=True,
        help_text="One-to-one constraint guarantees a request is never billed twice"
    )
    kind = models.CharField(
        max_length=12,
        choices=KIND_CHOICES,
        default='question'
    )
    tokens_used = models.IntegerField(default=0)
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0.0,
        help_text="Estimated cost calculated from price schedule"
    )
    period_day = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="UTC date for ultra-fast daily quota aggregation"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'usage_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'period_day'], name='idx_usage_user_day'),
            models.Index(fields=['workspace', 'period_day'], name='idx_usage_ws_day'),
        ]

    def __str__(self):
        return f"Usage #{self.id} - {self.user.email} - {self.kind} ({self.tokens_used} tokens, ${self.estimated_cost})"
