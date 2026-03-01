# IA_Educacao_V2 (NOVO CR) — Claude Code Configuration

> For general workspace rules (TDD, git workflow, discovery chain, subagents), see the root [CLAUDE.md](../CLAUDE.md).
> This file contains NOVO CR-specific configuration only.

---

## Project Overview

**NOVO CR** is an educational platform for automated test/exam grading using multiple AI models (OpenAI, Anthropic, Google). It processes student submissions, analyzes responses, and generates detailed feedback reports.

**Live Deployment:** https://ia-educacao-v2.onrender.com

---

## Quick Reference

| Resource | Location |
|----------|----------|
| Live API | `https://ia-educacao-v2.onrender.com/api/` |
| Backend Code | `backend/` |
| Frontend | `frontend/` |
| Test Suite | `backend/tests/` |
| **Style Guide** | `../.claude/design/STYLE_GUIDE.md` |
| **UI Element Catalog** | `../.claude/design/UI_ELEMENT_CATALOG.md` |
| Testing Guide | `backend/docs/TESTING_GUIDE.md` |
| Models Reference | `backend/docs/MODELS_REFERENCE.md` |

---

## MANDATORY: Check Design Guides First

Before making ANY UI/frontend decisions (layout, colors, components, visual patterns), ALWAYS read:
- `../.claude/design/STYLE_GUIDE.md` — design philosophy, branding, color palette, typography, visual standards
- `../.claude/design/UI_ELEMENT_CATALOG.md` — living catalog of all UI elements with current issues

These guides document existing patterns. Do NOT propose new UI elements or change visual patterns without checking them first. After implementing UI changes, UPDATE the catalog with any new elements added.

---

## Testing

### MANDATORY: Check Testing Guides First

Before making ANY test-related decisions (where tests go, what framework to use, what patterns to follow), ALWAYS read:
- `backend/tests/README.md` — test directory structure, markers, conventions
- `backend/docs/TESTING_GUIDE.md` — detailed testing guide

These guides document existing patterns. Do NOT propose new test locations or frameworks without checking them first.

### CRITICAL: Always Run from Backend Directory!

```bash
cd IA_Educacao_V2/backend  # REQUIRED - imports fail otherwise
```

### Feature-Conscious Testing

Run the **appropriate tests** based on what you changed:

| If You Changed... | Run These Tests |
|-------------------|-----------------|
| **Any code** (minimum) | `pytest tests/unit/ -v` |
| **UI/Frontend** | `pytest tests/ui/ -v` (requires local server) |
| **Model/AI code** | `pytest tests/models/ -v -m "not expensive"` |
| **Pipeline/executor** | `pytest tests/scenarios/ -v` |
| **API endpoints** | `pytest tests/integration/ -v` |
| **Before pushing** | `python test_runner.py --local` (full suite, run from backend/) |

### Core Tests (Must Always Pass)

These verify the system fundamentals:

```bash
# Quick sanity check (~30s)
pytest tests/unit/ -v

# Pipeline working? (~2min)
pytest tests/scenarios/test_happy_path.py -v

# Chat working?
pytest tests/integration/test_api_quick.py -v
```

### Quick Reference

```bash
# All tests with cheap models (recommended) — run from backend/
python test_runner.py --local

# Skip slow/expensive tests
pytest tests/ -v -m "not slow and not expensive"

# Specific provider only
pytest tests/ -v -m "openai"
pytest tests/ -v -m "anthropic"
pytest tests/ -v -m "google"

# UI tests (start server first!)
python -m uvicorn main_v2:app --port 8000 &
pytest tests/ui/ -v
```

### Model IDs Reference (Verified Feb 2026)

**Use these exact IDs** - check online docs if errors occur!

| Provider | Cheap/Fast | Balanced | Powerful |
|----------|------------|----------|----------|
| **OpenAI** | gpt-5-mini | gpt-5 | o3, o3-mini |
| **Anthropic** | claude-haiku-4-5-20251001 | claude-sonnet-4-5-20250929 | claude-opus-4-5-20251101 |
| **Google** | gemini-3-flash-preview | gemini-2.5-pro | gemini-3-pro-preview |

