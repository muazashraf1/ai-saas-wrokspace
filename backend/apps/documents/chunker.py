import re
from typing import List, Tuple, Dict, Any
from pypdf import PdfReader


class DocumentExtractionError(Exception):
    """Raised when text extraction fails or file is corrupted."""
    pass


class ScannedPDFError(DocumentExtractionError):
    """Raised when a PDF has no extractable text (scanned document)."""
    pass


def estimate_tokens(text: str) -> int:
    """
    Estimates token count for English text.
    Standard rule of thumb: ~4 characters per token or ~0.75 words per token.
    """
    if not text:
        return 0
    words = text.split()
    # Average of word-based (~1.3 tokens per word) and character-based (~4 chars per token)
    word_estimate = len(words) * 1.3
    char_estimate = len(text) / 4.0
    return max(1, int((word_estimate + char_estimate) / 2))


def extract_document_pages(file_path: str, mime_type: str) -> List[Tuple[int, str]]:
    """
    Extracts text page-by-page from a file.
    Returns: List of (page_number, page_text) tuples.
    Raises: ScannedPDFError or DocumentExtractionError.
    """
    pages_data: List[Tuple[int, str]] = []

    if mime_type == 'application/pdf':
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            total_text_length = 0

            for page_idx in range(total_pages):
                page = reader.pages[page_idx]
                page_text = page.extract_text() or ''
                # Clean extra whitespace
                cleaned_text = re.sub(r'[ \t]+', ' ', page_text).strip()
                pages_data.append((page_idx + 1, cleaned_text))
                total_text_length += len(cleaned_text)

            # Detect scanned PDF (no text across all pages)
            if total_text_length < 20:
                raise ScannedPDFError("Scanned PDF contains no extractable text. OCR is not supported.")

        except ScannedPDFError:
            raise
        except Exception as e:
            raise DocumentExtractionError(f"Failed to parse PDF document: {str(e)}")

    elif mime_type == 'text/plain':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            cleaned_text = re.sub(r'[ \t]+', ' ', content).strip()
            if not cleaned_text:
                raise DocumentExtractionError("Text document is empty.")
            pages_data.append((1, cleaned_text))
        except DocumentExtractionError:
            raise
        except Exception as e:
            raise DocumentExtractionError(f"Failed to read text file: {str(e)}")

    else:
        raise DocumentExtractionError(f"Unsupported mime type: {mime_type}")

    return pages_data


def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences adhering to paragraph and sentence boundaries.
    Prevents splitting numbers (e.g. 3.14) or abbreviations.
    """
    # Split on paragraph breaks first, then on sentence terminators followed by whitespace
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    sentences: List[str] = []

    for paragraph in paragraphs:
        # Split on sentence boundaries: . ! ? followed by space or newline
        raw_sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        for s in raw_sentences:
            cleaned = s.strip()
            if cleaned:
                sentences.append(cleaned)

    return sentences


def create_chunks_from_pages(
    pages_data: List[Tuple[int, str]],
    target_tokens: int = 400,
    overlap_tokens: int = 50
) -> List[Dict[str, Any]]:
    """
    Chunks extracted pages into semantic passages (~300-500 tokens with 10-15% overlap).
    Preserves page_number with every chunk for verifiable citations.

    Returns:
      List of dicts:
      [
        {
          'chunk_index': 0,
          'page_number': 1,
          'content': '...',
          'token_count': 380
        },
        ...
      ]
    """
    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    for page_number, page_text in pages_data:
        if not page_text:
            continue

        sentences = split_into_sentences(page_text)
        if not sentences:
            continue

        current_sentences: List[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = estimate_tokens(sentence)

            # If adding this sentence exceeds target tokens and we already have content
            if current_tokens + sentence_tokens > target_tokens and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append({
                    'chunk_index': chunk_index,
                    'page_number': page_number,
                    'content': chunk_text,
                    'token_count': current_tokens,
                })
                chunk_index += 1

                # Retain overlap sentences from the end of current chunk
                overlap_sentences: List[str] = []
                overlap_accumulated = 0
                for prev_sentence in reversed(current_sentences):
                    prev_tokens = estimate_tokens(prev_sentence)
                    if overlap_accumulated + prev_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, prev_sentence)
                        overlap_accumulated += prev_tokens
                    else:
                        break

                current_sentences = overlap_sentences + [sentence]
                current_tokens = sum(estimate_tokens(s) for s in current_sentences)
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens

        # Flush remaining sentences for this page
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append({
                'chunk_index': chunk_index,
                'page_number': page_number,
                'content': chunk_text,
                'token_count': current_tokens,
            })
            chunk_index += 1

    return chunks
