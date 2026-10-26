from django.contrib import admin
from .models import PlanLimit, UsageRecord


@admin.register(PlanLimit)
class PlanLimitAdmin(admin.ModelAdmin):
    list_display = ('plan', 'daily_questions', 'monthly_tokens', 'max_documents', 'max_file_mb')


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'workspace', 'kind', 'tokens_used', 'estimated_cost', 'period_day', 'created_at')
    search_fields = ('user__email', 'workspace__name')
    list_filter = ('kind', 'period_day', 'created_at')
    ordering = ('-created_at',)
