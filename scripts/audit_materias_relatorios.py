#!/usr/bin/env python3
"""Audit official NOVO CR subject readiness for aggregate reports.

The script is intentionally read-only. It uses public GET endpoints, optionally
downloads final-report PDFs, checks whether their text is extractable, and writes
a Markdown/JSON snapshot that can be pasted into Doc 09.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


DEFAULT_BASE_URL = "https://ia-educacao-v2.onrender.com"
AGGREGATE_TYPES = {
    "relatorio_desempenho_tarefa",
    "relatorio_desempenho_turma",
    "relatorio_desempenho_materia",
}


def _log(message: str) -> None:
    print(message, flush=True)


def _get_json(base_url: str, path: str, params: dict[str, Any] | None = None, timeout: int = 25) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    url = base_url.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), None
    except Exception as exc:  # noqa: BLE001 - audit must record and continue
        return None, {"url": url, "error": str(exc)}


def _download_document(base_url: str, doc_id: str, cache_dir: pathlib.Path, timeout: int) -> pathlib.Path | None:
    path = cache_dir / f"{doc_id}.pdf"
    if path.exists() and path.stat().st_size > 0:
        return path

    url = base_url.rstrip("/") + f"/api/documentos/{doc_id}/download"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            path.write_bytes(response.read())
        return path
    except Exception:
        return None


def _pdf_text_ok(
    base_url: str,
    document: dict[str, Any],
    cache_dir: pathlib.Path,
    timeout: int,
    read_pdfs: bool,
) -> tuple[str | None, bool, str]:
    doc_id = document.get("id")
    if not doc_id:
        return None, False, "sem id"
    if not read_pdfs:
        return doc_id, True, "PDF assumido legivel (--no-pdf-read)"

    path = _download_document(base_url, doc_id, cache_dir, timeout)
    if not path:
        return doc_id, False, "download falhou"

    try:
        import fitz  # type: ignore

        pdf = fitz.open(str(path))
        try:
            text = "".join(page.get_text() for page in pdf)
        finally:
            pdf.close()
        if text.strip():
            return doc_id, True, f"{len(text.strip())} chars"
        return doc_id, False, "PDF sem texto extraivel"
    except Exception as exc:  # noqa: BLE001 - audit must record and continue
        return doc_id, False, f"PDF ilegivel: {exc}"


def _fetch_inventory(base_url: str, workers: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    materias_data, err = _get_json(base_url, "/api/materias")
    if err:
        errors.append(err)
    turmas_data, err = _get_json(base_url, "/api/turmas")
    if err:
        errors.append(err)

    materias = (materias_data or {}).get("materias", [])
    turmas = (turmas_data or {}).get("turmas", [])
    _log(f"Inventario base: {len(materias)} materias, {len(turmas)} turmas")

    turma_alunos: dict[str, list[dict[str, Any]]] = {}
    turma_atividades: dict[str, list[dict[str, Any]]] = {}

    def fetch_turma(turma: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
        turma_id = turma["id"]
        local_errors: list[dict[str, str]] = []
        alunos_data, turma_err = _get_json(base_url, "/api/alunos", {"turma_id": turma_id})
        if turma_err:
            local_errors.append(turma_err)
        atividades_data, atividade_err = _get_json(base_url, "/api/atividades", {"turma_id": turma_id})
        if atividade_err:
            local_errors.append(atividade_err)
        return (
            turma_id,
            (alunos_data or {}).get("alunos", []),
            (atividades_data or {}).get("atividades", []),
            local_errors,
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_turma, turma) for turma in turmas]
        for index, future in enumerate(as_completed(futures), 1):
            turma_id, alunos, atividades, local_errors = future.result()
            turma_alunos[turma_id] = alunos
            turma_atividades[turma_id] = atividades
            errors.extend(local_errors)
            if index % 8 == 0 or index == len(futures):
                _log(f"Turmas detalhadas: {index}/{len(futures)}")

    atividade_docs: dict[str, list[dict[str, Any]]] = {}
    activities = [(turma_id, atividade) for turma_id, atividades in turma_atividades.items() for atividade in atividades]
    _log(f"Atividades encontradas: {len(activities)}")

    def fetch_docs(item: tuple[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]], dict[str, str] | None]:
        _turma_id, atividade = item
        atividade_id = atividade["id"]
        docs_data, docs_err = _get_json(base_url, "/api/documentos", {"atividade_id": atividade_id}, timeout=30)
        return atividade_id, (docs_data or {}).get("documentos", []), docs_err

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_docs, item) for item in activities]
        for index, future in enumerate(as_completed(futures), 1):
            atividade_id, docs, docs_err = future.result()
            atividade_docs[atividade_id] = docs
            if docs_err:
                errors.append(docs_err)
            if index % 10 == 0 or index == len(futures):
                _log(f"Documentos por atividade: {index}/{len(futures)}")

    return materias, turmas, turma_alunos, turma_atividades, atividade_docs, errors


def _validate_final_pdfs(
    base_url: str,
    turma_alunos: dict[str, list[dict[str, Any]]],
    turma_atividades: dict[str, list[dict[str, Any]]],
    atividade_docs: dict[str, list[dict[str, Any]]],
    cache_dir: pathlib.Path,
    workers: int,
    timeout: int,
    read_pdfs: bool,
) -> dict[str, tuple[bool, str]]:
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for turma_id, atividades in turma_atividades.items():
        enrolled = {aluno["id"] for aluno in turma_alunos.get(turma_id, [])}
        for atividade in atividades:
            atividade_id = atividade["id"]
            by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for document in atividade_docs.get(atividade_id, []):
                if document.get("tipo") == "relatorio_final" and document.get("aluno_id") in enrolled:
                    by_student[document["aluno_id"]].append(document)
            for aluno_id, docs in by_student.items():
                pdfs = [
                    doc
                    for doc in sorted(docs, key=lambda item: item.get("criado_em") or "", reverse=True)
                    if str(doc.get("extensao") or "").lower() == ".pdf" and doc.get("status") != "erro"
                ]
                if pdfs:
                    candidates[(atividade_id, aluno_id)] = pdfs[:2]

    flat_candidates = [document for docs in candidates.values() for document in docs]
    _log(f"PDFs finais candidatos para leitura: {len(flat_candidates)}")

    pdf_read: dict[str, tuple[bool, str]] = {}
    cache_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_pdf_text_ok, base_url, document, cache_dir, timeout, read_pdfs)
            for document in flat_candidates
        ]
        for index, future in enumerate(as_completed(futures), 1):
            doc_id, ok, reason = future.result()
            if doc_id:
                pdf_read[doc_id] = (ok, reason)
            if index % 20 == 0 or index == len(futures):
                _log(f"PDFs testados: {index}/{len(futures)}")

    return pdf_read


def _summarize(
    materias: list[dict[str, Any]],
    turmas: list[dict[str, Any]],
    turma_alunos: dict[str, list[dict[str, Any]]],
    turma_atividades: dict[str, list[dict[str, Any]]],
    atividade_docs: dict[str, list[dict[str, Any]]],
    pdf_read: dict[str, tuple[bool, str]],
) -> dict[str, Any]:
    all_turmas_by_materia: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for turma in turmas:
        all_turmas_by_materia[turma.get("materia_id")].append(turma)

    final_status_by_activity: dict[str, dict[str, Any]] = {}
    activity_summary: dict[str, dict[str, Any]] = {}

    for turma_id, atividades in turma_atividades.items():
        alunos = turma_alunos.get(turma_id, [])
        enrolled_ids = {aluno["id"] for aluno in alunos}
        for atividade in atividades:
            atividade_id = atividade["id"]
            docs = atividade_docs.get(atividade_id, [])
            by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
            type_counts: Counter[str] = Counter()
            aggregate_counts: Counter[str] = Counter()
            aggregate_pdf_counts: Counter[str] = Counter()

            for document in docs:
                doc_type = document.get("tipo")
                type_counts[doc_type] += 1
                if doc_type in AGGREGATE_TYPES:
                    aggregate_counts[doc_type] += 1
                    if str(document.get("extensao") or "").lower() == ".pdf" and document.get("status") != "erro":
                        aggregate_pdf_counts[doc_type] += 1
                if doc_type == "relatorio_final" and document.get("aluno_id"):
                    by_student[document["aluno_id"]].append(document)

            included: list[str] = []
            excluded: list[str] = []
            reasons: dict[str, str] = {}

            for aluno_id in sorted(enrolled_ids):
                student_docs = sorted(
                    by_student.get(aluno_id, []),
                    key=lambda item: item.get("criado_em") or "",
                    reverse=True,
                )
                formats = sorted({str(doc.get("extensao") or "?").lower() for doc in student_docs})
                if not student_docs:
                    excluded.append(aluno_id)
                    reasons[aluno_id] = "sem RELATORIO_FINAL"
                    continue
                pdfs = [
                    doc
                    for doc in student_docs
                    if str(doc.get("extensao") or "").lower() == ".pdf" and doc.get("status") != "erro"
                ]
                if not pdfs:
                    excluded.append(aluno_id)
                    reasons[aluno_id] = "sem RELATORIO_FINAL PDF concluido; formatos=" + ",".join(formats)
                    continue

                ok_doc = None
                failures = []
                for document in pdfs[:2]:
                    ok, reason = pdf_read.get(document.get("id"), (False, "PDF nao testado"))
                    if ok:
                        ok_doc = document
                        reasons[aluno_id] = reason
                        break
                    failures.append(f"{document.get('id')}: {reason}")
                if ok_doc:
                    included.append(aluno_id)
                else:
                    excluded.append(aluno_id)
                    reasons[aluno_id] = "; ".join(failures) or "PDF ilegivel"

            status = (
                "COMPLETO"
                if len(enrolled_ids) >= 2 and len(included) == len(enrolled_ids)
                else ("PARCIAL" if len(enrolled_ids) >= 2 and len(included) >= 2 else "BLOQUEADO_PREREQUISITO")
            )
            final_status_by_activity[atividade_id] = {"included": included, "excluded": excluded, "reasons": reasons}
            activity_summary[atividade_id] = {
                "atividade_id": atividade_id,
                "atividade_nome": atividade.get("nome"),
                "turma_id": turma_id,
                "alunos_total": len(enrolled_ids),
                "rf_legiveis": len(included),
                "rf_excluidos": len(excluded),
                "tarefa_ready": len(enrolled_ids) >= 2 and len(included) >= 2,
                "tarefa_status_previsto": status,
                "doc_type_counts": dict(type_counts),
                "aggregate_counts": dict(aggregate_counts),
                "aggregate_pdf_counts": dict(aggregate_pdf_counts),
            }

    turma_summary: dict[str, dict[str, Any]] = {}
    for turma in turmas:
        turma_id = turma["id"]
        alunos = turma_alunos.get(turma_id, [])
        atividades = turma_atividades.get(turma_id, [])
        narrativas = 0
        ready = 0
        partial = 0
        blocked = 0
        missing_names: list[str] = []
        aggregate_counts: Counter[str] = Counter()
        aggregate_pdf_counts: Counter[str] = Counter()

        for atividade in atividades:
            summary = activity_summary.get(atividade["id"], {})
            narrativas += summary.get("rf_legiveis", 0)
            if summary.get("tarefa_ready"):
                ready += 1
            else:
                blocked += 1
                missing_names.append(atividade.get("nome") or atividade["id"])
            if summary.get("tarefa_status_previsto") == "PARCIAL":
                partial += 1
            aggregate_counts.update(summary.get("aggregate_counts", {}))
            aggregate_pdf_counts.update(summary.get("aggregate_pdf_counts", {}))

        turma_ready = len(alunos) >= 2 and narrativas >= 2
        status = "BLOQUEADO_PREREQUISITO" if not turma_ready else ("PARCIAL" if blocked or partial else "COMPLETO")
        turma_summary[turma_id] = {
            "turma_id": turma_id,
            "turma_nome": turma.get("nome"),
            "materia_id": turma.get("materia_id"),
            "alunos_total": len(alunos),
            "atividades_total": len(atividades),
            "narrativas_legiveis": narrativas,
            "atividades_tarefa_ready": ready,
            "atividades_tarefa_blocked": blocked,
            "desempenho_turma_ready": turma_ready,
            "desempenho_turma_status_previsto": status,
            "aggregate_counts": dict(aggregate_counts),
            "aggregate_pdf_counts": dict(aggregate_pdf_counts),
            "missing_activity_names": missing_names[:8],
        }

    materia_summary: dict[str, dict[str, Any]] = {}
    for materia in materias:
        materia_id = materia["id"]
        materia_turmas = all_turmas_by_materia.get(materia_id, [])
        total_alunos = 0
        total_atividades = 0
        total_narrativas = 0
        tarefa_ready = 0
        tarefa_total = 0
        turma_ready = 0
        turmas_with_result: list[str] = []
        aggregate_counts: Counter[str] = Counter()
        aggregate_pdf_counts: Counter[str] = Counter()
        reasons: list[str] = []

        for turma in materia_turmas:
            summary = turma_summary.get(turma["id"], {})
            total_alunos += summary.get("alunos_total", 0)
            total_atividades += summary.get("atividades_total", 0)
            total_narrativas += summary.get("narrativas_legiveis", 0)
            if summary.get("narrativas_legiveis", 0) > 0:
                turmas_with_result.append(turma["id"])
            if summary.get("desempenho_turma_ready"):
                turma_ready += 1
            aggregate_counts.update(summary.get("aggregate_counts", {}))
            aggregate_pdf_counts.update(summary.get("aggregate_pdf_counts", {}))
            for atividade in turma_atividades.get(turma["id"], []):
                tarefa_total += 1
                if activity_summary.get(atividade["id"], {}).get("tarefa_ready"):
                    tarefa_ready += 1

        if not materia_turmas:
            status = "SEM_TURMA"
            reasons.append("sem turma")
        elif len(materia_turmas) < 2:
            status = "BLOQUEADO_PREREQUISITO"
            reasons.append("menos de 2 turmas")
        elif len(turmas_with_result) < 2:
            status = "BLOQUEADO_PREREQUISITO"
            reasons.append(f"apenas {len(turmas_with_result)} turma(s) com RELATORIO_FINAL legivel")
        elif turma_ready < len(materia_turmas) or tarefa_ready < tarefa_total:
            status = "PARCIAL"
            if turma_ready < len(materia_turmas):
                reasons.append(f"{len(materia_turmas) - turma_ready} turma(s) sem minimo para desempenho_turma")
            if tarefa_ready < tarefa_total:
                reasons.append(f"{tarefa_total - tarefa_ready} atividade(s) sem minimo para desempenho_tarefa")
        else:
            status = "COMPLETO"
            reasons.append("dados suficientes para executar todos os niveis previstos")

        materia_summary[materia_id] = {
            "materia_id": materia_id,
            "materia_nome": materia.get("nome"),
            "nivel": materia.get("nivel"),
            "turmas_total": len(materia_turmas),
            "alunos_total_soma_turmas": total_alunos,
            "atividades_total": total_atividades,
            "tarefa_ready": tarefa_ready,
            "tarefa_total": tarefa_total,
            "turma_ready": turma_ready,
            "turma_total": len(materia_turmas),
            "materia_ready": len(materia_turmas) >= 2 and len(turmas_with_result) >= 2 and total_narrativas >= 2,
            "materia_status_previsto": status,
            "turmas_com_resultado": len(turmas_with_result),
            "narrativas_legiveis": total_narrativas,
            "aggregate_counts": dict(aggregate_counts),
            "aggregate_pdf_counts": dict(aggregate_pdf_counts),
            "bloqueio_principal": "; ".join(reasons),
        }

    return {
        "materias": materia_summary,
        "turmas": turma_summary,
        "atividades": activity_summary,
        "atividade_final_status": final_status_by_activity,
    }


def _status_label(status: str) -> str:
    return {
        "COMPLETO": "completo provavel",
        "PARCIAL": "parcial provavel",
        "BLOQUEADO_PREREQUISITO": "bloqueado",
        "SEM_TURMA": "sem turma",
    }.get(status, status)


def _render_markdown(base_url: str, audit: dict[str, Any], errors: list[dict[str, str]]) -> str:
    materias = audit["materias"]
    turmas = audit["turmas"]
    status_counts = Counter(item["materia_status_previsto"] for item in materias.values())
    lines: list[str] = [
        "# Auditoria de materias para relatorios agregados",
        "",
        f"Gerado em `{_dt.datetime.now().isoformat(timespec='seconds')}` contra `{base_url}`.",
        "",
        "Regra P0: se uma barreira aparecer, ela deve ser respondida, registrada no log e o loop deve continuar com o proximo alvo possivel. Sem fallback silencioso.",
        "",
        "Criterio: `desempenho_tarefa` precisa de pelo menos 2 alunos matriculados e 2 `RELATORIO_FINAL` legiveis na atividade; `desempenho_turma` precisa de pelo menos 2 alunos e 2 narrativas legiveis na turma; `desempenho_materia` precisa de pelo menos 2 turmas com narrativa legivel.",
        "",
        f"Resumo: {status_counts.get('BLOQUEADO_PREREQUISITO', 0)} materias bloqueadas, {status_counts.get('SEM_TURMA', 0)} sem turma, {status_counts.get('PARCIAL', 0)} parcial, {status_counts.get('COMPLETO', 0)} completa.",
        "",
        "## Resumo por materia",
        "",
        "| Materia | Turmas | Alunos | Atividades | Tarefa pronta | Turma pronta | Status materia | Narrativas legiveis | Agregados PDF ja gerados | Bloqueio principal |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|---|",
    ]

    for _mid, summary in sorted(materias.items(), key=lambda item: (item[1]["materia_nome"] or "").lower()):
        aggregate_pdf = summary["aggregate_pdf_counts"]
        aggregate_text = (
            f"tarefa {aggregate_pdf.get('relatorio_desempenho_tarefa', 0)}, "
            f"turma {aggregate_pdf.get('relatorio_desempenho_turma', 0)}, "
            f"materia {aggregate_pdf.get('relatorio_desempenho_materia', 0)}"
        )
        lines.append(
            "| {nome} `{mid}` | {turmas} | {alunos} | {atividades} | {tarefa_ready}/{tarefa_total} | "
            "{turma_ready}/{turma_total} | {status} | {narrativas} | {aggregate} | {bloqueio} |".format(
                nome=summary["materia_nome"],
                mid=summary["materia_id"][:8],
                turmas=summary["turmas_total"],
                alunos=summary["alunos_total_soma_turmas"],
                atividades=summary["atividades_total"],
                tarefa_ready=summary["tarefa_ready"],
                tarefa_total=summary["tarefa_total"],
                turma_ready=summary["turma_ready"],
                turma_total=summary["turma_total"],
                status=_status_label(summary["materia_status_previsto"]),
                narrativas=summary["narrativas_legiveis"],
                aggregate=aggregate_text,
                bloqueio=summary["bloqueio_principal"],
            )
        )

    lines.extend(
        [
            "",
            "## Detalhe por turma",
            "",
            "| Materia | Turma | Alunos | Atividades | Atividades prontas p/ tarefa | Narrativas legiveis | Desempenho turma | Bloqueio/observacao |",
            "|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for _mid, summary in sorted(materias.items(), key=lambda item: (item[1]["materia_nome"] or "").lower()):
        materia_turmas = [
            turma for turma in turmas.values()
            if turma["materia_id"] == summary["materia_id"]
        ]
        for turma in sorted(materia_turmas, key=lambda item: item["turma_nome"] or ""):
            obs = "ok para rodar turma" if turma["desempenho_turma_ready"] else "faltam narrativas/alunos suficientes"
            if turma["missing_activity_names"]:
                obs += "; atividades bloqueadas: " + ", ".join(turma["missing_activity_names"])
            lines.append(
                "| {materia} | {turma} `{turma_id}` | {alunos} | {atividades} | {ready}/{total} | {narrativas} | {status} | {obs} |".format(
                    materia=summary["materia_nome"],
                    turma=turma["turma_nome"],
                    turma_id=turma["turma_id"][:8],
                    alunos=turma["alunos_total"],
                    atividades=turma["atividades_total"],
                    ready=turma["atividades_tarefa_ready"],
                    total=turma["atividades_total"],
                    narrativas=turma["narrativas_legiveis"],
                    status=_status_label(turma["desempenho_turma_status_previsto"]),
                    obs=obs,
                )
            )

    if errors:
        lines.extend(["", "## Barreiras tecnicas da auditoria", "", "| URL | Erro |", "|---|---|"])
        for error in errors[:100]:
            lines.append(f"| `{error['url']}` | {str(error['error']).replace('|', '/')} |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--out-md", default="/tmp/novocr_audit_materias_relatorios.md")
    parser.add_argument("--out-json", default="/tmp/novocr_audit_materias_relatorios.json")
    parser.add_argument("--cache-dir", default="/tmp/novocr_pdf_cache")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--download-timeout", type=int, default=25)
    parser.add_argument("--no-pdf-read", action="store_true", help="Do not download/read PDFs; count candidate final PDFs as legible.")
    args = parser.parse_args()

    if not args.no_pdf_read:
        try:
            import fitz  # noqa: F401
        except ModuleNotFoundError:
            print(
                "ERRO: PyMuPDF/fitz nao esta instalado neste Python. "
                "Rode com a venv do projeto ou use --no-pdf-read para uma auditoria "
                "menos rigorosa que nao valida texto extraivel dos PDFs.",
                file=sys.stderr,
            )
            return 2

    materias, turmas, turma_alunos, turma_atividades, atividade_docs, errors = _fetch_inventory(args.base_url, args.workers)
    pdf_read = _validate_final_pdfs(
        args.base_url,
        turma_alunos,
        turma_atividades,
        atividade_docs,
        pathlib.Path(args.cache_dir),
        max(1, min(args.workers, 8)),
        args.download_timeout,
        not args.no_pdf_read,
    )
    audit = _summarize(materias, turmas, turma_alunos, turma_atividades, atividade_docs, pdf_read)
    payload = {
        "generated_at": _dt.datetime.now().isoformat(),
        "base_url": args.base_url,
        "fetch_errors": errors,
        **audit,
    }

    pathlib.Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pathlib.Path(args.out_md).write_text(_render_markdown(args.base_url, audit, errors), encoding="utf-8")

    status_counts = Counter(summary["materia_status_previsto"] for summary in audit["materias"].values())
    print(
        json.dumps(
            {
                "materias": len(materias),
                "turmas": len(turmas),
                "atividades": sum(len(value) for value in turma_atividades.values()),
                "pdfs_testados": len(pdf_read),
                "fetch_errors": len(errors),
                "status_counts": dict(status_counts),
                "outputs": [args.out_json, args.out_md],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
