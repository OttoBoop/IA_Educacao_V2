"""
LLM Brain - Claude API integration for decision-making.

Uses Claude's vision capabilities to analyze screenshots and
decide what action a persona would take next.
"""

import json
import base64
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum

import httpx

from .personas import Persona
from .config import AgentConfig


class ActionType(str, Enum):
    """Types of actions the agent can take."""

    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    GIVE_UP = "give_up"
    DONE = "done"
    WAIT = "wait"
    RELOAD = "reload"
    BACK = "back"


@dataclass
class Action:
    """An action decided by the LLM."""

    action_type: ActionType
    target: str  # Selector or description
    thought: str  # Persona's reasoning
    frustration_level: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    text_to_type: Optional[str] = None  # For TYPE action
    scroll_direction: Optional[str] = None  # For SCROLL action


@dataclass
class JourneyStep:
    """A recorded step in the journey."""

    step_number: int
    url: str
    screenshot_path: str
    action: Action
    success: bool
    error_message: Optional[str] = None


@dataclass
class PainPoint:
    """A UX pain point discovered during the journey."""

    description: str
    severity: Literal["low", "medium", "high"]
    step_number: int
    suggestion: Optional[str] = None


@dataclass
class JourneyEvaluation:
    """Final evaluation of a journey."""

    success_rate: float
    total_steps: int
    give_up_points: List[int]
    pain_points: List[PainPoint]
    suggestions: List[str]
    overall_rating: float  # 1-5


class MaxLLMCallsExceededError(Exception):
    """Raised when the maximum number of LLM calls is exceeded."""
    pass


class LLMBrain:
    """
    The 'brain' that uses Claude to decide what a persona would do.

    Uses vision to analyze screenshots and DOM to understand page structure.
    """

    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, config: AgentConfig):
        self.config = config
        self.api_key = config.anthropic_api_key
        self.call_count = 0  # Track LLM API calls

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Set it in environment or config."
            )

    async def _call_claude(
        self,
        messages: List[dict],
        model: str,
        max_tokens: int = 1024,
        system: Optional[str] = None,
    ) -> str:
        """Make an API call to Claude."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.ANTHROPIC_API_URL,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Claude API error: {response.status_code} - {response.text}"
                )

            data = response.json()
            return data["content"][0]["text"]

    def _build_decision_system_prompt(self, persona: Persona, goal: str) -> str:
        """Build the system prompt for decision-making."""
        return f"""{persona.to_prompt_context()}

Your current goal: {goal}

Based on the screenshot and DOM structure I show you, decide what to do next.

IMPORTANT:
- Think like a real user, not a test automation engineer
- Express genuine confusion when UI is unclear
- Consider "giving up" if things are too frustrating
- Your frustration is a valuable UX signal

Available actions:
- click: Click an element (provide selector like "#button-id" or ".class-name")
- type: Type text into an input (provide selector and text)
- scroll: Scroll the page (direction: "up" or "down")
- wait: Wait for something to load
- reload: Reload the page (useful when something seems broken)
- back: Go back to the previous page
- give_up: Stop trying because UX is too bad (this is valuable feedback!)
- done: Goal achieved, stop journey

When the previous action failed:
- Consider what a real user would do: retry, try something else, reload, or give up
- Your reaction should match your patience level and technical skill
- Failure reactions are important UX feedback!

Respond ONLY with valid JSON (no markdown, no explanation outside JSON):
{{
  "thought": "What I'm thinking as this user...",
  "frustration_level": 0.0 to 1.0,
  "action_type": "click|type|scroll|wait|reload|back|give_up|done",
  "target": "selector or description",
  "confidence": 0.0 to 1.0,
  "text_to_type": "text if typing",
  "scroll_direction": "up or down if scrolling"
}}
"""

    async def decide_next_action(
        self,
        screenshot_base64: str,
        dom_snapshot: str,
        persona: Persona,
        goal: str,
        history: List[JourneyStep] = None,
        console_errors: List[str] = None,
        user_guidance: Optional[str] = None,
    ) -> Action:
        """
        Decide what action the persona would take next.

        Uses vision to analyze the screenshot and DOM for context.
        """
        # Check if max LLM calls exceeded
        if self.call_count >= self.config.max_llm_calls:
            raise MaxLLMCallsExceededError(
                f"Maximum LLM calls ({self.config.max_llm_calls}) exceeded"
            )

        history = history or []
        console_errors = console_errors or []

        # Build the user message with screenshot and context
        user_content = []

        # Add screenshot as image
        user_content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_base64,
                },
            }
        )

        # Add context text
        context_text = f"""
## Current Page Analysis

**DOM Structure (interactive elements):**
```
{dom_snapshot[:3000]}
```

