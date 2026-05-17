#!/usr/bin/env python3
"""Local-only form for updating Render env vars without exposing secrets.

The form binds to 127.0.0.1, accepts secrets as password fields, sends them
directly to the Render API, and prints only sanitized status lines.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs
from urllib.request import Request, urlopen


DEFAULT_SERVICE_ID = "srv-d5t8gbh4tr6s738fr3s0"
DEFAULT_API_BASE = "https://api.render.com/v1"
MAX_BODY_BYTES = 20_000


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def render_request(
    method: str,
    url: str,
    render_key: str,
    body: dict[str, str] | None = None,
) -> dict[str, object]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        url,
        data=payload,
        method=method,
        headers={
            "Authorization": f"Bearer {render_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "novocr-secure-render-env-form/1.0",
        },
    )
    try:
        with urlopen(req, timeout=45) as resp:
            resp.read()
            return {"ok": True, "status": resp.status, "reason": resp.reason}
    except HTTPError as exc:
        try:
            exc.read()
        except Exception:
            pass
        return {"ok": False, "status": exc.code, "reason": exc.reason}
    except URLError as exc:
        return {"ok": False, "status": "network", "reason": str(exc.reason)}
    except Exception as exc:
        return {"ok": False, "status": "error", "reason": type(exc).__name__}


def update_render_envs(
    api_base: str,
    service_id: str,
    render_key: str,
    updates: dict[str, str],
    do_deploy: bool,
) -> dict[str, object]:
    results = []
    api_base = api_base.rstrip("/")
    for key, value in updates.items():
        url = f"{api_base}/services/{service_id}/env-vars/{key}"
        result = render_request("PUT", url, render_key, {"value": value})
        results.append({"key": key, "preview": mask_secret(value), **result})
        value = ""

    deploy_result = None
    if do_deploy and all(bool(item["ok"]) for item in results):
        deploy_url = f"{api_base}/services/{service_id}/deploys"
        deploy_result = render_request(
            "POST",
            deploy_url,
            render_key,
            {"clearCache": "do_not_clear"},
        )
    return {"results": results, "deploy": deploy_result}


def choose_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def build_server(args: argparse.Namespace, token: str) -> tuple[HTTPServer, dict[str, object]]:
    state: dict[str, object] = {"done": False, "summary": None}
    api_base = args.api_base.rstrip("/")
    service_id = args.service_id

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
            checked = "" if args.no_deploy_default else "checked"
            self.send_html(
                200,
                f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NOVO CR - envio seguro de chaves</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 32px; background: #f7f7f3; color: #151515; }}
main {{ max-width: 760px; margin: auto; }}
label {{ display: block; margin: 18px 0 6px; font-weight: 700; }}
input[type=password] {{ width: 100%; box-sizing: border-box; font-size: 17px; padding: 12px; border: 1px solid #777; border-radius: 6px; }}
button {{ margin-top: 22px; padding: 12px 18px; border: 0; border-radius: 6px; background: #0d6b57; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }}
.notice {{ border-left: 4px solid #0d6b57; padding: 12px 16px; background: #fff; }}
.small {{ color: #555; font-size: 14px; }}
</style></head><body><main>
<h1>Envio seguro de chaves para o Render</h1>
<p class="notice">Cole as chaves aqui, nunca no chat. Esta pagina roda so em <b>127.0.0.1</b>, nao grava arquivo e nao imprime segredo.</p>
<form method="post" action="/{token}" autocomplete="off">
<label>Render API key</label>
<input type="password" name="render_key" required autocomplete="new-password" autofocus>
<p class="small">Usada apenas para atualizar env vars no servico <code>{html.escape(service_id)}</code> e disparar deploy.</p>
<label>GOOGLE_API_KEY nova ou corrigida</label>
<input type="password" name="GOOGLE_API_KEY" autocomplete="new-password">
<label>ANTHROPIC_API_KEY com creditos</label>
<input type="password" name="ANTHROPIC_API_KEY" autocomplete="new-password">
<label>OPENAI_API_KEY opcional, deixe vazio se nao quiser alterar</label>
<input type="password" name="OPENAI_API_KEY" autocomplete="new-password">
<p><label style="display:inline;font-weight:600"><input type="checkbox" name="deploy" value="1" {checked}> Reiniciar/deployar depois de salvar env vars para o site carregar as chaves novas</label></p>
<button type="submit">Enviar para Render sem expor no chat</button>
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

            render_key = (form.get("render_key", [""])[0] or "").strip()
            updates = {
                key: (form.get(key, [""])[0] or "").strip()
                for key in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
            }
            updates = {key: value for key, value in updates.items() if value}
            do_deploy = bool(form.get("deploy"))
            form = {}

            if not render_key:
                self.send_html(400, "<h1>Render API key ausente</h1>")
                return
            if not updates:
                self.send_html(400, "<h1>Nenhuma chave de provider foi informada</h1>")
                return

            summary = update_render_envs(api_base, service_id, render_key, updates, do_deploy)
            results = summary["results"]
            deploy_result = summary["deploy"]
            render_key = ""
            state["done"] = True
            state["summary"] = summary

            rows = "".join(
                "<tr><td>{key}</td><td>{preview}</td><td>{status} {reason}</td></tr>".format(
                    key=html.escape(str(item["key"])),
                    preview=html.escape(str(item["preview"])),
                    status=html.escape(str(item["status"])),
                    reason=html.escape(str(item["reason"])),
                )
                for item in results
            )
            deploy_html = ""
            if deploy_result:
                deploy_html = "<p><b>Deploy:</b> {status} {reason}</p>".format(
                    status=html.escape(str(deploy_result["status"])),
                    reason=html.escape(str(deploy_result["reason"])),
                )
            self.send_html(
                200,
                f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><title>Chaves enviadas</title>
<style>body{{font-family:system-ui;margin:32px;background:#f7f7f3;color:#151515}} main{{max-width:760px;margin:auto}} table{{border-collapse:collapse;width:100%;background:white}} td,th{{border:1px solid #bbb;padding:10px;text-align:left}} .ok{{border-left:4px solid #0d6b57;padding:12px;background:white}}</style>
</head><body><main><h1>Envio concluido</h1><p class="ok">Os valores completos nao foram impressos nem gravados. Pode fechar esta aba.</p>
<table><thead><tr><th>Variavel</th><th>Preview</th><th>Status Render</th></tr></thead><tbody>{rows}</tbody></table>{deploy_html}
</main></body></html>""",
            )
            threading.Thread(target=shutdown_later, args=(server,), daemon=True).start()

    server = HTTPServer((args.host, args.port), Handler)
    return server, state


