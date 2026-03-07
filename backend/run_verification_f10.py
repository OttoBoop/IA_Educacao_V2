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
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
    "THIS IS A JAVASCRIPT SINGLE-PAGE APP (SPA). URL always stays at '/'. DO NOT reload.\n\n"
    "=== COMPLETE STEP-BY-STEP INSTRUCTIONS ===\n\n"
    "PHASE 1 — NAVIGATE (use evaluate_js for ALL steps, do NOT click):\n"
    "  1a: evaluate_js → showMateria('f95445ace30e7dc5') — wait 5 seconds\n"
    "  1b: evaluate_js → showTurma('6b5dc44c08aaf375') — wait 8 seconds\n"
    "  1c: evaluate_js → showAtividade('effad48d128c7083') — wait 5 seconds\n"
    "You are now on the A1 - Cálculo 1 atividade page.\n\n"
    "PHASE 2 — TRIGGER PIPELINE FOR EACH OF 4 MODELS. "
    "For each model (gpt-4o, gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview):\n"
    "  2a: evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma')\n"
    "      (This opens a modal dialog)\n"
    "  2b: wait 2 seconds for modal to load\n"
    "  2c: select_option → select from the Modelo de IA dropdown "
    "(element with text containing 'gpt-4o' or 'haiku' or 'gemini' etc.)\n"
    "  2d: evaluate_js → executarPipelineCompleto()\n"
    "      (This is the function that the Executar button calls — do NOT try to click the button)\n"
    "  2e: wait 90 seconds (wait_duration_seconds=90) for pipeline to complete\n"
    "  2f: if still running, wait another 60 seconds\n"
    "  Repeat 2a-2f for all 4 models.\n\n"
    "PHASE 3 — DOWNLOAD & VALIDATE:\n"
    "  After pipelines complete, download_file for PDF and JSON from Documentos da Atividade.\n"
    "  Verify JSON contains: questao_id, nota, habilidades.\n"
    "  Check desempenho cascade reports exist (tarefa, turma, materia levels).\n\n"
    "KEY RULE: NEVER click any button to trigger the pipeline — use evaluate_js → executarPipelineCompleto() instead. "
    "NEVER scroll looking for a model dropdown on the main page — the dropdown is INSIDE the modal only. "
    "NEVER reload. NEVER re-navigate if you are already on the A1 page."
)