### Test Locations

```
tests/
├── unit/        # Fast, no API calls
├── models/      # AI provider tests (need API keys)
├── integration/ # External services
├── ui/          # Playwright browser tests
├── scenarios/   # E2E workflows
└── fixtures/    # Test data factories
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Run from `backend/` directory |
| API key missing | Check env vars or `data/api_keys.json` |
| Timeout | Use `--timeout 180` or faster model |
| Tests skip | Run with `-v` to see skip reasons |

**Detailed docs:** `backend/tests/README.md`, `backend/docs/TESTING_GUIDE.md`

---

## Common Workflows

### 1. Run Tests & Fix Failures

```bash
# MUST be in backend directory for imports to work!
cd IA_Educacao_V2/backend
pytest tests/unit/ -v
# Fix failures, then run again
```

### 2. Deploy & Verify (MANDATORY - READ THIS!)

**A task is NEVER complete until the live deployment is verified working.**

```bash
# Step 1: Commit and push
git add [files]
git commit -m "type: description"
git push  # Check for errors!

# Step 2: Begin verification loop
# Poll the API every 30-60 seconds to detect when deployment completes
# Look for changes in behavior that match your fix

# Step 3: If deployment takes too long (>5 min), DEBUG:
#   - Did git push succeed? Check for errors
#   - Is remote commit hash correct? `git ls-remote origin main`
#   - Start local server and compare behavior:
#     cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000
#   - Test local vs live to confirm code difference

# Step 4: VERIFY the fix works on LIVE
curl -s https://ia-educacao-v2.onrender.com/api/[endpoint-you-changed]

# Step 5: If changes touch frontend (index_v2.html, CSS, JS):
#   Run a journey to validate UX (see "Journey-Driven UX Validation" section)
#   Use tester persona with a checklist of what should work

# Step 6: ONLY THEN declare the task complete
```

**DO NOT** assume deployment will work. **DO NOT** guess. **VERIFY.**
**DO NOT** sleep/wait passively - actively poll and debug if needed.
**IF UI CHANGED:** Run a journey after verifying the deploy. See section "Journey-Driven UX Validation".

### 3. Debug Live API

```bash
# List materias
curl -s https://ia-educacao-v2.onrender.com/api/materias

# List turmas for a materia
curl -s "https://ia-educacao-v2.onrender.com/api/turmas?materia_id=ID"

# List atividades for a turma
curl -s "https://ia-educacao-v2.onrender.com/api/atividades?turma_id=ID"

# Get documentos for an atividade
curl -s "https://ia-educacao-v2.onrender.com/api/documentos?atividade_id=ID"
```

### 4. Start Local Server

```bash
cd IA_Educacao_V2/backend
python -m uvicorn main_v2:app --port 8000 --reload
```

### 5. Run Investor Journey Agent

**Preferred method:** Type `/journey` — it handles everything (pre-flight checks, persona menu, execution, analysis).

The Journey Agent simulates realistic users navigating the app. It uses Playwright + Claude Haiku to roleplay as different personas, taking screenshots and documenting frustration at each step. It produces a **self-contained HTML report** you can open in a browser or email.

**Manual CLI (if needed):**
```bash
# MUST run from backend directory
cd IA_Educacao_V2/backend

# Basic run against production (investor persona, iPhone viewport, 10 steps)
python -m tests.ui.investor_journey_agent \
    --persona investor \
    --url https://ia-educacao-v2.onrender.com \
    --max-steps 10

# Available personas: investor, student, confused_teacher, power_user, tester
# Available viewports: iphone_14, iphone_se, pixel_7, ipad_pro, desktop_1080p, desktop_1440p

