"""
Context store for saving/loading website descriptions per URL.

Persists website context in a JSON file keyed by URL, so repeat runs
on the same website auto-load the previous description.
"""

import json
from pathlib import Path
from typing import Optional

# Default store location: same directory as this module
_DEFAULT_STORE_PATH = Path(__file__).parent / "context_store.json"


def save_context(url: str, context: str, store_path: Path = None) -> None:
    """Save a website context description keyed by URL."""
    store_path = store_path or _DEFAULT_STORE_PATH

    # Load existing data
    data = {}
    if store_path.exists():
        data = json.loads(store_path.read_text(encoding="utf-8"))

    data[url] = context

    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_context(url: str, store_path: Path = None) -> Optional[str]:
    """Load a saved website context for a URL. Returns None if not found."""
    store_path = store_path or _DEFAULT_STORE_PATH

    if not store_path.exists():
        return None

    data = json.loads(store_path.read_text(encoding="utf-8"))
    return data.get(url)
