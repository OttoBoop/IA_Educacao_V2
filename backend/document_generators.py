"""
PROVA AI - Document Generators v1.0

Módulo para geração de documentos em múltiplos formatos:
- PDF (via reportlab)
- CSV (via csv module)
- DOCX (via python-docx)

Cada função recebe dados estruturados (Dict, VisaoAluno, etc.)
e retorna bytes ou string pronto para salvar.
"""

import csv
import io
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """Formatos de saída suportados"""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    DOCX = "docx"
    MD = "md"


# Mapeamento: tipo de documento do pipeline → formatos de saída
# Configura quais formatos gerar para cada tipo de resultado
STAGE_OUTPUT_FORMATS: Dict[str, List[OutputFormat]] = {
    "extracao_questoes": [OutputFormat.JSON],
    "extracao_respostas": [OutputFormat.JSON],
    "correcao": [OutputFormat.JSON, OutputFormat.PDF],
    "analise_habilidades": [OutputFormat.JSON, OutputFormat.PDF, OutputFormat.CSV],
    "relatorio_final": [OutputFormat.JSON, OutputFormat.PDF],
    "ranking": [OutputFormat.JSON, OutputFormat.CSV],
}


def get_output_formats(stage_type: str) -> List[OutputFormat]:
    """Retorna os formatos configurados para um tipo de documento"""
    return STAGE_OUTPUT_FORMATS.get(stage_type, [OutputFormat.JSON])


# ============================================================
# PDF GENERATION
# ============================================================

