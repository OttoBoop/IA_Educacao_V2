"""
Test matcher for finding relevant tests for features/components.

Provides:
- Match tests to features based on patterns
- Evaluate test coverage sufficiency
- Suggest which tests to run
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TestInfo:
    """Information about a test."""

    file_path: Path
    test_name: str
    markers: list[str] = field(default_factory=list)
    docstring: str = ""
    line_number: int = 0

    @property
    def full_id(self) -> str:
        """Get pytest-style test ID."""
        return f"{self.file_path}::{self.test_name}"

    @property
    def category(self) -> str:
        """Infer test category from path."""
        path_str = str(self.file_path)
        if "unit" in path_str:
            return "unit"
        elif "integration" in path_str:
            return "integration"
        elif "scenarios" in path_str:
            return "scenario"
        elif "models" in path_str:
            return "model"
        elif "ui" in path_str:
            return "ui"
        elif "fixtures" in path_str:
            return "fixture"
        return "unknown"


@dataclass
class CoverageGap:
    """Represents a gap in test coverage."""

    area: str
    description: str
    suggested_tests: list[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high


@dataclass
class MatchResult:
    """Result of matching tests to a feature."""

    feature: str
    matched_tests: list[TestInfo]
    coverage_score: float  # 0.0 to 1.0
    gaps: list[CoverageGap] = field(default_factory=list)
    is_sufficient: bool = True
    recommendation: str = ""


class TestMatcher:
    """Matches tests to features and evaluates coverage."""

    # Feature -> Test pattern mappings
    FEATURE_PATTERNS = {
        "document_upload": [
            r"test.*upload",
            r"test.*documento",
            r"test.*file",
            r"test.*storage",
            r"upload.*test",
        ],
        "document_download": [
            r"test.*download",
            r"test.*export",
            r"test.*regenerar",
        ],
        "document_corrupted": [
            r"test.*corrupt",
            r"test.*error",
            r"test.*invalid",
            r"test.*empty",
        ],
        "pipeline": [
            r"test.*pipeline",
            r"test.*executor",
            r"test.*etapa",
            r"test.*happy.*path",
        ],
        "chat": [
            r"test.*chat",
            r"test.*message",
            r"test.*conversation",
        ],
        "api": [
            r"test.*endpoint",
            r"test.*api",
            r"test.*route",
        ],
        "models": [
            r"test.*model",
            r"test.*openai",
            r"test.*anthropic",
            r"test.*google",
            r"test.*provider",
        ],
        "storage": [
            r"test.*storage",
            r"test.*supabase",
            r"test.*sync",
            r"test.*save",
        ],
    }

    # Expected test types per feature
    EXPECTED_COVERAGE = {
        "document_upload": {
            "unit": ["validation", "parsing"],
            "integration": ["endpoint", "storage"],
            "scenario": ["batch", "error_handling"],
        },
        "document_download": {
            "unit": ["format_conversion"],
            "integration": ["endpoint"],
            "scenario": ["full_workflow"],
        },
        "pipeline": {
            "unit": ["validation", "step_execution"],
            "integration": ["full_pipeline"],
            "scenario": ["happy_path", "error_recovery"],
        },
    }

    def __init__(self, tests_dir: Optional[Path] = None):
        """Initialize test matcher.

        Args:
            tests_dir: Path to tests directory. Defaults to backend/tests/
        """
        if tests_dir is None:
            tests_dir = Path(__file__).parent.parent
        self.tests_dir = Path(tests_dir)
        self._test_cache: Optional[list[TestInfo]] = None

    def discover_tests(self, refresh: bool = False) -> list[TestInfo]:
        """Discover all tests in the tests directory.

        Args:
            refresh: Force refresh of cached tests

        Returns:
            List of TestInfo objects
        """
        if self._test_cache is not None and not refresh:
            return self._test_cache

        tests = []
        for test_file in self.tests_dir.rglob("test_*.py"):
            tests.extend(self._extract_tests_from_file(test_file))

        self._test_cache = tests
        return tests

    def _extract_tests_from_file(self, file_path: Path) -> list[TestInfo]:
        """Extract test information from a Python file."""
        tests = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return tests

        # Pattern to match test functions/methods
        # Matches: def test_xxx(, async def test_xxx(
        test_pattern = r"^(?:async\s+)?def\s+(test_\w+)\s*\("
        marker_pattern = r"@pytest\.mark\.(\w+)"

        lines = content.split("\n")
        current_markers = []

        for i, line in enumerate(lines, 1):
            # Check for markers
            marker_match = re.search(marker_pattern, line)
            if marker_match:
                current_markers.append(marker_match.group(1))
                continue

            # Check for test function
            test_match = re.match(test_pattern, line.strip())
            if test_match:
                test_name = test_match.group(1)

                # Get docstring if present
                docstring = ""
                if i < len(lines):
                    next_lines = "\n".join(lines[i : i + 5])
                    doc_match = re.search(r'"""(.+?)"""', next_lines, re.DOTALL)
                    if doc_match:
                        docstring = doc_match.group(1).strip()

                tests.append(
                    TestInfo(
                        file_path=file_path,
                        test_name=test_name,
                        markers=current_markers.copy(),
                        docstring=docstring,
                        line_number=i,
                    )
                )
                current_markers = []
            elif not line.strip().startswith("@"):
                # Reset markers if we hit a non-decorator line
                current_markers = []

        return tests

    def match_feature(self, feature: str) -> MatchResult:
        """Match tests to a feature.

        Args:
            feature: Feature name (e.g., "document_upload")

        Returns:
            MatchResult with matched tests and coverage info
        """
        all_tests = self.discover_tests()

        # Get patterns for this feature
        patterns = self.FEATURE_PATTERNS.get(feature, [])
        if not patterns:
            # Try to match feature name directly
            patterns = [rf"test.*{feature}", rf"{feature}.*test"]

        # Find matching tests
        matched = []
        for test in all_tests:
            for pattern in patterns:
                if re.search(pattern, test.test_name, re.IGNORECASE) or re.search(
                    pattern, str(test.file_path), re.IGNORECASE
                ):
                    matched.append(test)
                    break

        # Calculate coverage score and gaps
        coverage_score, gaps = self._evaluate_coverage(feature, matched)

        is_sufficient = coverage_score >= 0.6 and len(gaps) == 0

        recommendation = self._generate_recommendation(feature, matched, gaps)

        return MatchResult(
            feature=feature,
            matched_tests=matched,
            coverage_score=coverage_score,
            gaps=gaps,
            is_sufficient=is_sufficient,
            recommendation=recommendation,
        )

    def _evaluate_coverage(
        self, feature: str, tests: list[TestInfo]
    ) -> tuple[float, list[CoverageGap]]:
        """Evaluate test coverage for a feature.

        Returns:
            Tuple of (coverage_score, list of gaps)
        """
        expected = self.EXPECTED_COVERAGE.get(feature, {})
        if not expected:
            # No expected coverage defined, assume sufficient if any tests exist
            return (1.0 if tests else 0.0, [])

        gaps = []
        covered = 0
        total = 0

        # Check each expected category
        for category, expected_types in expected.items():
            total += len(expected_types)

            # Find tests in this category
            category_tests = [t for t in tests if t.category == category]

            for expected_type in expected_types:
                # Check if any test matches this type
                found = any(
                    expected_type.lower() in t.test_name.lower() or expected_type.lower() in t.docstring.lower()
                    for t in category_tests
                )

                if found:
                    covered += 1
                else:
                    gaps.append(
                        CoverageGap(
                            area=f"{category}/{expected_type}",
                            description=f"Missing {category} test for {expected_type}",
                            suggested_tests=[f"test_{expected_type}_{feature}"],
                            priority="high" if category == "unit" else "medium",
                        )
                    )

        score = covered / total if total > 0 else 0.0
        return (score, gaps)

    def _generate_recommendation(
        self, feature: str, tests: list[TestInfo], gaps: list[CoverageGap]
    ) -> str:
        """Generate a recommendation for test coverage."""
        if not tests:
            return f"No tests found for '{feature}'. Consider creating unit tests first."

        if not gaps:
            return f"Test coverage for '{feature}' looks good. Found {len(tests)} relevant tests."

        high_priority = [g for g in gaps if g.priority == "high"]
        if high_priority:
            areas = ", ".join(g.area for g in high_priority[:3])
            return f"Missing critical tests for: {areas}. Create these tests first."

        return f"Found {len(tests)} tests but {len(gaps)} coverage gaps. Consider adding more tests."

    def find_tests_by_file(self, source_file: Path) -> list[TestInfo]:
        """Find tests related to a source file.

        Args:
            source_file: Path to a source file (e.g., executor.py)

        Returns:
            List of related tests
        """
        all_tests = self.discover_tests()
        file_stem = source_file.stem

        related = []
        for test in all_tests:
            # Check if test file name matches
            if file_stem in test.file_path.stem:
                related.append(test)
                continue

            # Check if source file is imported or referenced in test
            try:
                test_content = test.file_path.read_text(encoding="utf-8")
                if file_stem in test_content:
                    related.append(test)
            except Exception:
                pass

        return related

    def find_tests_by_pattern(self, pattern: str) -> list[TestInfo]:
        """Find tests matching a pattern.

        Args:
            pattern: Regex pattern to match against test names

        Returns:
            List of matching tests
        """
        all_tests = self.discover_tests()

        return [t for t in all_tests if re.search(pattern, t.test_name, re.IGNORECASE)]

    def get_test_command(self, tests: list[TestInfo], verbose: bool = True) -> str:
        """Generate a pytest command for the given tests.

        Args:
            tests: List of tests to run
            verbose: Add -v flag

        Returns:
            Pytest command string
        """
        if not tests:
            return "pytest tests/ -v"

        # Group tests by file
        files = set(str(t.file_path) for t in tests)

        if len(files) <= 3:
            # Run specific files
            files_str = " ".join(files)
            return f"pytest {files_str}{' -v' if verbose else ''}"
        else:
            # Run with pattern matching
            patterns = set(t.test_name for t in tests[:5])
            pattern_str = "|".join(patterns)
            return f"pytest tests/ -k '{pattern_str}'{' -v' if verbose else ''}"

    def suggest_new_tests(self, feature: str, gaps: list[CoverageGap]) -> list[dict]:
        """Suggest new tests to fill coverage gaps.

        Args:
            feature: Feature name
            gaps: List of coverage gaps

        Returns:
            List of suggested test specifications
        """
        suggestions = []

        for gap in gaps:
            category = gap.area.split("/")[0] if "/" in gap.area else "unit"
            test_type = gap.area.split("/")[1] if "/" in gap.area else gap.area

            suggestion = {
                "name": f"test_{test_type}_{feature}",
                "category": category,
                "file": f"tests/{category}/test_{feature}.py",
                "description": gap.description,
                "priority": gap.priority,
                "template": self._get_test_template(category, feature, test_type),
            }
            suggestions.append(suggestion)

        return suggestions

    def _get_test_template(self, category: str, feature: str, test_type: str) -> str:
        """Get a test template for a given category."""
        if category == "unit":
            return f'''
def test_{test_type}_{feature}():
    """Test {test_type} for {feature}."""
    # Arrange
    # TODO: Set up test data

    # Act
    # TODO: Call the function being tested

    # Assert
    # TODO: Verify the result
    assert False, "Test not implemented"
'''
        elif category == "integration":
            return f'''
@pytest.mark.integration
def test_{test_type}_{feature}(test_client):
    """Integration test for {test_type} in {feature}."""
    # Arrange
    # TODO: Set up test data

    # Act
    response = test_client.post("/api/...")

    # Assert
    assert response.status_code == 200
    assert False, "Test not implemented"
'''
        else:
            return f'''
@pytest.mark.{category}
def test_{test_type}_{feature}():
    """Scenario test for {test_type} in {feature}."""
    # TODO: Implement full scenario test
    assert False, "Test not implemented"
'''

    def get_coverage_summary(self) -> dict:
        """Get a summary of test coverage across all features.

        Returns:
            Dict with coverage info per feature
        """
        summary = {}

        for feature in self.FEATURE_PATTERNS.keys():
            result = self.match_feature(feature)
            summary[feature] = {
                "test_count": len(result.matched_tests),
                "coverage_score": result.coverage_score,
                "is_sufficient": result.is_sufficient,
                "gaps_count": len(result.gaps),
            }

        return summary
