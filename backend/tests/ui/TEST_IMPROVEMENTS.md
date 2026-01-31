# UI Test Improvements - test_mobile_modals.py

## Summary

The `test_mobile_modals.py` file has been significantly improved to be more robust, informative, and reliable. All identified issues have been addressed.

## Problems Fixed

### 1. Silent Passing Tests ✅

**Before:**
```python
if await element.is_visible():
    # Test code here
    assert something
# Test passes even if element doesn't exist!
```

**After:**
```python
# New helper function
async def assert_element_exists_and_visible(page, selector, element_name):
    """Assert that element exists AND is visible, or fail/skip with clear message."""
    element = page.locator(selector)
    count = await element.count()

    if count == 0:
        # Take screenshot for debugging
        pytest.fail(f"{element_name} not found (selector: {selector})...")

    is_visible = await element.first.is_visible(timeout=5000)
    if not is_visible:
        pytest.skip(f"{element_name} exists but not visible...")

    return element.first
```

**Usage in tests:**
```python
welcome_modal = await assert_element_exists_and_visible(
    mobile_page, "#modal-welcome", "Welcome modal"
)
# Now test FAILS if element missing, SKIPS if not visible
```

### 2. No Server Check ✅

**Before:**
- Tests would fail with cryptic Playwright errors
- No indication that server wasn't running

**After:**
```python
@pytest.fixture(scope="session", autouse=True)
async def check_server():
    """Verifies local server is running before tests."""
    if not os.getenv("RUN_UI_TESTS"):
        pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LOCAL_URL, timeout=5.0)
            if response.status_code != 200:
                pytest.exit(
                    f"Server at {LOCAL_URL} returned status {response.status_code}.\n"
                    f"Start the server with:\n"
                    f"  cd IA_Educacao_V2/backend\n"
                    f"  python -m uvicorn main_v2:app --port 8000 --reload"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.exit(
            f"Cannot connect to server at {LOCAL_URL}.\n"
            f"Please start the server first:\n"
            f"  cd IA_Educacao_V2/backend\n"
            f"  python -m uvicorn main_v2:app --port 8000 --reload\n"
            f"Error: {e}"
        )
```

### 3. No Screenshots on Failure ✅

**Before:**
- When tests failed, no visual feedback
- Hard to debug what went wrong

**After:**
```python
@pytest.fixture(scope="session")
def screenshots_dir():
    """Creates directory for test failure screenshots."""
    screenshot_path = Path(__file__).parent.parent.parent / "logs" / "ui_test_screenshots"
    screenshot_path.mkdir(parents=True, exist_ok=True)
    return screenshot_path

@pytest.fixture(scope="function")
async def mobile_page(browser, screenshots_dir, request):
    """Mobile page fixture with screenshot on failure."""
    viewport = IPHONE_14
    print(f"\n  [Testing on {viewport['name']}: {viewport['width']}x{viewport['height']}]")

    page = await browser.new_page(viewport=viewport)
    yield page

    # Capture screenshot on test failure
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        screenshot_path = screenshots_dir / f"{request.node.name}_mobile_failure.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"\n  [Screenshot saved: {screenshot_path}]")

    await page.close()

# Hook to capture test results
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to store test results for screenshot capture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
```

**Screenshots saved to:**
```
IA_Educacao_V2/backend/logs/ui_test_screenshots/
├── test_welcome_modal_has_flex_structure_mobile_failure.png
├── test_modal_close_button_size_mobile_failure.png
└── missing_Welcome_modal.png
```

### 4. No Progress Output ✅

**Before:**
- No indication of what was being tested
- Silent execution

**After:**
```python
# Print viewport info when fixture creates page
print(f"\n  [Testing on {viewport['name']}: {viewport['width']}x{viewport['height']}]")

# Print what each test is checking
print("\n  [Checking welcome modal flex structure...]")
print(f"  [Modal display: {display}, flex-direction: {flex_direction}]")

print("\n  [Checking modal close button size...]")
print(f"  [Modal close button size: {width}x{height}px]")

print("\n  [Testing task panel closes when modal opens...]")
print(f"  [Task panel test result: {result}]")
```

**Example output:**
```
tests/ui/test_mobile_modals.py::TestWelcomeModalScroll::test_welcome_modal_has_flex_structure
  [Testing on iPhone 14: 393x852]
  [Checking welcome modal flex structure...]
  [Modal display: flex, flex-direction: column]
PASSED

tests/ui/test_mobile_modals.py::TestTouchTargets::test_modal_close_button_size
  [Testing on iPhone 14: 393x852]
  [Checking modal close button size...]
  [Modal close button size: 44x44px]
PASSED
```

### 5. Generic Skip Messages ✅

**Before:**
```python
if not PLAYWRIGHT_AVAILABLE:
    pytest.skip("Playwright não instalado")
```

**After:**
```python
if not PLAYWRIGHT_AVAILABLE:
    pytest.skip(
        "Playwright não instalado. Execute:\n"
        "  pip install playwright pytest-playwright pytest-asyncio\n"
        "  playwright install chromium"
    )
```