def generate_pdf(data: Dict[str, Any], title: str = "Documento", 
                 doc_type: str = "generic") -> bytes:
    """
    Gera PDF a partir de dados estruturados.
    
    Args:
        data: Dicionário com dados do documento
        title: Título do documento
        doc_type: Tipo de documento (correcao, relatorio_final, analise_habilidades)
    
    Returns:
        bytes: Conteúdo do PDF
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        # Fallback: retorna texto se reportlab não disponível
        return _generate_text_fallback(data, title).encode('utf-8')
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#34495e')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    story = []
    
    # Título
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Geração baseada no tipo
    if doc_type == "correcao":
        story.extend(_build_correcao_pdf(data, styles, heading_style, body_style))
    elif doc_type == "relatorio_final":
        story.extend(_build_relatorio_pdf(data, styles, heading_style, body_style))
    elif doc_type == "analise_habilidades":
        story.extend(_build_analise_pdf(data, styles, heading_style, body_style))
    else:
        story.extend(_build_generic_pdf(data, styles, heading_style, body_style))
    
    # Footer com timestamp
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], 
                                   fontSize=8, textColor=colors.gray)
    story.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _build_correcao_pdf(data: Dict, styles, heading_style, body_style) -> List:
    """Constrói conteúdo PDF para correção"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    
    story = []
    
    # Resumo
    if "nota" in data:
        nota = data.get("nota", 0)
        nota_max = data.get("nota_maxima", 10)
        percentual = (nota / nota_max * 100) if nota_max > 0 else 0
        
        story.append(Paragraph("📊 Resumo", heading_style))
        summary_data = [
            ["Nota", f"{nota:.1f} / {nota_max:.1f}"],
            ["Percentual", f"{percentual:.1f}%"],
            ["Status", data.get("status", "N/A").upper()]
        ]
        table = Table(summary_data, colWidths=[150, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Correções por questão
    if "correcoes" in data:
        story.append(Paragraph("📝 Questões", heading_style))
        for i, c in enumerate(data["correcoes"], 1):
            q_num = c.get("questao_numero", i)
            story.append(Paragraph(f"<b>Questão {q_num}</b>", body_style))
            story.append(Paragraph(f"Nota: {c.get('nota', 0):.1f} / {c.get('nota_maxima', 1):.1f}", body_style))
            if c.get("feedback"):
                story.append(Paragraph(f"<i>{c.get('feedback')}</i>", body_style))
            story.append(Spacer(1, 10))
    
    # Feedback geral
    if data.get("feedback"):
        story.append(Paragraph("💬 Feedback", heading_style))
        story.append(Paragraph(data["feedback"], body_style))
    
    return story


def _build_relatorio_pdf(data: Dict, styles, heading_style, body_style) -> List:
    """Constrói conteúdo PDF para relatório final"""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    
    story = []
    
    # Info do aluno
    if data.get("aluno_nome"):
        story.append(Paragraph(f"<b>Aluno:</b> {data.get('aluno_nome')}", body_style))
    if data.get("atividade_nome"):
        story.append(Paragraph(f"<b>Atividade:</b> {data.get('atividade_nome')}", body_style))
    story.append(Spacer(1, 15))
    
    # Nota final
    story.append(Paragraph("📊 Resultado Final", heading_style))
    nota = data.get("nota_final", data.get("nota", 0))
    nota_max = data.get("nota_maxima", 10)
    percentual = data.get("percentual", (nota / nota_max * 100) if nota_max > 0 else 0)
    
    summary_data = [
        ["Nota Final", f"{nota:.1f} / {nota_max:.1f}"],
        ["Aproveitamento", f"{percentual:.1f}%"],
    ]
    
    if data.get("total_questoes"):
        summary_data.append(["Total de Questões", str(data["total_questoes"])])
        summary_data.append(["Corretas", str(data.get("questoes_corretas", 0))])
        summary_data.append(["Parciais", str(data.get("questoes_parciais", 0))])
        summary_data.append(["Incorretas", str(data.get("questoes_incorretas", 0))])
    
    table = Table(summary_data, colWidths=[150, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Feedback geral
    if data.get("feedback_geral"):
        story.append(Paragraph("💬 Comentários", heading_style))
        story.append(Paragraph(data["feedback_geral"], body_style))
    
    # Recomendações
    if data.get("recomendacoes"):
        story.append(Paragraph("📌 Recomendações", heading_style))
        for rec in data["recomendacoes"]:
            story.append(Paragraph(f"• {rec}", body_style))
    
    return story


def _build_analise_pdf(data: Dict, styles, heading_style, body_style) -> List:
    """Constrói conteúdo PDF para análise de habilidades"""
    from reportlab.platypus import Paragraph, Spacer
    
    story = []
    
    # Habilidades demonstradas
    habilidades = data.get("habilidades", {})
    
    if isinstance(habilidades, dict):
        dominadas = habilidades.get("dominadas", [])
        em_dev = habilidades.get("em_desenvolvimento", [])
        nao_dem = habilidades.get("nao_demonstradas", [])
    else:
        dominadas = data.get("habilidades_demonstradas", [])
        em_dev = []
        nao_dem = data.get("habilidades_faltantes", [])
    
    if dominadas:
        story.append(Paragraph("✅ Habilidades Demonstradas", heading_style))
        for h in dominadas:
            if isinstance(h, dict):
                story.append(Paragraph(f"• {h.get('nome', h)}", body_style))
            else:
                story.append(Paragraph(f"• {h}", body_style))
        story.append(Spacer(1, 10))
    
    if em_dev:
        story.append(Paragraph("🔄 Em Desenvolvimento", heading_style))
        for h in em_dev:
            if isinstance(h, dict):
                story.append(Paragraph(f"• {h.get('nome', h)}", body_style))
            else:
                story.append(Paragraph(f"• {h}", body_style))
        story.append(Spacer(1, 10))
    
    if nao_dem:
        story.append(Paragraph("⚠️ Precisam de Atenção", heading_style))
        for h in nao_dem:
            if isinstance(h, dict):
                story.append(Paragraph(f"• {h.get('nome', h)}", body_style))
            else:
                story.append(Paragraph(f"• {h}", body_style))
    
    return story


def _build_generic_pdf(data: Dict, styles, heading_style, body_style) -> List:
    """Constrói conteúdo PDF genérico para qualquer estrutura"""
    from reportlab.platypus import Paragraph, Spacer
    
    story = []
    
    for key, value in data.items():
        if key.startswith("_"):
            continue
            
        label = key.replace("_", " ").title()
        
        if isinstance(value, (list, dict)):
            story.append(Paragraph(f"<b>{label}:</b>", body_style))
            story.append(Paragraph(f"<pre>{json.dumps(value, indent=2, ensure_ascii=False)[:500]}</pre>", body_style))
        else:
            story.append(Paragraph(f"<b>{label}:</b> {value}", body_style))
        
        story.append(Spacer(1, 5))
    
    return story


def _generate_text_fallback(data: Dict, title: str) -> str:
    """Fallback para texto quando reportlab não está disponível"""
    lines = [f"{'='*50}", f" {title}", f"{'='*50}", ""]
    
    for key, value in data.items():
        if key.startswith("_"):
            continue
        label = key.replace("_", " ").title()
        if isinstance(value, (list, dict)):
            lines.append(f"{label}:")
            lines.append(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            lines.append(f"{label}: {value}")
    
    lines.extend(["", f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
    return "\n".join(lines)


# ============================================================
# CSV GENERATION
# ============================================================

def generate_csv(data: Union[List[Dict], Dict], 
                 headers: Optional[List[str]] = None,
                 doc_type: str = "generic") -> str:
    """
    Gera CSV a partir de dados estruturados.
    
    Args:
        data: Lista de dicionários ou dicionário único
        headers: Cabeçalhos opcionais (inferidos automaticamente)
        doc_type: Tipo de documento para formatação específica
    
    Returns:
        str: Conteúdo CSV
    """
    output = io.StringIO()
    
    # Normalizar para lista
    if isinstance(data, dict):
        # Caso especial: ranking ou lista dentro do dict
        if "ranking" in data:
            rows = data["ranking"]
        elif "correcoes" in data:
            rows = data["correcoes"]
        elif "habilidades" in data:
            rows = _flatten_habilidades(data["habilidades"])
        else:
            rows = [data]
    else:
        rows = data
    
    if not rows:
        return ""
    
    # Inferir headers
    if not headers:
        if rows and isinstance(rows[0], dict):
            headers = list(rows[0].keys())
        else:
            headers = ["value"]
            rows = [{"value": r} for r in rows]
    
    # Escrever CSV
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    
    for row in rows:
        if isinstance(row, dict):
            # Flatten nested values
            flat_row = {}
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    flat_row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat_row[k] = v
            writer.writerow(flat_row)
        else:
            writer.writerow({"value": row})
    
    return output.getvalue()


def _flatten_habilidades(habilidades: Dict) -> List[Dict]:
    """Transforma habilidades em lista para CSV"""
    rows = []
    
    if isinstance(habilidades, dict):
        for status, lista in habilidades.items():
            if isinstance(lista, list):
                for h in lista:
                    if isinstance(h, dict):
                        rows.append({"status": status, **h})
                    else:
                        rows.append({"status": status, "habilidade": h})
    
    return rows


# ============================================================
# MARKDOWN GENERATION
# ============================================================

def generate_markdown(data: Dict[str, Any], title: str = "Documento",
                      doc_type: str = "generic") -> str:
    """
    Gera Markdown a partir de dados estruturados.
    
    Args:
        data: Dicionário com dados
        title: Título do documento
        doc_type: Tipo de documento
    
    Returns:
        str: Conteúdo Markdown
    """
    lines = [f"# {title}", ""]
    
    if doc_type == "correcao":
        lines.extend(_build_correcao_md(data))
    elif doc_type == "relatorio_final":
        lines.extend(_build_relatorio_md(data))
    elif doc_type == "analise_habilidades":
        lines.extend(_build_analise_md(data))
    else:
        lines.extend(_build_generic_md(data))
    
    lines.extend(["", "---", f"*Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"])
    return "\n".join(lines)


def _build_correcao_md(data: Dict) -> List[str]:
    """Constrói Markdown para correção"""
    lines = []
    
    if "nota" in data:
        nota = data.get("nota", 0)
        nota_max = data.get("nota_maxima", 10)
        lines.extend([
            "## 📊 Resumo",
            "",
            f"| Métrica | Valor |",
            f"|---------|-------|",
            f"| Nota | {nota:.1f} / {nota_max:.1f} |",
            f"| Status | {data.get('status', 'N/A').upper()} |",
            ""
        ])
    
    if "correcoes" in data:
        lines.extend(["## 📝 Questões", ""])
        for i, c in enumerate(data["correcoes"], 1):
            q_num = c.get("questao_numero", i)
            lines.append(f"### Questão {q_num}")
            lines.append(f"**Nota:** {c.get('nota', 0):.1f} / {c.get('nota_maxima', 1):.1f}")
            if c.get("feedback"):
                lines.append(f"> {c.get('feedback')}")
            lines.append("")
    
    if data.get("feedback"):
        lines.extend(["## 💬 Feedback", "", data["feedback"], ""])
    
    return lines


def _build_relatorio_md(data: Dict) -> List[str]:
    """Constrói Markdown para relatório final"""
    lines = []
    
    if data.get("aluno_nome"):
        lines.append(f"**Aluno:** {data.get('aluno_nome')}")
    if data.get("atividade_nome"):
        lines.append(f"**Atividade:** {data.get('atividade_nome')}")
    lines.append("")
    
    nota = data.get("nota_final", data.get("nota", 0))
    nota_max = data.get("nota_maxima", 10)
    percentual = data.get("percentual", (nota / nota_max * 100) if nota_max > 0 else 0)
    
    lines.extend([
        "## 📊 Resultado Final",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Nota Final | {nota:.1f} / {nota_max:.1f} |",
        f"| Aproveitamento | {percentual:.1f}% |",
    ])
    
    if data.get("total_questoes"):
        lines.append(f"| Total de Questões | {data['total_questoes']} |")
        lines.append(f"| Corretas | {data.get('questoes_corretas', 0)} |")
    
    lines.append("")
    
    if data.get("recomendacoes"):
        lines.extend(["## 📌 Recomendações", ""])
        for rec in data["recomendacoes"]:
            lines.append(f"- {rec}")
        lines.append("")
    
    return lines


def _build_analise_md(data: Dict) -> List[str]:
    """Constrói Markdown para análise de habilidades"""
    lines = []
    
    habilidades = data.get("habilidades", {})
    
    if isinstance(habilidades, dict):
        dominadas = habilidades.get("dominadas", [])
        em_dev = habilidades.get("em_desenvolvimento", [])
        nao_dem = habilidades.get("nao_demonstradas", [])
    else:
        dominadas = data.get("habilidades_demonstradas", [])
        em_dev = []
        nao_dem = data.get("habilidades_faltantes", [])
    
    if dominadas:
        lines.extend(["## ✅ Habilidades Demonstradas", ""])
        for h in dominadas:
            nome = h.get("nome", h) if isinstance(h, dict) else h
            lines.append(f"- {nome}")
        lines.append("")
    
    if em_dev:
        lines.extend(["## 🔄 Em Desenvolvimento", ""])
        for h in em_dev:
            nome = h.get("nome", h) if isinstance(h, dict) else h
            lines.append(f"- {nome}")
        lines.append("")
    
    if nao_dem:
        lines.extend(["## ⚠️ Precisam de Atenção", ""])
        for h in nao_dem:
            nome = h.get("nome", h) if isinstance(h, dict) else h
            lines.append(f"- {nome}")
        lines.append("")
    
    return lines


def _build_generic_md(data: Dict) -> List[str]:
    """Constrói Markdown genérico"""
    lines = []
    
    for key, value in data.items():
        if key.startswith("_"):
            continue
        
        label = key.replace("_", " ").title()
        
        if isinstance(value, list):
            lines.extend([f"## {label}", ""])
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
                else:
                    lines.append(f"- {item}")
            lines.append("")
        elif isinstance(value, dict):
            lines.extend([f"## {label}", "", "```json", json.dumps(value, indent=2, ensure_ascii=False), "```", ""])
        else:
            lines.append(f"**{label}:** {value}")
    
    return lines


# ============================================================
# DOCX GENERATION (Basic)
# ============================================================

def generate_docx(data: Dict[str, Any], title: str = "Documento",
                  doc_type: str = "generic") -> bytes:
    """
    Gera DOCX a partir de dados estruturados.
    
    Args:
        data: Dicionário com dados
        title: Título do documento
        doc_type: Tipo de documento
    
    Returns:
        bytes: Conteúdo do DOCX
    """
    try:
        from docx import Document
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        # Fallback: retornar como texto
        return generate_markdown(data, title, doc_type).encode('utf-8')
    
    doc = Document()
    
    # Título
    title_para = doc.add_heading(title, 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Gerar conteúdo baseado no Markdown (simples)
    md_content = generate_markdown(data, "", doc_type)
    
    for line in md_content.split('\n'):
        if line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line.startswith('**') and ':**' in line:
            doc.add_paragraph(line.replace('**', ''))
        elif line.startswith('|'):
            # Skip table rows (simple)
            continue
        elif line.strip() and not line.startswith('#') and not line.startswith('---'):
            doc.add_paragraph(line)
    
    # Footer
    doc.add_paragraph("")
    footer = doc.add_paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    footer.runs[0].font.size = Pt(8)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


# ============================================================
# MAIN GENERATOR INTERFACE
# ============================================================

def generate_document(data: Dict[str, Any], 
                      format: OutputFormat,
                      title: str = "Documento",
                      doc_type: str = "generic") -> Union[bytes, str]:
    """
    Interface principal para gerar documento em qualquer formato.
    
    Args:
        data: Dados do documento
        format: Formato desejado (OutputFormat enum)
        title: Título do documento
        doc_type: Tipo de documento (correcao, relatorio_final, etc.)
    
    Returns:
        bytes ou str dependendo do formato
    """
    if format == OutputFormat.PDF:
        return generate_pdf(data, title, doc_type)
    elif format == OutputFormat.CSV:
        return generate_csv(data, doc_type=doc_type)
    elif format == OutputFormat.DOCX:
        return generate_docx(data, title, doc_type)
    elif format == OutputFormat.MD:
        return generate_markdown(data, title, doc_type)
    elif format == OutputFormat.JSON:
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Formato não suportado: {format}")


def get_file_extension(format: OutputFormat) -> str:
    """Retorna a extensão de arquivo para um formato"""
    extensions = {
        OutputFormat.PDF: ".pdf",
        OutputFormat.CSV: ".csv",
        OutputFormat.DOCX: ".docx",
        OutputFormat.MD: ".md",
        OutputFormat.JSON: ".json",
    }
    return extensions.get(format, ".txt")
