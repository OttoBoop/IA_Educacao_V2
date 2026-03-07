#!/usr/bin/env python3
"""
Generate PDFs from existing desempenho JSON files.

Reads the 'resposta_raw' markdown field from each desempenho JSON
and converts it to a PDF using markdown2 + weasyprint (or reportlab fallback).

Usage: python scripts/generate_desempenho_pdfs.py

Requirements (install if needed):
  pip install markdown2 weasyprint
  OR (fallback): pip install reportlab
"""

import json
import sys
from pathlib import Path

DESEMPENHO_DIR = Path(__file__).parent.parent / "test_downloads" / "desempenho"

# ─────────────────────────────────────────────────────────────────────────────
# Markdown → HTML → PDF via weasyprint
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
@page { margin: 2cm; size: A4; }
body { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #222; }
h1 { font-size: 20pt; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 6pt; margin-top: 24pt; }
h2 { font-size: 15pt; color: #1a3a5c; margin-top: 18pt; }
h3 { font-size: 12pt; color: #2c5f8a; margin-top: 12pt; }
p { margin: 6pt 0; }
strong { color: #1a3a5c; }
ul, ol { margin: 6pt 0 6pt 20pt; }
li { margin: 3pt 0; }
hr { border: none; border-top: 1px solid #ccc; margin: 16pt 0; }
blockquote { border-left: 3px solid #1a3a5c; margin-left: 0; padding-left: 12pt; color: #555; }
"""


def generate_pdf_weasyprint(markdown_text: str, output_path: Path, title: str) -> bool:
    try:
        import markdown2
        from weasyprint import HTML, CSS as WeasyCss
    except ImportError:
        return False

    html_body = markdown2.markdown(markdown_text, extras=["fenced-code-blocks", "tables"])
    full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body>{html_body}</body></html>"""

    HTML(string=full_html).write_pdf(
        str(output_path),
        stylesheets=[WeasyCss(string=CSS)]
    )
    return True


def generate_pdf_reportlab(markdown_text: str, output_path: Path, title: str) -> bool:
    """Fallback PDF generator using reportlab — plain text, no markdown rendering."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
    except ImportError:
        print("  ❌ Neither weasyprint nor reportlab is installed.")
        print("     Run: pip install weasyprint   OR   pip install reportlab")
        return False

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2", parent=styles["Heading1"],
        fontSize=18, textColor=colors.HexColor("#1a3a5c"), spaceAfter=12
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#1a3a5c"), spaceAfter=8
    )
    h3_style = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=11, textColor=colors.HexColor("#2c5f8a"), spaceAfter=6
    )
    body_style = ParagraphStyle(
        "Body2", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=4
    )

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3*cm))

    for line in markdown_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.2*cm))
        elif stripped.startswith("### "):
            story.append(Paragraph(stripped[4:].replace("**", ""), h3_style))
        elif stripped.startswith("## "):
            story.append(Paragraph(stripped[3:].replace("**", ""), h2_style))
        elif stripped.startswith("# "):
            story.append(Paragraph(stripped[2:].replace("**", ""), h2_style))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 0.3*cm))
        else:
            # Clean basic markdown for reportlab
            text = stripped
            text = text.replace("**", "<b>", 1).replace("**", "</b>", 1)
            text = text.replace("*", "<i>", 1).replace("*", "</i>", 1)
            if text.startswith("- ") or text.startswith("* "):
                text = "• " + text[2:]
            story.append(Paragraph(text, body_style))

    doc.build(story)
    return True


def process_json_file(json_path: Path) -> bool:
    """Read a desempenho JSON, extract resposta_raw, generate PDF."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    markdown_text = data.get("resposta_raw") or data.get("conteudo") or data.get("narrativa")

    if not markdown_text:
        print(f"  ⚠️  No narrative field found in {json_path.name}")
        print(f"     Keys: {list(data.keys())}")
        return False

    # Title from filename: type_date → "Relatório Desempenho Tarefa — 28/02/2026"
    stem = json_path.stem  # e.g., relatorio_desempenho_tarefa_20260302_001418
    parts = stem.replace("relatorio_", "").split("_")
    tipo = " ".join(p.capitalize() for p in parts[:2])  # "Desempenho Tarefa"
    date_str = parts[2] if len(parts) > 2 else ""
    if len(date_str) == 8:
        date_str = f"{date_str[6:]}/{date_str[4:6]}/{date_str[:4]}"
    title = f"Relatório — {tipo} ({date_str})"

    pdf_path = json_path.with_suffix(".pdf")

    # Try weasyprint first, then reportlab
    if generate_pdf_weasyprint(markdown_text, pdf_path, title):
        size_kb = pdf_path.stat().st_size // 1024
        print(f"  ✅ PDF (weasyprint): {pdf_path.name} ({size_kb} KB)")
        return True
    elif generate_pdf_reportlab(markdown_text, pdf_path, title):
        size_kb = pdf_path.stat().st_size // 1024
        print(f"  ✅ PDF (reportlab):  {pdf_path.name} ({size_kb} KB)")
        return True
    else:
        return False


def main():
    print("=" * 60)
    print("📄 Desempenho PDF Generator")
    print(f"   Source: {DESEMPENHO_DIR}")
    print("=" * 60)

    if not DESEMPENHO_DIR.exists():
        print(f"\n❌ Directory not found: {DESEMPENHO_DIR}")
        print("   Run download_desempenho.py first.")
        sys.exit(1)

    # Find all desempenho JSON files (not the _conteudo.json copies)
    json_files = [
        f for f in DESEMPENHO_DIR.rglob("*.json")
        if "conteudo" not in f.name and "summary" not in f.name
    ]

    if not json_files:
        print("❌ No JSON files found.")
        sys.exit(1)

    print(f"\nFound {len(json_files)} JSON files to convert:\n")
    success = 0
    for jf in sorted(json_files):
        rel = jf.relative_to(DESEMPENHO_DIR)
        print(f"\n[{rel.parent}] {jf.name}")
        if process_json_file(jf):
            success += 1

    print(f"\n{'='*60}")
    print(f"✅ Done: {success}/{len(json_files)} PDFs generated")
    print(f"   Output: {DESEMPENHO_DIR}")

    # List generated PDFs
    pdfs = list(DESEMPENHO_DIR.rglob("*.pdf"))
    if pdfs:
        print(f"\n📋 Generated PDFs ({len(pdfs)}):")
        for pdf in sorted(pdfs):
            size_kb = pdf.stat().st_size // 1024
            print(f"   {pdf.relative_to(DESEMPENHO_DIR)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
