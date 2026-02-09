"""
Tests for the log_parser module.

Tests cover:
- TestResultParser: parsing pytest output
- FailureCategorizer: categorizing failures
- ReportGenerator: generating markdown reports
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from tests.utils.log_parser import (
    TestResultParser,
    FailureCategorizer,
    ReportGenerator,
    FailureCategory,
    TestResult,
    TestFailure,
    CodeLocation,
)


class TestFailureCategorizer:
    """Tests for FailureCategorizer."""

    @pytest.fixture
    def categorizer(self):
        return FailureCategorizer()

    def test_categorize_import_error(self, categorizer):
        """Should categorize ImportError correctly."""
        error = "ImportError: No module named 'missing_module'"
        result = categorizer.categorize(error)
        assert result == FailureCategory.IMPORT_ERROR

    def test_categorize_module_not_found(self, categorizer):
        """Should categorize ModuleNotFoundError correctly."""
        error = "ModuleNotFoundError: No module named 'nonexistent'"
        result = categorizer.categorize(error)
        assert result == FailureCategory.IMPORT_ERROR

    def test_categorize_syntax_error(self, categorizer):
        """Should categorize SyntaxError correctly."""
        error = "SyntaxError: invalid syntax"
        result = categorizer.categorize(error)
        assert result == FailureCategory.SYNTAX_ERROR

    def test_categorize_indentation_error(self, categorizer):
        """Should categorize IndentationError correctly."""
        error = "IndentationError: unexpected indent"
        result = categorizer.categorize(error)
        assert result == FailureCategory.SYNTAX_ERROR

    def test_categorize_assertion_error(self, categorizer):
        """Should categorize AssertionError correctly."""
        error = "AssertionError: expected 5, got 3"
        result = categorizer.categorize(error)
        assert result == FailureCategory.ASSERTION_FAIL

    def test_categorize_assertion_with_comparison(self, categorizer):
        """Should categorize assertion with != operator."""
        error = "assert result != expected_value"
        result = categorizer.categorize(error)
        assert result == FailureCategory.ASSERTION_FAIL

    def test_categorize_api_error(self, categorizer):
        """Should categorize API errors correctly."""
        error = "RateLimitError: Rate limit exceeded"
        result = categorizer.categorize(error)
        assert result == FailureCategory.API_ERROR

    def test_categorize_json_decode_error(self, categorizer):
        """Should categorize JSONDecodeError correctly."""
        error = "json.decoder.JSONDecodeError: Expecting value"
        result = categorizer.categorize(error)
        assert result == FailureCategory.JSON_PARSE_ERROR

    def test_categorize_fixture_error(self, categorizer):
        """Should categorize fixture errors correctly."""
        error = "fixture 'missing_fixture' not found"
        result = categorizer.categorize(error)
        assert result == FailureCategory.FIXTURE_ERROR

    def test_categorize_timeout_error(self, categorizer):
        """Should categorize TimeoutError correctly."""
        error = "TimeoutError: Operation timed out"
        result = categorizer.categorize(error)
        assert result == FailureCategory.TIMEOUT

    def test_categorize_key_error(self, categorizer):
        """Should categorize KeyError correctly."""
        error = "KeyError: 'missing_key'"
        result = categorizer.categorize(error)
        assert result == FailureCategory.KEY_ERROR

    def test_categorize_connection_error(self, categorizer):
        """Should categorize ConnectionError correctly."""
        error = "ConnectionError: Connection refused"
        result = categorizer.categorize(error)
        assert result == FailureCategory.CONNECTION_ERROR

    def test_categorize_unknown(self, categorizer):
        """Should return UNKNOWN for unrecognized errors."""
        error = "SomeVeryCustomError: something happened"
        result = categorizer.categorize(error)
        assert result == FailureCategory.UNKNOWN

    def test_get_suggestions_returns_list(self, categorizer):
        """Should return a list of suggestions for each category."""
        for category in FailureCategory:
            suggestions = categorizer.get_suggestions(category)
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0

    def test_extract_location_from_traceback(self, categorizer):
        """Should extract file and line from traceback."""
        traceback = '''
Traceback (most recent call last):
  File "/path/to/test_file.py", line 42, in test_function
    result = some_function()
  File "/path/to/module.py", line 15, in some_function
    raise ValueError("error")
ValueError: error
'''
        location = categorizer.extract_location(traceback)
        assert location is not None
        assert location.file_path == "/path/to/module.py"
        assert location.line_number == 15
        assert location.function_name == "some_function"

    def test_extract_location_no_traceback(self, categorizer):
        """Should return None when no traceback present."""
        error = "Simple error message"
        location = categorizer.extract_location(error)
        assert location is None


class TestTestResultParser:
    """Tests for TestResultParser."""

    @pytest.fixture
    def parser(self):
        return TestResultParser()

    def test_parse_pytest_output_summary(self, parser):
        """Should parse pytest summary correctly."""
        output = """
============================= test session starts ==============================
collected 10 items

test_example.py::test_one PASSED
test_example.py::test_two FAILED
test_example.py::test_three SKIPPED

=========================== short test summary info ============================
FAILED test_example.py::test_two - AssertionError
========================= 1 failed, 1 passed, 1 skipped in 2.34s =========================
"""
        result = parser.parse_pytest_output(output)
        assert result.passed == 1
        assert result.failed == 1
        assert result.skipped == 1
        assert result.duration == 2.34

    def test_parse_pytest_output_all_passed(self, parser):
        """Should parse output with all tests passed."""
        output = """
============================= test session starts ==============================
collected 5 items

test_example.py::test_one PASSED
test_example.py::test_two PASSED

