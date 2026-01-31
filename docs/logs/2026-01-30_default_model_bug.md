# Bug Fix Log: Multiple Default Models

**Date:** 2026-01-30
**Status:** RESOLVED
**Commit:** 380d9ea (fix), 992d946 (docs)

---

## Problem

Two models were marked as `is_default: true` in `models.json`:
- **Claude Haiku 4.5** (line 119) - Correct
- **Llama 3.2 (Local)** (line 259) - Error

## Symptoms

- API `/api/settings/models` returned 2 models with `is_default: true`
- `model_manager.get_default()` returned unpredictable results
- UI showed confusing state in model selection

## Root Cause Analysis

**NOT caused by:**
- Legacy systems or duplicate endpoints
- Multiple endpoints for setting default model
- Code bugs in `set_default()` method

**Actual cause:**
- `ModelManager._load()` in `chat_service.py` loaded models without validating uniqueness
- Data corruption in `models.json` (likely from manual editing or migration)
- No auto-correction mechanism existed

## Solution Implemented

### Code Changes

**File:** `IA_Educacao_V2/backend/chat_service.py`

Added `_ensure_single_default()` method (lines 493-530):

```python
def _ensure_single_default(self):
    """Garante que apenas um modelo seja marcado como padrao."""
    defaults = [m for m in self.models.values() if m.is_default]

    if len(defaults) > 1:
        # Keep Haiku (if present) or first
        haiku = next((m for m in defaults if "haiku" in m.nome.lower()), None)
        keep = haiku if haiku else defaults[0]

        for m in self.models.values():
            m.is_default = (m.id == keep.id)

        self._save()  # Persist fix
```

Called automatically at end of `_load()`.

### Tests Added

**File:** `IA_Educacao_V2/backend/tests/unit/test_model_manager.py`

10 tests covering:
- `test_only_one_default_model_after_load`
- `test_haiku_preferred_as_default`
- `test_set_default_removes_previous_default`
- `test_can_change_default_model`
- `test_set_default_nonexistent_model_fails`
- `test_first_model_becomes_default`
- `test_second_model_not_default`
- `test_no_default_without_models`
- `test_default_persists_after_reload`
- `test_corrupted_data_fixed_on_reload`

## Verification

### Local
```bash
cd IA_Educacao_V2/backend
pytest tests/unit/test_model_manager.py -v
# Expected: 10 passed
```

### Live Deployment
```bash
curl -s https://ia-educacao-v2.onrender.com/api/settings/models | grep -o '"is_default":true' | wc -l
# Expected: 1
```

## TDD Process Used

1. **RED:** Wrote failing tests for uniqueness validation
2. **GREEN:** Implemented `_ensure_single_default()` method
3. **REFACTOR:** Documentation added

## Lessons Learned

1. **Data validation on load is critical** - Don't trust persisted data
2. **Auto-correction is better than failing** - Fix corrupted data silently with logging
3. **Preference rules matter** - When multiple defaults exist, having a deterministic choice (Haiku) prevents randomness

## Related Files

- `IA_Educacao_V2/backend/chat_service.py` - ModelManager class
- `IA_Educacao_V2/backend/tests/unit/test_model_manager.py` - Tests
- `IA_Educacao_V2/backend/tests/README.md` - Test documentation
- `docs/PLAN_DEFAULT_MODELS.md` - Original plan
