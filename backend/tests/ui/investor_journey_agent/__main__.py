"""
CLI interface for the Investor Journey Agent.

Usage:
    python -m tests.ui.investor_journey_agent --help

Examples:
    # Run investor journey on production
    python -m tests.ui.investor_journey_agent \\
        --persona investor \\
        --url https://ia-educacao-v2.onrender.com

    # Run student journey on local with in-depth analysis
    python -m tests.ui.investor_journey_agent \\
        --persona student \\
        --url http://localhost:8000 \\
        --mode in_depth

    # Run with visible browser (for debugging)
    python -m tests.ui.investor_journey_agent \\
        --persona confused_teacher \\
        --url http://localhost:8000 \\
        --no-headless
"""

import argparse
import asyncio
import sys
import webbrowser
from pathlib import Path

# Fix Windows console encoding for Unicode (LLM responses contain emojis)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .agent import InvestorJourneyAgent
from .config import AgentConfig, VIEWPORT_CONFIGS, LOCAL_URL, PRODUCTION_URL
from .personas import PERSONAS
from .progress_narrator import ProgressNarrator
from .report_generator import ReportGenerator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Investor Journey Agent - Simulate user journeys with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --persona investor --url https://ia-educacao-v2.onrender.com
  %(prog)s --persona student --url http://localhost:8000 --mode in_depth
  %(prog)s --persona confused_teacher --url http://localhost:8000 --no-headless
        """,
    )

    parser.add_argument(
        "--persona",
        type=str,
        default="investor",
        choices=list(PERSONAS.keys()),
        help=f"User persona to simulate. Available: {', '.join(PERSONAS.keys())}",
    )

    parser.add_argument(
        "--viewport",
        type=str,
        default="iphone_14",
        choices=list(VIEWPORT_CONFIGS.keys()),
        help=f"Device viewport. Available: {', '.join(VIEWPORT_CONFIGS.keys())}",
    )

    parser.add_argument(
        "--url",
        type=str,
        default=PRODUCTION_URL,
        help=f"URL to test. Default: {PRODUCTION_URL}",
    )

    parser.add_argument(
        "--goal",
        type=str,
        default="Explore the application and understand what it does",
        help="Goal for the persona to achieve",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="basic",
        choices=["basic", "in_depth"],
        help="Mode: 'basic' for report only, 'in_depth' for analysis",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maximum number of steps before stopping",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for report (default: auto-generated)",
    )

    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window (for debugging)",
    )

    parser.add_argument(
        "--ask",
        action="store_true",
        help="Ask for confirmation before each action",
    )

    parser.add_argument(
        "--local",
        action="store_true",
        help=f"Use local URL ({LOCAL_URL}) instead of production",
    )

    parser.add_argument(
        "--no-narrate",
        action="store_true",
        help="Disable periodic progress narration during the run",
    )

    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't auto-open HTML report in browser after generation",
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Resolve URL
    url = LOCAL_URL if args.local else args.url

    # Create config
    config = AgentConfig(
        ask_before_action=args.ask,
        max_steps=args.max_steps,
    )

    if args.output:
        config.output_dir = Path(args.output)

    # Create narrator (enabled by default)
    narrator = None if args.no_narrate else ProgressNarrator(interval=3)

    # Create agent
    agent = InvestorJourneyAgent(
        persona=args.persona,
        viewport=args.viewport,
        mode=args.mode,
        config=config,
        headless=not args.no_headless,
        narrator=narrator,
    )

    print(f"\n{'='*60}")
    print("INVESTOR JOURNEY AGENT")
    print(f"{'='*60}")
    print(f"Persona:  {args.persona}")
    print(f"Viewport: {args.viewport}")
    print(f"URL:      {url}")
    print(f"Mode:     {args.mode}")
    print(f"Goal:     {args.goal}")
    print(f"{'='*60}\n")

    # Run journey
    try:
        report = await agent.run_journey(
            url=url,
            goal=args.goal,
            max_steps=args.max_steps,
        )

        # Generate report
        generator = ReportGenerator()
        result = generator.generate(report)

        print(f"\n{'='*60}")
        print("JOURNEY COMPLETE")
        print(f"{'='*60}")
        print(f"Total Steps:  {len(report.steps)}")
        print(f"Success Rate: {report.success_rate:.0%}")
        print(f"Gave Up:      {'Yes' if report.gave_up else 'No'}")

        if report.evaluation:
            print(f"\nOverall Rating: {'*' * int(report.evaluation.overall_rating)}/5")
            print(f"Pain Points:    {len(report.evaluation.pain_points)}")

        # Print all generated file locations
        print(f"\n{result.get_file_locations_summary()}")
        print(f"{'='*60}\n")

        # Auto-open HTML report in browser
        if not args.no_open and result.html_report_path and result.html_report_path.exists():
            html_url = result.html_report_path.resolve().as_uri()
            print(f"Opening HTML report in browser...")
            webbrowser.open(html_url)

        # Return exit code based on success
        if report.gave_up:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n\nJourney interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\nError: {e}")
        return 1


def cli():
    """CLI entry point."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli()