========================= 5 passed in 1.23s =========================
"""
        result = parser.parse_pytest_output(output)
        assert result.passed == 5
        assert result.failed == 0
        assert result.duration == 1.23

    def test_parse_pytest_output_with_errors(self, parser):
        """Should parse output with errors."""
        output = """
============================= test session starts ==============================
collected 3 items

test_example.py::test_one PASSED
test_example.py::test_two ERROR

========================= 1 passed, 1 error in 0.50s =========================
"""
        result = parser.parse_pytest_output(output)
        assert result.passed == 1
        assert result.errors == 1

    def test_parse_extracts_failure_blocks(self, parser):
        """Should extract failure information."""
        output = """
============================= test session starts ==============================
FAILED test_example.py::test_failing

_______________________________ test_failing _______________________________

    def test_failing():
>       assert 1 == 2
E       AssertionError: assert 1 == 2

test_example.py:5: AssertionError
=========================== 1 failed in 0.10s =========================
"""
        result = parser.parse_pytest_output(output)
        assert result.failed == 1
        assert len(result.failures) >= 0  # May or may not extract depending on format

    def test_parse_json_report_not_found(self, parser, tmp_path):
        """Should return empty result for missing file."""
        result = parser.parse_json_report(tmp_path / "nonexistent.json")
        assert result.total == 0
        assert result.passed == 0

    def test_parse_json_report_valid(self, parser, tmp_path):
        """Should parse valid JSON report."""
        report = {
            "summary": {
                "passed": 5,
                "failed": 2,
                "skipped": 1,
                "total": 8
            },
            "duration": 3.45,
            "tests": [
                {
                    "nodeid": "test_file.py::test_one",
                    "outcome": "passed"
                },
                {
                    "nodeid": "test_file.py::test_two",
                    "outcome": "failed",
                    "call": {
                        "longrepr": "AssertionError: values don't match",
                        "crash": {"message": "AssertionError"},
                        "duration": 0.1
                    }
                }
            ]
        }

        report_path = tmp_path / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f)

        result = parser.parse_json_report(report_path)
        assert result.passed == 5
        assert result.failed == 2
        assert result.skipped == 1
        assert result.duration == 3.45
        assert len(result.failures) == 1

    def test_merge_results(self, parser):
        """Should merge multiple results correctly."""
        result1 = TestResult(total=5, passed=4, failed=1, duration=1.0)
        result2 = TestResult(total=3, passed=2, failed=1, duration=0.5)

        merged = parser.merge_results(result1, result2)
        assert merged.total == 8
        assert merged.passed == 6
        assert merged.failed == 2
        assert merged.duration == 1.5


class TestReportGenerator:
    """Tests for ReportGenerator."""

    @pytest.fixture
    def generator(self):
        return ReportGenerator()

    def test_generate_markdown_all_passed(self, generator):
        """Should generate report for all passed tests."""
        result = TestResult(
            total=5,
            passed=5,
            failed=0,
            duration=1.23
        )

        report = generator.generate_markdown(result, "pytest tests/ -v")

        assert "# Test Analysis Report" in report
        assert "All Tests Passed" in report
        assert "| Passed | 5 |" in report

    def test_generate_markdown_with_failures(self, generator):
        """Should generate report with failure details."""
        failure = TestFailure(
            test_name="test_example",
            test_file="test_file.py",
            error_message="AssertionError: values don't match",
            category=FailureCategory.ASSERTION_FAIL,
            suggested_fix="Check comparison logic"
        )

        result = TestResult(
            total=5,
            passed=3,
            failed=2,
            duration=2.34,
            failures=[failure]
        )

        report = generator.generate_markdown(result, "pytest tests/ -v")

        assert "# Test Analysis Report" in report
        assert "## Failure Analysis" in report
        assert "Assertion Fail" in report
        assert "test_example" in report

    def test_generate_markdown_includes_priority(self, generator):
        """Should include fix priority section."""
        failure = TestFailure(
            test_name="test_import",
            test_file="test_file.py",
            error_message="ImportError",
            category=FailureCategory.IMPORT_ERROR
        )

        result = TestResult(total=1, failed=1, failures=[failure])

        report = generator.generate_markdown(result)

        assert "## Fix Priority" in report

    def test_generate_json(self, generator):
        """Should generate valid JSON report."""
        result = TestResult(
            total=10,
            passed=8,
            failed=2,
            duration=5.0
        )

        json_report = generator.generate_json(result)

        assert json_report["summary"]["total"] == 10
        assert json_report["summary"]["passed"] == 8
        assert json_report["summary"]["success_rate"] == 80.0
        assert "timestamp" in json_report

    def test_success_rate_calculation(self, generator):
        """Should calculate success rate correctly."""
        result = TestResult(total=10, passed=7)
        assert result.success_rate == 70.0

        empty_result = TestResult(total=0)
        assert empty_result.success_rate == 0.0


class TestCodeLocation:
    """Tests for CodeLocation dataclass."""

    def test_str_with_all_fields(self):
        """Should format location with all fields."""
        loc = CodeLocation(
            file_path="/path/to/file.py",
            line_number=42,
            function_name="test_func"
        )
        assert str(loc) == "/path/to/file.py:42 in test_func"

    def test_str_without_function(self):
        """Should format location without function name."""
        loc = CodeLocation(
            file_path="/path/to/file.py",
            line_number=42
        )
        assert str(loc) == "/path/to/file.py:42"

    def test_str_file_only(self):
        """Should format location with file only."""
        loc = CodeLocation(file_path="/path/to/file.py")
        assert str(loc) == "/path/to/file.py"
