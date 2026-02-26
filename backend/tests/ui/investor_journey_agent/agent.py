"""
Investor Journey Agent - Main orchestrator.

Coordinates browser automation and LLM decision-making
to simulate realistic user journeys.
"""

import asyncio
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

    @property
    def success_rate(self) -> float:
        """Calculate success rate from steps."""
        if not self.steps:
            return 0.0
        successful = sum(1 for s in self.steps if s.success)
        return successful / len(self.steps)

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
        viewport: str = "iphone_14",
        mode: Literal["basic", "in_depth"] = "basic",
        config: Optional[AgentConfig] = None,
        on_step: Optional[Callable[[JourneyStep], None]] = None,
        headless: bool = True,
        narrator: Optional["ProgressNarrator"] = None,
        event_emitter: Optional[EventEmitter] = None,
        command_receiver: Optional[CommandReceiver] = None,
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

        # Will be initialized in run_journey
        self._browser: Optional[BrowserInterface] = None
        self._brain: Optional[LLMBrain] = None

    async def run_journey(
        self,
        url: str,
        goal: str,
        max_steps: Optional[int] = None,
        website_context: Optional[str] = None,
    ) -> JourneyReport:
        """
        Run a simulated user journey.

        Args:
            url: Starting URL
            goal: What the persona is trying to achieve
            max_steps: Maximum steps before stopping

        Returns:
            JourneyReport with all steps and evaluation
        """
        max_steps = max_steps or self.config.max_steps
        start_time = datetime.now()
        steps: List[JourneyStep] = []

        # Create output directory
        output_dir = self.config.output_dir / start_time.strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir = output_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)

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

            # Main journey loop
            incomplete = False
            incomplete_reason = None
            step_number = 0

            user_guidance = None  # For mid-journey guidance from operator

            try:
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

                    if step.action.action_type == ActionType.DONE:
                        print("\n[DONE] Goal achieved!")
                        break

                    if step.action.action_type == ActionType.GIVE_UP:
                        print(f"\n[GAVE UP] {step.action.thought}")
                        break

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

        if self.event_emitter:
            self.event_emitter.emit_step(step)
        if self.on_step:
            self.on_step(step)
        self._narrate_step(step)

        # Wait for page to settle
        await self._browser.wait_for_idle()
        await asyncio.sleep(self.config.wait_after_action_ms / 1000)

        return step

    async def _execute_action(self, action: Action) -> tuple[bool, Optional[str]]:
        """Execute an action and return (success, error_message)."""
        try:
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
                await asyncio.sleep(1)
                return True, None

            elif action.action_type == ActionType.RELOAD:
                success = await self._browser.reload()
                return success, None if success else "Could not reload page"

            elif action.action_type == ActionType.BACK:
                success = await self._browser.go_back()
                return success, None if success else "Could not go back"

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


# Convenience function for CLI usage
async def run_journey(
    url: str,
    goal: str,
    persona: str = "investor",
    viewport: str = "iphone_14",
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
