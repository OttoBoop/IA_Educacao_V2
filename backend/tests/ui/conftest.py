import os
import pytest
from pathlib import Path

_BASE_DIR = Path(__file__).parent.resolve()

def pytest_collection_modifyitems(config, items):
    if os.getenv('RUN_UI_TESTS', '') == '1':
        return
    skip = pytest.mark.skip(reason='UI tests disabled by default; set RUN_UI_TESTS=1')
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        if _BASE_DIR in item_path.parents:
            item.add_marker(skip)