# B1: Keyword-based PASS marking removed — caused false positives.
# Checklist items must be marked by human review after the run, not auto-detected.


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

    # Format 1: table row with item_id in it — e.g. "| pipeline-trigger-gpt4o | desc | PENDING | |"
    # After group1 ends at "|", the literal " PENDING " is consumed, leaving "| obs |" (no leading space).
    pattern = rf"(\| {re.escape(item_id)} \|[^|]*\|) PENDING (\|[^|]*\|)"
    replacement = rf"\1 {status} \2"
    new_content = re.sub(pattern, replacement, content)

    # Format 2: section-header item — "### Checklist: item_id" followed by "| PENDING | |"
    if new_content == content:
        # Find the section for this item_id and replace the next PENDING in its table
        header_pattern = rf"(### Checklist: {re.escape(item_id)}.*?)\| PENDING \|"
        new_content = re.sub(header_pattern, rf"\1| {status} |", content, count=1, flags=re.DOTALL)

    if new_content != content:
        report_path.write_text(new_content, encoding="utf-8")
        print(f"[CTRL] PASS: Marked {item_id} -> {status}")


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
    step_count = 0
    running = True
    # Track recent actions for repetition-based stuck detection
    recent_actions: list[tuple[str, str]] = []  # (action_type, target_prefix)
    guidance_cooldown = 0  # Steps to wait before sending another guidance
    # B3: count executarPipelineCompleto triggers to detect when Phase 3 should start
    pipeline_trigger_count = 0
    phase3_injected = False

    while running:
        try:
            new_events, last_event_count = read_new_events(events_path, last_event_count)

            for event in new_events:
                etype = event.get("event_type")

                if etype == "step_completed":
                    step_count += 1
                    action = event.get("action", "")
                    target = event.get("target", "")
                    thought = event.get("thought", "")
                    success = event.get("success", False)
                    text = (thought + " " + action + " " + target).lower()

                    status_char = "OK" if success else "!!"
                    print(
                        f"[CTRL] Step {event.get('step'):>3}/{MAX_STEPS} "
                        f"[{status_char}] {action[:40]} | {target[:40]}..."
                    )

                    # Track recent actions for repetition detection
                    recent_actions.append((action, target[:40]))
                    if len(recent_actions) > 10:
                        recent_actions.pop(0)
                    if guidance_cooldown > 0:
                        guidance_cooldown -= 1

                    # B3: count executarPipelineCompleto triggers
                    if "executarPipelineCompleto" in (action + " " + target + " " + thought) and success:
                        pipeline_trigger_count += 1
                        print(f"[CTRL] PIPELINE TRIGGER #{pipeline_trigger_count} detected")

                elif etype == "stuck":
                    stuck_pending = True
                    print(
                        f"[CTRL] STUCK: {event.get('action_type')} on '{event.get('target')}'"
                    )

                elif etype == "paused":
                    step = event.get("step", "?")

                    # Detect repetition-based stuck: same action_type 5+ times in last 8 steps
                    # Excludes "scroll" (normal page exploration) and single-shot actions
                    repetition_stuck = False
                    reload_stuck = False
                    no_progress_stuck = False
                    if guidance_cooldown == 0:
                        action_types = [a for a, _ in recent_actions[-8:]]
                        non_scroll = [a for a in action_types if a not in ("scroll", "wait")]
                        # B2: Exempt first 10 steps — Phase 1 navigation uses 4+ evaluate_js calls
                        if step_count > 10 and len(non_scroll) >= 5:
                            most_common = max(set(non_scroll), key=non_scroll.count)
                            if non_scroll.count(most_common) >= 5:
                                repetition_stuck = True
                                stuck_action_type = most_common
                                print(f"[CTRL] REPEAT-STUCK: '{stuck_action_type}' x{non_scroll.count(most_common)} in last 8 steps")

                        # Detect reload in recent actions (harmful in SPA)
                        if action_types and action_types[-1] == "reload":
                            reload_stuck = True
                            print("[CTRL] RELOAD-STUCK: agent just reloaded (harmful in SPA)")

                        # No-progress stuck: 80+ steps with 0 pipeline triggers
                        if step_count >= 80 and pipeline_trigger_count == 0:
                            no_progress_stuck = True
                            print(f"[CTRL] NO-PROGRESS: {step_count} steps with 0 pipeline triggers")

                    # B3: Inject Phase 3 guidance when all 4 pipelines have been triggered
                    if pipeline_trigger_count >= 4 and not phase3_injected:
                        phase3_injected = True
                        phase3_instruction = (
                            "PHASE 3 — All 4 pipeline triggers detected. Now download and validate:\n"
                            "1. Locate the Documentos da Atividade section on the page.\n"
                            "2. Use download_file for each PDF report and JSON output available.\n"
                            "3. For each JSON file downloaded, verify it contains: questao_id, nota, habilidades.\n"
                            "4. Check that desempenho cascade reports exist at tarefa, turma, and materia levels.\n"
                            "5. If desempenho reports are missing, report what was found instead.\n"
                            "IMPORTANT: Do NOT trigger any more pipelines. Download and inspect outputs only."
                        )
                        send_command(commands_path, "guidance", {"instruction": phase3_instruction})
                        print("[CTRL] PHASE 3 guidance injected — all 4 pipelines triggered")

                    if stuck_pending or repetition_stuck or reload_stuck or no_progress_stuck:
                        if reload_stuck:
                            instruction = (
                                "STOP! Do NOT reload the page. Reloading in this SPA takes you back "
                                "to the home screen, losing all navigation progress. "
                                "If you just reloaded, the page is now back to home. "
                                "Navigate again using evaluate_js (NOT clicks):\n"
                                "  evaluate_js: showMateria('f95445ace30e7dc5') → wait 5s\n"
                                "  evaluate_js: showTurma('6b5dc44c08aaf375') → wait 8s\n"
                                "  evaluate_js: showAtividade('effad48d128c7083') → wait 5s\n"
                                "Console 404 errors are NORMAL background API calls — they are NOT "
                                "a reason to reload. Ignore them and continue navigating."
                            )
                        elif repetition_stuck:
                            instruction = (
                                f"STOP! You've been repeating '{stuck_action_type}' actions with no progress. "
                                "IMPORTANT: Look at the current screenshot carefully.\n"
                                "If you see pipeline buttons (Executar Etapa, Pipeline Aluno, Pipeline Todos os Alunos): "
                                "you are ALREADY on the A1 atividade page! Stop re-navigating. "
                                "Use evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma'), "
                                "wait 2s, select the model from the dropdown, "
                                "then evaluate_js → executarPipelineCompleto(). "
                                "NEVER click the Executar button directly — always call executarPipelineCompleto() via evaluate_js.\n"
                                "If you do NOT see pipeline buttons: re-navigate using evaluate_js:\n"
                                "  evaluate_js: showMateria('f95445ace30e7dc5') → wait 5s\n"
                                "  evaluate_js: showTurma('6b5dc44c08aaf375') → wait 8s\n"
                                "  evaluate_js: showAtividade('effad48d128c7083') → wait 5s"
                            )
                        elif no_progress_stuck:
                            instruction = (
                                f"After {step_count} steps, no pipeline verification has started. "
                                "Navigate directly using evaluate_js:\n"
                                "  Step 1: evaluate_js: showMateria('f95445ace30e7dc5') → then wait 5 seconds\n"
                                "  Step 2: evaluate_js: showTurma('6b5dc44c08aaf375') → then wait 8 seconds\n"
                                "  Step 3: evaluate_js: showAtividade('effad48d128c7083') → then wait 5 seconds\n"
                                "After step 3 you should see the A1 atividade page with pipeline controls. "
                                "DO NOT use click for navigation. DO NOT reload."
                            )
                        else:
                            instruction = (
                                "You seem stuck. Are you on the A1 atividade page? "
                                "If YES: run evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma'), "
                                "wait 2s, select gpt-4o from dropdown, "
                                "then evaluate_js → executarPipelineCompleto(), then wait 90s. "
                                "If NO: navigate → showMateria('f95445ace30e7dc5') → showTurma('6b5dc44c08aaf375') "
                                "→ showAtividade('effad48d128c7083'). "
                                "NEVER reload. NEVER click the Executar button — always use evaluate_js instead."
                            )
                        send_command(commands_path, "guidance", {"instruction": instruction})
                        stuck_pending = False
                        guidance_cooldown = 6  # Don't send guidance again for 6 steps
                        recent_actions.clear()
                        no_progress_stuck = False
                    else:
                        send_command(commands_path, "continue")

                elif etype in ("complete", "gave_up", "stopped", "error"):
                    print(f"\n[CTRL] Journey ended: {etype}")
                    print(f"[CTRL] Total steps completed: {step_count}")
                    print(f"[CTRL] Pipeline triggers detected: {pipeline_trigger_count}")
                    print(f"[CTRL] Phase 3 injected: {phase3_injected}")
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


