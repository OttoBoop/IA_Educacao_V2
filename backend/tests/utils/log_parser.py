"""
Log parser module for analyzing pytest output and categorizing failures.

Provides:
- TestResultParser: Parse pytest console output and JSON reports
- FailureCategorizer: Categorize failures by type for targeted fixes
- ReportGenerator: Generate user-friendly markdown reports
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class FailureCategory(Enum):
    """Categories of test failures for targeted fix suggestions."""

    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    ASSERTION_FAIL = "assertion_fail"
    API_ERROR = "api_error"
    JSON_PARSE_ERROR = "json_parse_error"
    FIXTURE_ERROR = "fixture_error"
    TIMEOUT = "timeout"
    KEY_ERROR = "key_error"
    CONNECTION_ERROR = "connection_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN = "unknown"


@dataclass
class CodeLocation:
    """Location of code in a file."""

    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None

    def __str__(self) -> str:
        result = self.file_path
        if self.line_number:
            result += f":{self.line_number}"
        if self.function_name:
            result += f" in {self.function_name}"
        return result


@dataclass
class TestFailure:
    """Represents a single test failure with details."""

    test_name: str
    test_file: str
    error_message: str
    category: FailureCategory
    traceback: str = ""
    location: Optional[CodeLocation] = None
    duration: float = 0.0
    markers: list[str] = field(default_factory=list)
    fixtures_used: list[str] = field(default_factory=list)
    suggested_fix: str = ""


@dataclass
class TestResult:
    """Represents overall test run results."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    failures: list[TestFailure] = field(default_factory=list)
    command: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class FailureCategorizer:
    """Categorizes test failures based on error patterns."""

    # Pattern -> Category mapping
    PATTERNS = {
        FailureCategory.IMPORT_ERROR: [
            r"ImportError",
            r"ModuleNotFoundError",
            r"No module named",
        ],
        FailureCategory.SYNTAX_ERROR: [
            r"SyntaxError",
            r"IndentationError",
            r"TabError",
        ],
        FailureCategory.ASSERTION_FAIL: [
            r"AssertionError",
            r"assert\s+",
            r"expected.*got",
            r"!=",
        ],
        FailureCategory.API_ERROR: [
            r"APIError",
            r"RateLimitError",
            r"AuthenticationError",
            r"InvalidAPIKey",
            r"openai\.error",
            r"anthropic\.error",
        ],
        FailureCategory.JSON_PARSE_ERROR: [
            r"JSONDecodeError",
            r"json\.loads",
            r"Expecting.*JSON",
            r"Invalid JSON",
        ],
        FailureCategory.FIXTURE_ERROR: [
            r"fixture.*not found",
            r"conftest",
            r"@pytest\.fixture",
            r"FixtureLookupError",
        ],
        FailureCategory.TIMEOUT: [
            r"TimeoutError",
            r"pytest\.mark\.timeout",
            r"timed out",
            r"deadline exceeded",
        ],
        FailureCategory.KEY_ERROR: [
            r"KeyError",
        ],
        FailureCategory.TYPE_ERROR: [
            r"TypeError",
            r"expected.*type",
        ],
        FailureCategory.VALUE_ERROR: [
            r"ValueError",
            r"invalid value",
        ],
        FailureCategory.CONNECTION_ERROR: [
            r"ConnectionError",
            r"ConnectionRefused",
            r"httpx\.",
            r"requests\.exceptions",
            r"aiohttp\.",
            r"Network.*unreachable",
        ],
        FailureCategory.FILE_NOT_FOUND: [
            r"FileNotFoundError",
            r"No such file",
            r"Path.*does not exist",
        ],
        FailureCategory.PERMISSION_ERROR: [
            r"PermissionError",
            r"Permission denied",
            r"Access denied",
        ],
    }

    # Fix suggestions per category
    FIX_SUGGESTIONS = {
        FailureCategory.IMPORT_ERROR: [
            "Check if the module is installed: pip install <module>",
            "Verify the import path is correct",
            "Ensure __init__.py exists in the package",
        ],
        FailureCategory.SYNTAX_ERROR: [
            "Check for missing colons, parentheses, or brackets",
            "Verify indentation is consistent (spaces vs tabs)",
            "Look for unclosed strings or comments",
        ],
        FailureCategory.ASSERTION_FAIL: [
            "Compare expected vs actual values in the test",
            "Check if the implementation logic is correct",
            "Verify test expectations match the requirements",
        ],
        FailureCategory.API_ERROR: [
            "Check if API keys are configured correctly",
            "Verify API rate limits haven't been exceeded",
            "Use --skip-expensive to skip API tests temporarily",
        ],
        FailureCategory.JSON_PARSE_ERROR: [
            "Validate the JSON structure being parsed",
            "Check for trailing commas or missing quotes",
            "Verify the API response format hasn't changed",
        ],
        FailureCategory.FIXTURE_ERROR: [
            "Ensure the fixture is defined in conftest.py",
            "Check fixture scope (function, class, module, session)",
            "Verify fixture dependencies are available",
        ],
        FailureCategory.TIMEOUT: [
            "Increase test timeout with @pytest.mark.timeout(300)",
            "Check for infinite loops or blocking operations",
            "Consider using async/await for I/O operations",
        ],
        FailureCategory.KEY_ERROR: [
            "Verify the key exists in the dictionary",
            "Use .get() with a default value",
            "Check if the data structure has changed",
        ],
        FailureCategory.TYPE_ERROR: [
            "Check argument types match function signature",
            "Verify return types are correct",
            "Use type hints to catch issues early",
        ],
        FailureCategory.VALUE_ERROR: [
            "Validate input values before processing",
            "Check for empty or None values",
            "Verify value is within expected range",
        ],
        FailureCategory.CONNECTION_ERROR: [
            "Check if the service is running",
            "Verify network connectivity",
            "Check firewall/proxy settings",
        ],
        FailureCategory.FILE_NOT_FOUND: [
            "Verify the file path is correct",
            "Check if the file was created before the test",
            "Use Path.exists() to check before accessing",
        ],
        FailureCategory.PERMISSION_ERROR: [
            "Check file/directory permissions",
            "Run with appropriate privileges",
            "Verify the path is writable",
        ],
        FailureCategory.UNKNOWN: [
            "Review the full traceback for clues",
            "Search for the error message online",
            "Check recent code changes that might have caused this",
        ],
    }

    def categorize(self, error_message: str, traceback: str = "") -> FailureCategory:
        """Categorize a failure based on error message and traceback."""
        combined = f"{error_message}\n{traceback}"

        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return category

        return FailureCategory.UNKNOWN

    def get_suggestions(self, category: FailureCategory) -> list[str]:
        """Get fix suggestions for a failure category."""
        return self.FIX_SUGGESTIONS.get(category, self.FIX_SUGGESTIONS[FailureCategory.UNKNOWN])

    def extract_location(self, traceback: str) -> Optional[CodeLocation]:
        """Extract code location from traceback."""
        # Pattern: File "path/to/file.py", line 42, in function_name
        pattern = r'File "([^"]+)", line (\d+)(?:, in (\w+))?'
        matches = list(re.finditer(pattern, traceback))

        if not matches:
            return None

        # Get the last match (usually the actual error location)
        last_match = matches[-1]
        return CodeLocation(
            file_path=last_match.group(1),
            line_number=int(last_match.group(2)),
            function_name=last_match.group(3),
        )


