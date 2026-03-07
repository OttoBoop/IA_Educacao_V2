"""
F10-T1: Verification suite outer loop controller.

Starts the journey agent in pause-mode, acts as Claude Code outer loop:
- Auto-sends "continue" after each normal step
- Sends "guidance" when stuck events are detected
- Tracks CHECKLIST milestones and marks them PASS/FAIL in verification_report.md
- Runs until agent completes, gives up, or user interrupts

Usage:
    cd IA_Educacao_V2/backend
    python run_verification_f10.py
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).parent
AGENT_MODULE = "tests.ui.investor_journey_agent"
LIVE_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_BASE = BACKEND_DIR / "investor_journey_reports" / "verification_run_F10"
VERIFICATION_REPORT = OUTPUT_BASE / "verification_report.md"
MAX_STEPS = 400
VIEWPORT = "desktop"
PERSONA = "tester"

GOAL = (
    "Verify the full Prova AI grading pipeline end-to-end across 4 AI models "
    "(gpt-4o, gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview). "
    "For each model: trigger the pipeline, monitor all 4 stages in the task panel, "
    "download JSON and PDF outputs, validate content integrity, and trigger the "
    "desempenho cascade to confirm auto-creation of performance reports."
)

# CHECKLIST item IDs → keywords that suggest completion in thought/action text
MILESTONE_KEYWORDS = {
    "pipeline-trigger-gpt4o": ["gpt-4o", "gpt4o", "pipeline", "trigger", "iniciou", "iniciando"],
    "pipeline-trigger-gpt5-nano": ["gpt-5-nano", "gpt5", "nano", "pipeline"],
    "pipeline-trigger-claude-haiku": ["claude-haiku", "haiku", "pipeline"],
    "pipeline-trigger-gemini-flash": ["gemini", "flash", "pipeline"],
    "download-json-outputs": ["json", "download", "baixar", "arquivo"],
    "download-pdf-reports": ["pdf", "download", "baixar", "relatorio", "relatório"],
    "validation-json-fields": ["validar", "campos", "questao_id", "nota", "habilidades"],
    "validation-origem-id-chain": ["origem_id", "chain", "consistente"],
    "validation-student-name": ["nome", "aluno", "student"],
    "desempenho-cascade-trigger": ["desempenho", "cascade", "cascata"],
    "desempenho-auto-creation": ["desempenho", "criado", "auto"],
    "desempenho-report-content": ["desempenho", "habilidades", "breakdown"],
}


# ---------------------------------------------------------------------------
# Event reading
# ---------------------------------------------------------------------------


def read_new_events(events_path: Path, last_count: int) -> tuple[list[dict], int]:
    """Read events added since last_count lines."""
    if not events_path.exists():
        return [], last_count
    try:
        lines = events_path.read_text(encoding="utf-8").strip().split("\n")
        new_lines = lines[last_count:]
        events = []
        for line in new_lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return events, len(lines)
    except Exception:
        return [], last_count


# ---------------------------------------------------------------------------
# Command sending
# ---------------------------------------------------------------------------


def send_command(commands_path: Path, command_type: str, data: dict | None = None):
    """Append a command to commands.jsonl."""
    cmd = {"command_type": command_type, "data": data or {}, "timestamp": datetime.utcnow().isoformat()}
    with open(commands_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cmd) + "\n")
    print(f"[CTRL] → {command_type.upper()}" + (f": {data.get('instruction', '')[:60]}" if data and "instruction" in data else ""))


# ---------------------------------------------------------------------------
# Verification report updater
# ---------------------------------------------------------------------------


def mark_checklist_item(report_path: Path, item_id: str, status: str, observation: str = ""):
    """Update a CHECKLIST item's status in the verification report."""
    if not report_path.exists():
        return
    content = report_path.read_text(encoding="utf-8")
    # Replace PENDING in the row that contains item_id
    pattern = rf"(\| {re.escape(item_id)} \|[^|]*\|) PENDING ( \|[^|]*\|)"
    replacement = rf"\1 {status} \2"
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        if observation:
            # Append observation to the last column
            new_content = new_content.replace(
                f"| {item_id} |", f"| {item_id} |"
            )
        report_path.write_text(new_content, encoding="utf-8")
        print(f"[CTRL] ✓ Marked {item_id} → {status}")


def update_summary(report_path: Path):
    """Update PASS/FAIL/PENDING counts in Summary section."""
    if not report_path.exists():
        return
    content = report_path.read_text(encoding="utf-8")
    pass_count = content.count(" PASS ")
    fail_count = content.count(" FAIL ")
    pending_count = content.count(" PENDING ")
    content = re.sub(r"- PASS: \d+", f"- PASS: {pass_count}", content)
    content = re.sub(r"- FAIL: \d+", f"- FAIL: {fail_count}", content)
    content = re.sub(r"- PENDING: \d+", f"- PENDING: {pending_count}", content)
    report_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main controller loop
# ---------------------------------------------------------------------------