def warmup_server(url: str, max_attempts: int = 5) -> bool:
    """Pre-warm the Render server to avoid cold-start errors during the run."""
    print(f"[CTRL] Pre-warming server: {url}/api/materias ...")
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.urlopen(f"{url}/api/materias", timeout=30)
            data = req.read()
            if b"materias" in data:
                print(f"[CTRL] Server warm! (attempt {attempt})")
                return True
        except Exception as e:
            print(f"[CTRL] Warmup attempt {attempt}/{max_attempts} failed: {e}")
            time.sleep(5)
    print("[CTRL] WARNING: Server may still be cold — proceeding anyway")
    return False


def main():
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    # Pre-warm the Render server to avoid cold-start errors in the agent
    warmup_server(LIVE_URL)

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

    # Pre-inject startup guidance into commands.jsonl before the agent's first pause.
    # This tells the agent to use evaluate_js for navigation (avoids click resolution issues).
    commands_path = ipc_dir / "commands.jsonl"
    ipc_dir.mkdir(parents=True, exist_ok=True)
    startup_instruction = (
        "STARTUP INSTRUCTIONS — follow exactly:\n"
        "Step 1: If you see 'Bem-vindo ao NOVO CR' modal → evaluate_js: closeWelcome()\n"
        "Step 2: evaluate_js → showMateria('f95445ace30e7dc5') — wait 5s\n"
        "Step 3: evaluate_js → showTurma('6b5dc44c08aaf375') — wait 8s\n"
        "Step 4: evaluate_js → showAtividade('effad48d128c7083') — wait 5s\n"
        "Step 5: evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma') — wait 2s\n"
        "Step 6: select_option → pick the gpt-4o option from the Modelo de IA dropdown\n"
        "Step 7: evaluate_js → executarPipelineCompleto()\n"
        "Step 8: wait 90 seconds (wait_duration_seconds=90)\n"
        "Step 9: Repeat steps 5-8 for gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview\n"
        "CRITICAL: Do NOT click any button to trigger the pipeline. "
        "Use evaluate_js → executarPipelineCompleto() instead. "
        "Do NOT scroll the main page looking for a model dropdown. "
        "The model dropdown only exists INSIDE the modal (step 6)."
    )
    send_command(commands_path, "guidance", {"instruction": startup_instruction})
    print("[CTRL] Startup guidance pre-injected into commands.jsonl")

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
