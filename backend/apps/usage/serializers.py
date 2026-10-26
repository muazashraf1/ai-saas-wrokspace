from rest_framework import serializers


class UsageSummarySerializer(serializers.Serializer):
    """Serializer displaying active user's quota, limits, and reset time (Section 8.1 & 8.2)."""
    plan = serializers.CharField()
    daily_questions_used = serializers.IntegerField()
    daily_questions_limit = serializers.IntegerField()
    daily_questions_remaining = serializers.IntegerField()
    monthly_tokens_used = serializers.IntegerField()
    monthly_tokens_limit = serializers.IntegerField()
    monthly_tokens_remaining = serializers.IntegerField()
    estimated_cost_usd = serializers.DecimalField(max_digits=12, decimal_places=6)
    max_documents_limit = serializers.IntegerField()
    max_file_mb_limit = serializers.IntegerField()
    resets_at = serializers.CharField()
    member_usage = serializers.ListField(child=serializers.DictField(), required=False)
