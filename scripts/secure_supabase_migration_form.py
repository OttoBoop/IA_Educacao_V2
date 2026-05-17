#!/usr/bin/env python3
"""Local-only form for applying the token_usage Supabase migration.

The form binds to 127.0.0.1, accepts the Postgres connection URL as a password
field, applies only backend/migrations/002_create_token_usage.sql, and prints no
secret values.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import urllib.request
import venv
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs


HOST = "127.0.0.1"
MAX_BODY_BYTES = 25_000
DEFAULT_SITE_URL = "https://ia-educacao-v2.onrender.com"
MIGRATION_PATH = Path("backend/migrations/002_create_token_usage.sql")


def choose_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def mask_url(value: str) -> str:
    if "@" not in value:
        return "***"
    left, right = value.rsplit("@", 1)
    scheme = left.split("://", 1)[0] if "://" in left else "postgresql"
    host = right.split("/", 1)[0]
    return f"{scheme}://***@{host}/***"


def sanitize_error(text: str, secret_value: str) -> str:
    safe = text.replace(secret_value, mask_url(secret_value)) if secret_value else text
    if "://" in safe and "@" in safe:
        scheme, rest = safe.split("://", 1)
        if "@" in rest:
            safe = f"{scheme}://***@" + rest.rsplit("@", 1)[1]
    return safe[:500]


def python_in_venv(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_driver(temp_dir: Path) -> Path:
    venv_dir = temp_dir / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    python = python_in_venv(venv_dir)
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--quiet",
            "psycopg[binary]>=3.2,<4",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    return python


def apply_migration(database_url: str, migration_file: Path) -> dict[str, object]:
    if not database_url.startswith(("postgresql://", "postgres://")):
        return {
            "ok": False,
            "reason": "A URL precisa comecar com postgresql:// ou postgres://.",
        }
    if not migration_file.exists():
        return {"ok": False, "reason": f"Migration ausente: {migration_file}"}

    child_code = textwrap.dedent(
        """
        import os
        import sys
        from pathlib import Path

        import psycopg

        db_url = os.environ.pop("NOVOCR_DATABASE_URL")
        sql = Path(sys.argv[1]).read_text(encoding="utf-8")

        with psycopg.connect(db_url, connect_timeout=20) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

        print("migration_applied")
        """
    ).strip()

    try:
        with tempfile.TemporaryDirectory(prefix="novocr_supabase_migration_") as tmp:
            python = ensure_driver(Path(tmp))
            env = dict(os.environ)
            env["NOVOCR_DATABASE_URL"] = database_url
            proc = subprocess.run(
                [str(python), "-c", child_code, str(migration_file)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            env["NOVOCR_DATABASE_URL"] = ""
    except Exception as exc:
        return {
            "ok": False,
            "reason": sanitize_error(f"{type(exc).__name__}: {exc}", database_url),
        }

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip().splitlines()
        reason = stderr[-1] if stderr else "migration_failed"
        return {"ok": False, "reason": sanitize_error(reason, database_url)}
    return {"ok": True, "reason": "migration_applied"}


def fetch_cost_status(site_url: str) -> dict[str, object]:
    url = site_url.rstrip("/") + "/api/custos/status?limit=20"
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        backend = data.get("token_usage_backend", {})
        supabase = backend.get("supabase", {}) if isinstance(backend, dict) else {}
        return {
            "ok": bool(data.get("ok")),
            "durable": bool(backend.get("durable")) if isinstance(backend, dict) else False,
            "table_available": supabase.get("table_available"),
            "error_code": supabase.get("error_code"),
            "missing_migration": supabase.get("missing_migration"),
        }
    except Exception as exc:
        return {"ok": False, "reason": type(exc).__name__}


def build_server(args: argparse.Namespace, token: str) -> tuple[HTTPServer, dict[str, object]]:
    repo_root = Path(args.repo_root).resolve()
    migration_file = repo_root / MIGRATION_PATH
    site_url = args.site_url.rstrip("/")
    state: dict[str, object] = {"done": False, "summary": None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def send_html(self, status: int, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path != f"/{token}":
                self.send_html(404, "<h1>404</h1>")
                return
            self.send_html(
                200,
                f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVO CR - migration segura Supabase</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 32px; background: #f7f7f3; color: #151515; }}
main {{ max-width: 780px; margin: auto; }}
label {{ display: block; margin: 18px 0 6px; font-weight: 700; }}
input[type=password] {{ width: 100%; box-sizing: border-box; font-size: 17px; padding: 12px; border: 1px solid #777; border-radius: 6px; }}
button {{ margin-top: 22px; padding: 12px 18px; border: 0; border-radius: 6px; background: #0d6b57; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }}
.notice {{ border-left: 4px solid #0d6b57; padding: 12px 16px; background: #fff; }}
.small {{ color: #555; font-size: 14px; }}
code {{ background: #fff; padding: 2px 4px; border-radius: 4px; }}
</style></head><body><main>
<h1>Aplicar migration token_usage no Supabase</h1>
<p class="notice">Cole a URL Postgres aqui, nunca no chat. Esta pagina roda so em <b>127.0.0.1</b>, nao grava arquivo e nao imprime segredo.</p>
<p>Migration permitida: <code>{html.escape(str(MIGRATION_PATH))}</code></p>
<form method="post" action="/{token}" autocomplete="off">
<label>Postgres connection URL do Supabase</label>
<input type="password" name="database_url" required autocomplete="new-password" autofocus>
<p class="small">Use a connection string direta ou pooler com permissao para criar tabela em <code>public</code>.</p>
<p><label style="display:inline;font-weight:600"><input type="checkbox" name="confirm" value="1" required> Confirmo aplicar somente <code>002_create_token_usage.sql</code></label></p>
<button type="submit">Aplicar migration sem expor segredo</button>
</form></main></body></html>""",
            )

        def do_POST(self) -> None:
            if self.path != f"/{token}":
                self.send_html(404, "<h1>404</h1>")
                return
            length = min(int(self.headers.get("Content-Length", "0")), MAX_BODY_BYTES)
            raw = self.rfile.read(length).decode("utf-8", "replace")
            form = parse_qs(raw, keep_blank_values=True)
            raw = ""
            database_url = (form.get("database_url", [""])[0] or "").strip()
            confirmed = bool(form.get("confirm"))
            form = {}

            if not confirmed:
                summary = {"ok": False, "reason": "confirmacao_obrigatoria"}
            else:
                summary = {
                    "database_preview": mask_url(database_url),
                    "migration": str(MIGRATION_PATH),
                    **apply_migration(database_url, migration_file),
                }
                database_url = ""
                if summary.get("ok"):
                    time.sleep(args.verify_delay)
                    summary["cost_status"] = fetch_cost_status(site_url)
            state["summary"] = summary
            state["done"] = True

            rows = "".join(
                f"<li><b>{html.escape(str(k))}</b>: {html.escape(str(v))}</li>"
                for k, v in summary.items()
            )
            self.send_html(
                200,
                f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<title>NOVO CR - migration Supabase</title></head><body>
<h1>Resultado seguro</h1><ul>{rows}</ul>
<p>Esta janela ja pode ser fechada.</p>
</body></html>""",
            )

    port = args.port or choose_port(HOST)
    return HTTPServer((HOST, port), Handler), state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL)
    parser.add_argument("--port", type=int)
    parser.add_argument("--verify-delay", type=float, default=3.0)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    token = secrets.token_urlsafe(24)
    server, state = build_server(args, token)
    url = f"http://{HOST}:{server.server_port}/{token}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print("Secure Supabase migration form ready:")
    print(url)
    print("No secrets will be printed. Waiting for one submission...")
    if args.open:
        webbrowser.open(url)

    try:
        while not state["done"]:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        thread.join(timeout=2)

    summary = state.get("summary")
    print("Summary:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary and summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
