"""
Test utilities package.

Provides:
- log_parser: Parse pytest output and categorize failures
- state_manager: Save/rollback state for auto-fix operations
- test_matcher: Match relevant tests to features
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name in (
        "TestResultParser",
        "FailureCategorizer",
        "ReportGenerator",
        "FailureCategory",
        "TestResult",
        "TestFailure",
    ):
        from .log_parser import (
            TestResultParser,
            FailureCategorizer,
            ReportGenerator,
            FailureCategory,
            TestResult,
            TestFailure,
        )
        return locals()[name]
    elif name == "StateManager":
        from .state_manager import StateManager
        return StateManager
    elif name in ("TestMatcher", "TestInfo", "MatchResult", "CoverageGap"):
        from .test_matcher import TestMatcher, TestInfo, MatchResult, CoverageGap
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TestResultParser",
    "FailureCategorizer",
    "ReportGenerator",
    "FailureCategory",
    "TestResult",
    "TestFailure",
    "StateManager",
    "TestMatcher",
    "TestInfo",
    "MatchResult",
    "CoverageGap",
]