**Previous Actions ({len(history)} steps so far):**
"""
        if history:
            for step in history[-3:]:  # Last 3 steps
                status = 'success' if step.success else 'failed'
                context_text += f"- Step {step.step_number}: {step.action.action_type.value} on {step.action.target} ({status})\n"

            # Check if the last action failed - add prominent failure notice
            last_step = history[-1]
            if not last_step.success:
                context_text += f"\n**⚠️ LAST ACTION FAILED!**\n"
                context_text += f"Action: {last_step.action.action_type.value} on {last_step.action.target}\n"
                if last_step.error_message:
                    context_text += f"Error: {last_step.error_message}\n"
                context_text += "\nHow would you react to this failure? Consider your patience level and decide: retry, try something else, reload the page, or give up?\n"
        else:
            context_text += "None yet - this is the first step.\n"

        if console_errors:
            context_text += f"\n**Console Errors:** {', '.join(console_errors[:5])}"

        if user_guidance:
            context_text += f"\n\n**Guidance from operator:** {user_guidance}"

        context_text += "\n\nWhat would you do next? Remember to respond ONLY with JSON."

        user_content.append({"type": "text", "text": context_text})

        messages = [{"role": "user", "content": user_content}]

        system_prompt = self._build_decision_system_prompt(persona, goal)

        try:
            response_text = await self._call_claude(
                messages=messages,
                model=self.config.step_model,
                max_tokens=512,
                system=system_prompt,
            )

            # Increment call count after successful call
            self.call_count += 1

            # Parse JSON response
            # Clean up response (remove markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text.strip())

            return Action(
                action_type=ActionType(data.get("action_type", "wait")),
                target=data.get("target", ""),
                thought=data.get("thought", ""),
                frustration_level=float(data.get("frustration_level", 0.0)),
                confidence=float(data.get("confidence", 0.5)),
                text_to_type=data.get("text_to_type"),
                scroll_direction=data.get("scroll_direction"),
            )

        except json.JSONDecodeError as e:
            # If parsing fails, return a safe wait action
            return Action(
                action_type=ActionType.WAIT,
                target="",
                thought=f"I couldn't understand the response: {e}",
                frustration_level=0.3,
                confidence=0.0,
            )
        except Exception as e:
            return Action(
                action_type=ActionType.WAIT,
                target="",
                thought=f"Error during decision: {e}",
                frustration_level=0.5,
                confidence=0.0,
            )

    async def evaluate_journey(
        self,
        steps: List[JourneyStep],
        persona: Persona,
        goal: str,
    ) -> JourneyEvaluation:
        """
        Evaluate the completed journey and generate insights.

        Uses a more capable model for final analysis.
        """
        # Build summary of journey
        journey_summary = f"""
## Journey Summary

**Persona:** {persona.name}
**Goal:** {goal}
**Total Steps:** {len(steps)}

### Step-by-Step:
"""
        for step in steps:
            journey_summary += f"""
**Step {step.step_number}:**
- Action: {step.action.action_type.value} on "{step.action.target}"
- Thought: "{step.action.thought}"
- Frustration: {step.action.frustration_level:.1%}
- Result: {"Success" if step.success else f"Failed: {step.error_message}"}
"""

        system_prompt = f"""You are a UX analyst evaluating a user journey through the Prova AI application.

The user was roleplaying as: {persona.name} - {persona.description}

Analyze the journey and provide:
1. Success rate (0.0 to 1.0)
2. Pain points with severity (low/medium/high)
3. Actionable suggestions for improvement
4. Overall rating (1-5)

Respond ONLY with valid JSON:
{{
  "success_rate": 0.0 to 1.0,
  "give_up_points": [step numbers where user wanted to give up],
  "pain_points": [
    {{"description": "...", "severity": "low|medium|high", "step_number": N, "suggestion": "..."}}
  ],
  "suggestions": ["...", "..."],
  "overall_rating": 1 to 5
}}
"""

        messages = [{"role": "user", "content": journey_summary}]

        try:
            response_text = await self._call_claude(
                messages=messages,
                model=self.config.analysis_model,
                max_tokens=1024,
                system=system_prompt,
            )

            # Clean and parse response
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text.strip())

            pain_points = [
                PainPoint(
                    description=pp.get("description", ""),
                    severity=pp.get("severity", "medium"),
                    step_number=pp.get("step_number", 0),
                    suggestion=pp.get("suggestion"),
                )
                for pp in data.get("pain_points", [])
            ]

            return JourneyEvaluation(
                success_rate=float(data.get("success_rate", 0.5)),
                total_steps=len(steps),
                give_up_points=data.get("give_up_points", []),
                pain_points=pain_points,
                suggestions=data.get("suggestions", []),
                overall_rating=float(data.get("overall_rating", 3.0)),
            )

        except Exception as e:
            # Return a basic evaluation on error
            give_up_steps = [
                s.step_number
                for s in steps
                if s.action.action_type == ActionType.GIVE_UP
            ]
            failed_steps = [s for s in steps if not s.success]
            success_rate = (len(steps) - len(failed_steps)) / max(len(steps), 1)

            return JourneyEvaluation(
                success_rate=success_rate,
                total_steps=len(steps),
                give_up_points=give_up_steps,
                pain_points=[
                    PainPoint(
                        description=f"Analysis error: {e}",
                        severity="low",
                        step_number=0,
                    )
                ],
                suggestions=["Manual review needed due to analysis error"],
                overall_rating=3.0,
            )
