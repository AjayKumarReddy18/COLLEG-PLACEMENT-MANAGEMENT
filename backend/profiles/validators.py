import os
import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

ALLOWED_RESUME_EXTENSIONS = [".pdf", ".doc", ".docx"]
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_resume_file(file):
    """
    Validates that the uploaded resume is an allowed file format (PDF, DOC, DOCX)
    and does not exceed the maximum allowed size (5MB).
    """
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file format '{ext}'. Allowed formats are: {', '.join(ALLOWED_RESUME_EXTENSIONS)}."
        )

    if file.size > MAX_RESUME_SIZE_BYTES:
        max_mb = MAX_RESUME_SIZE_BYTES / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds the {max_mb:.0f}MB limit. Current size is {file.size / (1024 * 1024):.2f}MB."
        )


def validate_instagram_url(value):
    """
    Validates that a given URL is a valid Instagram profile URL.
    Accepts empty or None values (since field is optional).
    """
    if not value:
        return

    # First validate as a proper URL
    url_validator = URLValidator()
    url_validator(value)

    # Validate Instagram domain pattern
    pattern = r"^https?:\/\/(www\.)?instagram\.com\/[A-Za-z0-9_.]+\/?(\?.*)?$"
    if not re.match(pattern, value, re.IGNORECASE):
        raise ValidationError(
            "Enter a valid Instagram profile URL (e.g., https://www.instagram.com/username/)."
        )
