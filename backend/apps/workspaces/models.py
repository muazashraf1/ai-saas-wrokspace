from django.db import models
from django.conf import settings
from django.utils import timezone


class Workspace(models.Model):
    """
    Tenant Root Model.
    All documents, chunks, ask requests, and usage records belong to a workspace.
    """
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]

    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_workspaces'
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='free'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'workspaces'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.plan})"


class WorkspaceMember(models.Model):
    """
    RBAC Model managing user membership and roles inside a workspace.
    Roles:
      - owner: Created the workspace, full rights including deletion.
      - admin: Can invite/remove members, manage documents, view usage.
      - member: Standard user, can upload documents, ask questions, see own usage.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'workspace_members'
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'],
                name='unique_workspace_member'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'workspace'], name='idx_ws_member_user_ws'),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"

    @property
    def is_admin_or_owner(self):
        return self.role in ['owner', 'admin']
