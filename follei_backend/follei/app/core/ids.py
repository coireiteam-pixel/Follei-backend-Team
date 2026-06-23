import secrets
import string

# Prefix letters for different entity types
ID_PREFIXES = ["T", "A", "C", "L", "I", "D", "E", "P", "S", "M"]

SHORT_ID_LENGTH = 3  # Number suffix length


def short_id(prefix: str | None = None) -> str:
    """
    Generate a short alphanumeric ID.
    Format: Letter + 3 digits (e.g., 'T007', 'A123', 'C001')
    Total length: 4 characters
    """
    if prefix is None:
        prefix = secrets.choice(ID_PREFIXES)
    number = ''.join(secrets.choice(string.digits) for _ in range(SHORT_ID_LENGTH))
    return f"{prefix}{number}"