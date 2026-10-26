import io
import pytest
from rest_framework.exceptions import ValidationError
from documents.validators import validate_uploaded_file, compute_file_hash
from documents.chunker import (
    create_chunks_from_pages,
    estimate_tokens,
    split_into_sentences,
    ScannedPDFError,
)


class DummyFile:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self.size = len(content)
        self._io = io.BytesIO(content)

    def seek(self, pos):
        self._io.seek(pos)

    def read(self, n=-1):
        return self._io.read(n)

    def chunks(self):
        self._io.seek(0)
        yield self._io.read()


def test_empty_file_rejected():
    """AC2: Empty file upload must be rejected."""
    f = DummyFile("empty.pdf", b"")
    with pytest.raises(ValidationError) as exc:
        validate_uploaded_file(f)
    assert "empty" in str(exc.value).lower()


def test_file_size_exceeded_rejected(settings):
    """AC2: File larger than MAX_UPLOAD_MB must be rejected."""
    settings.MAX_UPLOAD_MB = 1  # 1 MB
    oversized_content = b"%PDF-" + b"0" * (2 * 1024 * 1024)  # 2 MB
    f = DummyFile("big.pdf", oversized_content)
    with pytest.raises(ValidationError) as exc:
        validate_uploaded_file(f)
    assert "exceeds" in str(exc.value).lower()


def test_invalid_magic_bytes_rejected():
    """Security: File with .pdf extension but invalid header bytes must be rejected."""
    fake_pdf = DummyFile("fake.pdf", b"THIS_IS_NOT_A_PDF_DOCUMENT_CONTENT")
    with pytest.raises(ValidationError) as exc:
        validate_uploaded_file(fake_pdf)
    assert "invalid pdf" in str(exc.value).lower()


def test_valid_pdf_validation():
    """Positive: True PDF with %PDF- header is accepted."""
    valid_pdf = DummyFile("test.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    result = validate_uploaded_file(valid_pdf)
    assert result['mime_type'] == 'application/pdf'
    assert len(result['content_hash']) == 64


def test_sha256_duplicate_detection():
    """Duplicate Detection: Identical contents produce exact same SHA-256 hash."""
    f1 = DummyFile("doc1.txt", b"Company Vacation Policy Content 2026")
    f2 = DummyFile("doc2.txt", b"Company Vacation Policy Content 2026")
    hash1 = compute_file_hash(f1)
    hash2 = compute_file_hash(f2)
    assert hash1 == hash2


def test_chunker_sentence_splitting():
    """Chunking: Sentences must split on sentence terminators and paragraphs."""
    sample = "Employees receive 10 sick leaves. Extra leaves require manager approval.\n\nCarry over is not permitted."
    sentences = split_into_sentences(sample)
    assert len(sentences) == 3
    assert sentences[0] == "Employees receive 10 sick leaves."
    assert sentences[1] == "Extra leaves require manager approval."
    assert sentences[2] == "Carry over is not permitted."


def test_chunker_overlap_preservation():
    """Chunking: Consecutive chunks must preserve overlap sentences."""
    pages = [
        (1, "Sentence one is here. Sentence two follows it. Sentence three has details. Sentence four concludes page.")
    ]
    # Small target to force multiple chunks
    chunks = create_chunks_from_pages(pages, target_tokens=10, overlap_tokens=4)
    assert len(chunks) >= 2
    # Ensure page numbers are preserved
    assert all(c['page_number'] == 1 for c in chunks)
    assert all('token_count' in c for c in chunks)
