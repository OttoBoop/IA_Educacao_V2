"""
Configuration for the Investor Journey Agent.

Contains viewport definitions, model settings, and agent configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


# Viewport configurations for different devices
VIEWPORT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "iphone_14": {
        "width": 393,
        "height": 852,
        "name": "iPhone 14",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "iphone_se": {
        "width": 375,
        "height": 667,
        "name": "iPhone SE",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "ipad_portrait": {
        "width": 768,
        "height": 1024,
        "name": "iPad Portrait",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "ipad_landscape": {
        "width": 1024,
        "height": 768,
        "name": "iPad Landscape",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "android_small": {
        "width": 360,
        "height": 640,
        "name": "Android Small",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
    "desktop": {
        "width": 1440,
        "height": 900,
        "name": "Desktop",
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
    "desktop_small": {
        "width": 1280,
        "height": 720,
        "name": "Desktop Small",
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
    },
}

# Default URLs
LOCAL_URL = "http://localhost:8000"
PRODUCTION_URL = "https://ia-educacao-v2.onrender.com"


@dataclass
class AgentConfig:
    """Configuration for the Investor Journey Agent."""

    # API Keys path (for loading from app's encrypted store)
    api_keys_path: Optional[str] = None

    # API Keys (loaded from file or environment)
    anthropic_api_key: Optional[str] = field(default=None)

    # Model settings
    step_model: str = "claude-haiku-4-5-20251001"  # Cheap, fast for decisions
    analysis_model: str = "claude-sonnet-4-5-20250929"  # Quality for final analysis

    # Agent behavior
    max_steps: int = 50
    timeout_per_step_ms: int = 10000
    wait_after_action_ms: int = 1000
    wait_for_network_idle: bool = True

    # Screenshot settings
    screenshot_quality: int = 80
    screenshot_format: str = "png"

    # DOM analysis
    dom_max_depth: int = 5
    dom_max_elements: int = 100

    # User interaction
    ask_before_action: bool = True

    # Output settings
    output_dir: Optional[Path] = None

    def __post_init__(self):
        if self.output_dir is None:
            self.output_dir = Path("investor_journey_reports")
        elif isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Load API key using key_loader with decryption if not explicitly provided
        if self.anthropic_api_key is None:
            from .key_loader import load_anthropic_key_with_decryption
            self.anthropic_api_key = load_anthropic_key_with_decryption(config_path=self.api_keys_path)


# Default configuration
DEFAULT_CONFIG = AgentConfig()
