"""
API Key Loader for Investor Journey Agent.

Loads Anthropic API keys from the app's encrypted key store
(data/api_keys.json) with fallback to environment variables.
"""

import os
import json
from pathlib import Path
from typing import Optional


# Default path to api_keys.json (relative to backend directory)
DEFAULT_API_KEYS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "api_keys.json"


def load_anthropic_key(config_path: Optional[str] = None) -> Optional[str]:
    """
    Load Anthropic API key from the app's key store.

    Tries to load from:
    1. api_keys.json at the specified path (or default path)
    2. Falls back to ANTHROPIC_API_KEY environment variable

    Args:
        config_path: Optional path to api_keys.json. If None, uses default path.

    Returns:
        The Anthropic API key, or None if not found.
    """
    # Determine config path
    if config_path is None:
        path = DEFAULT_API_KEYS_PATH
    else:
        path = Path(config_path)

    # Try to load from api_keys.json
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find Anthropic key
            for key_config in data.get("keys", []):
                if key_config.get("empresa") == "anthropic" and key_config.get("ativo", True):
                    api_key = key_config.get("api_key")
                    if api_key:
                        return api_key

        except (json.JSONDecodeError, IOError):
            # Fall through to env var fallback
            pass

    # Fallback to environment variable
    env_key = os.getenv("ANTHROPIC_API_KEY")
    if env_key:
        return env_key

    return None
