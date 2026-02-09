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

from .config import AgentConfig, VIEWPORT_CONFIGS, DEFAULT_CONFIG
from .personas import Persona, PERSONAS, get_persona
from .browser_interface import BrowserInterface
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

        # Will be initialized in run_journey
        self._browser: Optional[BrowserInterface] = None
        self._brain: Optional[LLMBrain] = None

    async def run_journey(
        self,
        url: str,
        goal: str,
        max_steps: Optional[int] = None,
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
                print("Failed to load initial page!")
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

            try:
                while step_number < max_steps:
                    step_number += 1

                    # Get current state
                    state = await browser.get_state()

                    # Save screenshot
                    screenshot_path = screenshots_dir / f"step_{step_number:02d}.png"
                    await browser.save_screenshot(screenshot_path)

                    # Get LLM decision
                    action = await self._brain.decide_next_action(
                        screenshot_base64=state.screenshot_base64,
                        dom_snapshot=state.dom_snapshot,
                        persona=self.persona,
                        goal=goal,
                        history=steps,
                        console_errors=state.console_errors,
                    )

                    # Print step info
                    self._print_step(step_number, action)

                    # Check for terminal actions
                    if action.action_type == ActionType.DONE:
                        step = JourneyStep(
                            step_number=step_number,
                            url=state.url,
                            screenshot_path=str(screenshot_path),
                            action=action,
                            success=True,
                        )
                        steps.append(step)
                        if self.on_step:
                            self.on_step(step)
                        self._narrate_step(step)
                        print("\n[DONE] Goal achieved!")
                        break

                    if action.action_type == ActionType.GIVE_UP:
                        step = JourneyStep(
                            step_number=step_number,
                            url=state.url,
                            screenshot_path=str(screenshot_path),
                            action=action,
                            success=False,
                            error_message="User gave up due to frustration",
                        )
                        steps.append(step)
                        if self.on_step:
                            self.on_step(step)
                        self._narrate_step(step)
                        print(f"\n[GAVE UP] {action.thought}")
                        break

                    # Ask for confirmation if configured
                    if self.config.ask_before_action:
                        if not await self._confirm_action(action):
                            print("Action skipped by user")
                            continue

                    # Execute the action
                    success, error = await self._execute_action(action)

                    step = JourneyStep(
                        step_number=step_number,
                        url=state.url,
                        screenshot_path=str(screenshot_path),
                        action=action,
                        success=success,
                        error_message=error,
                    )
                    steps.append(step)

                    if self.on_step:
                        self.on_step(step)
                    self._narrate_step(step)

                    # Wait for page to settle
                    await browser.wait_for_idle()
                    await asyncio.sleep(self.config.wait_after_action_ms / 1000)

            except Exception as e:
                incomplete = True
                incomplete_reason = str(e)
                print(f"\n[ERROR] Journey interrupted: {e}")

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
