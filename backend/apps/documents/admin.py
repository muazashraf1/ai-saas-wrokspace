from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_name', 'workspace', 'uploaded_by', 'status', 'size_bytes', 'created_at')
    search_fields = ('original_name', 'content_hash', 'workspace__name', 'uploaded_by__email')
    list_filter = ('status', 'mime_type', 'created_at')
    ordering = ('-created_at',)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'workspace', 'chunk_index', 'page_number', 'token_count')
    search_fields = ('content', 'document__original_name')
    list_filter = ('workspace', 'page_number')
    ordering = ('document', 'chunk_index')
