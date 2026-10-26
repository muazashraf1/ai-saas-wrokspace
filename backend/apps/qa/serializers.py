from rest_framework import serializers
from .models import AskRequest, RequestSource
from users.serializers import UserSerializer


class RequestSourceSerializer(serializers.ModelSerializer):
    """Serializer for individual citation sources."""
    n = serializers.IntegerField(source='rank', read_only=True)
    document = serializers.CharField(source='document_name', read_only=True)
    page = serializers.IntegerField(source='page_number', read_only=True)
    score = serializers.FloatField(source='similarity_score', read_only=True)
    snippet = serializers.SerializerMethodField()

    class Meta:
        model = RequestSource
        fields = ['n', 'document', 'page', 'score', 'snippet']

    def get_snippet(self, obj):
        if obj.chunk:
            return obj.chunk.content[:200]
        return ""


class AskQuestionInputSerializer(serializers.Serializer):
    """Validates user question input."""
    question = serializers.CharField(
        min_length=3,
        max_length=1000,
        required=True,
        error_messages={
            'min_length': 'Question must be at least 3 characters long.',
            'max_length': 'Question cannot exceed 1000 characters.',
        }
    )


class AskResponseSerializer(serializers.Serializer):
    """Formats the Ask endpoint success response (Section 8.2)."""
    request_id = serializers.IntegerField()
    status = serializers.CharField()
    answer = serializers.CharField()
    sources = RequestSourceSerializer(many=True)
    usage = serializers.DictField(required=False)


class AskRequestListSerializer(serializers.ModelSerializer):
    """Serializer for request history listings."""
    user = UserSerializer(read_only=True)
    sources_count = serializers.SerializerMethodField()

    class Meta:
        model = AskRequest
        fields = [
            'id',
            'user',
            'question',
            'answer',
            'status',
            'provider',
            'latency_ms',
            'sources_count',
            'created_at',
        ]

    def get_sources_count(self, obj):
        return obj.sources.count()


class AskRequestDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a single request including citations."""
    user = UserSerializer(read_only=True)
    sources = RequestSourceSerializer(many=True, read_only=True)

    class Meta:
        model = AskRequest
        fields = [
            'id',
            'workspace',
            'user',
            'question',
            'answer',
            'status',
            'failure_code',
            'provider',
            'model',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'latency_ms',
            'idempotency_key',
            'sources',
            'created_at',
        ]