def shutdown_later(server: HTTPServer) -> None:
    time.sleep(2)
    server.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument(
        "--service-id",
        default=os.environ.get("RENDER_SERVICE_ID", DEFAULT_SERVICE_ID),
    )
    parser.add_argument("--api-base", default=os.environ.get("RENDER_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--open", action="store_true", help="Open the form in the default browser.")
    parser.add_argument("--yad", action="store_true", help="Use a native yad password dialog instead of the browser form.")
    parser.add_argument("--no-deploy-default", action="store_true")
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        raise SystemExit("Refusing to bind outside 127.0.0.1")
    if args.port == 0:
        args.port = choose_port(args.host)
    return args


def print_summary(summary: dict[str, object]) -> None:
    for item in summary.get("results", []):
        print(f"UPDATED {item['key']} -> HTTP {item['status']}")
    deploy = summary.get("deploy")
    if deploy:
        print(f"DEPLOY_REQUEST -> HTTP {deploy['status']}")


def run_yad(args: argparse.Namespace) -> int:
    if not shutil.which("yad"):
        print("SECURE_KEY_POPUP_UNAVAILABLE")
        return 2
    default_deploy = "FALSE" if args.no_deploy_default else "TRUE"
    result = subprocess.run(
        [
            "yad",
            "--form",
            "--title=NOVO CR - chaves Render",
            "--width=620",
            "--center",
            "--on-top",
            "--text=Envie as chaves aqui, nunca no chat. O deploy/restart so acontece depois de salvar as env vars, para o site carregar as chaves novas.",
            "--separator=\n",
            "--button=Cancelar:1",
            "--button=Enviar para Render:0",
            "--field=Render API key:H",
            "--field=GOOGLE_API_KEY:H",
            "--field=ANTHROPIC_API_KEY:H",
            "--field=OPENAI_API_KEY opcional:H",
            "--field=Reiniciar/deployar apos salvar env vars:CHK",
            "",
            "",
            "",
            "",
            default_deploy,
        ],
        capture_output=True,
        text=True,
        timeout=None,
    )
    if result.returncode != 0:
        print("SECURE_KEY_POPUP_CANCELLED")
        return 1

    lines = result.stdout.splitlines()
    while len(lines) < 5:
        lines.append("")
    render_key = lines[0].strip()
    updates = {
        "GOOGLE_API_KEY": lines[1].strip(),
        "ANTHROPIC_API_KEY": lines[2].strip(),
        "OPENAI_API_KEY": lines[3].strip(),
    }
    updates = {key: value for key, value in updates.items() if value}
    do_deploy = lines[4].strip().upper() in {"TRUE", "1", "YES", "SIM"}
    if not render_key:
        print("SECURE_KEY_POPUP_ERROR render_key_missing")
        return 1
    if not updates:
        print("SECURE_KEY_POPUP_ERROR no_provider_keys")
        return 1

    print("SECURE_KEY_POPUP_SUBMITTED")
    summary = update_render_envs(args.api_base, args.service_id, render_key, updates, do_deploy)
    render_key = ""
    print_summary(summary)
    return 0 if all(bool(item["ok"]) for item in summary["results"]) else 1


def main() -> int:
    args = parse_args()
    if args.yad:
        return run_yad(args)
    token = secrets.token_urlsafe(24)
    server, state = build_server(args, token)
    url = f"http://{args.host}:{args.port}/{token}"
    print("SECURE_KEY_FORM_READY")
    print(url)
    print("Aguardando envio local. Nenhum segredo sera impresso.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        print("SECURE_KEY_FORM_CLOSED")
        summary = state.get("summary")
        if isinstance(summary, dict):
            print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
