from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAIProvider(ABC):
    """
    Abstract Base Class for AI Providers (Mock, OpenAI, Gemini).
    Allows zero-cost offline mock execution and easy swapping with real APIs.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name identifier of the provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model name used by the provider."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates a vector embedding for a single text string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a list of text strings in batch."""
        pass

    @abstractmethod
    def generate_answer(
        self,
        system_prompt: str,
        context_chunks: List[Dict[str, Any]],
        question: str,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Calls LLM to generate an answer grounded in the provided context chunks.
        Returns a dictionary:
        {
            "answer": str,
            "cited_source_indices": List[int],
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "model": str,
            "provider": str,
        }
        """
        pass
