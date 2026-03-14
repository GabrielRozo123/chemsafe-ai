from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from core.models import ReportBundle
from data.prompts import REPORT_WRITER_SYSTEM
from services.ai_client import AIClient


def _safe_rows(data: Any) -> List[List[str]]:
    if isinstance(data, list) and data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [headers]
        for row in data:
            rows.append([str(row.get(h, '')) for h in headers])
        return rows
    if isinstance(data, list) and data and isinstance(data[0], (list, tuple)):
        return [[str(c) for c in row] for row in data]
    return [['Campo', 'Valor'], ['payload', json.dumps(data, ensure_ascii=False, indent=2)]]


def _markdown_to_html(md: str) -> str:
    try:
        import markdown2  # type: ignore
        return markdown2.markdown(md, extras=['tables', 'fenced-code-blocks'])
    except Exception:
        paragraphs = []
        for block in md.split('\n\n'):
            text = block.strip()
            if not text:
                continue
            if text.startswith('## '):
                paragraphs.append(f"<h2>{text[3:]}</h2>")
            elif text.startswith('# '):
                paragraphs.append(f"<h1>{text[2:]}</h1>")
            else:
                paragraphs.append(f"<p>{text}</p>")
        return ''.join(paragraphs)


class ReportService:
    def __init__(self, ai: AIClient) -> None:
        self.ai = ai

    def build_narrative(self, payload: Dict[str, Any]) -> str:
        if not self.ai.enabled:
            return (
                '## Resumo executivo\n\n'
                'Relatório gerado em modo offline. Revise manualmente as premissas, os dados de entrada, '
                'as salvaguardas independentes e os limites de aplicação dos modelos simplificados.\n\n'
                '## Observações\n\n'
                '- Resultados de consequência são de triagem.\n'
                '- LOPA/SIL deve ser revisada por profissional habilitado.\n'
                '- Modelos simplificados não substituem PHAST, SAFETI ou ALOHA.\n'
            )
        prompt = (
            'Com base no payload JSON abaixo, redija um relatório técnico preliminar com as seções: '
            'Resumo executivo, Descrição do caso, Principais perigos, Salvaguardas, Resultado de screening, '
            'Limitações e Próximos passos.\n\n'
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        return self.ai.ask(prompt, system_prompt=REPORT_WRITER_SYSTEM, reasoning=False).answer

    def render_html(self, case_name: str, payload: Dict[str, Any], narrative_md: str) -> bytes:
        json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
        narrative_html = _markdown_to_html(narrative_md)
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
            env = Environment(
                loader=FileSystemLoader(str(Path(__file__).resolve().parent.parent / 'templates')),
                autoescape=select_autoescape(['html', 'xml']),
            )
            template = env.get_template('report.html')
            html = template.render(
                case_name=case_name,
                generated_at=datetime.now().strftime('%d/%m/%Y %H:%M'),
                narrative_html=narrative_html,
                payload=payload,
                json_payload=json_payload,
            )
        except Exception:
            html = f"""<!DOCTYPE html><html><body><h1>{case_name}</h1><div>{narrative_html}</div><pre>{json_payload}</pre></body></html>"""
        return html.encode('utf-8')

    def render_pdf(self, case_name: str, payload: Dict[str, Any], narrative_md: str) -> bytes:
        try:
            from reportlab.lib import colors  # type: ignore
            from reportlab.lib.pagesizes import A4  # type: ignore
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore
            from reportlab.lib.units import cm  # type: ignore
            from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore
        except Exception:
            return (f'PDF generation unavailable.\n\nCase: {case_name}\n\n{narrative_md}\n\n{json.dumps(payload, ensure_ascii=False, indent=2)}').encode('utf-8')

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CaseTitle', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0f2747')))
        styles.add(ParagraphStyle(name='BodySmall', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#334155')))
        styles.add(ParagraphStyle(name='SubTitleBlue', fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=colors.HexColor('#1d4ed8')))
        story = []
        story.append(Paragraph('ChemSafe Pro AI — Technical Risk Screening Report', styles['CaseTitle']))
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph(f'<b>Case:</b> {case_name}', styles['BodySmall']))
        story.append(Paragraph(f'<b>Generated:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}', styles['BodySmall']))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph('Executive narrative', styles['SubTitleBlue']))
        for line in narrative_md.splitlines():
            if line.strip():
                story.append(Paragraph(line.replace('#', '').strip(), styles['BodySmall']))
                story.append(Spacer(1, 0.1 * cm))
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph('Structured results', styles['SubTitleBlue']))
        for section_name, section_payload in payload.items():
            story.append(Spacer(1, 0.15 * cm))
            story.append(Paragraph(str(section_name), styles['BodySmall']))
            rows = _safe_rows(section_payload)
            table = Table(rows, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f2747')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('LEADING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
        story.append(PageBreak())
        story.append(Paragraph('Engineering disclaimer', styles['SubTitleBlue']))
        story.append(Paragraph('Este documento é uma ferramenta de screening e apoio à decisão. Não substitui PHA formal, verificação de SIS, estudo regulatório ou validação por profissional habilitado.', styles['BodySmall']))
        doc.build(story)
        return buffer.getvalue()

    def build_bundle(self, case_name: str, payload: Dict[str, Any]) -> ReportBundle:
        narrative = self.build_narrative(payload)
        html = self.render_html(case_name, payload, narrative)
        pdf = self.render_pdf(case_name, payload, narrative)
        return ReportBundle(
            html=html,
            pdf=pdf,
            markdown=narrative.encode('utf-8'),
            filename_stem=case_name.replace(' ', '_').lower(),
        )
