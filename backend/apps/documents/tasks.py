import logging
from celery import shared_task
from django.db import transaction
from .models import Document, DocumentChunk
from .chunker import (
    extract_document_pages,
    create_chunks_from_pages,
    ScannedPDFError,
    DocumentExtractionError,
)
from ai.factory import get_ai_provider

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_document_task(self, document_id: int):
    """
    Asynchronous Celery task for full document ingestion:
    1. Extract text page-by-page (PDF / TXT).
    2. Detect scanned/empty documents.
    3. Split into overlapping token chunks (~300-500 tokens).
    4. Call AI provider for batch embeddings.
    5. Persist chunks and update document status to 'ready' (Idempotent).
    """
    try:
        document = Document.objects.select_related('workspace').get(id=document_id)
    except Document.DoesNotExist:
        logger.error(f"process_document_task: Document id={document_id} does not exist.")
        return {"status": "error", "message": "Document not found."}

    logger.info(f"Starting ingestion for document id={document.id} ({document.original_name})")

    # Step 1: Transition status to 'processing'
    document.status = 'processing'
    document.failure_reason = None
    document.save(update_fields=['status', 'failure_reason', 'updated_at'])

    try:
        # Step 2: Extract text page by page
        pages_data = extract_document_pages(
            file_path=document.storage_key,
            mime_type=document.mime_type
        )

        # Step 3: Split into chunks preserving page numbers
        raw_chunks = create_chunks_from_pages(
            pages_data=pages_data,
            target_tokens=400,
            overlap_tokens=50
        )

        if not raw_chunks:
            raise DocumentExtractionError("No valid text chunks could be generated from this document.")

        # Step 4: Generate vector embeddings in batch
        ai_provider = get_ai_provider()
        chunk_texts = [c['content'] for c in raw_chunks]
        embeddings = ai_provider.embed_batch(chunk_texts)

        # Step 5: Idempotent Database Persistence (Section 7.7)
        # Delete any existing chunks for this document before inserting
        with transaction.atomic():
            DocumentChunk.objects.filter(document=document).delete()

            chunk_objects = []
            for idx, c in enumerate(raw_chunks):
                chunk_objects.append(
                    DocumentChunk(
                        document=document,
                        workspace=document.workspace,
                        chunk_index=c['chunk_index'],
                        page_number=c['page_number'],
                        content=c['content'],
                        token_count=c['token_count'],
                        embedding=embeddings[idx]
                    )
                )

            DocumentChunk.objects.bulk_create(chunk_objects)

            # Step 6: Mark document as ready
            document.status = 'ready'
            document.page_count = len(pages_data)
            document.failure_reason = None
            document.save(update_fields=['status', 'page_count', 'failure_reason', 'updated_at'])

        logger.info(f"Ingestion successful for document {document.id}: generated {len(chunk_objects)} chunks.")
        return {
            "status": "ready",
            "document_id": document.id,
            "chunks_count": len(chunk_objects),
            "page_count": len(pages_data),
        }

    except ScannedPDFError as exc:
        # Non-retriable failure: scanned PDF without text
        logger.warning(f"Document {document.id} failed: Scanned PDF without text.")
        document.status = 'failed'
        document.failure_reason = str(exc)
        document.save(update_fields=['status', 'failure_reason', 'updated_at'])
        return {"status": "failed", "reason": str(exc)}

    except Exception as exc:
        logger.error(f"Error during ingestion of document {document.id}: {str(exc)}", exc_info=True)
        # Check if Celery retries remain
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying ingestion for document {document.id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

        # Retries exhausted -> mark as failed
        document.status = 'failed'
        document.failure_reason = f"Processing failed: {str(exc)}"
        document.save(update_fields=['status', 'failure_reason', 'updated_at'])
        return {"status": "failed", "reason": str(exc)}
