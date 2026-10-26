import hashlib
from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED_MIME_TYPES = {
    'application/pdf': 'PDF',
    'text/plain': 'TXT',
}

ALLOWED_EXTENSIONS = ('.pdf', '.txt')


def compute_file_hash(file_obj) -> str:
    """
    Computes SHA-256 hash of a file object in chunks.
    Resets the file pointer to the beginning after reading.
    """
    hasher = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(65536), b''):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def validate_uploaded_file(file_obj, max_upload_mb=None) -> dict:
    """
    Validates uploaded file against:
    1. Empty file (size == 0)
    2. File size limit (<= MAX_UPLOAD_MB, default 10MB)
    3. File extension (.pdf, .txt)
    4. Content inspection (Magic bytes: '%PDF-' for PDFs, valid UTF-8 for TXT)

    Returns a dict with: {'mime_type': str, 'size_bytes': int, 'content_hash': str}
    """
    # 1. Check empty file
    if not file_obj or file_obj.size == 0:
        raise ValidationError("Uploaded file is empty. Please upload a valid document.")

    # 2. Check size limit
    max_mb = max_upload_mb if max_upload_mb is not None else getattr(settings, 'MAX_UPLOAD_MB', 10)
    max_bytes = max_mb * 1024 * 1024
    if file_obj.size > max_bytes:
        raise ValidationError(
            f"File size exceeds the maximum limit of {max_mb} MB (received {file_obj.size / (1024 * 1024):.2f} MB)."
        )

    # 3. Check filename extension
    filename = file_obj.name.lower()
    if not filename.endswith(ALLOWED_EXTENSIONS):
        raise ValidationError(
            f"Unsupported file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are supported."
        )

    # 4. Content sniffing / Magic bytes verification
    file_obj.seek(0)
    header = file_obj.read(1024)
    file_obj.seek(0)

    if filename.endswith('.pdf'):
        if not header.startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF file: corrupted or not a true PDF document.")
        mime_type = 'application/pdf'
    elif filename.endswith('.txt'):
        try:
            # Verify text is decodable as utf-8 or ascii
            header.decode('utf-8')
            mime_type = 'text/plain'
        except UnicodeDecodeError:
            raise ValidationError("Invalid text file: file contains non-text or corrupted binary data.")
    else:
        mime_type = 'application/octet-stream'

    content_hash = compute_file_hash(file_obj)

    return {
        'mime_type': mime_type,
        'size_bytes': file_obj.size,
        'content_hash': content_hash,
    }
