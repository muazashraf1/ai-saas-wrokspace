from django.contrib import admin
from .models import AskRequest, RequestSource


class RequestSourceInline(admin.TabularInline):
    model = RequestSource
    extra = 0
    readonly_fields = ('document_name', 'page_number', 'similarity_score', 'rank')


@admin.register(AskRequest)
class AskRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'workspace', 'status', 'provider', 'latency_ms', 'created_at')
    search_fields = ('question', 'answer', 'user__email', 'workspace__name', 'idempotency_key')
    list_filter = ('status', 'provider', 'created_at')
    inlines = [RequestSourceInline]
    ordering = ('-created_at',)


@admin.register(RequestSource)
class RequestSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'document_name', 'page_number', 'similarity_score', 'rank')
    search_fields = ('document_name', 'request__question')
    list_filter = ('rank', 'page_number')
