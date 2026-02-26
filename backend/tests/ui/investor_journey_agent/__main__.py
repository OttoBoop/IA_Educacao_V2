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
import os
import sys
import webbrowser
from pathlib import Path

# Fix Windows console encoding for Unicode (LLM responses contain emojis)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .agent import InvestorJourneyAgent
from .config import AgentConfig, VIEWPORT_CONFIGS, LOCAL_URL, PRODUCTION_URL
from .event_emitter import EventEmitter
from .command_receiver import CommandReceiver
from .personas import PERSONAS
from .progress_narrator import ProgressNarrator
from .report_generator import ReportGenerator
from .url_utils import resolve_url
from .context_store import load_context, save_context


def resolve_context(cli_context, url, store_path=None):
    """Resolve website context: CLI flag overrides saved, saves new context."""
    if cli_context:
        save_context(url, cli_context, store_path=store_path)
        return cli_context
    return load_context(url, store_path=store_path)


def build_parser():
    """Build the argument parser. Separated for testability."""
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
        default=200,
        help="Maximum number of steps before stopping",
    )

    parser.add_argument(
        "--start-url",
        type=str,
        default=None,
        help="Navigate to this URL/fragment after base URL (e.g. /#turmas, /dashboard)",
    )

    parser.add_argument(
        "--setup",
        type=str,
        default=None,
        help="Path to a Python file to exec() before the step loop (e.g., setup.py). "
        "Script receives 'page' and 'browser' in its local namespace.",
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

    # Interactive mode (for Claude Code IPC)
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable IPC mode: emit events to events.jsonl, accept commands from commands.jsonl",
    )

    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Resume from a saved state directory (reads state.json)",
    )

    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Website description to help the AI persona understand what it's looking at",
    )

    return parser


def parse_args():
    """Parse command line arguments."""
    return build_parser().parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Resolve URL (supports file paths, file:// URLs, and http(s) URLs)
    if args.local:
        url = LOCAL_URL
    else:
        url = resolve_url(args.url)

    # Resolve website context (CLI flag overrides saved, auto-loads from store)
    website_context = resolve_context(cli_context=args.context, url=url)

    # Create config
    config = AgentConfig(
        ask_before_action=args.ask,
        max_steps=args.max_steps,
        website_context=website_context,
    )

    if args.output:
        config.output_dir = Path(args.output)

    # Create narrator (enabled by default)
    narrator = None if args.no_narrate else ProgressNarrator(interval=3)

    # Interactive mode: set up IPC components
    event_emitter = None
    command_receiver = None
    if args.interactive:
        # Output dir needs to be resolved early for IPC
        from datetime import datetime
        output_dir = config.output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        config.output_dir = output_dir.parent  # Agent will use output_dir parent

        event_emitter = EventEmitter(
            output_dir=output_dir,
            max_steps=args.max_steps,
            persona=args.persona,
        )
        command_receiver = CommandReceiver(output_dir=output_dir)

        # Print IPC dir as first line for caller to parse
        print(f"IPC_DIR={output_dir}")
        sys.stdout.flush()

    # Create agent
    agent = InvestorJourneyAgent(
        persona=args.persona,
        viewport=args.viewport,
        mode=args.mode,
        config=config,
        headless=not args.no_headless,
        narrator=narrator,
        event_emitter=event_emitter,
        command_receiver=command_receiver,
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
            website_context=website_context,
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
            html_path = str(result.html_report_path.resolve())
            print(f"Opening HTML report in browser...")
            if sys.platform == "win32":
                os.startfile(html_path)
            else:
                webbrowser.open(result.html_report_path.resolve().as_uri())

        # Return exit code based on success
        if report.gave_up:
            return 1
        return 0

    except KeyboardInterrupt:
        print("\n\nJourney interrupted by user.")
        return 130
    except Exception as e:
        import traceback
        print(f"\n\nError: {e}")
        traceback.print_exc()
        return 1


def cli():
    """CLI entry point."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    cli()
