# Quick Start - UI Tests

## TL;DR

```bash
# 1. Install (one time)
pip install playwright pytest-playwright pytest-asyncio httpx
playwright install chromium

# 2. Start server (terminal 1)
cd IA_Educacao_V2/backend
python -m uvicorn main_v2:app --port 8000 --reload

# 3. Run tests (terminal 2)
cd IA_Educacao_V2/backend
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v
```

## What's New?

The UI tests have been completely overhauled. They now:

### 1. Check Server Automatically
```
❌ Before: Cryptic Playwright connection errors
✅ Now:    Clear message with exact commands to start server
```

### 2. Show Progress
```
❌ Before: Silent execution
✅ Now:
  [Testing on iPhone 14: 393x852]
  [Checking welcome modal flex structure...]
  [Modal display: flex, flex-direction: column]
  PASSED
```

### 3. Take Screenshots on Failure
```
❌ Before: No visual feedback
✅ Now:    Screenshot saved: .../logs/ui_test_screenshots/test_name_failure.png
```

### 4. Fail Loudly Instead of Silently Passing
```
❌ Before: if element.is_visible(): assert something  # Passes if element missing!
✅ Now:    element = await assert_element_exists_and_visible(...)  # Fails if missing
```

### 5. Better Error Messages
```
❌ Before: "Playwright não instalado"
✅ Now:    "Playwright não instalado. Execute:
             pip install playwright pytest-playwright pytest-asyncio
             playwright install chromium"
```

## Common Issues

### Server Not Running

**Error:**
```
Cannot connect to server at http://localhost:8000.
Please start the server first:
  cd IA_Educacao_V2/backend
  python -m uvicorn main_v2:app --port 8000 --reload
```

**Solution:**
Open a new terminal and run the exact command shown.

### Playwright Not Installed

**Error:**
```
SKIPPED - Playwright não instalado. Execute:
  pip install playwright pytest-playwright pytest-asyncio
  playwright install chromium
```

**Solution:**
Run both commands shown.

### Tests Skipped (RUN_UI_TESTS not set)

**Error:**
```
SKIPPED - UI tests disabled. Set RUN_UI_TESTS=1 to enable
```

**Solution:**
```bash
# Windows PowerShell
$env:RUN_UI_TESTS="1"
pytest tests/ui/test_mobile_modals.py -v

# Windows CMD
set RUN_UI_TESTS=1
pytest tests/ui/test_mobile_modals.py -v

# Linux/Mac
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v
```

### Element Not Found

**Error:**
```
Welcome modal not found (selector: #modal-welcome).
Screenshot saved to: .../logs/ui_test_screenshots/missing_Welcome_modal.png
```

**Solution:**
1. Check the screenshot to see what the page looks like
2. Verify the element exists in the HTML
3. Check if element ID changed
4. Check if element is dynamically loaded (may need wait)

## Test Structure

```
test_mobile_modals.py
│
├── Fixtures
│   ├── check_server()          # Verifies server before tests
│   ├── screenshots_dir()       # Creates screenshot directory
│   ├── browser()               # Playwright browser instance
│   ├── mobile_page()           # iPhone 14 viewport (393x852)
│   └── tablet_page()           # iPad Portrait (768x1024)
│
├── Helpers
│   ├── close_welcome_modal_if_visible()      # Closes welcome modal
│   └── assert_element_exists_and_visible()   # Fails if element missing
│
└── Test Classes
    ├── TestWelcomeModalScroll      # Welcome modal scroll tests
    ├── TestChatModalScroll         # Chat modal scroll tests
    ├── TestTouchTargets            # Touch target size tests (44px minimum)
    ├── TestZIndexStacking          # Z-index layering tests
    ├── TestSafeArea                # Safe area for notch devices
    └── TestTutorialModalScroll     # Tutorial modal scroll tests
```

## Screenshots Location

Failed tests save screenshots here:
```
IA_Educacao_V2/backend/logs/ui_test_screenshots/
├── test_welcome_modal_has_flex_structure_mobile_failure.png
├── test_modal_close_button_size_tablet_failure.png
└── missing_Welcome_modal.png
```

## Example: Interpreting Test Output

### Successful Test
```
tests/ui/test_mobile_modals.py::TestTouchTargets::test_modal_close_button_size
  [Testing on iPhone 14: 393x852]
  [Checking modal close button size...]
  [Modal close button size: 44x44px]
PASSED
```

**What this means:**
- ✅ Server is running
- ✅ Page loaded successfully
- ✅ Modal close button exists
- ✅ Button is visible
- ✅ Button is exactly 44x44 pixels

### Failed Test
```
tests/ui/test_mobile_modals.py::TestTouchTargets::test_modal_close_button_size
  [Testing on iPhone 14: 393x852]
  [Checking modal close button size...]
  [Modal close button size: 40x40px]
FAILED

AssertionError: Modal close width deve ser >= 44px, mas é: 40px

  [Screenshot saved: .../test_modal_close_button_size_mobile_failure.png]
```

**What this means:**
- ✅ Server is running
- ✅ Page loaded successfully
- ✅ Modal close button exists
- ✅ Button is visible
- ❌ Button is 40x40 pixels (should be 44x44)
- 📸 Screenshot saved for debugging

### Skipped Test
```
tests/ui/test_mobile_modals.py::TestTouchTargets::test_section_header_buttons_size
  [Testing on iPhone 14: 393x852]
  [Checking section header button sizes...]
SKIPPED (No section header buttons found. This may be normal if no sections are populated.)
```

**What this means:**
- ✅ Server is running
- ✅ Page loaded successfully
- ⚠️ Expected element not found (but this is OK)
- ℹ️ Test skipped with explanation

## Running Specific Tests

```bash
# All UI tests
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v

# Specific test class
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py::TestWelcomeModalScroll -v

# Specific test method
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py::TestWelcomeModalScroll::test_welcome_modal_has_flex_structure -v

# With output (see print statements)
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v -s

# Stop on first failure
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v -x

# Show local variables on failure
RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v -l
```

## Pro Tips

1. **Always check screenshots on failures** - They often reveal the exact problem
2. **Run with `-s` flag during development** - Shows all print statements
3. **Use `-x` to stop on first failure** - Faster debugging
4. **Keep server running between test runs** - Faster test execution
5. **Check `RUN_UI_TESTS` is set** - Common mistake on new terminals

## Troubleshooting Checklist

- [ ] Server is running on port 8000
- [ ] `RUN_UI_TESTS=1` is set
- [ ] Playwright is installed (`pip install playwright`)
- [ ] Chromium is installed (`playwright install chromium`)
- [ ] Running from `backend/` directory
- [ ] Check screenshots in `logs/ui_test_screenshots/`

## Need Help?

1. Check `TEST_IMPROVEMENTS.md` for detailed explanation
2. Look at screenshot if test failed
3. Run with `-v -s` for full output
4. Check server logs for errors
5. Verify element exists in browser DevTools

## Related Files

- `test_mobile_modals.py` - The test file
- `TEST_IMPROVEMENTS.md` - Detailed explanation of improvements
- `QUICK_START.md` - This file
