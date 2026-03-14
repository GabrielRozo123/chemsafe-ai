from __future__ import annotations

import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import settings


@dataclass
class ReportBundle:
    filename_stem: str
    html: bytes
    pdf: bytes
    markdown: bytes


class ReportService:
    def __init__(self, ai_client: Any) -> None:
        self.ai = ai_client

    def build_bundle(self, case_name: str, payload: Dict[str, Any]) -> ReportBundle:
        case_name = case_name.strip() or "Untitled case"
        filename_stem = self._slugify(case_name)

        executive_summary = self._build_executive_summary(case_name, payload)
        html_doc = self._render_html(case_name, payload, executive_summary)
        markdown_doc = self._render_markdown(case_name, payload, executive_summary)
        pdf_doc = self._render_pdf(case_name, markdown_doc.decode("utf-8", errors="ignore"))

        return ReportBundle(
            filename_stem=filename_stem,
            html=html_doc.encode("utf-8"),
            pdf=pdf_doc,
            markdown=markdown_doc,
        )

    # ------------------------------------------------------------------
    # summary
    # ------------------------------------------------------------------
    def _build_executive_summary(self, case_name: str, payload: Dict[str, Any]) -> str:
        if getattr(self.ai, "enabled", False):
            try:
                prompt = f"""
Elabore um resumo executivo técnico, conciso e profissional para um relatório preliminar de segurança de processo.

Nome do caso: {case_name}

Contexto estruturado:
{json.dumps(payload, ensure_ascii=False, default=str)[:12000]}

Requisitos:
- 3 a 6 parágrafos curtos;
- linguagem de engenharia e process safety;
- destacar principais riscos, lacunas, consequências e próximos passos;
- não inventar dados fora do contexto;
- deixar claro quando a análise é preliminar / screening.
""".strip()

                answer = self.ai.ask(
                    prompt,
                    system_prompt=(
                        "Você é um engenheiro sênior de segurança de processo. "
                        "Escreva sumários executivos técnicos para triagem de risco, "
                        "HAZOP preliminar, LOPA screening e consequence analysis."
                    ),
                    reasoning=False,
                ).answer

                if answer and answer.strip():
                    return answer.strip()
            except Exception:
                pass

        return self._fallback_summary(case_name, payload)

    def _fallback_summary(self, case_name: str, payload: Dict[str, Any]) -> str:
        compound = payload.get("compound") or {}
        hazop_ai = payload.get("hazop_ai") or []
        lopa = payload.get("lopa") or {}
        dispersion = payload.get("dispersion") or {}
        pool_fire = payload.get("pool_fire") or {}
        doc_insights = payload.get("document_insights") or {}

        lines: List[str] = []
        lines.append(
            f"O caso '{case_name}' foi consolidado como uma análise preliminar de segurança de processo com foco em identificação de perigos, cenários de desvio, screening de consequências e verificação inicial de camadas de proteção."
        )

        if compound:
            lines.append(
                f"O composto principal identificado foi {compound.get('nome', 'não especificado')}, com CAS {compound.get('cas', '—')}. "
                "Os perigos químicos e propriedades relevantes foram usados apenas como base de triagem rápida."
            )

        if hazop_ai:
            lines.append(
                f"Foram gerados {len(hazop_ai)} cenários preliminares de HAZOP por IA, complementando a base determinística do aplicativo."
            )

        if lopa:
            lines.append(
                f"A avaliação LOPA indicou MCF de {lopa.get('mcf', '—')} e classificação preliminar de {lopa.get('sil', 'Não requerido')}."
            )

        if dispersion:
            lines.append(
                f"O screening de dispersão estimou distância até o critério IDLH de {dispersion.get('x_idlh', '>3 km')} m."
            )

        if pool_fire:
            lines.append(
                f"No cenário de pool fire, o fluxo térmico estimado no alvo foi de {pool_fire.get('q_kW_m2', '—')} kW/m², enquadrado como '{pool_fire.get('zone', '—')}'."
            )

        if doc_insights:
            lines.append(
                "A leitura documental também extraiu informações úteis sobre equipamentos, salvaguardas, instrumentos e limites operacionais, servindo como suporte ao entendimento do caso."
            )

        lines.append(
            "Este material deve ser tratado como screening técnico e apoio à decisão preliminar, não como substituto de estudo formal de HAZOP, LOPA, SIS/SIL ou consequence analysis conduzido por profissionais habilitados."
        )

        return "\n\n".join(lines)

    # ------------------------------------------------------------------
    # render html
    # ------------------------------------------------------------------
    def _render_html(self, case_name: str, payload: Dict[str, Any], executive_summary: str) -> str:
        compound = payload.get("compound") or {}
        hazop_base = payload.get("hazop_base") or {}
        hazop_ai = payload.get("hazop_ai") or []
        lopa = payload.get("lopa") or {}
        dispersion = payload.get("dispersion") or {}
        pool_fire = payload.get("pool_fire") or {}
        document_insights = payload.get("document_insights") or {}
        chat_summary = payload.get("chat_summary") or []

        generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='pt-BR'>",
            "<head>",
            "<meta charset='utf-8'/>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
            f"<title>{html.escape(case_name)} - {html.escape(settings.app_name)}</title>",
            "<style>",
            self._html_css(),
            "</style>",
            "</head>",
            "<body>",
            "<div class='page'>",
            "<header class='hero'>",
            f"<div class='eyebrow'>{html.escape(settings.app_name)} · Relatório técnico preliminar</div>",
            f"<h1>{html.escape(case_name)}</h1>",
            "<p class='subtitle'>HAZOP preliminar · LOPA screening · consequence analysis · intelligence documental</p>",
            "<div class='meta-row'>",
            f"<div><b>Emitido em:</b> {html.escape(generated_at)}</div>",
            f"<div><b>Plataforma:</b> {html.escape(settings.app_name)} v{html.escape(settings.app_version)}</div>",
            f"<div><b>Autor / contato:</b> <a href='{html.escape(settings.linkedin_url)}'>{html.escape(settings.linkedin_url)}</a></div>",
            "</div>",
            "</header>",
            self._section("Resumo executivo", self._paragraphs_to_html(executive_summary)),
        ]

        # compound
        if compound:
            compound_table = self._kv_table(
                {
                    "Nome": compound.get("nome", "—"),
                    "CAS": compound.get("cas", "—"),
                    "Fórmula": compound.get("formula", "—"),
                    "AIT": compound.get("ait", "—"),
                    "NFPA": "/".join(map(str, compound.get("nfpa", (0, 0, 0, ""))[:3])) if compound.get("nfpa") else "—",
                }
            )
            hazards_html = self._bullet_list(compound.get("hazards", []))
            html_parts.append(self._section("Consulta química", compound_table + hazards_html))

        # hazop base
        if hazop_base:
            hz_rows = []
            causes = hazop_base.get("causas", [])
            cons = hazop_base.get("conseqs", [])
            sav = hazop_base.get("salvags", [])
            rec = hazop_base.get("rec", [])
            for i, cause in enumerate(causes):
                hz_rows.append(
                    {
                        "Causa": cause,
                        "Consequência": cons[i] if i < len(cons) else (cons[0] if cons else "—"),
                        "Salvaguarda": sav[i] if i < len(sav) else (sav[0] if sav else "—"),
                        "Recomendação": rec[i] if i < len(rec) else (rec[0] if rec else "—"),
                    }
                )
            html_parts.append(self._section("HAZOP base", self._table_from_rows(hz_rows)))

        # hazop ai
        if hazop_ai:
            ai_rows = []
            for item in hazop_ai:
                ai_rows.append(
                    {
                        "Nó": item.get("node", "—"),
                        "Desvio": item.get("deviation", "—"),
                        "Causa": item.get("cause", "—"),
                        "Consequência": item.get("consequence", "—"),
                        "Salvaguardas": ", ".join(item.get("safeguards", [])) if isinstance(item.get("safeguards"), list) else "—",
                        "Recomendações": ", ".join(item.get("recommendations", [])) if isinstance(item.get("recommendations"), list) else "—",
                        "Risco": item.get("risk_rank", "—"),
                    }
                )
            html_parts.append(self._section("Pré-HAZOP gerado por IA", self._table_from_rows(ai_rows)))

        # lopa
        if lopa:
            cards = self._metric_cards(
                [
                    ("F_ie", self._fmt_num(lopa.get("f_ie")), "blue"),
                    ("PFD total", self._fmt_num(lopa.get("pfd_total")), "blue"),
                    ("MCF", self._fmt_num(lopa.get("mcf")), "red" if (lopa.get("ratio", 0) or 0) > 1 else "green"),
                    ("SIL requerido", str(lopa.get("sil", "—")), "amber"),
                ]
            )
            ipl_rows = []
            for item in lopa.get("selected_ipls", []):
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    ipl_rows.append({"IPL": item[0], "PFD": item[1]})
            body = cards
            if ipl_rows:
                body += self._table_from_rows(ipl_rows)
            html_parts.append(self._section("LOPA → SIL", body))

        # consequences
        consequence_blocks = []
        if dispersion:
            consequence_blocks.append(
                self._mini_panel(
                    "Dispersão gaussiana",
                    {
                        "Distância até IDLH": f"{dispersion.get('x_idlh', '>3 km')} m",
                        "Concentração @100 m": self._fmt_num(dispersion.get("c_at_100m")),
                    },
                )
            )
        if pool_fire:
            consequence_blocks.append(
                self._mini_panel(
                    "Pool fire",
                    {
                        "Fluxo no alvo": f"{self._fmt_num(pool_fire.get('q_kW_m2'))} kW/m²",
                        "Zona": pool_fire.get("zone", "—"),
                        "Altura da chama": f"{self._fmt_num(pool_fire.get('Hf_m'))} m",
                    },
                )
            )
        if consequence_blocks:
            html_parts.append(self._section("Consequence screening", "".join(consequence_blocks)))

        # doc insights
        if document_insights:
            di_html = []
            for key in ["chemicals", "equipment", "instruments", "safeguards", "operating_limits", "hazards", "notes"]:
                values = document_insights.get(key, [])
                if values:
                    di_html.append(f"<h3>{html.escape(key.replace('_', ' ').title())}</h3>")
                    di_html.append(self._bullet_list(values))
            html_parts.append(self._section("Document intelligence", "".join(di_html)))

        # chat summary
        if chat_summary:
            chat_html = []
            for msg in chat_summary:
                role = msg.get("role", "message").title()
                content = msg.get("content", "")
                chat_html.append(
                    f"<div class='chat-block'><div class='chat-role'>{html.escape(role)}</div><div>{html.escape(str(content))}</div></div>"
                )
            html_parts.append(self._section("Trechos recentes do copiloto", "".join(chat_html)))

        html_parts.append(
            self._section(
                "Aviso e limitações",
                """
                <p>Este relatório é um material de triagem técnica e apoio preliminar à decisão. Ele não substitui estudo formal de HAZOP, LOPA, SIL verification, QRA ou consequence analysis detalhada conduzida por profissionais habilitados.</p>
                <p>Resultados numéricos, classificações e recomendações devem ser validados com dados de processo, critérios corporativos, normas aplicáveis e julgamento de engenharia.</p>
                """,
            )
        )

        html_parts.extend(["</div>", "</body>", "</html>"])
        return "\n".join(html_parts)

    # ------------------------------------------------------------------
    # render markdown
    # ------------------------------------------------------------------
    def _render_markdown(self, case_name: str, payload: Dict[str, Any], executive_summary: str) -> bytes:
        compound = payload.get("compound") or {}
        hazop_ai = payload.get("hazop_ai") or []
        lopa = payload.get("lopa") or {}
        dispersion = payload.get("dispersion") or {}
        pool_fire = payload.get("pool_fire") or {}
        document_insights = payload.get("document_insights") or {}

        lines: List[str] = []
        lines.append(f"# {case_name}")
        lines.append("")
        lines.append(f"**Plataforma:** {settings.app_name} v{settings.app_version}")
        lines.append(f"**Emitido em:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")
        lines.append("## Resumo executivo")
        lines.append("")
        lines.append(executive_summary)
        lines.append("")

        if compound:
            lines.append("## Consulta química")
            lines.append("")
            for k in ["nome", "cas", "formula", "ait"]:
                if k in compound:
                    lines.append(f"- **{k.upper()}**: {compound.get(k)}")
            if compound.get("hazards"):
                lines.append("- **Perigos:**")
                for hz in compound["hazards"]:
                    lines.append(f"  - {hz}")
            lines.append("")

        if hazop_ai:
            lines.append("## Pré-HAZOP gerado por IA")
            lines.append("")
            for i, item in enumerate(hazop_ai, start=1):
                lines.append(f"### Cenário {i}")
                lines.append(f"- **Nó:** {item.get('node', '—')}")
                lines.append(f"- **Desvio:** {item.get('deviation', '—')}")
                lines.append(f"- **Causa:** {item.get('cause', '—')}")
                lines.append(f"- **Consequência:** {item.get('consequence', '—')}")
                if item.get("safeguards"):
                    lines.append("- **Salvaguardas:**")
                    for s in item.get("safeguards", []):
                        lines.append(f"  - {s}")
                if item.get("recommendations"):
                    lines.append("- **Recomendações:**")
                    for r in item.get("recommendations", []):
                        lines.append(f"  - {r}")
                lines.append(f"- **Risco:** {item.get('risk_rank', '—')}")
                lines.append("")

        if lopa:
            lines.append("## LOPA → SIL")
            lines.append("")
            lines.append(f"- **F_ie:** {self._fmt_num(lopa.get('f_ie'))}")
            lines.append(f"- **PFD total:** {self._fmt_num(lopa.get('pfd_total'))}")
            lines.append(f"- **MCF:** {self._fmt_num(lopa.get('mcf'))}")
            lines.append(f"- **SIL requerido:** {lopa.get('sil', '—')}")
            lines.append("")

        if dispersion or pool_fire:
            lines.append("## Consequence screening")
            lines.append("")
            if dispersion:
                lines.append(f"- **Dispersão:** distância até IDLH = {dispersion.get('x_idlh', '>3 km')} m")
                lines.append(f"- **Concentração @100 m:** {self._fmt_num(dispersion.get('c_at_100m'))} g/m³")
            if pool_fire:
                lines.append(f"- **Pool fire:** fluxo no alvo = {self._fmt_num(pool_fire.get('q_kW_m2'))} kW/m²")
                lines.append(f"- **Zona:** {pool_fire.get('zone', '—')}")
            lines.append("")

        if document_insights:
            lines.append("## Document intelligence")
            lines.append("")
            for key, values in document_insights.items():
                if values:
                    lines.append(f"### {str(key).replace('_', ' ').title()}")
                    if isinstance(values, list):
                        for v in values:
                            lines.append(f"- {v}")
                    else:
                        lines.append(f"- {values}")
                    lines.append("")

        lines.append("## Aviso")
        lines.append("")
        lines.append(
            "Este relatório é preliminar e não substitui estudo formal conduzido por profissionais habilitados."
        )
        lines.append("")

        return "\n".join(lines).encode("utf-8")

    # ------------------------------------------------------------------
    # render pdf
    # ------------------------------------------------------------------
    def _render_pdf(self, case_name: str, text_content: str) -> bytes:
        # PDF mínimo, sem dependências externas
        lines = [case_name, ""] + text_content.splitlines()
        lines = [self._pdf_escape(line[:110]) for line in lines[:120]]

        content_stream = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        first = True
        for line in lines:
            if first:
                content_stream.append(f"({line}) Tj")
                first = False
            else:
                content_stream.append(f"T* ({line}) Tj")
        content_stream.append("ET")
        stream = "\n".join(content_stream).encode("latin-1", errors="ignore")

        objects = []
        offsets = []

        def add_obj(obj_bytes: bytes) -> None:
            offsets.append(sum(len(x) for x in objects))
            objects.append(obj_bytes)

        header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

        add_obj(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
        add_obj(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
        add_obj(
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
        )
        add_obj(f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")
        add_obj(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

        body = b"".join(objects)
        xref_start = len(header) + len(body)

        xref = [b"xref\n", f"0 {len(objects) + 1}\n".encode("latin-1"), b"0000000000 65535 f \n"]
        running = len(header)
        for obj in objects:
            xref.append(f"{running:010d} 00000 n \n".encode("latin-1"))
            running += len(obj)

        trailer = (
            b"trailer<< "
            + f"/Size {len(objects) + 1} /Root 1 0 R ".encode("latin-1")
            + b">>\nstartxref\n"
            + str(xref_start).encode("latin-1")
            + b"\n%%EOF"
        )

        return header + body + b"".join(xref) + trailer

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _slugify(self, value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9\-_\s]+", "", value)
        value = re.sub(r"\s+", "_", value)
        return value or "report"

    def _fmt_num(self, value: Any) -> str:
        try:
            return f"{float(value):.3e}"
        except Exception:
            return str(value)

    def _paragraphs_to_html(self, text: str) -> str:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "".join([f"<p>{html.escape(p)}</p>" for p in paragraphs])

    def _bullet_list(self, items: List[Any]) -> str:
        if not items:
            return "<p>—</p>"
        lis = "".join([f"<li>{html.escape(str(x))}</li>" for x in items])
        return f"<ul>{lis}</ul>"

    def _kv_table(self, mapping: Dict[str, Any]) -> str:
        rows = []
        for k, v in mapping.items():
            rows.append(
                f"<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>"
            )
        return f"<table class='kv-table'>{''.join(rows)}</table>"

    def _table_from_rows(self, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "<p>—</p>"
        headers = list(rows[0].keys())
        thead = "<tr>" + "".join([f"<th>{html.escape(str(h))}</th>" for h in headers]) + "</tr>"
        body_rows = []
        for row in rows:
            body_rows.append(
                "<tr>" + "".join([f"<td>{html.escape(str(row.get(h, '')))}</td>" for h in headers]) + "</tr>"
            )
        return f"<table><thead>{thead}</thead><tbody>{''.join(body_rows)}</tbody></table>"

    def _metric_cards(self, items: List[tuple]) -> str:
        blocks = []
        for label, value, tone in items:
            blocks.append(
                f"<div class='metric {tone}'><div class='metric-label'>{html.escape(str(label))}</div><div class='metric-value'>{html.escape(str(value))}</div></div>"
            )
        return f"<div class='metrics-grid'>{''.join(blocks)}</div>"

    def _mini_panel(self, title: str, mapping: Dict[str, Any]) -> str:
        body = "".join(
            [
                f"<div class='mini-row'><span>{html.escape(str(k))}</span><b>{html.escape(str(v))}</b></div>"
                for k, v in mapping.items()
            ]
        )
        return f"<div class='mini-panel'><h3>{html.escape(title)}</h3>{body}</div>"

    def _section(self, title: str, body_html: str) -> str:
        return f"<section class='section'><h2>{html.escape(title)}</h2>{body_html}</section>"

    def _pdf_escape(self, text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def _html_css(self) -> str:
        return """
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: #eef2f7;
            font-family: Arial, Helvetica, sans-serif;
            color: #152033;
        }
        .page {
            max-width: 1100px;
            margin: 24px auto;
            background: #ffffff;
            border-radius: 18px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        }
        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            color: #fff;
            padding: 28px;
            border-radius: 16px;
            margin-bottom: 24px;
        }
        .hero h1 {
            margin: 8px 0 8px 0;
            font-size: 32px;
        }
        .subtitle {
            margin: 0 0 12px 0;
            color: #d5e3ff;
        }
        .eyebrow {
            font-size: 12px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #9fc1ff;
        }
        .meta-row {
            display: flex;
            gap: 18px;
            flex-wrap: wrap;
            font-size: 13px;
            color: #d8e5ff;
        }
        .section {
            margin: 24px 0;
            padding: 22px;
            border: 1px solid #dbe4f0;
            border-radius: 14px;
            background: #fbfdff;
        }
        .section h2 {
            margin-top: 0;
            font-size: 20px;
            color: #14325c;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }
        th, td {
            border: 1px solid #dbe4f0;
            padding: 10px;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
        }
        th {
            background: #edf4ff;
            color: #14325c;
        }
        .kv-table th {
            width: 220px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }
        .metric {
            border-radius: 12px;
            padding: 14px;
            color: #fff;
        }
        .metric.blue { background: #2457a7; }
        .metric.green { background: #167a57; }
        .metric.red { background: #a72842; }
        .metric.amber { background: #b66b12; }
        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.85;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 20px;
            font-weight: bold;
        }
        .mini-panel {
            border: 1px solid #dbe4f0;
            border-radius: 14px;
            padding: 16px;
            margin: 10px 0;
            background: #ffffff;
        }
        .mini-panel h3 {
            margin-top: 0;
            color: #14325c;
        }
        .mini-row {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            padding: 6px 0;
            border-bottom: 1px dashed #dbe4f0;
        }
        .mini-row:last-child {
            border-bottom: none;
        }
        .chat-block {
            border-left: 4px solid #2457a7;
            background: #f5f9ff;
            padding: 12px 14px;
            margin-bottom: 12px;
            border-radius: 0 10px 10px 0;
        }
        .chat-role {
            font-weight: bold;
            color: #14325c;
            margin-bottom: 6px;
        }
        ul {
            padding-left: 20px;
        }
        a {
            color: #cfe2ff;
        }
        """