# Other useful flags:
#   --mode in_depth    → adds pain point analysis
#   --no-headless      → show browser window
#   --local            → use http://localhost:8000
#   --no-narrate       → disable progress summaries
#   --viewport pixel_7 → change device
```

**After the run completes:**
1. It prints all generated file paths (HTML, markdown, JSON, screenshots)
2. The HTML report is the main deliverable — open it in a browser
3. Use `/analyze-journey` to have Claude Code read and summarize the results
4. Requires `ANTHROPIC_API_KEY` (for LLM decisions) and Playwright installed

**Output location:** `investor_journey_reports/<timestamp>/`

### 6. Journey-Driven UX Validation

**This is the closed-loop workflow for using journey findings to drive quality improvements.**

After any journey run, Claude Code should automatically follow this loop:

```
Journey Run -> /analyze-journey -> Triage (minor/major)
    -> For each finding: /discover -> /plan -> /tdd -> Deploy
    -> Re-run journey (tester persona) to verify fixes
```

#### When to Run Journeys

| Trigger | Action |
|---------|--------|
| **After deploying UI changes** | ALWAYS run a journey if changes touch `index_v2.html`, CSS, or JS |
| **On-demand** | Anytime the user requests it |
| **After fixing journey findings** | Re-run with `tester` persona to verify fixes |

Claude Code should **proactively suggest** a journey run after UI deploys. No special commands needed — this is default behavior.

#### Minor vs Major Classification (Conservative Defaults)

When triaging journey findings, classify each issue:

| Classification | Criteria | Action |
|---------------|----------|--------|
| **Minor** | CSS-only property change on existing element (cursor, opacity, color). NO new visual features. | Propose TDD fix, ask user for go-ahead |
| **Major** | Adds new elements, changes HTML structure, adds JS behavior, introduces new visual features, changes layout | Enter `/discover` mode, get user approval |
| **Uncertain** | Doesn't clearly fit either category | **Default to major** — always ask |

**The Chevron Test:** Adding a `::after` pseudo-element with a chevron icon = **MAJOR** (new visual feature, not a property fix). When in doubt, it's major.

#### Cost Configuration

- **Default daily cap:** $1/day (~3-10 journey runs)
- Claude Code tracks cumulative journey cost per session
- **After hitting cap:** Ask user for manual approval before additional runs
- **Adjustable:** User can say "raise the cap" or "no limit today"

#### Dynamic Step Count

Claude Code chooses step count based on context — no fixed default:

| Context | Suggested Steps |
|---------|----------------|
| Verifying a CSS fix | 5-10 steps |
| Testing a UI feature | 15-25 steps |
| Deep exploration of nested features | 25-50 steps |
| Quick smoke test | 5 steps |

Can abort early if the issue is reproduced/verified immediately. User can always override with an explicit count.

#### Local Fallback Pattern

If the live deployment is down:
1. Run journey against `localhost:8000` as a quick check
2. **BUT** this creates a mandatory follow-up: verify on live once it's back
3. **Never** declare a journey-verified task complete based on local-only results

#### Tester Persona

Use the `tester` persona for targeted verification after fixes:

```bash
python -m tests.ui.investor_journey_agent \
    --persona tester \
    --goal "Verify: 1) Sidebar works on mobile 2) Cards show click affordance" \
    --max-steps 15
```

**Interactive checklist flow:**
1. Claude Code reads previous journey findings
2. Proposes a verification checklist to user
3. User approves/modifies the checklist
4. Claude Code runs tester persona with the checklist as `--goal`

---

## Project Structure

```
IA_Educacao_V2/
├── CLAUDE.md                    # This file (NOVO CR-specific config)
├── backend/
│   ├── main_v2.py               # FastAPI app entry
│   ├── chat_service.py          # AI chat integration
│   ├── executor.py              # Pipeline execution
│   ├── tests/                   # Test suite
│   │   ├── unit/
│   │   ├── models/
│   │   ├── integration/
│   │   ├── ui/
│   │   ├── scenarios/
│   │   └── fixtures/
│   └── docs/
│       ├── TESTING_GUIDE.md
│       └── MODELS_REFERENCE.md
└── frontend/
    ├── index_v2.html
    └── static/
