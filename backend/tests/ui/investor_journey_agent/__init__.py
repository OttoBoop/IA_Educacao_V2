"""
Investor Journey Agent - UI Testing with LLM Roleplay

This module provides an AI-powered UI testing agent that simulates
realistic user behavior while navigating the Prova AI application.

Key Features:
- LLM roleplays as different personas (investor, student, teacher)
- Takes screenshots at each step with documented reasoning
- Simulates real human behavior including frustration
- Two modes: Basic (report) and In-depth (suggestions)

Usage:
    from tests.ui.investor_journey_agent import InvestorJourneyAgent, PERSONAS

    agent = InvestorJourneyAgent(
        persona=PERSONAS["investor"],
        viewport="iphone_14"
    )
    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="View the dashboard and understand the product"
    )
"""

from .config import VIEWPORT_CONFIGS, AgentConfig, LOCAL_URL, PRODUCTION_URL
from .personas import PERSONAS, Persona, get_persona
from .agent import InvestorJourneyAgent, JourneyReport, run_journey
from .browser_interface import BrowserInterface, PageState, ClickableElement
from .llm_brain import LLMBrain, Action, ActionType, JourneyStep, JourneyEvaluation
from .report_generator import ReportGenerator, GenerationResult

__all__ = [
    # Main agent
    "InvestorJourneyAgent",
    "JourneyReport",
    "run_journey",
    # Personas
    "PERSONAS",
    "Persona",
    "get_persona",
    # Configuration
    "VIEWPORT_CONFIGS",
    "AgentConfig",
    "LOCAL_URL",
    "PRODUCTION_URL",
    # Browser
    "BrowserInterface",
    "PageState",
    "ClickableElement",
    # LLM
    "LLMBrain",
    "Action",
    "ActionType",
    "JourneyStep",
    "JourneyEvaluation",
    # Report
    "ReportGenerator",
    "GenerationResult",
]
