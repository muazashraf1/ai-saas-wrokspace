import logging
from typing import List, Dict, Any, Tuple
from django.conf import settings
from django.db import connection
from pgvector.django import CosineDistance

from documents.models import DocumentChunk
from ai.factory import get_ai_provider

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(
    workspace_id: int,
    query_text: str,
    top_k: int = None,
    threshold: float = None
) -> Dict[str, Any]:
    """
    Executes tenant-isolated vector retrieval:
    1. Embeds user query using configured AI provider.
    2. Runs pgvector cosine similarity search filtered strictly by workspace_id and document.status='ready'.
    3. Evaluates top chunk against similarity threshold (Cost control & hallucination guard).
    
    Returns:
    {
        "is_supported": bool,
        "best_score": float,
        "chunks": List[Dict[str, Any]],
        "threshold": float,
    }
    """
    ai_provider = get_ai_provider()
    if threshold is None:
        setting_name = 'MOCK_SIMILARITY_THRESHOLD' if ai_provider.provider_name == 'mock' else 'SIMILARITY_THRESHOLD'
        threshold = float(getattr(settings, setting_name, 0.30 if ai_provider.provider_name == 'mock' else 0.55))
    top_k = top_k if top_k is not None else int(getattr(settings, 'TOP_K_CHUNKS', 4))
    top_k = max(1, min(int(top_k), 20))
    query_vector = ai_provider.embed_text(query_text)

    # Tenant-isolated vector search using pgvector CosineDistance operator <=>
    # HARDCODED: WHERE workspace_id = :workspace_id AND document.status = 'ready'
    base_qs = (
        DocumentChunk.objects
        .filter(workspace_id=workspace_id, document__status='ready')
        .select_related('document')
    )

    if connection.vendor == 'postgresql':
        chunks_with_scores = [
            (chunk, max(0.0, min(1.0, 1.0 - float(chunk.distance))))
            for chunk in base_qs.annotate(
                distance=CosineDistance('embedding', query_vector)
            ).order_by('distance')[:top_k]
        ]
    else:
        # Test/development fallback. Production uses pgvector's indexed cosine
        # operator; SQLite computes the same score in Python for small fixtures.
        def cosine_similarity(left, right):
            left = list(left or [])
            right = list(right or [])
            if not left or not right:
                return 0.0
            dot = sum(a * b for a, b in zip(left, right))
            left_norm = sum(a * a for a in left) ** 0.5
            right_norm = sum(b * b for b in right) ** 0.5
            return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

        chunks_with_scores = sorted(
            ((chunk, cosine_similarity(chunk.embedding, query_vector)) for chunk in base_qs),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]

    retrieved_chunks: List[Dict[str, Any]] = []
    for rank, (chunk, raw_similarity) in enumerate(chunks_with_scores, start=1):
        similarity_score = max(0.0, min(1.0, float(raw_similarity)))
        retrieved_chunks.append({
            'chunk_id': chunk.id,
            'document_id': chunk.document_id,
            'document_name': chunk.document.original_name,
            'page_number': chunk.page_number,
            'content': chunk.content,
            'token_count': chunk.token_count,
            'similarity_score': round(similarity_score, 4),
            'rank': rank,
        })

    best_score = retrieved_chunks[0]['similarity_score'] if retrieved_chunks else 0.0

    # Main Plan Rule (Section 7.3): If best score < threshold, treat as unsupported.
    # Do NOT call the AI provider. This saves inference cost and avoids hallucination.
    is_supported = bool(retrieved_chunks and best_score >= threshold)

    logger.info(
        f"Workspace {workspace_id} Retrieval: {len(retrieved_chunks)} chunks retrieved. "
        f"Best score: {best_score:.4f} (Threshold: {threshold}). Supported: {is_supported}"
    )

    return {
        "is_supported": is_supported,
        "best_score": best_score,
        "chunks": retrieved_chunks,
        "threshold": threshold,
    }
