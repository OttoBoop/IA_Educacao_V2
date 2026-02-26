"""
URL utilities for the Investor Journey Agent.

Handles detection of file paths vs URLs and conversion to proper file:// URLs.
"""

from pathlib import Path
from urllib.parse import urlparse, urljoin


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


def resolve_start_url(base_url: str, start_url: str) -> str:
    """
    Resolve a start_url relative to the base_url.

    - If start_url starts with '#', append it to the full base_url.
    - If start_url starts with '/', replace the path on the base_url's origin.

    Args:
        base_url: The base URL the journey navigated to (e.g. "https://example.com/home")
        start_url: A fragment ("#turmas") or absolute path ("/dashboard")

    Returns:
        Fully resolved URL string.
    """
    parsed = urlparse(base_url)
    if start_url.startswith("#"):
        # Append fragment to the full base_url (including existing path)
        return base_url.rstrip("#") + start_url
    else:
        # Replace path: use origin + start_url (start_url starts with '/')
        origin = f"{parsed.scheme}://{parsed.netloc}"
        return origin + start_url
