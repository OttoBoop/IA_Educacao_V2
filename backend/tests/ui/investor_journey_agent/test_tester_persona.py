"""
Tests for the tester persona - a goal-directed QA verification agent.

The tester persona is designed for targeted verification after fixes,
using a checklist passed via --goal flag rather than open-ended exploration.
"""

import unittest

from tests.ui.investor_journey_agent.personas import PERSONAS, Persona, get_persona


class TestTesterPersonaExists(unittest.TestCase):
    """Verify the tester persona is registered and accessible."""

    def test_tester_in_personas_dict(self):
        """Tester persona must be a key in PERSONAS."""
        self.assertIn("tester", PERSONAS)

    def test_get_persona_returns_tester(self):
        """get_persona('tester') must return a Persona instance."""
        persona = get_persona("tester")
        self.assertIsInstance(persona, Persona)

    def test_get_persona_case_insensitive(self):
        """get_persona should work with 'Tester' or 'TESTER'."""
        persona = get_persona("Tester")
        self.assertEqual(persona.name, "QA Tester")


class TestTesterPersonaAttributes(unittest.TestCase):
    """Verify the tester persona has correct characteristics."""

    def setUp(self):
        self.persona = get_persona("tester")

    def test_high_patience(self):
        """Tester should have high patience (>= 8) for thorough verification."""
        self.assertGreaterEqual(self.persona.patience_level, 8)

    def test_high_tech_savviness(self):
        """Tester should have high tech savviness (>= 9) as a QA professional."""
        self.assertGreaterEqual(self.persona.tech_savviness, 9)

    def test_goals_are_empty_by_default(self):
        """Tester goals should be empty - populated dynamically via --goal flag."""
        self.assertEqual(self.persona.goals, [])

    def test_has_frustration_triggers(self):
        """Tester should have QA-relevant frustration triggers."""
        self.assertGreater(len(self.persona.frustration_triggers), 0)

    def test_language_is_pt_br(self):
        """Tester persona should use pt-BR like all other personas."""
        self.assertEqual(self.persona.language, "pt-BR")


class TestTesterPersonaPrompt(unittest.TestCase):
    """Verify the tester persona generates appropriate LLM context."""

    def setUp(self):
        self.persona = get_persona("tester")
        self.context = self.persona.to_prompt_context()

    def test_prompt_mentions_qa_tester(self):
        """The prompt context should identify the role as QA Tester."""
        self.assertIn("QA Tester", self.context)

    def test_prompt_mentions_checklist(self):
        """The prompt context should mention checklist-driven verification."""
        self.assertIn("checklist", self.context.lower())

    def test_prompt_shows_very_patient(self):
        """High patience should be reflected in the prompt."""
        self.assertIn("very patient", self.context)

    def test_prompt_shows_expert(self):
        """High tech savviness should show as 'expert' in the prompt."""
        self.assertIn("expert", self.context)


class TestTesterPersonaDefaultGoals(unittest.TestCase):
    """F7-T1: Tester persona must have ≥3 default goals for pipeline verification."""

    def setUp(self):
        self.persona = get_persona("tester")

    def test_tester_has_at_least_three_default_goals(self):
        """Tester persona must have at least 3 default goals covering pipeline verification."""
        self.assertGreaterEqual(
            len(self.persona.goals),
            3,
            f"PERSONAS['tester'].goals must have ≥3 entries for pipeline verification. "
            f"Currently has {len(self.persona.goals)}: {self.persona.goals}. "
            "Add default goals to the tester persona in personas.py.",
        )


if __name__ == "__main__":
    unittest.main()