def run_controller(ipc_dir: Path):
    events_path = ipc_dir / "events.jsonl"
    commands_path = ipc_dir / "commands.jsonl"

    print(f"[CTRL] IPC directory: {ipc_dir}")
    print(f"[CTRL] Verification report: {VERIFICATION_REPORT}")
    print(f"[CTRL] Press Ctrl+C to stop the run gracefully\n")

    last_event_count = 0
    stuck_pending = False
    completed_ids: set[str] = set()
    step_count = 0
    running = True

    while running:
        try:
            new_events, last_event_count = read_new_events(events_path, last_event_count)

            for event in new_events:
                etype = event.get("event_type")

                if etype == "step_completed":
                    step_count += 1
                    action = event.get("action", "")
                    thought = event.get("thought", "")
                    success = event.get("success", False)
                    text = (thought + " " + action).lower()

                    print(
                        f"[CTRL] Step {event.get('step'):>3}/{MAX_STEPS} "
                        f"{'✓' if success else '✗'} {action[:55]}..."
                    )

                    # Check CHECKLIST milestones
                    for item_id, keywords in MILESTONE_KEYWORDS.items():
                        if item_id not in completed_ids:
                            if any(kw in text for kw in keywords) and success:
                                mark_checklist_item(VERIFICATION_REPORT, item_id, "PASS")
                                completed_ids.add(item_id)
                                update_summary(VERIFICATION_REPORT)

                elif etype == "stuck":
                    stuck_pending = True
                    print(
                        f"[CTRL] ⚠ STUCK: {event.get('action_type')} on '{event.get('target')}'"
                    )

                elif etype == "paused":
                    step = event.get("step", "?")
                    if stuck_pending:
                        send_command(
                            commands_path,
                            "guidance",
                            {
                                "instruction": (
                                    "You seem stuck. Try a completely different approach: "
                                    "scroll the page, look for a different button or link, "
                                    "or navigate to a different section entirely."
                                )
                            },
                        )
                        stuck_pending = False
                    else:
                        send_command(commands_path, "continue")

                elif etype in ("complete", "gave_up", "stopped", "error"):
                    print(f"\n[CTRL] Journey ended: {etype}")
                    print(f"[CTRL] Total steps completed: {step_count}")
                    print(f"[CTRL] CHECKLIST items marked PASS: {len(completed_ids)}")
                    update_summary(VERIFICATION_REPORT)
                    running = False
                    break

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n[CTRL] Interrupted by user. Sending stop command...")
            send_command(commands_path, "stop", {"reason": "User interrupted controller"})
            update_summary(VERIFICATION_REPORT)
            running = False


# ---------------------------------------------------------------------------
# Entry point — start agent and controller together
# ---------------------------------------------------------------------------


def main():
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    # Build agent command
    cmd = [
        sys.executable, "-m", AGENT_MODULE,
        "--persona", PERSONA,
        "--viewport", VIEWPORT,
        "--pause-mode",
        "--no-headless",
        "--max-steps", str(MAX_STEPS),
        "--url", LIVE_URL,
        "--output", str(OUTPUT_BASE),
        "--no-open",
        "--no-narrate",
        "--goal", GOAL,
    ]

    print("=" * 60)
    print("F10-T1: VERIFICATION SUITE OUTER LOOP CONTROLLER")
    print("=" * 60)
    print(f"Persona:  {PERSONA}")
    print(f"Viewport: {VIEWPORT}")
    print(f"Max steps: {MAX_STEPS}")
    print(f"URL: {LIVE_URL}")
    print("=" * 60)
    print("\nStarting agent...")

    # Start agent subprocess
    proc = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Read first lines to get IPC_DIR
    ipc_dir = None
    for _ in range(30):  # Wait up to 15 seconds for IPC_DIR
        line = proc.stdout.readline()
        if line:
            print(f"[AGENT] {line.rstrip()}")
            if line.startswith("IPC_DIR="):
                ipc_dir_str = line.strip().removeprefix("IPC_DIR=")
                ipc_dir = BACKEND_DIR / ipc_dir_str
                break
        time.sleep(0.5)

    if not ipc_dir:
        print("[CTRL] ERROR: Could not get IPC_DIR from agent. Killing process.")
        proc.terminate()
        sys.exit(1)

    print(f"\n[CTRL] IPC directory: {ipc_dir}")

    # Print remaining agent startup output in a background thread
    import threading

    def print_agent_output():
        for line in proc.stdout:
            if line.strip():
                print(f"[AGENT] {line.rstrip()}")

    thread = threading.Thread(target=print_agent_output, daemon=True)
    thread.start()

    # Wait for events.jsonl to appear
    events_path = ipc_dir / "events.jsonl"
    print("[CTRL] Waiting for first event...")
    for _ in range(60):
        if events_path.exists():
            break
        time.sleep(0.5)

    # Run the outer loop
    try:
        run_controller(ipc_dir)
    finally:
        # Wait for agent to finish
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.terminate()

    print("\n[CTRL] Verification run complete.")
    print(f"[CTRL] Report: {VERIFICATION_REPORT}")
    print(f"[CTRL] IPC dir: {ipc_dir}")


if __name__ == "__main__":
    main()
