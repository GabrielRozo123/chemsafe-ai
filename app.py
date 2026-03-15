from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from config import settings
from state import init_state
from chemicals import DB
from refs import REFS
from hazop_db import HAZOP_DB
from ai_client import AIClient
from deterministic import (
    IPL_CATALOG,
    chemical_lookup,
    compute_lopa,
    gaussian_dispersion,
    hazop_template,
    pool_fire,
    recommend_modules,
)
from hazard_extractor import extract_document_insights, generate_hazop_from_text
from rag import LocalKnowledgeBase
from report_service import ReportService
from theme import APP_CSS

st.set_page_config(
    page_title=settings.app_name,
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(APP_CSS, unsafe_allow_html=True)
init_state()

if "last_hazop_raw" not in st.session_state:
    st.session_state.last_hazop_raw = None

ai = AIClient()
if st.session_state.knowledge_base is None:
    st.session_state.knowledge_base = LocalKnowledgeBase(ai)
kb: LocalKnowledgeBase = st.session_state.knowledge_base
report_service = ReportService(ai)


def hero() -> None:
    st.markdown(
        f"""
        <div class='hero'>
          <h1>{settings.app_name}</h1>
          <p>Segurança de processo assistida por IA: HAZOP · LOPA · SIL · consequence screening · RAG documental · relatórios executivos</p>
          <div>
            <span class='badge'>IEC 61882</span>
            <span class='badge'>CCPS LOPA</span>
            <span class='badge'>IEC 61511</span>
            <span class='badge'>API RP 521</span>
            <span class='badge'>Pasquill-Gifford</span>
            <span class='badge'>Shokri-Beyler</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, klass: str = "risk-blue") -> str:
    return f"<div class='metric-box'><div class='metric-label'>{label}</div><div class='metric-value {klass}'>{value}</div></div>"


with st.sidebar:
    st.markdown(f"### ⚗️ {settings.app_name}")
    st.caption(f"v{settings.app_version} · deterministic core + AI copilot")
    st.markdown("---")
    st.write("**Integrações**")
    st.write(f"OpenAI copiloto: {'✅ habilitado' if ai.enabled else '⚪ offline'}")
    st.write("RAG local: ✅")
    st.write("Relatórios PDF/HTML: ✅")
    st.markdown("---")
    st.write("**Acesso rápido**")
    for key, value in DB.items():
        if st.button(value["nome"], key=f"quick_{key}", width="stretch"):
            st.session_state.selected_compound = value
    st.markdown("---")
    st.write("**Memória da sessão**")
    st.caption(f"Documentos indexados: {len(kb.chunks)} chunks")
    st.caption(f"Histórico: {len(st.session_state.history)} itens")

hero()

overview, chemicals_tab, hazop_tab, bowtie_tab, lopa_tab, consequence_tab, docs_tab, copilot_tab, reports_tab, refs_tab = st.tabs(
    [
        "Overview",
        "Consulta química",
        "HAZOP + IA",
        "Bow-Tie",
        "LOPA → SIL",
        "Consequências",
        "Document Intelligence",
        "Copiloto",
        "Relatórios",
        "Referências",
    ]
)

with overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        metric_card(
            "OpenAI",
            "ON" if ai.enabled else "OFF",
            "risk-green" if ai.enabled else "risk-amber",
        ),
        unsafe_allow_html=True,
    )
    c2.markdown(metric_card("Chunks RAG", str(len(kb.chunks))), unsafe_allow_html=True)
    c3.markdown(
        metric_card("Cenários HAZOP IA", str(len(st.session_state.get("risk_register", [])))),
        unsafe_allow_html=True,
    )
    c4.markdown(
        metric_card("Último caso", st.session_state.get("last_case_name", "untitled_case")),
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='panel'><div class='note-card'>Arquitetura recomendada: use a IA para estruturar, comparar, resumir e redigir. Mantenha decisões numéricas críticas no motor determinístico e sob revisão de engenharia.</div></div>",
        unsafe_allow_html=True,
    )
    with st.expander("O que esta versão faz na prática"):
        st.markdown(
            """
- Gera pré-HAZOP a partir de texto livre.
- Lê PDFs, DOCX, planilhas e usa esses documentos como contexto para o copiloto.
- Extrai equipamentos, químicos, instrumentos e salvaguardas dos documentos enviados.
- Gera relatório profissional em HTML, PDF e Markdown.
- Mantém rastreabilidade via log das chamadas LLM.
        """
        )

with chemicals_tab:
    left, right = st.columns([3, 1])
    with left:
        q = st.text_input("Pesquisar composto", placeholder="Ex.: etanol, amônia, 64-17-5")
    with right:
        find_btn = st.button("Consultar", type="primary", width="stretch")
    if find_btn and q:
        result = chemical_lookup(q)
        if result:
            st.session_state.selected_compound = result
            st.session_state.history.append(
                {"name": result["nome"], "at": datetime.now().strftime("%H:%M")}
            )
        else:
            st.warning("Composto não localizado na base local.")
    compound = st.session_state.selected_compound
    if compound:
        a, b, c, d = st.columns(4)
        nfpa = compound.get("nfpa", (0, 0, 0, ""))
        a.markdown(metric_card("Composto", compound["nome"]), unsafe_allow_html=True)
        b.markdown(metric_card("CAS", compound["cas"]), unsafe_allow_html=True)
        c.markdown(metric_card("NFPA F/H/R", f"{nfpa[0]}/{nfpa[1]}/{nfpa[2]}"), unsafe_allow_html=True)
        d.markdown(
            metric_card("AIT", f"{compound.get('ait', '—')} °C" if compound.get("ait") else "—"),
            unsafe_allow_html=True,
        )
        l1, l2 = st.columns(2)
        with l1:
            st.markdown("<div class='panel'><b>Perigos GHS</b></div>", unsafe_allow_html=True)
            for hz in compound.get("hazards", []):
                st.error(hz)
        with l2:
            st.markdown("<div class='panel'><b>Propriedades</b></div>", unsafe_allow_html=True)
            st.table(pd.DataFrame(compound.get("props", []), columns=["Propriedade", "Valor"]))
        st.markdown(
            "<div class='small-muted'>Use esta base como screening rápido. Para classificação formal, confira a SDS/FISPQ do fornecedor e critérios regulatórios vigentes.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Selecione um composto na barra lateral ou pesquise por nome/CAS.")

with hazop_tab:
    c1, c2, c3 = st.columns(3)
    equipment = c1.selectbox(
        "Equipamento / nó",
        [
            "Tanque atmosférico",
            "Reator CSTR exotérmico",
            "Vaso de pressão",
            "Trocador de calor",
            "Tubulação de processo",
            "Bomba centrífuga",
        ],
    )
    parameter = c2.selectbox("Parâmetro", list(HAZOP_DB.keys()))
    guideword = c3.selectbox("Palavra-guia", ["MAIS", "MENOS", "NÃO / NENHUM"])

    if st.button("Gerar HAZOP base", type="primary"):
        st.session_state.hazop_result = hazop_template(parameter, guideword)

    hz = st.session_state.hazop_result
    if hz:
        st.subheader("Worksheet HAZOP base")
        rows = []
        for idx, cause in enumerate(hz.get("causas", [])):
            rows.append(
                {
                    "Desvio": f"{guideword} {parameter}" if idx == 0 else "idem",
                    "Causa": cause,
                    "Consequência": hz.get("conseqs", ["—"])[idx if idx < len(hz.get("conseqs", [])) else 0],
                    "Salvaguarda": hz.get("salvags", ["—"])[idx if idx < len(hz.get("salvags", [])) else 0],
                    "Recomendação": hz.get("rec", ["—"])[idx if idx < len(hz.get("rec", [])) else 0],
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Pré-HAZOP por IA")
    process_description = st.text_area(
        "Descrição do processo",
        height=180,
        placeholder="Descreva o processo, os fluidos, utilidades, instrumentos e condição operacional.",
    )
    operating_context = st.text_area(
        "Contexto operacional",
        height=100,
        placeholder="Ex.: resfriamento por água industrial, atmosfera inerte, operação em batelada...",
    )

    if st.button("Gerar pré-HAZOP com IA", type="primary", disabled=not ai.enabled):
        if not process_description.strip() or not operating_context.strip():
            st.warning("Preencha a descrição do processo e o contexto operacional.")
        else:
            with st.spinner("Consultando IA e estruturando cenários..."):
                raw_result = ai.ask_json(
                    f"""
Gere um pré-HAZOP técnico para o seguinte caso.

Equipamento / nó:
{equipment}

Descrição do processo:
{process_description}

Contexto operacional:
{operating_context}

Requisitos:
- retornar cenários tecnicamente plausíveis para segurança de processo;
- incluir desvio, causa, consequência, salvaguardas existentes e recomendação;
- priorizar linguagem de engenharia química / process safety;
- considerar cenários de perda de contenção, sobrepressão, runaway, toxic release, incêndio e falhas instrumentadas quando aplicável.
""".strip(),
                    system_prompt="""
Você é um especialista sênior em segurança de processo, HAZOP, LOPA, SIS/SIL e consequence analysis.
Responda estritamente em JSON conforme o schema solicitado.
""".strip(),
                    reasoning=True,
                    schema={
                        "name": "prehazop_payload",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "scenarios": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "node": {"type": "string"},
                                            "deviation": {"type": "string"},
                                            "cause": {"type": "string"},
                                            "consequence": {"type": "string"},
                                            "safeguards": {"type": "array", "items": {"type": "string"}},
                                            "recommendations": {"type": "array", "items": {"type": "string"}},
                                            "severity": {"type": "string"},
                                            "likelihood": {"type": "string"},
                                            "risk_rank": {"type": "string"},
                                        },
                                        "required": [
                                            "node",
                                            "deviation",
                                            "cause",
                                            "consequence",
                                            "safeguards",
                                            "recommendations",
                                            "severity",
                                            "likelihood",
                                            "risk_rank",
                                        ],
                                        "additionalProperties": False,
                                    },
                                }
                            },
                            "required": ["scenarios"],
                            "additionalProperties": False,
                        },
                    },
                )

                st.session_state.last_hazop_raw = raw_result

                raw_items = raw_result.get("scenarios", []) if isinstance(raw_result, dict) else []
                scenarios = raw_items if isinstance(raw_items, list) else []

                st.session_state.risk_register = scenarios
                st.session_state.last_case_name = equipment

                if not scenarios:
                    st.warning(
                        "A IA respondeu, mas nenhum cenário estruturado foi extraído. "
                        "Veja a resposta bruta no bloco de debug abaixo."
                    )

    if st.session_state.risk_register:
        st.subheader("Cenários gerados")
        st.dataframe(pd.DataFrame(st.session_state.risk_register), width="stretch", hide_index=True)

    if st.session_state.get("last_hazop_raw") is not None:
        with st.expander("Debug — resposta bruta da IA"):
            st.json(st.session_state.last_hazop_raw)

with bowtie_tab:
    st.markdown(
        "<div class='panel'><b>Bow-Tie simplificado</b><div class='small-muted'>Use esta aba como estrutura visual de ameaças → top event → consequências.</div></div>",
        unsafe_allow_html=True,
    )
    top_event = st.text_input("Top event", value="Perda de contenção primária")
    threats = st.text_area("Ameaças (uma por linha)", value="Corrosão\nOverfill\nErro operacional\nImpacto externo")
    prev = st.text_area(
        "Barreiras preventivas",
        value="Inspeção de integridade\nLAHH + SIS\nProcedimento operacional\nBarreiras físicas",
    )
    cons = st.text_area(
        "Consequências",
        value="Pool fire\nVCE\nContaminação ambiental\nPerda econômica",
    )
    mitig = st.text_area(
        "Barreiras mitigadoras",
        value="Dique\nDetecção de incêndio\nEspuma\nPlano de emergência",
    )
    bt_cols = st.columns(4)
    bt_cols[0].markdown("### Ameaças\n" + "\n".join([f"- {x}" for x in threats.splitlines() if x.strip()]))
    bt_cols[1].markdown("### Prevenção\n" + "\n".join([f"- {x}" for x in prev.splitlines() if x.strip()]))
    bt_cols[2].markdown(f"### Top event\n**{top_event}**")
    bt_cols[3].markdown(
        "### Mitigação / Consequências\n"
        + "\n".join([f"- {x}" for x in (mitig + "\n" + cons).splitlines() if x.strip()])
    )

with lopa_tab:
    left, right = st.columns(2)
    with left:
        f_ie = st.number_input(
            "Frequência do evento iniciador (1/ano)",
            value=0.1,
            min_value=0.000001,
            format="%.6f",
        )
        criterion_label = st.selectbox(
            "Critério de risco tolerável",
            [
                "Fatalidade / catástrofe ambiental — 1e-5/ano",
                "Lesão grave / dano severo — 1e-4/ano",
                "Lesão moderada — 1e-3/ano",
            ],
        )
        criterion = {
            "Fatalidade / catástrofe ambiental — 1e-5/ano": 1e-5,
            "Lesão grave / dano severo — 1e-4/ano": 1e-4,
            "Lesão moderada — 1e-3/ano": 1e-3,
        }[criterion_label]
    with right:
        selected = st.multiselect(
            "IPLs independentes",
            options=[f"{n} (PFD={p})" for n, p in IPL_CATALOG],
            default=[f"{IPL_CATALOG[0][0]} (PFD={IPL_CATALOG[0][1]})"],
        )

    if st.button("Calcular LOPA / SIL", type="primary"):
        chosen = []
        for label in selected:
            for name, pfd in IPL_CATALOG:
                if name in label:
                    chosen.append((name, pfd))
                    break
        st.session_state.lopa_result = compute_lopa(f_ie, criterion, chosen)

    if st.session_state.lopa_result:
        r = st.session_state.lopa_result
        a, b, c, d = st.columns(4)
        a.markdown(metric_card("F_ie", f"{r['f_ie']:.2e}/ano"), unsafe_allow_html=True)
        b.markdown(metric_card("PFD total", f"{r['pfd_total']:.2e}"), unsafe_allow_html=True)
        c.markdown(
            metric_card(
                "MCF",
                f"{r['mcf']:.2e}/ano",
                "risk-green" if r["ratio"] <= 1 else "risk-red",
            ),
            unsafe_allow_html=True,
        )
        d.markdown(
            metric_card(
                "SIL requerido",
                r["sil"],
                "risk-green" if r["sil"] == "Não requerido" else "risk-amber",
            ),
            unsafe_allow_html=True,
        )
        st.dataframe(
            pd.DataFrame(r["selected_ipls"], columns=["IPL", "PFD"]),
            width="stretch",
            hide_index=True,
        )
        st.markdown(
            f"<div class='note-card'>Razão MCF/critério = <b>{r['ratio']:.2f}</b>. {'Risco tolerável' if r['ratio'] <= 1 else 'Adicionar camada independente ou reduzir frequência do evento iniciador.'}</div>",
            unsafe_allow_html=True,
        )

with consequence_tab:
    disp_tab, fire_tab, suggest_tab = st.tabs(["Dispersão gaussiana", "Pool fire", "Sugerir módulos"])

    with disp_tab:
        a, b, c = st.columns(3)
        q_g_s = a.number_input("Q (g/s)", value=10.0, min_value=0.001)
        wind = b.number_input("u (m/s)", value=3.0, min_value=0.2)
        stability = c.selectbox("Classe de estabilidade", list("ABCDEF"), index=3)
        d1, d2, d3 = st.columns(3)
        idlh_ppm = d1.number_input("IDLH (ppm)", value=300.0, min_value=0.001)
        mw = d2.number_input("PM do gás", value=17.0, min_value=1.0)
        h = d3.number_input("Altura da fonte (m)", value=0.0, min_value=0.0)

        if st.button("Rodar dispersão", type="primary"):
            st.session_state.dispersion_result = gaussian_dispersion(q_g_s, wind, stability, idlh_ppm, mw, h)

        if st.session_state.dispersion_result:
            r = st.session_state.dispersion_result
            x_display = f"{r['x_idlh']} m" if r["x_idlh"] else "> 3 km"
            u1, u2 = st.columns(2)
            u1.markdown(
                metric_card(
                    "Distância até IDLH",
                    x_display,
                    "risk-red" if r["x_idlh"] and r["x_idlh"] < 500 else "risk-green",
                ),
                unsafe_allow_html=True,
            )
            u2.markdown(metric_card("Concentração @100 m", f"{r['c_at_100m']:.4f} g/m³"), unsafe_allow_html=True)
            df = pd.DataFrame({"x_m": r["xs"], "c_g_m3": r["cs"]})
            st.line_chart(df.set_index("x_m"))

    with fire_tab:
        a, b, c, d = st.columns(4)
        diameter = a.number_input("Diâmetro da poça (m)", value=5.0, min_value=0.5)
        burn = b.number_input('m" (kg/m²·s)', value=0.024, min_value=0.001)
        hc = c.number_input("Hc (kJ/kg)", value=44000.0, min_value=1000.0)
        distance = d.number_input("Distância ao alvo (m)", value=20.0, min_value=1.0)

        if st.button("Rodar pool fire", type="primary"):
            st.session_state.pool_fire_result = pool_fire(diameter, burn, hc, distance)

        if st.session_state.pool_fire_result:
            r = st.session_state.pool_fire_result
            p1, p2, p3 = st.columns(3)
            p1.markdown(metric_card("Altura da chama", f"{r['Hf_m']:.1f} m"), unsafe_allow_html=True)
            p2.markdown(metric_card("Poder emissivo", f"{r['E_kW_m2']:.1f} kW/m²"), unsafe_allow_html=True)
            p3.markdown(
                metric_card(
                    "Fluxo no alvo",
                    f"{r['q_kW_m2']:.2f} kW/m²",
                    "risk-red" if r["q_kW_m2"] > 12.5 else "risk-amber" if r["q_kW_m2"] > 4.7 else "risk-green",
                ),
                unsafe_allow_html=True,
            )
            st.markdown(f"<div class='note-card'><b>Zona:</b> {r['zone']}</div>", unsafe_allow_html=True)

    with suggest_tab:
        process_txt = st.text_area("Descrição resumida do caso", height=140)
        compound_name = st.text_input(
            "Composto principal",
            value=st.session_state.selected_compound["nome"] if st.session_state.selected_compound else "",
        )
        if st.button("Sugerir caminhos de análise"):
            recs = recommend_modules(process_txt, compound_name)
            for item in recs:
                st.success(item)

with docs_tab:
    uploads = st.file_uploader(
        "Enviar documentos técnicos",
        accept_multiple_files=True,
        type=["pdf", "docx", "xlsx", "xls", "csv", "txt", "md", "json"],
    )
    c1, c2 = st.columns([1, 2])

    with c1:
        if st.button("Indexar documentos", type="primary", disabled=not uploads):
            with st.spinner("Indexando documentos..."):
                added = kb.ingest_streamlit_uploads(uploads or [])
                st.success(f"{added} chunks indexados.")

    with c2:
        st.caption("Faça upload de PFD, procedimentos, memoriais descritivos, FISPQ, planilhas e relatórios.")

    search_query = st.text_input(
        "Buscar no acervo da sessão",
        placeholder="Ex.: LAHH, amônia, intertravamento, temperatura máxima",
    )
    if search_query:
        hits = kb.search(search_query, top_k=6)
        for hit in hits:
            st.markdown(
                f"**{hit.chunk.source_name}** · página {hit.chunk.page or '—'} · score={hit.score:.3f} · {hit.match_reason}"
            )
            st.caption(hit.chunk.text[:500] + ("..." if len(hit.chunk.text) > 500 else ""))

    if st.button("Extrair insights de segurança com IA", disabled=(not ai.enabled or not kb.chunks)):
        with st.spinner("Extraindo insights documentais..."):
            hits = kb.search("chemicals equipment instruments safeguards interlocks operating limits hazards", top_k=8)
            context_blocks = [{"source": f"{h.chunk.source_name} p.{h.chunk.page or '-'}", "text": h.chunk.text} for h in hits]
            st.session_state.doc_insights = extract_document_insights(ai, context_blocks)

    if st.session_state.doc_insights:
        st.subheader("Insights documentais")
        st.json(st.session_state.doc_insights)

with copilot_tab:
    st.markdown(
        "<div class='panel'><b>Copiloto técnico</b><div class='small-muted'>Pergunte sobre HAZOP, salvaguardas, lacunas, cenários de consequência ou síntese documental.</div></div>",
        unsafe_allow_html=True,
    )
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ex.: Quais lacunas de salvaguarda aparecem neste caso?"):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        context_hits = kb.search(prompt, top_k=6)
        context_blocks = [{"source": f"{h.chunk.source_name} p.{h.chunk.page or '-'}", "text": h.chunk.text} for h in context_hits]
        structured_context = {
            "compound": st.session_state.selected_compound,
            "hazop_base": st.session_state.hazop_result,
            "hazop_ai": st.session_state.risk_register,
            "lopa": st.session_state.lopa_result,
            "dispersion": st.session_state.dispersion_result,
            "pool_fire": st.session_state.pool_fire_result,
            "doc_insights": st.session_state.doc_insights,
        }
        context_blocks.append(
            {
                "source": "session_state",
                "text": json.dumps(structured_context, ensure_ascii=False, default=str)[:7000],
            }
        )

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                answer = ai.ask(prompt, context_blocks=context_blocks, reasoning=True).answer
                st.markdown(answer)

        st.session_state.copilot_messages.append({"role": "assistant", "content": answer})

with reports_tab:
    st.subheader("Gerador de relatório profissional")
    case_name = st.text_input("Nome do caso", value=st.session_state.get("last_case_name", "Untitled case"))

    if st.button("Montar relatório", type="primary"):
        payload = {
            "compound": st.session_state.selected_compound or {},
            "hazop_base": st.session_state.hazop_result or {},
            "hazop_ai": st.session_state.risk_register or [],
            "lopa": st.session_state.lopa_result or {},
            "dispersion": st.session_state.dispersion_result or {},
            "pool_fire": st.session_state.pool_fire_result or {},
            "document_insights": st.session_state.doc_insights or {},
            "chat_summary": st.session_state.copilot_messages[-6:],
        }
        with st.spinner("Gerando relatório..."):
            st.session_state.report_payload = payload
            st.session_state.report_bundle = report_service.build_bundle(case_name, payload)
            st.success("Relatório gerado.")

    bundle = st.session_state.get("report_bundle")
    if bundle:
        st.download_button("Baixar HTML", bundle.html, file_name=f"{bundle.filename_stem}.html", mime="text/html", width="stretch")
        st.download_button("Baixar PDF", bundle.pdf, file_name=f"{bundle.filename_stem}.pdf", mime="application/pdf", width="stretch")
        st.download_button("Baixar Markdown", bundle.markdown, file_name=f"{bundle.filename_stem}.md", mime="text/markdown", width="stretch")
        with st.expander("Pré-visualizar markdown"):
            st.markdown(bundle.markdown.decode("utf-8"))

with refs_tab:
    st.subheader("Normas e referências-base")
    st.table(pd.DataFrame(REFS, columns=["Fonte", "Título"]))
    st.markdown(
        "<div class='small-muted'>Esta base referencia o núcleo determinístico e a linguagem dos relatórios. Para uso formal, valide edição, critérios corporativos e aderência regulatória local.</div>",
        unsafe_allow_html=True,
    )