**Also improved element-specific skips:**
```python
if scroll_height <= client_height:
    pytest.skip(
        f"Modal content does not exceed viewport (scrollHeight={scroll_height}, "
        f"clientHeight={client_height}). Cannot test scroll functionality."
    )

if button_count == 0:
    pytest.skip(
        "No section header buttons found. This may be normal if no sections "
        "are populated. Skipping test."
    )
```

## Additional Improvements

### Helper Functions

1. **`close_welcome_modal_if_visible()`**
   - Reusable function to close welcome modal
   - Prevents code duplication
   - Handles cases where modal isn't present

2. **`assert_element_exists_and_visible()`**
   - Ensures elements exist before testing
   - Takes screenshots when elements are missing
   - Provides clear error messages with selectors

### Better Error Messages

**Before:**
```
AssertionError: Modal deve ter display: flex, mas tem: block
```

**After:**
```
Welcome modal not found (selector: #modal-welcome).
Screenshot saved to: .../logs/ui_test_screenshots/missing_Welcome_modal.png

Chat modal (#modal-chat) not found in DOM

Modal overlay deve ter classe 'modal-chat', mas tem: modal-overlay

Task panel deve ser fechado quando modal abre. Reason: still_open
```

### Environment Variable Gate

Tests now check `RUN_UI_TESTS` environment variable:

```python
if not os.getenv("RUN_UI_TESTS"):
    pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")
```

This prevents UI tests from running accidentally in CI or when server isn't available.

## Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install playwright pytest-playwright pytest-asyncio httpx

# Install browser
playwright install chromium

# Start local server
cd IA_Educacao_V2/backend
python -m uvicorn main_v2:app --port 8000 --reload
```

### Execute Tests

```bash
# In another terminal
cd IA_Educacao_V2/backend

# Run UI tests
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v

# Run specific test class
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py::TestWelcomeModalScroll -v

# Run with more details
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v -s
```

## Test Output Example

```
tests/ui/test_mobile_modals.py::TestWelcomeModalScroll::test_welcome_modal_has_flex_structure
  [Testing on iPhone 14: 393x852]
  [Checking welcome modal flex structure...]
  [Modal display: flex, flex-direction: column]
PASSED

tests/ui/test_mobile_modals.py::TestWelcomeModalScroll::test_welcome_modal_body_is_scrollable
  [Testing on iPhone 14: 393x852]
  [Checking welcome modal body scrollability...]
  [Modal-body overflow-y: auto, flex-grow: 1]
PASSED

tests/ui/test_mobile_modals.py::TestTouchTargets::test_modal_close_button_size
  [Testing on iPhone 14: 393x852]
  [Checking modal close button size...]
  [Modal close button size: 44x44px]
PASSED

tests/ui/test_mobile_modals.py::TestTouchTargets::test_section_header_buttons_size
  [Testing on iPhone 14: 393x852]
  [Checking section header button sizes...]
SKIPPED (No section header buttons found. This may be normal if no sections are populated. Skipping test.)
```

## Failure Example

```
tests/ui/test_mobile_modals.py::TestChatModalScroll::test_chat_modal_overlay_has_class
  [Testing on iPhone 14: 393x852]
  [Checking chat modal overlay class attribute...]
  [Chat modal classes: modal-overlay]
FAILED

AssertionError: Modal overlay deve ter classe 'modal-chat', mas tem: modal-overlay

  [Screenshot saved: .../logs/ui_test_screenshots/test_chat_modal_overlay_has_class_mobile_failure.png]
```

## Benefits

1. **Reliability**: Tests fail loudly when elements are missing instead of silently passing
2. **Debuggability**: Screenshots and detailed logs make failures easy to investigate
3. **Informativeness**: Progress output shows what's being tested in real-time
4. **User-friendliness**: Clear error messages with actionable instructions
5. **Robustness**: Server checks prevent cryptic Playwright errors
6. **Maintainability**: Helper functions reduce code duplication

## Files Modified

- `IA_Educacao_V2/backend/tests/ui/test_mobile_modals.py` - Main test file (complete rewrite)
- `IA_Educacao_V2/backend/tests/ui/TEST_IMPROVEMENTS.md` - This document

## Files Created (by tests)

- `IA_Educacao_V2/backend/logs/ui_test_screenshots/` - Screenshot directory (auto-created)
- `IA_Educacao_V2/backend/logs/ui_test_screenshots/*.png` - Failure screenshots

## Next Steps

Consider applying these patterns to other UI test files:
- `tests/ui/test_mobile_responsiveness.py`
- `tests/ui/test_accessibility.py`
- Any future UI tests

## References

- Playwright Documentation: https://playwright.dev/python/
- pytest-playwright: https://github.com/microsoft/playwright-pytest
- pytest hooks: https://docs.pytest.org/en/stable/reference/reference.html#hooks
