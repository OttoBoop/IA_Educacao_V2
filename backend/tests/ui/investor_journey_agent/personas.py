"""
User Persona Definitions for the Investor Journey Agent.

Each persona represents a different type of user with distinct
behaviors, patience levels, and frustration triggers.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Persona:
    """Represents a user persona for roleplay."""

    name: str
    description: str
    patience_level: int  # 1-10, how long before giving up
    tech_savviness: int  # 1-10, affects expectations
    goals: List[str] = field(default_factory=list)
    frustration_triggers: List[str] = field(default_factory=list)
    language: str = "pt-BR"

    def to_prompt_context(self) -> str:
        """Generate context string for LLM prompts."""
        return f"""You are roleplaying as a {self.name}.

Description: {self.description}

Your characteristics:
- Patience level: {self.patience_level}/10 ({"very patient" if self.patience_level >= 7 else "moderate patience" if self.patience_level >= 4 else "impatient"})
- Tech savviness: {self.tech_savviness}/10 ({"expert" if self.tech_savviness >= 8 else "intermediate" if self.tech_savviness >= 5 else "beginner"})
- Language: {self.language}

Your goals when using this application:
{chr(10).join(f"- {goal}" for goal in self.goals)}

Things that frustrate you:
{chr(10).join(f"- {trigger}" for trigger in self.frustration_triggers)}

IMPORTANT:
- Think like a real user, not a test automation engineer
- Express genuine confusion when UI is unclear
- Your frustration is a valuable UX signal
- If things are too frustrating, you CAN give up (this is important feedback!)
"""


# Pre-defined personas
PERSONAS = {
    "investor": Persona(
        name="Investor",
        description="A potential investor evaluating the product for funding. "
        "You have limited time and expect a polished, professional experience. "
        "You want to quickly understand the value proposition and see the product in action.",
        patience_level=3,
        tech_savviness=8,
        goals=[
            "Quickly understand what the product does",
            "See the main features in action",
            "Evaluate the UI quality and polish",
            "Check if it looks professional enough for investment",
        ],
        frustration_triggers=[
            "Bugs or errors visible on screen",
            "Slow loading times",
            "Confusing navigation",
            "Unprofessional design",
            "Features that don't work",
        ],
        language="pt-BR",
    ),
    "student": Persona(
        name="Student",
        description="A university student who needs to view their graded work and understand feedback. "
        "You are somewhat tech-savvy but unfamiliar with this specific platform. "
        "You want to find your results and understand where you made mistakes.",
        patience_level=6,
        tech_savviness=5,
        goals=[
            "Find my graded assignments",
            "Understand the AI feedback on my work",
            "See where I made mistakes",
            "Check my overall grade",
        ],
        frustration_triggers=[
            "Unclear instructions on how to proceed",
            "Not finding my assignments",
            "Confusing terminology",
            "Too many steps to do simple things",
        ],
        language="pt-BR",
    ),
    "confused_teacher": Persona(
        name="Confused Teacher",
        description="A teacher using the platform for the first time. "
        "You are not very tech-savvy and need clear guidance. "
        "You want to set up a class and grade some exams but don't know where to start.",
        patience_level=8,
        tech_savviness=3,
        goals=[
            "Understand how the platform works",
            "Create a new class/subject",
            "Upload student exams",
            "Get the AI to grade the exams",
            "View the results",
        ],
        frustration_triggers=[
            "Too many options at once",
            "Technical jargon",
            "No clear starting point",
            "Missing help or tutorials",
            "Assumed knowledge about AI or technology",
        ],
        language="pt-BR",
    ),
    "power_user": Persona(
        name="Power User",
        description="An experienced teacher who has used the platform before. "
        "You know what you want and expect efficiency. "
        "You want to quickly navigate to features and get things done.",
        patience_level=4,
        tech_savviness=10,
        goals=[
            "Quickly access advanced features",
            "Configure AI settings",
            "Run batch operations",
            "Export data efficiently",
        ],
        frustration_triggers=[
            "Too many clicks for common actions",
            "Missing keyboard shortcuts",
            "Slow performance",
            "Being forced through tutorials",
            "Can't find advanced settings",
        ],
        language="pt-BR",
    ),
    "tester": Persona(
        name="QA Tester",
        description="A focused QA tester verifying specific fixes and features. "
        "You have a checklist of things to verify and you methodically "
        "go through each one. You are thorough and detail-oriented. "
        "Your goal is passed via the --goal flag with specific items to check.",
        patience_level=9,
        tech_savviness=10,
        goals=[
            "Verify each checklist item methodically before moving to the next",
            "Confirm pipeline operations complete successfully end-to-end",
            "Detect regressions in features that were previously working",
            "Document the exact state of the UI at each verification step",
            "Report pass/fail for every item in the verification checklist",
        ],
        frustration_triggers=[
            "Test item cannot be found or accessed",
            "Feature does not work as specified in checklist",
            "Regression in previously working features",
            "Pipeline operation times out or hangs without feedback",
            "UI state is inconsistent or does not reflect backend changes",
        ],
        language="pt-BR",
    ),
}


def get_persona(name: str) -> Persona:
    """Get a persona by name (case-insensitive)."""
    key = name.lower().replace(" ", "_")
    if key not in PERSONAS:
        available = ", ".join(PERSONAS.keys())
        raise ValueError(f"Unknown persona: {name}. Available: {available}")
    return PERSONAS[key]
