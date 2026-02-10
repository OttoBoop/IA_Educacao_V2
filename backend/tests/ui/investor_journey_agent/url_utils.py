"""
URL utilities for the Investor Journey Agent.

Handles detection of file paths vs URLs and conversion to proper file:// URLs.
"""

from pathlib import Path
from urllib.parse import urlparse


def resolve_url(url_or_path: str) -> str:
    """
    Resolve a URL or file path to a proper URL.

    - HTTP/HTTPS/file:// URLs pass through unchanged.
    - Absolute file paths are converted to file:// URLs.
    - Non-existent file paths raise FileNotFoundError.

    Args:
        url_or_path: A URL string or absolute file path.

    Returns:
        A valid URL string (http://, https://, or file://).

    Raises:
        FileNotFoundError: If the path looks like a file path but doesn't exist.
    """
    # Already a URL with a scheme
    parsed = urlparse(url_or_path)
    if parsed.scheme in ("http", "https", "file"):
        return url_or_path

    # Treat as a file path
    path = Path(url_or_path)
    if path.is_absolute():
        if not path.exists():
            raise FileNotFoundError(f"File not found: {url_or_path}")
        return path.resolve().as_uri()

    # Relative path or something else - try to resolve
    resolved = path.resolve()
    if resolved.exists():
        return resolved.as_uri()

    raise FileNotFoundError(f"File not found: {url_or_path}")
