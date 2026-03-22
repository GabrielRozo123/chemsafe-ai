from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

from action_processing import get_action_col
from app_runtime import bowtie_payload, apply_loaded_case
from chart_utils import (
    is_valid_df,
    render_modern_gauge,
    render_modern_radar,
    render_action_donut,
    render_action_bar,
)
from case_domain import (
    CASE_STATUS_OPTIONS,
    build_case_header,
    build_review_event,
    gate_to_status,
    infer_case_gate,
)
from case_store import list_cases, load_case, save_case
from executive_report import build_executive_bundle
from snapshot_engine import build_case_snapshot_html, build_case_snapshot_payload
from ui_components import render_hero_panel, render_evidence_panel, metric_card
from ui_states import render_empty_state, render_success_state


def _safe_text(value, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _safe_case_name(case_name: str | None, profile) -> str:
    raw = (case_name or "").strip()
    if raw:
        return raw
    return _safe_text(profile.identity.get("name"), "Caso")


def _build_open_actions_df(df):
    if df is None or getattr(df, "empty", True):
        return df
    if "Status" not in df.columns:
        return df.copy()
    return df[df["Status"] != "Fechado"].copy()


def _sum_if_exists(df, col: str) -> float:
    if df is None or getattr(df, "empty", True):
        return 0.0
    if col not in df.columns:
        return 0.0
    try:
        return float(df[col].fillna(0).sum())
    except Exception:
        return 0.0


def _count_equals(df, col: str, value: str) -> int:
    if df is None or getattr(df, "empty", True):
        return 0
    if col not in df.columns:
        return 0
    try:
        return int((df[col] == value).sum())
    except Exception:
        return 0


def _build_action_briefing(edited_df, profile, node_name: str, action_col: str) -> str:
    lines: list[str] = []
    lines.append("ORDEM DE SERVIÇO - SEGURANÇA DE PROCESSOS")
    lines.append(f"Ativo: {profile.identity.get('name', 'N/A')}")
    lines.append(f"Topologia: {node_name}")
    lines.append("=" * 60)
    lines.append("")

    if edited_df is None or getattr(edited_df, "empty", True):
        lines.append("Nenhuma ação cadastrada.")
        return "\n".join(lines)

    working_df = edited_df[edited_df["Status"] != "Fechado"].copy() if "Status" in edited_df.columns else edited_df.copy()
    if working_df.empty:
        lines.append("Nenhuma ação aberta no momento.")
        return "\n".join(lines)

    responsaveis = [r for r in working_df["Responsável"].dropna().unique().tolist() if str(r).strip()] if "Responsável" in working_df.columns else ["Equipe responsável"]

    for resp in responsaveis:
        lines.append(f"[EQUIPE: {str(resp).upper()}]")
        acoes_resp = working_df[working_df["Responsável"] == resp] if "Responsável" in working_df.columns else working_df

        for _, row in acoes_resp.iterrows():
            criticidade = row["Criticidade"] if "Criticidade" in row.index else "Normal"
            prazo = row["Prazo (Dias)"] if "Prazo (Dias)" in row.index else "N/A"
            status = row["Status"] if "Status" in row.index else "Aberto"
            acao = row[action_col] if action_col in row.index else "Ação não especificada"
            lines.append(f"- [{criticidade}] {acao} | Prazo: {prazo} dias | Status: {status}")
        lines.append("")

    return "\n".join(lines)


def _ensure_review_history(case_status: str, case_gate: str, actor: str, note: str) -> None:
    history = st.session_state.get("review_history", [])
    latest = history[-1] if history else None

    if latest and latest.get("status") == case_status and latest.get("gate") == case_gate and latest.get("note") == (note or "").strip():
        return

    history.append(build_review_event(status=case_status, note=note, actor=actor, gate=case_gate))
    st.session_state.review_history = history[-25:]


# ======================================================================
# Função principal — assinatura limpa (sem _fn params)
# ======================================================================

def render_executive_module(
    profile,
    cri_data: dict,
    action_df_dash,
    has_actions: bool,
    num_acoes_pendentes: int,
    gaps_criticos: int,
    menu_styles: dict,
    psi_df_dash=None,
    psi_summary=None,
    traceability_df=None,
):
    case_header = build_case_header(
        profile=profile,
        node_name=st.session_state.current_node_name,
        case_name=st.session_state.current_case_name,
        owner=st.session_state.case_owner,
        reviewer=st.session_state.case_reviewer,
    )
    inferred_gate = infer_case_gate(
        cri_data=cri_data,
        psi_summary=psi_summary or {},
        gaps_criticos=gaps_criticos,
        moc_result=st.session_state.get("moc_result"),
        pssr_result=st.session_state.get("pssr_result"),
        lopa_result=st.session_state.get("lopa_result"),
    )
    st.session_state.case_decision_gate = st.session_state.case_decision_gate or inferred_gate
    if not st.session_state.case_status or st.session_state.case_status == "rascunho":
        st.session_state.case_status = gate_to_status(st.session_state.case_decision_gate)

    exec_tab = option_menu(
        menu_title=None,
        options=["Dashboard Global", "Action Plan", "Relatório Automático", "Meus Projetos", "Governança do Caso"],
        icons=["bar-chart", "list-check", "file-earmark-pdf", "folder2-open", "shield-check"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    # ==================================================================
    # Dashboard Global
    # ==================================================================
    if exec_tab == "Dashboard Global":
        render_hero_panel(
            title="Cockpit Executivo de Segurança de Processos",
            subtitle="Visão consolidada da prontidão do caso, gaps críticos, workflow e ações abertas para acelerar decisão com governança técnica.",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="KPIs executivos do caso",
                purpose="Painel executivo consolidado do caso com prontidão técnica, gate decisório e pendências de execução.",
                method="Agregação de CRI + PSI 2.0 + action hub + workflow do caso.",
                references=["CCPS RBPS", "OSHA 1910.119", "AACE Class 5"],
                assumptions=["Indicadores são de priorização e screening executivo.", "A decisão formal requer revisão técnica complementar.", "A robustez do caso depende da qualidade dos dados e do contexto operacional."],
                inputs={"Maturidade global": f"{cri_data.get('index', 0)}%", "PSI score": f"{float((psi_summary or {}).get('score', 0) or 0):.1f}", "Gate": st.session_state.case_decision_gate, "Status": st.session_state.case_status},
                formula="Gate = função de CRI + PSI crítico + proteção + prontidão operacional",
                note="Use o gate como recomendação de avanço do caso, não como autorização automática.",
            )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(metric_card("Maturidade Global", f"{cri_data.get('index', 0)}%", cri_data.get("color_class", "risk-blue"), mono=True), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("PSI Score", f"{float((psi_summary or {}).get('score', 0) or 0):.1f}", "risk-violet", mono=True), unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card("Ações Pendentes", str(num_acoes_pendentes), "risk-amber" if num_acoes_pendentes > 0 else "risk-green", mono=True), unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card("Gaps Críticos", str((psi_summary or {}).get("critical_gaps", gaps_criticos)), "risk-red" if (psi_summary or {}).get("critical_gaps", gaps_criticos) > 0 else "risk-green", mono=True), unsafe_allow_html=True)

        st.markdown(
            f"""<div class="panel"><h3>Gate do Caso</h3>
            <div class="note-card">
                <strong>Status:</strong> {st.session_state.case_status}<br>
                <strong>Gate recomendado:</strong> {st.session_state.case_decision_gate}<br>
                <strong>Owner:</strong> {_safe_text(st.session_state.case_owner, 'Não definido')}<br>
                <strong>Reviewer:</strong> {_safe_text(st.session_state.case_reviewer, 'Não definido')}
            </div></div>""",
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_gauge(cri_data.get("index", 0), cri_data.get("band", "N/A")), use_container_width=True, theme=None, config={"displayModeBar": False})
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_radar(cri_data), use_container_width=True, theme=None, config={"displayModeBar": False})

        if psi_df_dash is not None and not getattr(psi_df_dash, "empty", True):
            st.markdown("<div class='panel'><h3>PSI Readiness 2.0 — Domínios críticos</h3></div>", unsafe_allow_html=True)
            psi_view = psi_df_dash[["Domínio", "Item", "Status", "Severidade do gap", "Decisão bloqueada", "Ação recomendada"]].copy()
            st.dataframe(psi_view, use_container_width=True, hide_index=True)

    # ==================================================================
    # Action Plan
    # ==================================================================
    elif exec_tab == "Action Plan":
        render_hero_panel(
            title="Action Hub com Priorização e Faixa de Investimento",
            subtitle="As ações são organizadas para execução operacional, com criticidade, responsável, prazo e estimativa financeira de referência.",
            kicker="Execution Readiness",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Estimativa preliminar do Action Hub",
                purpose="Consolidar ações e orçamento conceitual para priorização gerencial.",
                method="Roteamento textual da ação para pacotes CAPEX/OPEX + biblioteca interna AACE/CCPS.",
                references=["AACE Class 5", "CCPS RBPS"],
                assumptions=["Estimativa conceitual preliminar.", "Classificação depende da semântica do texto das ações.", "Faixas precisam recalibração por escopo real."],
                inputs={"Ações consolidadas": len(action_df_dash) if has_actions else 0, "Critérios": "keyword routing + hierarquia", "Saída": "CAPEX/OPEX + faixa min/P50/máx"},
                formula="Ação -> pacote técnico -> recurso -> faixa min/P50/máx",
                note="Use para triagem e priorização, não como orçamento executivo.",
            )

        st.markdown("<div class='panel'><h3>Centro de Comando: Ações de Mitigação (OSHA/CCPS)</h3></div>", unsafe_allow_html=True)

        if has_actions:
            col_acao = get_action_col(action_df_dash)
            abertas_df = _build_open_actions_df(action_df_dash)

            capex_qty = _count_equals(abertas_df, "Recurso", "CAPEX")
            opex_qty = _count_equals(abertas_df, "Recurso", "OPEX")
            orcamento_min = _sum_if_exists(abertas_df, "Custo Min (R$)")
            orcamento_p50 = _sum_if_exists(abertas_df, "Custo P50 (R$)")
            orcamento_max = _sum_if_exists(abertas_df, "Custo Máx (R$)")

            col_chart1, col_chart2, col_budget = st.columns([1.15, 1.15, 1.1])
            with col_chart1:
                st.plotly_chart(render_action_donut(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
            with col_chart2:
                st.plotly_chart(render_action_bar(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
            with col_budget:
                st.markdown(
                    f"""<div style="background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(16,185,129,0.10)); border: 1px solid var(--accent-blue); border-radius: 10px; padding: 20px; height: 250px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #9ca3af; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Orçamento Classe 5 (AACE/CCPS)</div>
                        <div style="color: white; font-size: 1.65rem; font-weight: 800; margin-bottom: 10px;">P50: R$ {orcamento_p50:,.0f}</div>
                        <div style="font-size: 0.82rem; color: #d1d5db; margin-bottom: 16px;">Faixa estimada: R$ {orcamento_min:,.0f} → R$ {orcamento_max:,.0f}</div>
                        <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#f59e0b">● CAPEX:</span> {capex_qty} itens</div>
                        <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#3b82f6">● OPEX:</span> {opex_qty} itens</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

            col_config = {}
            if "Status" in action_df_dash.columns:
                col_config["Status"] = st.column_config.SelectboxColumn("Status", options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"], required=True)
            if "Responsável" in action_df_dash.columns:
                col_config["Responsável"] = st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "Operação", "HSE"])
            if "Prazo (Dias)" in action_df_dash.columns:
                col_config["Prazo (Dias)"] = st.column_config.NumberColumn("Prazo", min_value=1, max_value=365, step=1)
            if "Requer MOC?" in action_df_dash.columns:
                col_config["Requer MOC?"] = st.column_config.CheckboxColumn("Requer MOC?", default=False)
            if col_acao in action_df_dash.columns:
                col_config[col_acao] = st.column_config.TextColumn("Ação Recomendada", width="large")

            disabled_cols = [c for c in [col_acao, "Recurso", "Hierarquia NIOSH", "Pacote AACE", "Custo Min (R$)", "Custo P50 (R$)", "Custo Máx (R$)", "Criticidade"] if c in action_df_dash.columns]
            edited_df = st.data_editor(action_df_dash.copy(), hide_index=True, column_config=col_config, disabled=disabled_cols, use_container_width=True)

            total = len(edited_df)
            fechadas = int((edited_df["Status"] == "Fechado").sum()) if "Status" in edited_df.columns else 0
            st.progress((fechadas / total) if total > 0 else 0.0, text=f"Progresso: {fechadas}/{total} ações concluídas")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button("📥 Baixar Planilha para SAP (CSV)", edited_df.to_csv(index=False).encode("utf-8"), "action_plan.csv", "text/csv", use_container_width=True)
            with btn_col2:
                briefing_text = _build_action_briefing(edited_df=edited_df, profile=profile, node_name=st.session_state.current_node_name, action_col=col_acao)
                st.download_button("📋 Gerar Briefing de Manutenção (TXT)", briefing_text.encode("utf-8"), "ordem_servico.txt", "text/plain", use_container_width=True)
        else:
            render_success_state(title="Nenhuma ação pendente no momento", message="A consolidação atual não identificou ações abertas de segurança de processos para este caso.")

    # ==================================================================
    # Relatório Automático
    # ==================================================================
    elif exec_tab == "Relatório Automático":
        render_hero_panel(title="Relatório Executivo Automatizado", subtitle="Geração rápida de documento consolidado do caso com foco em comunicação técnica e tomada de decisão.", kicker="Reporting")

        report_case_name = st.text_input("Nome do Relatório", value=_safe_case_name(st.session_state.current_case_name, profile))

        if st.button("Gerar Relatório Completo", type="primary"):
            context = {
                "lopa_result": st.session_state.get("lopa_result"),
                "moc_result": st.session_state.get("moc_result"),
                "pssr_result": st.session_state.get("pssr_result"),
                "reactivity_result": st.session_state.get("reactivity_result"),
                "psi_summary": psi_summary,
                "evidence_summary": {
                    "linhas": len(traceability_df) if traceability_df is not None else 0,
                    "oficial": len(getattr(profile, "references", [])),
                    "curado": len(getattr(profile, "source_trace", [])),
                    "revisar": len(getattr(profile, "validation_gaps", [])),
                    "com_link": len(getattr(profile, "storage", {}).get("official_links", {})),
                },
                "evidence_recommendations": list(getattr(profile, "validation_gaps", [])),
                "hazop_priorities": [],
            }
            st.session_state.report_bundle = build_executive_bundle(case_name=_safe_case_name(report_case_name, profile), profile=profile, context=context)
            st.success("Relatório compilado com sucesso.")

        if st.session_state.get("report_bundle"):
            safe_name = _safe_case_name(report_case_name, profile)
            st.download_button("📥 Baixar Documento (HTML)", st.session_state.report_bundle["html"], file_name=f"{safe_name}.html", mime="text/html")

    # ==================================================================
    # Meus Projetos
    # ==================================================================
    elif exec_tab == "Meus Projetos":
        render_hero_panel(title="Gestão de Projetos e Casos", subtitle="Salve e recupere estudos em andamento para manter continuidade analítica, workflow e rastreabilidade do trabalho.", kicker="Project Memory")

        col_save, col_load = st.columns(2)

        with col_save:
            case_name = st.text_input("Salvar Projeto Atual Como:", value=_safe_case_name(st.session_state.current_case_name, profile))
            if st.button("Salvar Progresso", type="primary"):
                case_name_clean = _safe_case_name(case_name, profile)
                _ensure_review_history(case_status=st.session_state.case_status, case_gate=st.session_state.case_decision_gate, actor=st.session_state.case_owner or "analista", note=st.session_state.case_status_note)
                save_case(
                    case_name=case_name_clean, profile=profile, notes="",
                    lopa_result=st.session_state.get("lopa_result"), selected_ipl_names=[], bowtie=bowtie_payload(),
                    moc_result=st.session_state.get("moc_result"), pssr_result=st.session_state.get("pssr_result"),
                    reactivity_result=st.session_state.get("reactivity_result"),
                    current_node_name=st.session_state.current_node_name, case_status=st.session_state.case_status,
                    case_status_note=st.session_state.case_status_note, case_owner=st.session_state.case_owner,
                    case_reviewer=st.session_state.case_reviewer, case_decision_gate=st.session_state.case_decision_gate,
                    review_history=st.session_state.get("review_history", []),
                    traceability_rows=[] if traceability_df is None else traceability_df.to_dict(orient="records"),
                    psi_summary=psi_summary or {}, case_header=case_header,
                )
                st.session_state.current_case_name = case_name_clean
                st.success(f"Projeto '{case_name_clean}' salvo com segurança.")

        cases = list_cases()
        with col_load:
            if cases:
                selected_case = st.selectbox("Carregar Projeto Existente", [c["case_name"] for c in cases])
                if st.button("Carregar Projeto"):
                    loaded = load_case(selected_case)
                    if loaded:
                        apply_loaded_case(loaded)
                        st.rerun()
                    else:
                        st.error("Não foi possível carregar o projeto selecionado.")
            else:
                st.info("Ainda não há projetos salvos.")

        if cases:
            st.dataframe(pd.DataFrame(cases), use_container_width=True, hide_index=True)
        else:
            render_empty_state(title="Nenhum projeto salvo ainda", message="Salve o caso atual para habilitar rastreabilidade, retomada de estudos e comparação entre cenários.")

    # ==================================================================
    # Governança do Caso
    # ==================================================================
    elif exec_tab == "Governança do Caso":
        render_hero_panel(title="Governança, Workflow e Rastreabilidade", subtitle="Consolide status do caso, gate decisório, histórico de revisão e evidências por cálculo para tornar o pacote defensável.", kicker="Case Governance")

        left, right = st.columns([1.05, 1.35])

        with left:
            st.markdown("<div class='panel'><h3>Workflow do Caso</h3></div>", unsafe_allow_html=True)
            st.session_state.case_owner = st.text_input("Owner do caso", value=st.session_state.case_owner)
            st.session_state.case_reviewer = st.text_input("Reviewer / aprovador", value=st.session_state.case_reviewer)
            st.session_state.case_status = st.selectbox("Status do caso", CASE_STATUS_OPTIONS, index=CASE_STATUS_OPTIONS.index(st.session_state.case_status) if st.session_state.case_status in CASE_STATUS_OPTIONS else 0)
            suggested_gate = infer_case_gate(cri_data=cri_data, psi_summary=psi_summary or {}, gaps_criticos=gaps_criticos, moc_result=st.session_state.get("moc_result"), pssr_result=st.session_state.get("pssr_result"), lopa_result=st.session_state.get("lopa_result"))
            st.session_state.case_decision_gate = st.text_input("Gate decisório", value=st.session_state.case_decision_gate or suggested_gate)
            st.session_state.case_status_note = st.text_area("Nota técnica de status", value=st.session_state.case_status_note, height=140, placeholder="Explique por que o caso está neste status, o que bloqueia avanço e o que precisa ser fechado.")

            if st.button("Registrar evento de revisão", type="primary"):
                _ensure_review_history(case_status=st.session_state.case_status, case_gate=st.session_state.case_decision_gate, actor=st.session_state.case_owner or "analista", note=st.session_state.case_status_note)
                st.success("Evento de revisão registrado.")

            st.markdown("<div class='panel'><h3>Resumo de bloqueios</h3></div>", unsafe_allow_html=True)
            blocked = (psi_summary or {}).get("blocked_decisions", [])
            if blocked:
                for item in blocked:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- Nenhuma decisão explicitamente bloqueada pelo PSI.")

        with right:
            st.markdown("<div class='panel'><h3>Snapshot técnico do caso</h3></div>", unsafe_allow_html=True)
            payload = build_case_snapshot_payload(case_header=case_header, profile=profile, psi_summary=psi_summary or {}, cri_data=cri_data, case_status=st.session_state.case_status, case_gate=st.session_state.case_decision_gate, status_note=st.session_state.case_status_note, review_history=st.session_state.get("review_history", []), traceability_df=traceability_df, action_df=action_df_dash)
            snapshot_html = build_case_snapshot_html(payload, traceability_df=traceability_df, action_df=action_df_dash)

            cjson, chtml = st.columns(2)
            with cjson:
                st.download_button("📦 Baixar Snapshot JSON", json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), file_name=f"{_safe_case_name(st.session_state.current_case_name, profile)}_snapshot.json", mime="application/json", use_container_width=True)
            with chtml:
                st.download_button("🧾 Baixar Snapshot HTML", snapshot_html, file_name=f"{_safe_case_name(st.session_state.current_case_name, profile)}_snapshot.html", mime="text/html", use_container_width=True)

            st.markdown("<div class='panel'><h3>Matriz de Rastreabilidade</h3></div>", unsafe_allow_html=True)
            if traceability_df is not None and not getattr(traceability_df, "empty", True):
                st.dataframe(traceability_df, use_container_width=True, hide_index=True)
            else:
                render_empty_state(title="Sem rastreabilidade compilada", message="Ainda não foi possível compilar linhas de rastreabilidade para este caso.", icon="🧭")

            if st.session_state.get("review_history"):
                st.markdown("<div class='panel'><h3>Histórico de revisão</h3></div>", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(st.session_state.review_history), use_container_width=True, hide_index=True)