```

---

## External Services

### Live Deployment
- **URL:** https://ia-educacao-v2.onrender.com
- **Platform:** Render (auto-deploys on git push to `main` branch)
- **Typical deploy time:** 2-5 minutes after push

### AI Model Providers
- **OpenAI:** GPT-5, GPT-5-mini, o3-mini
- **Anthropic:** Claude Opus 4.5, Sonnet 4.5, Haiku 4.5
- **Google:** Gemini 3 Flash/Pro Preview, Gemini 2.5

### Infrastructure
- **Render:** Hosting & deployment
- **Supabase:** Database & file storage
- **E2B:** Code execution sandbox

---

## Documentation Links

When you need reference docs for AI providers or infrastructure:
- **OpenAI:** https://platform.openai.com/docs
- **Anthropic:** https://docs.anthropic.com
- **Google AI:** https://ai.google.dev/docs
- **Render:** https://render.com/docs
- **Supabase:** https://supabase.com/docs
- **E2B:** https://e2b.dev/docs

---

## Environment Variables

Required for full functionality:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
E2B_API_KEY=e2b_...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
```

---

## Warnings & Gotchas

### CRITICAL: Deployment Verification Required

**A bug fix or feature is NEVER complete until verified on the LIVE deployment.**

This means:
1. Push code to git
2. Wait for Render deployment to complete (2-5 min)
3. Test the LIVE API endpoint with curl or browser
4. Confirm the fix actually works in production
5. ONLY THEN mark the task as complete

**NEVER:**
- Declare "task complete" after just pushing code
- Assume deployment will work without testing
- Trust local tests alone - production environment differs
- Stop working before live verification
- Wait passively - actively poll and debug

**Verification Loop:**
1. Push code, check for errors
2. Poll live API every 30-60 seconds
3. If >5 min with no change: DEBUG
   - Verify remote has correct commit: `git ls-remote origin main`
   - Start local server: `python -m uvicorn main_v2:app --port 8000`
   - Compare local vs live behavior
   - If local works but live doesn't, investigate Render logs
4. Only mark complete when LIVE endpoint shows the fix

**Past Failure:** On 2026-01-30, a bug fix was declared complete after local tests passed, but the live deployment was never verified. The fix wasn't actually deployed. This wasted time and left the bug unfixed. See postmortem if needed.

---

### CRITICAL: API Provider Issues

When model API calls fail (OpenAI, Anthropic, Google):

1. **NEVER** change endpoints, model IDs, or API parameters from memory
2. **ALWAYS** fetch the latest documentation first:
   - OpenAI: https://platform.openai.com/docs
   - Anthropic: https://docs.anthropic.com
   - Google AI: https://ai.google.dev/docs
3. **ALWAYS** ask the user before making changes
4. **DOCUMENT** the solution in a commit message or note

This has caused many debugging hours in the past. Model IDs and endpoints change frequently - your training data may be outdated!

---

### DO NOT:
- Declare a task complete without verifying the LIVE deployment works
- Assume "git push" means the fix is deployed and working
- Change API keys/credentials without approval
- Modify model endpoints without checking docs AND user approval
- Make UI changes without reading the Design Guides first (`../.claude/design/`)

### ALWAYS:
- VERIFY fixes work on https://ia-educacao-v2.onrender.com BEFORE declaring complete
- Wait for Render deployment and test the live API endpoint
- Check Design Guides before any UI decisions
- Run tests from the `backend/` directory

---

## Deprecation & Unification

The `../docs/guides/GENERAL_DEPRECATION_AND_UNIFICATION_GUIDE.md` is the **canonical deprecation guide** for this project. Use it whenever you need to deprecate, unify, or remove anything (endpoints, files, modules):

1. Consult `../docs/guides/GENERAL_DEPRECATION_AND_UNIFICATION_GUIDE.md`
2. Follow the TDD workflow from the guide
3. Document in the deprecation history
4. Verify whether to unify or NOT before starting

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-18 | Initial creation — extracted from root CLAUDE.md during generalization |
