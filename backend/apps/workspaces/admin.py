from django.contrib import admin
from .models import Workspace, WorkspaceMember


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'plan', 'created_at')
    search_fields = ('name', 'owner__email')
    list_filter = ('plan', 'created_at')
    ordering = ('-created_at',)


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'workspace', 'user', 'role', 'created_at')
    search_fields = ('workspace__name', 'user__email')
    list_filter = ('role', 'created_at')
    ordering = ('-created_at',)
