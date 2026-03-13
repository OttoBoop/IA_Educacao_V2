"""
Investor Journey Agent - Main orchestrator.

Coordinates browser automation and LLM decision-making
to simulate realistic user journeys.
"""

import asyncio
import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal, Callable

from .command_receiver import CommandReceiver
from .config import AgentConfig, VIEWPORT_CONFIGS, DEFAULT_CONFIG
from .event_emitter import EventEmitter
from .personas import Persona, PERSONAS, get_persona
from .browser_interface import BrowserInterface
from .intent_resolver import IntentResolver
from .llm_brain import LLMBrain, Action, ActionType, JourneyStep, JourneyEvaluation
from .scenario import MODELS
from .url_utils import resolve_start_url


@dataclass
class JourneyReport:
    """Complete report of a journey."""

    persona: Persona
    goal: str
    url: str
    viewport_name: str
    start_time: datetime
    end_time: datetime
    steps: List[JourneyStep]
    evaluation: Optional[JourneyEvaluation]
    output_dir: Path
    incomplete: bool = False
    incomplete_reason: Optional[str] = None
    blocked: bool = False
    blocked_reason: Optional[str] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate from steps."""
        if not self.steps:
            return 0.0
        successful = sum(1 for s in self.steps if s.success)
        return successful / len(self.steps)

    @property
    def status(self) -> str:
        """High-level run status for reports and summaries."""
        if self.blocked:
            return "blocked"
        if self.incomplete:
            return "incomplete"
        if self.gave_up:
            return "gave_up"
        return "completed"

    @property
    def gave_up(self) -> bool:
        """Check if the journey ended with giving up."""
        if not self.steps:
            return False
        return self.steps[-1].action.action_type == ActionType.GIVE_UP


class InvestorJourneyAgent:
    """
    Main agent that simulates realistic user journeys.

    Usage:
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14"
        )
        report = await agent.run_journey(
            url="http://localhost:8000",
            goal="View the dashboard"
        )
    """

    def __init__(
        self,
        persona: str | Persona = "investor",
        viewport: str = "desktop",
        mode: Literal["basic", "in_depth"] = "basic",
        config: Optional[AgentConfig] = None,
        on_step: Optional[Callable[[JourneyStep], None]] = None,
        headless: bool = True,
        narrator: Optional["ProgressNarrator"] = None,
        event_emitter: Optional[EventEmitter] = None,
        command_receiver: Optional[CommandReceiver] = None,
        pause_mode: bool = False,
    ):
        """
        Initialize the agent.

        Args:
            persona: Persona name or Persona object
            viewport: Viewport configuration name
            mode: "basic" for report only, "in_depth" for analysis
            config: Agent configuration
            on_step: Callback called after each step
            headless: Run browser in headless mode
            narrator: Optional ProgressNarrator for periodic summaries
            event_emitter: Optional EventEmitter for structured IPC output
            command_receiver: Optional CommandReceiver for IPC commands
            pause_mode: If True, pause after each step and wait for continue command
        """
        # Resolve persona
        if isinstance(persona, str):
            self.persona = get_persona(persona)
        else:
            self.persona = persona

        # Resolve viewport
        if viewport not in VIEWPORT_CONFIGS:
            available = ", ".join(VIEWPORT_CONFIGS.keys())
            raise ValueError(f"Unknown viewport: {viewport}. Available: {available}")
        self.viewport_config = VIEWPORT_CONFIGS[viewport]
        self.viewport_name = viewport

        self.mode = mode
        self.config = config or DEFAULT_CONFIG
        self.on_step = on_step
        self.headless = headless
        self.narrator = narrator
        self.event_emitter = event_emitter
        self.command_receiver = command_receiver
        self.pause_mode = pause_mode

        # Will be initialized in run_journey
        self._browser: Optional[BrowserInterface] = None
        self._brain: Optional[LLMBrain] = None
        self._artifact_manifest_path: Optional[Path] = None
        self._last_action_result: dict = {}
        self._selected_model: Optional[str] = None
        self._triggered_models: list[str] = []

    async def run_journey(
        self,
        url: str,
        goal: str,
        max_steps: Optional[int] = None,
        website_context: Optional[str] = None,
        start_url: Optional[str] = None,
        setup: Optional[str] = None,
    ) -> JourneyReport:
        """
        Run a simulated user journey.

        Args:
            url: Starting URL
            goal: What the persona is trying to achieve
            max_steps: Maximum steps before stopping
            website_context: Optional description of the website
            start_url: Optional fragment/path to navigate to after base URL
            setup: Optional path to a Python file to exec() before the step loop

        Returns:
            JourneyReport with all steps and evaluation
        """
        max_steps = max_steps or self.config.max_steps
        start_time = datetime.now()
        steps: List[JourneyStep] = []

        # Create output directory
        if self.event_emitter is not None:
            output_dir = self.event_emitter.output_dir
        else:
            output_dir = self.config.output_dir / start_time.strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir = output_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        self.config.output_dir = output_dir
        downloads_root = output_dir / "downloads"
        self.config.downloads_dir = (
            downloads_root / "_incoming" if self.pause_mode else downloads_root
        )
        self.config.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._artifact_manifest_path = output_dir / "artifact_manifest.jsonl"
        self._last_action_result = {}
        self._selected_model = None
        self._triggered_models = []

        # Initialize components
        self._brain = LLMBrain(self.config)
        self._resolver = IntentResolver()

        async with BrowserInterface(
            viewport_config=self.viewport_config,
            headless=self.headless,
        ) as browser:
            self._browser = browser

            # Navigate to starting URL
            print(f"\n{'='*50}")
            print(f"Starting journey as: {self.persona.name}")
            print(f"Goal: {goal}")
            print(f"URL: {url}")
            print(f"Viewport: {self.viewport_config['name']}")
            print(f"{'='*50}\n")

            success = await browser.goto(url)
            if not success:
                errors = browser._console_errors
                print(f"Failed to load initial page! Errors: {errors}")
                return JourneyReport(
                    persona=self.persona,
                    goal=goal,
                    url=url,
                    viewport_name=self.viewport_name,
                    start_time=start_time,
                    end_time=datetime.now(),
                    steps=[],
                    evaluation=None,
                    output_dir=output_dir,
                )

            # Navigate to start_url if provided (deep-link navigation)
            if start_url:
                resolved = resolve_start_url(url, start_url)
                print(f"[START-URL] Navigating to: {resolved}")
                await browser.goto(resolved)

            # Run setup script if provided
            if setup:
                print(f"[SETUP] Running setup file: {setup}")
                self._run_setup(setup, page=browser.page, browser=browser)

            # Main journey loop
            incomplete = False
            incomplete_reason = None
            blocked = False
            blocked_reason = None
            step_number = 0

            user_guidance = None  # For mid-journey guidance from operator
            recent_actions: deque = deque(maxlen=3)  # For stuck detection

            try:
                while True:  # outer pause/resume loop
                    while step_number < max_steps:
                        step_number += 1

                        # Poll for external commands
                        if self.command_receiver:
                            for cmd in self.command_receiver.poll_all():
                                if cmd.command_type == "stop":
                                    reason = cmd.data.get("reason", "Stopped by external command")
                                    incomplete = True
                                    incomplete_reason = reason
                                    print(f"\n[STOP] {reason}")
                                    if self.event_emitter:
                                        self.event_emitter.emit_stopped(reason=reason, steps_completed=len(steps))
                                    break
                                elif cmd.command_type == "guidance":
                                    user_guidance = cmd.data.get("instruction", "")
                                    print(f"\n[GUIDANCE] {user_guidance}")
                            if incomplete:
                                break

                        # Execute one step (get state → decide → execute → record)
                        step = await self._do_step(
                            step_number=step_number,
                            steps=steps,
                            goal=goal,
                            screenshots_dir=screenshots_dir,
                            website_context=website_context,
                            user_guidance=user_guidance,
                        )
                        user_guidance = None  # Clear after use (one-shot)

                        if step is None:
                            # Step was skipped (user confirmation denied)
                            continue

                        steps.append(step)

                        if step.action.decision_error and step.action.decision_error_is_blocking:
                            blocked = True
                            blocked_reason = step.error_message or step.action.decision_error
                            incomplete = True
                            incomplete_reason = blocked_reason
                            print(f"\n[BLOCKED] {blocked_reason}")
                            if self.event_emitter:
                                self.event_emitter.emit_stopped(
                                    reason=blocked_reason,
                                    steps_completed=len(steps),
                                )
                            break

                        # Pause mode: emit "paused" event and wait for a "continue" command
                        if self.pause_mode and self.command_receiver:
                            if self.event_emitter:
                                self.event_emitter.emit_paused(step_number=step_number)
                            pause_done = False
                            while not pause_done:
                                await asyncio.sleep(0.5)
                                for cmd in self.command_receiver.poll_all():
                                    if cmd.command_type == "continue":
                                        pause_done = True
                                    elif cmd.command_type == "stop":
                                        incomplete = True
                                        incomplete_reason = cmd.data.get("reason", "Stopped during pause")
                                        if self.event_emitter:
                                            self.event_emitter.emit_stopped(
                                                reason=incomplete_reason,
                                                steps_completed=len(steps),
                                            )
                                        pause_done = True
                                    elif cmd.command_type == "guidance":
                                        user_guidance = cmd.data.get("instruction", "")
                                        print(f"\n[GUIDANCE] {user_guidance}")
                                        pause_done = True  # Apply guidance on next step
                        if incomplete:
                            break

                        # Stuck detection: same (action_type, target) 3x in a row
                        action_key = (step.action.action_type.value, step.action.target)
                        recent_actions.append(action_key)
                        if (
                            len(recent_actions) == 3
                            and len(set(recent_actions)) == 1
                            and step.action.action_type not in (ActionType.DONE, ActionType.GIVE_UP)
                        ):
                            print(f"\n[STUCK] Same action repeated 3x: {action_key[0]} on '{action_key[1]}'")
                            if self.event_emitter:
                                self.event_emitter.emit_stuck(
                                    step_number=step_number,
                                    action_type=action_key[0],
                                    target=action_key[1] or "",
                                    times_repeated=3,
                                )
                            user_guidance = (
                                f"You seem stuck repeating '{action_key[0]}' on '{action_key[1]}'. "
                                "Try a completely different approach or element."
                            )

                        if step.action.action_type == ActionType.DONE:
                            print("\n[DONE] Goal achieved!")
                            break

                        if step.action.action_type == ActionType.GIVE_UP:
                            print(f"\n[GAVE UP] {step.action.thought}")
                            break

                    # Inner loop exited. Determine why:
                    if incomplete:
                        break  # Stopped by command

                    if steps and steps[-1].action.action_type in (ActionType.DONE, ActionType.GIVE_UP):
                        break  # Journey ended naturally

                    # Hit step limit — pause and ask user how many more steps
                    extra = await self._pause_and_extend(step_number=step_number)
                    if extra == 0:
                        incomplete = True
                        incomplete_reason = f"Paused by user at step {step_number}"
                        break
                    max_steps += extra  # Extend the limit for N more steps

            except KeyboardInterrupt:
                incomplete = True
                incomplete_reason = "Interrupted by user (KeyboardInterrupt)"
                print(f"\n[INTERRUPTED] Journey stopped by user")
                if self.event_emitter:
                    self.event_emitter.emit_stopped(
                        reason="Interrupted by user",
                        steps_completed=len(steps),
                    )

            except Exception as e:
                incomplete = True
                incomplete_reason = str(e)
                print(f"\n[ERROR] Journey interrupted: {e}")
                if self.event_emitter:
                    import traceback
                    self.event_emitter.emit_error(
                        error=str(e),
                        traceback_str=traceback.format_exc(),
                    )

            # Print final narrator summary
            if self.narrator:
                print(self.narrator.final_summary())

            # Generate evaluation if in-depth mode
            evaluation = None
            if self.mode == "in_depth" and steps and not incomplete:
                print("\nGenerating in-depth analysis...")
                evaluation = await self._brain.evaluate_journey(
                    steps=steps,
                    persona=self.persona,
                    goal=goal,
                )

        end_time = datetime.now()

        # Emit final event
        if self.event_emitter and not incomplete:
            self.event_emitter.emit_complete(
                success_rate=sum(1 for s in steps if s.success) / len(steps) if steps else 0.0,
                total_steps=len(steps),
                gave_up=bool(steps and steps[-1].action.action_type == ActionType.GIVE_UP),
            )

        return JourneyReport(
            persona=self.persona,
            goal=goal,
            url=url,
            viewport_name=self.viewport_name,
            start_time=start_time,
            end_time=end_time,
            steps=steps,
            evaluation=evaluation,
            output_dir=output_dir,
            incomplete=incomplete,
            incomplete_reason=incomplete_reason,
            blocked=blocked,
            blocked_reason=blocked_reason,
        )

    async def _do_step(
        self,
        step_number: int,
        steps: List[JourneyStep],
        goal: str,
        screenshots_dir: Path,
        website_context: Optional[str] = None,
        user_guidance: Optional[str] = None,
    ) -> Optional[JourneyStep]:
        """
        Execute a single step of the journey: get state → decide → execute → record.

        Returns:
            JourneyStep if the step was taken (check action_type for DONE/GIVE_UP)
            None if the step was skipped by user confirmation
        """
        # Get current state (pre-action)
        state = await self._browser.get_state()

        # Get LLM decision
        action = await self._brain.decide_next_action(
            screenshot_base64=state.screenshot_base64,
            dom_snapshot=state.dom_snapshot,
            persona=self.persona,
            goal=goal,
            history=steps,
            console_errors=state.console_errors,
            user_guidance=user_guidance,
            website_context=website_context,
            clickable_elements=state.clickable_elements,
        )

        # Print step info
        self._print_step(step_number, action)

        if action.decision_error:
            screenshot_path = screenshots_dir / f"step_{step_number:02d}.png"
            await self._browser.save_screenshot(screenshot_path)
            step = JourneyStep(
                step_number=step_number,
                url=state.url,
                screenshot_path=str(screenshot_path),
                action=action,
                success=False,
                error_message=action.decision_error,
            )
            if self.event_emitter:
                self.event_emitter.emit_step(step)
            if self.on_step:
                self.on_step(step)
            self._narrate_step(step)
            return step

        # Handle terminal actions (DONE / GIVE_UP) — save screenshot and return
        if action.action_type in (ActionType.DONE, ActionType.GIVE_UP):
            screenshot_path = screenshots_dir / f"step_{step_number:02d}.png"
            await self._browser.save_screenshot(screenshot_path)
            step = JourneyStep(
                step_number=step_number,
                url=state.url,
                screenshot_path=str(screenshot_path),
                action=action,
                success=action.action_type == ActionType.DONE,
                error_message=None if action.action_type == ActionType.DONE else "User gave up due to frustration",
            )
            if self.event_emitter:
                self.event_emitter.emit_step(step)
            if self.on_step:
                self.on_step(step)
            self._narrate_step(step)
            return step

        # Ask for confirmation if configured
        if self.config.ask_before_action:
            if not await self._confirm_action(action):
                print("Action skipped by user")
                return None

        # Execute the action (with IntentResolver for clicks)
        retry_result = await self._resolver.execute_with_retry(
            action=action,
            clickable_elements=state.clickable_elements,
            browser=self._browser,
        )
        self._last_action_result = {}

        if retry_result is not None:
            success, error = retry_result
        else:
            success, error = await self._execute_action(action)

        # Save screenshot AFTER action (post-action)
        screenshot_path = screenshots_dir / f"step_{step_number:02d}.png"
        await self._browser.save_screenshot(screenshot_path)

        step = JourneyStep(
            step_number=step_number,
            url=state.url,
            screenshot_path=str(screenshot_path),
            action=action,
            success=success,
            error_message=error,
        )
        self._record_step_artifact_event(step)

        if self.event_emitter:
            self.event_emitter.emit_step(step)
        if self.on_step:
            self.on_step(step)
        self._narrate_step(step)

        # Wait for page to settle
        await self._browser.wait_for_idle()
        await asyncio.sleep(self.config.wait_after_action_ms / 1000)

        return step

    def _normalize_model_token(self, value: str) -> str:
        """Normalize free-form text for model-name matching."""
        return "".join(ch for ch in value.lower() if ch.isalnum())

    def _infer_explicit_model_context(self, *values: str) -> tuple[Optional[str], str]:
        """Infer a model only when it is explicitly named in text or filenames."""
        normalized_values = [self._normalize_model_token(value) for value in values if value]
        for model in MODELS:
            model_token = self._normalize_model_token(model)
            if any(model_token and model_token in value for value in normalized_values):
                return model, "explicit_text"
        return None, "unknown"

    def _append_artifact_manifest(self, entry: dict) -> None:
        """Append a machine-readable artifact event for the current run."""
        if self._artifact_manifest_path is None:
            return
        with open(self._artifact_manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _record_step_artifact_event(self, step: JourneyStep) -> None:
        """Record model-selection, trigger, and download evidence for Phase 3 validation."""
        if not step.success:
            return

        timestamp = datetime.now().isoformat()

        if step.action.action_type == ActionType.SELECT_OPTION:
            selected_value = self._last_action_result.get("selected_value")
            if selected_value in MODELS:
                self._selected_model = selected_value
                self._append_artifact_manifest({
                    "event_type": "model_selected",
                    "timestamp": timestamp,
                    "step": step.step_number,
                    "selected_value": selected_value,
                    "target": step.action.target,
                })
            return

        if (
            step.action.action_type == ActionType.EVALUATE_JS
            and "executarpipelinecompleto" in (step.action.eval_script or "").lower()
        ):
            model, source = self._infer_explicit_model_context(
                step.action.target,
                step.action.thought,
                step.action.eval_script or "",
            )
            if model is None and self._selected_model in MODELS:
                model = self._selected_model
                source = "selected_value"
            if model and model not in self._triggered_models:
                self._triggered_models.append(model)
            self._append_artifact_manifest({
                "event_type": "pipeline_trigger",
                "timestamp": timestamp,
                "step": step.step_number,
                "model_context": model,
                "model_context_source": source,
                "selected_model_context": self._selected_model,
                "triggered_models_so_far": list(self._triggered_models),
                "eval_script": step.action.eval_script,
            })
            return

        if step.action.action_type == ActionType.DOWNLOAD_FILE:
            download_path = self._last_action_result.get("download_path")
            download_filename = self._last_action_result.get("download_filename", "")
            model, source = self._infer_explicit_model_context(
                step.action.target,
                step.action.thought,
                download_filename,
                str(download_path or ""),
            )
            self._append_artifact_manifest({
                "event_type": "download_saved",
                "timestamp": timestamp,
                "step": step.step_number,
                "target": step.action.target,
                "thought": step.action.thought,
                "saved_path": download_path,
                "saved_filename": download_filename,
                "model_context": model,
                "model_context_source": source,
                "selected_model_context": self._selected_model,
                "triggered_models_so_far": list(self._triggered_models),
            })

    async def _pause_and_extend(self, step_number: int) -> int:
        """
        Prompt the user to extend the journey after reaching the step limit.

        Returns:
            0 to stop the journey
            N > 0 to extend by N more steps
        """
        loop = asyncio.get_running_loop()
        prompt = f"\n[PAUSED] Journey paused at step {step_number}. How many more steps? [0 to stop]: "
        while True:
            try:
                raw = await loop.run_in_executor(None, input, prompt)
                n = int(raw.strip())
                return n
            except ValueError:
                print("Please enter a valid integer.")
                continue

    def _run_setup(self, path: str, page, browser) -> None:
        """
        Execute a setup Python file before the journey loop.

        Args:
            path: Path to the .py setup file
            page: The browser page object (exposed as 'page' in the script)
            browser: The browser interface (exposed as 'browser' in the script)

        Raises:
            RuntimeError: If the setup file raises an exception (includes file path)
        """
        try:
            code = Path(path).read_text(encoding="utf-8")
            exec(code, {"page": page, "browser": browser})
        except Exception as e:
            raise RuntimeError(f"Setup file failed: {path}: {e}") from e

    async def _execute_action(self, action: Action) -> tuple[bool, Optional[str]]:
        """Execute an action and return (success, error_message)."""
        try:
            self._last_action_result = {}
            if action.action_type == ActionType.CLICK:
                success = await self._browser.click(action.target)
                return success, None if success else f"Could not click {action.target}"

            elif action.action_type == ActionType.TYPE:
                if not action.text_to_type:
                    return False, "No text provided for TYPE action"
                success = await self._browser.type_text(
                    action.target, action.text_to_type
                )
                return success, None if success else f"Could not type in {action.target}"

            elif action.action_type == ActionType.SCROLL:
                direction = action.scroll_direction or "down"
                success = await self._browser.scroll(direction)
                return success, None if success else "Could not scroll"

            elif action.action_type == ActionType.WAIT:
                await asyncio.sleep(action.wait_duration_seconds or 1)
                return True, None

            elif action.action_type == ActionType.RELOAD:
                success = await self._browser.reload()
                return success, None if success else "Could not reload page"

            elif action.action_type == ActionType.BACK:
                success = await self._browser.go_back()
                return success, None if success else "Could not go back"

            elif action.action_type == ActionType.SELECT_OPTION:
                if not action.select_value:
                    return False, "No select_value provided for SELECT_OPTION action"
                success = await self._browser.select_option(
                    action.target, action.select_value
                )
                if success:
                    self._last_action_result = {"selected_value": action.select_value}
                return success, None if success else f"Could not select '{action.select_value}' in {action.target}"

            elif action.action_type == ActionType.DOWNLOAD_FILE:
                result = await self._browser.download_file(
                    action.target, self.config.downloads_dir
                )
                if result:
                    self._last_action_result = {
                        "download_path": str(result),
                        "download_filename": result.name,
                    }
                    return True, None
                return False, f"Could not download file from {action.target}"

            elif action.action_type == ActionType.CHECKBOX_TOGGLE:
                success = await self._browser.checkbox_toggle(action.target)
                return success, None if success else f"Could not toggle checkbox {action.target}"

            elif action.action_type == ActionType.READ_PAGE_TEXT:
                text = await self._browser.read_page_text(action.target)
                if text is not None:
                    return True, None
                return False, f"Could not read text from {action.target}"

            elif action.action_type == ActionType.EVALUATE_JS:
                if not action.eval_script:
                    return False, "No eval_script provided for EVALUATE_JS action"
                await self._browser.evaluate_js(action.eval_script)
                self._last_action_result = {"eval_script": action.eval_script}
                return True, None

            else:
                return True, None

        except Exception as e:
            return False, str(e)

    def _narrate_step(self, step: JourneyStep):
        """Feed step to narrator and print summary if produced."""
        if self.narrator:
            summary = self.narrator.on_step(step)
            if summary:
                print(summary)

    def _log_verbose(self, **kwargs) -> str:
        """Return a formatted string containing all provided keyword argument values."""
        parts = [f"{k}={v}" for k, v in kwargs.items()]
        return " ".join(parts)

    def _print_step(self, step_number: int, action: Action):
        """Print step information to console."""
        frustration_bar = "=" * int(action.frustration_level * 10)
        frustration_bar = frustration_bar.ljust(10, "-")

        print(f"\n--- Step {step_number} ---")
        print(f"Thought: \"{action.thought}\"")
        print(f"Action: {action.action_type.value} -> {action.target}")
        print(f"Frustration: [{frustration_bar}] {action.frustration_level:.0%}")
        print(f"Confidence: {action.confidence:.0%}")

    async def _confirm_action(self, action: Action) -> bool:
        """Ask user to confirm action. Returns True if confirmed."""
        print(f"\n[?] Execute {action.action_type.value} on '{action.target}'?")
        print("    [Enter] to execute | [s] to skip | [q] to quit")

        # For now, auto-confirm in async context
        # In real CLI, this would use input()
        return True

    async def _download_file(self, url: str, model: str, stage: str, student: str):
        """Download a file from url into the model/stage/student directory."""
        pass

    def _ensure_download_dir(self, model: str, stage: str, student: str) -> Path:
        """Create and return the downloads/model/stage/student directory."""
        path = self.config.downloads_dir / model / stage / student
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_verification_entry(self, model: str, stage: str, status: str, details: str) -> Path:
        """Legacy standalone writer kept only for non-controller journey compatibility."""
        report_path = self.config.output_dir / "verification_report.md"
        if not report_path.exists():
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("# Verification Report\n\n")
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(f"## {model} — {stage}\n\n")
            f.write(f"**Status:** {status}\n\n")
            f.write(f"**Details:** {details}\n\n")
            f.write("---\n\n")
        return report_path

    def _check_budget(self, current_step: int) -> dict:
        remaining = self.config.max_steps - current_step
        return {
            "remaining": remaining,
            "total": self.config.max_steps,
            "is_low": remaining < self.config.max_steps * 0.1,
        }

    def _on_budget_exhaustion(self) -> Path:
        return self._write_verification_entry(
            model="unknown",
            stage="budget_exhaustion",
            status="PARTIAL",
            details="Journey stopped: budget exhausted.",
        )


# Convenience function for CLI usage
async def run_journey(
    url: str,
    goal: str,
    persona: str = "investor",
    viewport: str = "desktop",
    mode: str = "basic",
    headless: bool = True,
    ask_before_action: bool = False,
) -> JourneyReport:
    """
    Convenience function to run a journey.

    Args:
        url: Starting URL
        goal: What to achieve
        persona: Persona name
        viewport: Viewport name
        mode: "basic" or "in_depth"
        headless: Run browser headless
        ask_before_action: Confirm each action

    Returns:
        JourneyReport
    """
    config = AgentConfig(ask_before_action=ask_before_action)

    agent = InvestorJourneyAgent(
        persona=persona,
        viewport=viewport,
        mode=mode,
        config=config,
        headless=headless,
    )

    return await agent.run_journey(url=url, goal=goal)
