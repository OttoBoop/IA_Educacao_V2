"""
E2E rebrand verification test — comprehensive catch-all sweep.

G-T1: Scans ALL project files for residual 'Prova AI' brand references.
Catches anything missed by individual feature tests (A-T1 through F-T4).

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_e2e.py -v
"""

import re
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BACKEND_DIR.parent  # IA_Educacao_V2/
WORKSPACE_DIR = PROJECT_DIR.parent  # prova-ai/
FRONTEND_DIR = PROJECT_DIR / "frontend"

# Files that reference old brand name by design
EXCLUDED_PREFIXES = ("PLAN_", "DISCOVERY_", "IDEAS_", "test_rebrand_")
EXCLUDED_NAMES = {"openapi_dump.json"}


def _is_excluded(path: Path) -> bool:
    """Check if file should be excluded from brand scanning."""
    if path.name in EXCLUDED_NAMES:
        return True
    for prefix in EXCLUDED_PREFIXES:
        if path.name.startswith(prefix):
            return True
    if "__pycache__" in str(path):
        return True
    return False


def _find_violations(directory: Path, extensions: set, patterns: list) -> list:
    """Scan directory recursively for brand reference violations."""
    violations = []
    for ext in extensions:
        for f in directory.rglob(f"*{ext}"):
            if _is_excluded(f):
                continue
            try:
                content = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for i, line in enumerate(content.split("\n"), 1):
                for pattern in patterns:
                    if pattern in line:
                        rel = f.relative_to(directory)
                        violations.append(f"{rel}:{i}: {line.strip()[:120]}")
    return violations


# ── Catch-All Sweep: No Residual Brand References ──────────


class TestNoResidualBrandRefs:
    """G-T1: No residual 'Prova AI' brand references across the entire project."""

    def test_frontend_no_prova_ai(self):
        """All frontend files must be free of 'Prova AI' brand reference."""
        violations = _find_violations(
            FRONTEND_DIR, {".html", ".js", ".css"}, ["Prova AI"]
        )
        assert not violations, (
            f"Found {len(violations)} 'Prova AI' in frontend:\n"
            + "\n".join(violations)
        )

    def test_frontend_no_old_localstorage_prefix(self):
        """Frontend must not use old 'prova-ai-' localStorage prefix."""
        violations = _find_violations(
            FRONTEND_DIR, {".html", ".js"}, ["prova-ai-"]
        )
        assert not violations, (
            f"Found {len(violations)} 'prova-ai-' keys:\n"
            + "\n".join(violations)
        )

    def test_backend_py_no_prova_ai(self):
        """All backend .py files must be free of 'Prova AI' / 'PROVA AI'."""
        violations = _find_violations(
            BACKEND_DIR, {".py"}, ["Prova AI", "PROVA AI"]
        )
        assert not violations, (
            f"Found {len(violations)} brand refs in backend .py:\n"
            + "\n".join(violations)
        )

    def test_scripts_no_prova_ai(self):
        """Shell scripts must be free of 'Prova AI' / 'PROVA AI'."""
        violations = _find_violations(
            PROJECT_DIR, {".sh"}, ["Prova AI", "PROVA AI"]
        )
        assert not violations, (
            f"Found {len(violations)} brand refs in scripts:\n"
            + "\n".join(violations)
        )

    def test_docs_no_prova_ai(self):
        """All documentation .md files must be free of 'Prova AI'."""
        violations = []
        # Backend docs directory
        violations.extend(
            _find_violations(BACKEND_DIR / "docs", {".md"}, ["Prova AI"])
        )
        # Project-level markdown files
        for md in [PROJECT_DIR / "README.md", PROJECT_DIR / "CLAUDE.md"]:
            if md.exists() and not _is_excluded(md):
                content = md.read_text(encoding="utf-8")
                for i, line in enumerate(content.split("\n"), 1):
                    if "Prova AI" in line:
                        violations.append(f"{md.name}:{i}: {line.strip()[:120]}")
        # STYLE_GUIDE.md (workspace-level)
        sg = WORKSPACE_DIR / ".claude" / "design" / "STYLE_GUIDE.md"
        if sg.exists():
            content = sg.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                if "Prova AI" in line:
                    violations.append(f"STYLE_GUIDE.md:{i}: {line.strip()[:120]}")
        # tests/README.md
        tr = BACKEND_DIR / "tests" / "README.md"
        if tr.exists() and not _is_excluded(tr):
            content = tr.read_text(encoding="utf-8")
            for i, line in enumerate(content.split("\n"), 1):
                if "Prova AI" in line:
                    violations.append(f"tests/README.md:{i}: {line.strip()[:120]}")
        assert not violations, (
            f"Found {len(violations)} 'Prova AI' in docs:\n"
            + "\n".join(violations)
        )


# ── Positive Assertions: NOVO CR in Key Locations ──────────


class TestBrandPresence:
    """G-T1: 'NOVO CR' must be present in all key locations."""

    def test_html_title(self):
        """HTML <title> must contain 'NOVO CR'."""
        content = (FRONTEND_DIR / "index_v2.html").read_text(encoding="utf-8")
        match = re.search(r"<title>(.*?)</title>", content)
        assert match, "No <title> tag found"
        assert "NOVO CR" in match.group(1)

    def test_sidebar_brand_text(self):
        """Sidebar must display 'NOVO CR' brand text."""
        content = (FRONTEND_DIR / "index_v2.html").read_text(encoding="utf-8")
        assert "NOVO CR</span>" in content or "NOVO CR<" in content

    def test_tagline(self):
        """Tagline 'Mais que um Número' must be present."""
        content = (FRONTEND_DIR / "index_v2.html").read_text(encoding="utf-8")
        assert "Mais que um Número" in content

    def test_css_logo_cr(self):
        """CSS logo must display 'CR' text (not emoji)."""
        content = (FRONTEND_DIR / "index_v2.html").read_text(encoding="utf-8")
        match = re.search(r'class="logo-icon"[^>]*>(.*?)<', content)
        assert match, "No .logo-icon element found"
        assert "CR" in match.group(1)

    def test_fastapi_title(self):
        """FastAPI app title must contain 'NOVO CR'."""
        content = (BACKEND_DIR / "main_v2.py").read_text(encoding="utf-8")
        match = re.search(r'title\s*=\s*"(.+?)"', content)
        assert match, "No FastAPI title= found"
        assert "NOVO CR" in match.group(1)

    def test_readme_title(self):
        """README.md first line must contain 'NOVO CR'."""
        content = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")
        assert "NOVO CR" in content.split("\n")[0]

    def test_localstorage_novocr_prefix(self):
        """localStorage must use 'novocr-' key prefix."""
        content = (FRONTEND_DIR / "index_v2.html").read_text(encoding="utf-8")
        assert "novocr-" in content
