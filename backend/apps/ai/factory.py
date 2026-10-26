from django.conf import settings
from .base import BaseAIProvider
from .mock_provider import MockAIProvider
from .real_provider import RealAIProvider


def get_ai_provider() -> BaseAIProvider:
    """
    Factory function to instantiate the configured AI Provider.
    Configured via settings.AI_PROVIDER ('mock', 'openai', 'gemini').
    """
    provider_type = getattr(settings, 'AI_PROVIDER', 'mock').lower()

    if provider_type == 'mock':
        return MockAIProvider()
    if provider_type == 'gemini':
        return RealAIProvider()
    raise ValueError("AI_PROVIDER must be either 'mock' or 'gemini'.")
