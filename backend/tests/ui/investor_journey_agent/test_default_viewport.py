"""
Tests for F8-T7: Change default viewport to desktop (1440x900).

Verifies that:
1. InvestorJourneyAgent defaults to "desktop" viewport when none specified
2. CLI --viewport argument defaults to "desktop"
3. Module-level run_journey() convenience function defaults to "desktop"
"""


class TestAgentDefaultViewport:
    """InvestorJourneyAgent must default to desktop viewport."""

    def test_agent_default_viewport_is_desktop(self):
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        agent = InvestorJourneyAgent(
            persona="investor",
            mode="basic",
            config=config,
        )
        assert agent.viewport_name == "desktop"

    def test_agent_viewport_config_is_1440x900(self):
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        agent = InvestorJourneyAgent(
            persona="investor",
            mode="basic",
            config=config,
        )
        assert agent.viewport_config["width"] == 1440
        assert agent.viewport_config["height"] == 900


class TestCliDefaultViewport:
    """build_parser() must default --viewport to desktop."""

    def test_parser_viewport_defaults_to_desktop(self):
        from tests.ui.investor_journey_agent.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.viewport == "desktop"

    def test_parser_viewport_can_be_overridden(self):
        from tests.ui.investor_journey_agent.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["--viewport", "iphone_14"])
        assert args.viewport == "iphone_14"


class TestConvenienceFunctionDefaultViewport:
    """Module-level run_journey() must default to desktop viewport."""

    def test_run_journey_defaults_to_desktop(self):
        import inspect
        from tests.ui.investor_journey_agent.agent import run_journey

        sig = inspect.signature(run_journey)
        assert sig.parameters["viewport"].default == "desktop"
