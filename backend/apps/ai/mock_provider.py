import math
import hashlib
import re
from typing import List, Dict, Any
from django.conf import settings
from .base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """
    Deterministic Mock AI Provider.
    Requires NO API keys and incurs ZERO external cost.
    Generates unit-normalized deterministic vectors that work with pgvector cosine distance,
    and produces grounded answers with proper citations for testing.
    """

    def __init__(self, dimensions: int = None):
        self.dimensions = dimensions or getattr(settings, 'EMBEDDING_DIMENSIONS', 1536)

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return getattr(settings, 'AI_MODEL_NAME', 'mock-gpt-4o-mini')

    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'do', 'does', 'for',
        'from', 'get', 'how', 'in', 'is', 'it', 'of', 'on', 'or', 'per', 'the',
        'this', 'to', 'what', 'when', 'where', 'which', 'who', 'with', 'your',
    }

    @classmethod
    def _tokens(cls, text: str) -> List[str]:
        """Return simple, deterministic lexical features for offline retrieval."""
        raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
        tokens: List[str] = []
        for token in raw_tokens:
            if token in cls.STOP_WORDS:
                continue
            if token.endswith('ies') and len(token) > 4:
                token = token[:-3] + 'y'
            elif token.endswith('s') and not token.endswith('ss') and len(token) > 3:
                token = token[:-1]
            tokens.append(token)
        return tokens

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """
        Creates a deterministic feature-hashed lexical vector.

        Unlike a seeded random vector, related text shares unigram/bigram features,
        so the mock provider can exercise the complete offline RAG journey without
        pretending to be a production semantic embedding model.
        """
        tokens = self._tokens(text)
        features = [(token, 1.0) for token in tokens]
        features.extend(
            (f"{left}_{right}", 1.5)
            for left, right in zip(tokens, tokens[1:])
        )

        vector = [0.0] * self.dimensions
        for feature, weight in features:
            digest = hashlib.sha256(feature.encode('utf-8')).digest()
            index = int.from_bytes(digest[:8], 'big') % self.dimensions
            vector[index] += weight

        # Normalize to unit length (L2 norm = 1.0) for cosine distance
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        else:
            # Stable non-zero vector for empty/stop-word-only text.
            vector[0] = 1.0

        return vector

    def embed_text(self, text: str) -> List[float]:
        return self._generate_deterministic_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    def generate_answer(
        self,
        system_prompt: str,
        context_chunks: List[Dict[str, Any]],
        question: str,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Synthesizes a realistic mock answer citing retrieved context chunks.
        """
        if not context_chunks:
            return {
                "answer": "I could not find this in your documents.",
                "cited_source_indices": [],
                "prompt_tokens": 120,
                "completion_tokens": 12,
                "total_tokens": 132,
                "model": self.model_name,
                "provider": self.provider_name,
            }

        # Pick top chunk snippet
        primary_chunk = context_chunks[0]
        snippet = primary_chunk.get('content', '').strip()
        doc_name = primary_chunk.get('document_name', 'document')
        page_num = primary_chunk.get('page_number', 1)

        # Take first 150 characters for clean summary
        first_sentence = snippet.split('.')[0] if '.' in snippet else snippet[:150]

        answer_text = (
            f"Based on your documents, {first_sentence.strip()} [1]."
        )

        prompt_tokens = len(system_prompt.split()) + sum(len(c.get('content', '').split()) for c in context_chunks)
        completion_tokens = len(answer_text.split())

        return {
            "answer": answer_text,
            "cited_source_indices": [1],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "model": self.model_name,
            "provider": self.provider_name,
        }