class TestResultParser:
    """Parses pytest output and JSON reports."""

    def __init__(self):
        self.categorizer = FailureCategorizer()

    def parse_pytest_output(self, output: str) -> TestResult:
        """Parse pytest console output into TestResult."""
        result = TestResult()

        # Extract summary line: "5 passed, 2 failed, 1 skipped in 3.45s"
        summary_pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error|in\s+([\d.]+)s"
        for match in re.finditer(summary_pattern, output):
            if match.group(1):
                result.passed = int(match.group(1))
            elif match.group(2):
                result.failed = int(match.group(2))
            elif match.group(3):
                result.skipped = int(match.group(3))
            elif match.group(4):
                result.errors = int(match.group(4))
            elif match.group(5):
                result.duration = float(match.group(5))

        result.total = result.passed + result.failed + result.skipped + result.errors

        # Extract individual failures
        failure_blocks = self._extract_failure_blocks(output)
        for block in failure_blocks:
            failure = self._parse_failure_block(block)
            if failure:
                result.failures.append(failure)

        return result

    def _extract_failure_blocks(self, output: str) -> list[str]:
        """Extract individual failure blocks from pytest output."""
        blocks = []

        # Pattern for failure header: "FAILED test_file.py::test_name"
        # Or: "_____ test_name _____"
        failure_pattern = r"(?:FAILED\s+([^\s]+)|_{3,}\s+(\w+)\s+_{3,})"

        # Split on failure headers
        parts = re.split(r"(?=FAILED\s+|_{5,}\s+\w+\s+_{5,})", output)

        for part in parts:
            if "FAILED" in part or ("_" * 5) in part:
                blocks.append(part.strip())

        return blocks

    def _parse_failure_block(self, block: str) -> Optional[TestFailure]:
        """Parse a single failure block into TestFailure."""
        # Extract test name
        name_match = re.search(r"(?:FAILED\s+)?([^\s:]+)::(\w+)", block)
        if not name_match:
            # Try alternative pattern
            name_match = re.search(r"_{5,}\s+(\w+)\s+_{5,}", block)
            if not name_match:
                return None
            test_file = "unknown"
            test_name = name_match.group(1)
        else:
            test_file = name_match.group(1)
            test_name = name_match.group(2)

        # Extract error message (usually after the last "E" line)
        error_lines = re.findall(r"^E\s+(.+)$", block, re.MULTILINE)
        error_message = "\n".join(error_lines) if error_lines else "Unknown error"

        # Categorize the failure
        category = self.categorizer.categorize(error_message, block)
        location = self.categorizer.extract_location(block)
        suggestions = self.categorizer.get_suggestions(category)

        return TestFailure(
            test_name=test_name,
            test_file=test_file,
            error_message=error_message,
            category=category,
            traceback=block,
            location=location,
            suggested_fix=suggestions[0] if suggestions else "",
        )

    def parse_json_report(self, report_path: Path) -> TestResult:
        """Parse pytest JSON report into TestResult."""
        if not report_path.exists():
            return TestResult()

        with open(report_path) as f:
            data = json.load(f)

        result = TestResult()

        # Parse summary
        summary = data.get("summary", {})
        result.passed = summary.get("passed", 0)
        result.failed = summary.get("failed", 0)
        result.skipped = summary.get("skipped", 0)
        result.errors = summary.get("error", 0)
        result.total = summary.get("total", 0)
        result.duration = data.get("duration", 0.0)

        # Parse individual tests
        for test in data.get("tests", []):
            if test.get("outcome") == "failed":
                call = test.get("call", {})
                longrepr = call.get("longrepr", "")

                category = self.categorizer.categorize(longrepr)
                location = self.categorizer.extract_location(longrepr)
                suggestions = self.categorizer.get_suggestions(category)

                failure = TestFailure(
                    test_name=test.get("nodeid", "").split("::")[-1],
                    test_file=test.get("nodeid", "").split("::")[0],
                    error_message=call.get("crash", {}).get("message", "Unknown error"),
                    category=category,
                    traceback=longrepr,
                    location=location,
                    duration=call.get("duration", 0.0),
                    suggested_fix=suggestions[0] if suggestions else "",
                )
                result.failures.append(failure)

        return result

    def merge_results(self, *results: TestResult) -> TestResult:
        """Merge multiple TestResult objects into one."""
        merged = TestResult()

        for result in results:
            merged.total += result.total
            merged.passed += result.passed
            merged.failed += result.failed
            merged.skipped += result.skipped
            merged.errors += result.errors
            merged.duration += result.duration
            merged.failures.extend(result.failures)

        return merged


