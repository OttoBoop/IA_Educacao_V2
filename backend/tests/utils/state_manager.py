"""
State manager for auto-fix operations with rollback capability.

Provides:
- Save state before making changes
- Track fix attempts with history
- Rollback to previous state
- Clean up after successful fixes
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FixAttempt:
    """Represents a single fix attempt."""

    timestamp: str
    action: str
    files_modified: list[str]
    result: str  # "SUCCESS", "STILL_FAILING", "REGRESSION"
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "files_modified": self.files_modified,
            "result": self.result,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FixAttempt":
        return cls(**data)


@dataclass
class FailureState:
    """Tracks the state of a single test failure."""

    test_id: str  # e.g., "test_file.py::test_name"
    category: str
    first_seen: str
    attempts: list[FixAttempt] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, IN_PROGRESS, FIXED, STUCK
    max_attempts: int = 3
    user_input_requested: bool = False
    questions: list[str] = field(default_factory=list)

    @property
    def is_stuck(self) -> bool:
        return len(self.attempts) >= self.max_attempts and self.status != "FIXED"

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "category": self.category,
            "first_seen": self.first_seen,
            "attempts": [a.to_dict() for a in self.attempts],
            "status": self.status,
            "max_attempts": self.max_attempts,
            "user_input_requested": self.user_input_requested,
            "questions": self.questions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FailureState":
        attempts = [FixAttempt.from_dict(a) for a in data.get("attempts", [])]
        return cls(
            test_id=data["test_id"],
            category=data["category"],
            first_seen=data["first_seen"],
            attempts=attempts,
            status=data.get("status", "PENDING"),
            max_attempts=data.get("max_attempts", 3),
            user_input_requested=data.get("user_input_requested", False),
            questions=data.get("questions", []),
        )


@dataclass
class SessionState:
    """Tracks the overall fix session state."""

    session_id: str
    test_command: str
    started_at: str
    failures: dict[str, FailureState] = field(default_factory=dict)
    total_attempts: int = 0
    successful_fixes: int = 0

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "test_command": self.test_command,
            "started_at": self.started_at,
            "failures": {k: v.to_dict() for k, v in self.failures.items()},
            "total_attempts": self.total_attempts,
            "successful_fixes": self.successful_fixes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        failures = {k: FailureState.from_dict(v) for k, v in data.get("failures", {}).items()}
        return cls(
            session_id=data["session_id"],
            test_command=data["test_command"],
            started_at=data["started_at"],
            failures=failures,
            total_attempts=data.get("total_attempts", 0),
            successful_fixes=data.get("successful_fixes", 0),
        )


class StateManager:
    """Manages state saving, rollback, and fix attempt tracking."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize state manager.

        Args:
            base_dir: Base directory for state storage. Defaults to backend/.fix_state/
        """
        if base_dir is None:
            # Default to backend/.fix_state/
            base_dir = Path(__file__).parent.parent.parent / ".fix_state"
        self.base_dir = Path(base_dir)
        self.current_session: Optional[SessionState] = None
        self._session_dir: Optional[Path] = None

    def start_session(self, test_command: str) -> str:
        """Start a new fix session.

        Args:
            test_command: The pytest command being run

        Returns:
            Session ID
        """
        session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self._session_dir = self.base_dir / f"session_{session_id}"
        self._session_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self._session_dir / "files").mkdir(exist_ok=True)
        (self._session_dir / "test_results").mkdir(exist_ok=True)

        self.current_session = SessionState(
            session_id=session_id,
            test_command=test_command,
            started_at=datetime.now().isoformat(),
        )

        self._save_manifest()
        return session_id

    def load_session(self, session_id: str) -> bool:
        """Load an existing session.

        Args:
            session_id: The session ID to load

        Returns:
            True if session was loaded, False if not found
        """
        self._session_dir = self.base_dir / f"session_{session_id}"
        manifest_path = self._session_dir / "manifest.json"

        if not manifest_path.exists():
            return False

        with open(manifest_path) as f:
            data = json.load(f)

        self.current_session = SessionState.from_dict(data)
        return True

    def get_latest_session(self) -> Optional[str]:
        """Get the most recent session ID.

        Returns:
            Session ID or None if no sessions exist
        """
        if not self.base_dir.exists():
            return None

        sessions = sorted(self.base_dir.glob("session_*"), reverse=True)
        if not sessions:
            return None

        return sessions[0].name.replace("session_", "")

    def save_file_state(self, file_path: Path, reason: str = "") -> bool:
        """Save the current state of a file before modification.

        Args:
            file_path: Path to the file to save
            reason: Why this file is being saved

        Returns:
            True if file was saved, False if error
        """
        if not self._session_dir:
            raise RuntimeError("No active session. Call start_session() first.")

        if not file_path.exists():
            return False

        # Create backup with relative path preserved
        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = file_path.name

        backup_path = self._session_dir / "files" / str(relative_path).replace("/", "_").replace("\\", "_")
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, backup_path)

        # Update manifest with file info
        self._add_file_to_manifest(str(file_path), str(backup_path), reason)

        return True

    def save_multiple_files(self, file_paths: list[Path], reason: str = "") -> list[Path]:
        """Save multiple files before modification.

        Args:
            file_paths: List of file paths to save
            reason: Why these files are being saved

        Returns:
            List of successfully saved file paths
        """
        saved = []
        for path in file_paths:
            if self.save_file_state(path, reason):
                saved.append(path)
        return saved

    def record_fix_attempt(
        self,
        test_id: str,
        category: str,
        action: str,
        files_modified: list[str],
        result: str,
        error_message: str = "",
    ) -> FailureState:
        """Record a fix attempt for a test.

        Args:
            test_id: The test identifier (e.g., "test_file.py::test_name")
            category: Failure category
            action: Description of what was done
            files_modified: List of files that were modified
            result: "SUCCESS", "STILL_FAILING", or "REGRESSION"
            error_message: Error message if still failing

        Returns:
            Updated FailureState
        """
        if not self.current_session:
            raise RuntimeError("No active session. Call start_session() first.")

        # Get or create failure state
        if test_id not in self.current_session.failures:
            self.current_session.failures[test_id] = FailureState(
                test_id=test_id,
                category=category,
                first_seen=datetime.now().isoformat(),
            )

        failure = self.current_session.failures[test_id]

        # Record attempt
        attempt = FixAttempt(
            timestamp=datetime.now().isoformat(),
            action=action,
            files_modified=files_modified,
            result=result,
            error_message=error_message,
        )
        failure.attempts.append(attempt)
        self.current_session.total_attempts += 1

        # Update status
        if result == "SUCCESS":
            failure.status = "FIXED"
            self.current_session.successful_fixes += 1
        elif failure.is_stuck:
            failure.status = "STUCK"
            failure.user_input_requested = True
        else:
            failure.status = "IN_PROGRESS"

        self._save_manifest()
        return failure

    def add_user_question(self, test_id: str, question: str) -> None:
        """Add a question for the user about a stuck failure.

        Args:
            test_id: The test identifier
            question: Question to ask the user
        """
        if not self.current_session:
            raise RuntimeError("No active session. Call start_session() first.")

        if test_id not in self.current_session.failures:
            raise ValueError(f"Unknown test: {test_id}")

        failure = self.current_session.failures[test_id]
        failure.questions.append(question)
        failure.user_input_requested = True
        self._save_manifest()

    def get_stuck_failures(self) -> list[FailureState]:
        """Get all failures that are stuck and need user input.

        Returns:
            List of stuck FailureState objects
        """
        if not self.current_session:
            return []

        return [f for f in self.current_session.failures.values() if f.is_stuck]

    def get_pending_questions(self) -> dict[str, list[str]]:
        """Get all pending questions for the user.

        Returns:
            Dict mapping test_id to list of questions
        """
        if not self.current_session:
            return {}

        return {
            f.test_id: f.questions
            for f in self.current_session.failures.values()
            if f.user_input_requested and f.questions
        }

    def rollback_file(self, file_path: Path) -> bool:
        """Rollback a single file to its saved state.

        Args:
            file_path: Path to the file to rollback

        Returns:
            True if rollback succeeded, False otherwise
        """
        if not self._session_dir:
            raise RuntimeError("No active session.")

        # Find backup
        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = file_path.name

        backup_name = str(relative_path).replace("/", "_").replace("\\", "_")
        backup_path = self._session_dir / "files" / backup_name

        if not backup_path.exists():
            return False

        shutil.copy2(backup_path, file_path)
        return True

    def rollback_all(self) -> list[Path]:
        """Rollback all saved files to their original state.

        Returns:
            List of files that were rolled back
        """
        if not self._session_dir:
            raise RuntimeError("No active session.")

        rolled_back = []
        backup_dir = self._session_dir / "files"

        if not backup_dir.exists():
            return rolled_back

        manifest_path = self._session_dir / "manifest.json"
        if not manifest_path.exists():
            return rolled_back

        with open(manifest_path) as f:
            manifest = json.load(f)

        for file_info in manifest.get("saved_files", []):
            original_path = Path(file_info["original_path"])
            backup_path = Path(file_info["backup_path"])

            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                rolled_back.append(original_path)

        return rolled_back

    def save_test_results(self, results_json: dict, stage: str = "before") -> None:
        """Save test results for comparison.

        Args:
            results_json: Test results as JSON dict
            stage: "before" or "after"
        """
        if not self._session_dir:
            raise RuntimeError("No active session.")

        results_path = self._session_dir / "test_results" / f"{stage}.json"
        with open(results_path, "w") as f:
            json.dump(results_json, f, indent=2)

    def cleanup_session(self, delete: bool = True) -> None:
        """Clean up after a successful session.

        Args:
            delete: If True, delete the session directory. If False, just mark as complete.
        """
        if not self._session_dir:
            return

        if delete:
            shutil.rmtree(self._session_dir, ignore_errors=True)
        else:
            # Mark session as complete
            manifest_path = self._session_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                manifest["completed_at"] = datetime.now().isoformat()
                manifest["status"] = "COMPLETED"
                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2)

        self.current_session = None
        self._session_dir = None

    def has_regressions(self, before_results: dict, after_results: dict) -> list[str]:
        """Check if any previously passing tests are now failing.

        Args:
            before_results: Test results before fix
            after_results: Test results after fix

        Returns:
            List of test IDs that regressed
        """
        before_passed = set()
        after_failed = set()

        # Extract passing tests from before
        for test in before_results.get("tests", []):
            if test.get("outcome") == "passed":
                before_passed.add(test.get("nodeid", ""))

        # Extract failing tests from after
        for test in after_results.get("tests", []):
            if test.get("outcome") in ("failed", "error"):
                after_failed.add(test.get("nodeid", ""))

        # Regressions are tests that passed before but fail now
        return list(before_passed & after_failed)

    def _save_manifest(self) -> None:
        """Save the session manifest."""
        if not self._session_dir or not self.current_session:
            return

        manifest_path = self._session_dir / "manifest.json"

        # Load existing manifest if it exists
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {"saved_files": []}

        # Update with session state
        manifest.update(self.current_session.to_dict())

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _add_file_to_manifest(self, original_path: str, backup_path: str, reason: str) -> None:
        """Add a saved file to the manifest."""
        if not self._session_dir:
            return

        manifest_path = self._session_dir / "manifest.json"

        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {"saved_files": []}

        manifest["saved_files"].append({
            "original_path": original_path,
            "backup_path": backup_path,
            "reason": reason,
            "saved_at": datetime.now().isoformat(),
        })

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def get_session_summary(self) -> dict:
        """Get a summary of the current session.

        Returns:
            Dict with session summary info
        """
        if not self.current_session:
            return {}

        stuck = self.get_stuck_failures()
        fixed = [f for f in self.current_session.failures.values() if f.status == "FIXED"]
        in_progress = [f for f in self.current_session.failures.values() if f.status == "IN_PROGRESS"]

        return {
            "session_id": self.current_session.session_id,
            "test_command": self.current_session.test_command,
            "started_at": self.current_session.started_at,
            "total_failures": len(self.current_session.failures),
            "fixed": len(fixed),
            "stuck": len(stuck),
            "in_progress": len(in_progress),
            "total_attempts": self.current_session.total_attempts,
            "needs_user_input": len(stuck) > 0,
            "questions_pending": sum(len(f.questions) for f in stuck),
        }
