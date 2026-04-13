"""
Input sanitization for all user-supplied data that feeds into LLM prompts.

bleach.clean() strips all HTML tags and attributes.
Additional guards: null-byte removal, length capping, XML delimiter wrapping
to prevent semantic prompt injection attacks.
"""

import bleach

# Allow zero HTML in LLM inputs
_ALLOWED_TAGS: list = []
_ALLOWED_ATTRS: dict = {}

# Hard cap on a single text field before it enters a prompt
_MAX_FIELD_LEN = 5000


def sanitize_text(value) -> str:
    """Strip HTML, null bytes, and excess whitespace from a string."""
    if not isinstance(value, str):
        value = str(value) if value is not None else ''
    cleaned = bleach.clean(value, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)
    cleaned = cleaned.replace('\x00', '')  # null-byte removal
    cleaned = ' '.join(cleaned.split())    # normalise whitespace
    return cleaned[:_MAX_FIELD_LEN]


def sanitize_dict(data: dict, keys: list) -> dict:
    """Return a copy of `data` with the specified keys sanitized."""
    result = dict(data)
    for key in keys:
        if key in result:
            result[key] = sanitize_text(result[key]) if result[key] is not None else ''
    return result


def wrap_for_prompt(label: str, value: str) -> str:
    """
    Wrap a user-supplied value in XML-style delimiters so Claude treats it
    as data, not as instructions (prompt injection mitigation).

    Example:
        wrap_for_prompt('business_name', 'Bob\'s Gym')
        → '<business_name>Bob\'s Gym</business_name>'
    """
    safe_value = sanitize_text(value)
    return f'<{label}>{safe_value}</{label}>'