class ReportGenerator:
    """Generates user-friendly markdown reports from test results."""

    def __init__(self, categorizer: Optional[FailureCategorizer] = None):
        self.categorizer = categorizer or FailureCategorizer()

    def generate_markdown(self, result: TestResult, command: str = "") -> str:
        """Generate a markdown report from test results."""
        lines = [
            "# Test Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if command:
            lines.append(f"**Command:** `{command}`")

        lines.extend([
            f"**Duration:** {result.duration:.2f}s",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Status | Count |",
            "|--------|-------|",
            f"| Passed | {result.passed} |",
            f"| Failed | {result.failed} |",
            f"| Skipped | {result.skipped} |",
            f"| Errors | {result.errors} |",
            "",
            f"**Success Rate:** {result.success_rate:.1f}%",
            "",
        ])

        if not result.failures:
            lines.extend([
                "---",
                "",
                "## All Tests Passed!",
                "",
                "No failures to report.",
            ])
            return "\n".join(lines)

        # Group failures by category
        by_category: dict[FailureCategory, list[TestFailure]] = {}
        for failure in result.failures:
            if failure.category not in by_category:
                by_category[failure.category] = []
            by_category[failure.category].append(failure)

        lines.extend([
            "---",
            "",
            "## Failure Analysis",
            "",
        ])

        for category, failures in by_category.items():
            lines.extend([
                f"### {category.value.replace('_', ' ').title()} ({len(failures)} failure{'s' if len(failures) > 1 else ''})",
                "",
            ])

            # Add category-level suggestions
            suggestions = self.categorizer.get_suggestions(category)
            lines.extend([
                "**Common fixes:**",
            ])
            for suggestion in suggestions[:2]:
                lines.append(f"- {suggestion}")
            lines.append("")

            # Add individual failures
            for failure in failures:
                lines.extend([
                    f"#### {failure.test_file}::{failure.test_name}",
                    "",
                    f"- **Error:** `{failure.error_message[:200]}{'...' if len(failure.error_message) > 200 else ''}`",
                ])

                if failure.location:
                    lines.append(f"- **Location:** `{failure.location}`")

                if failure.suggested_fix:
                    lines.append(f"- **Suggested Fix:** {failure.suggested_fix}")

                lines.append("")

        # Add fix priority section
        lines.extend([
            "---",
            "",
            "## Fix Priority",
            "",
        ])

        # Priority order: Syntax > Import > Fixture > Assertion > Others
        priority_order = [
            FailureCategory.SYNTAX_ERROR,
            FailureCategory.IMPORT_ERROR,
            FailureCategory.FIXTURE_ERROR,
            FailureCategory.ASSERTION_FAIL,
        ]

        priority_num = 1
        for category in priority_order:
            if category in by_category:
                lines.append(f"{priority_num}. **{category.value.replace('_', ' ').title()}** - Fix these first")
                priority_num += 1

        for category in by_category:
            if category not in priority_order:
                lines.append(f"{priority_num}. **{category.value.replace('_', ' ').title()}**")
                priority_num += 1

        return "\n".join(lines)

    def generate_json(self, result: TestResult) -> dict:
        """Generate JSON report from test results."""
        return {
            "timestamp": result.timestamp.isoformat(),
            "summary": {
                "total": result.total,
                "passed": result.passed,
                "failed": result.failed,
                "skipped": result.skipped,
                "errors": result.errors,
                "duration": result.duration,
                "success_rate": result.success_rate,
            },
            "failures": [
                {
                    "test_name": f.test_name,
                    "test_file": f.test_file,
                    "category": f.category.value,
                    "error_message": f.error_message,
                    "location": str(f.location) if f.location else None,
                    "suggested_fix": f.suggested_fix,
                }
                for f in result.failures
            ],
            "failures_by_category": {
                category.value: len([f for f in result.failures if f.category == category])
                for category in FailureCategory
                if any(f.category == category for f in result.failures)
            },
        }
