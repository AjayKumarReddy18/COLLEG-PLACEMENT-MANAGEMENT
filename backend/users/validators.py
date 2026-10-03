from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def validate_email_address(value):
    value = value.strip()
    EmailValidator(message="Please enter a valid email address.")(value)

    local_part, separator, _domain = value.rpartition("@")
    if (
        not separator
        or ".." in value
        or local_part.startswith(".")
        or local_part.endswith(".")
    ):
        raise ValidationError("Please enter a valid email address.")