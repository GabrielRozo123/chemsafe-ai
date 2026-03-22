from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from case_store import list_cases, load_case, save_case
from executive_report import build_executive_bundle
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


def _count_open_actions(df) -> int:
    if df is None or getattr(df, "empty", True):
        return 0
    if "Status" not in df.columns:
        return len(df)
    return int((df["Status"] != "Fechado").sum())


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

    if "Status" in edited_df.columns:
        working_df = edited_df[edited_df["Status"] != "Fechado"].copy()
    else:
        working_df = edited_df.copy()

    if working_df.empty:
        lines.append("Nenhuma ação aberta no momento.")
        return "\n".join(lines)

    if "Responsável" in working_df.columns:
        responsaveis = [r for r in working_df["Responsável"].dropna().unique().tolist() if str(r).strip()]
    else:
        responsaveis = ["Equipe responsável"]

    for resp in responsaveis:
        lines.append(f"[EQUIPE: {str(resp).upper()}]")

        if "Responsável" in working_df.columns:
            acoes_resp = working_df[working_df["Responsável"] == resp]
        else:
            acoes_resp = working_df

        for _, row in acoes_resp.iterrows():
            criticidade = row["Criticidade"] if "Criticidade" in row.index else "Normal"
            prazo = row["Prazo (Dias)"] if "Prazo (Dias)" in row.index else "N/A"
            status = row["Status"] if "Status" in row.index else "Aberto"
            acao = row[action_col] if action_col in row.index else "Ação não especificada"

            lines.append(
                f"- [{criticidade}] {acao} | Prazo: {prazo} dias | Status: {status}"
            )
        lines.append("")

    return "\n".join(lines)


def render_executive_module(
    profile,
    cri_data: dict,
    action_df_dash,
    has_actions: bool,
    num_acoes_pendentes: int,
    gaps_criticos: int,
    menu_styles: dict,
    bowtie_payload_fn,
    apply_loaded_case_fn,
    render_modern_gauge_fn,
    render_modern_radar_fn,
    render_action_donut_fn,
    render_action_bar_fn,
    get_action_col_fn,
):
    exec_tab = option_menu(
        menu_title=None,
        options=["Dashboard Global", "Action Plan", "Relatório Automático", "Meus Projetos"],
        icons=["bar-chart", "list-check", "file-earmark-pdf", "folder2-open"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    # ==========================================================================
    # TAB 1: DASHBOARD GLOBAL
    # ==========================================================================
    if exec_tab == "Dashboard Global":
        render_hero_panel(
            title="Cockpit Executivo de Segurança de Processos",
            subtitle=(
                "Visão consolidada da prontidão do caso, gaps críticos e ações abertas "
                "para acelerar decisão com governança técnica."
            ),
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="KPIs executivos do caso",
                purpose=(
                    "Este painel consolida prontidão, gaps críticos e pendências para "
                    "leitura gerencial rápida com foco em PSM e execução."
                ),
                method=(
                    "Agregação interna de readiness do caso + plano de ação consolidado "
                    "+ criticidade registrada."
                ),
                references=["CCPS RBPS", "OSHA 1910.119", "AACE Class 5"],
                assumptions=[
                    "Indicadores têm caráter gerencial e de priorização, não substituindo estudo formal detalhado.",
                    "A maturidade global depende da qualidade dos dados alimentados no caso.",
                    "A criticidade consolidada reflete o estado atual do conjunto de ações disponível no app.",
                ],
                inputs={
                    "Maturidade global": f"{cri_data.get('index', 0)}%",
                    "Ações pendentes": num_acoes_pendentes,
                    "Gaps críticos": gaps_criticos,
                    "Modo auditoria": "Ativo",
                },
                formula=(
                    "CRI = função consolidada do caso\n"
                    "Gaps críticos = contagem de ações com criticidade Alta/Crítica\n"
                    "Pendências = total de ações abertas/consolidadas"
                ),
                note=(
                    "Painel executivo voltado a priorização. Para aprovação de investimento "
                    "ou aceite de risco, complementar com revisão técnica formal."
                ),
            )

        st.markdown("<div class='panel'><h3>KPIs Executivos</h3></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                metric_card(
                    "Maturidade Global",
                    f"{cri_data.get('index', 0)}%",
                    cri_data.get("color_class", "risk-blue"),
                    mono=True,
                ),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                metric_card(
                    "Ações Pendentes",
                    str(num_acoes_pendentes),
                    "risk-amber" if num_acoes_pendentes > 0 else "risk-green",
                    mono=True,
                ),
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                metric_card(
                    "Gaps Críticos",
                    str(gaps_criticos),
                    "risk-red" if gaps_criticos > 0 else "risk-green",
                    mono=True,
                ),
                unsafe_allow_html=True,
            )

        left, right = st.columns(2)

        with left:
            st.markdown(
                "<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                render_modern_gauge_fn(cri_data.get("index", 0), cri_data.get("band", "N/A")),
                use_container_width=True,
                theme=None,
                config={"displayModeBar": False},
            )

        with right:
            st.markdown(
                "<div class='panel'><h3>Distribuição por Pilares</h3></div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                render_modern_radar_fn(cri_data),
                use_container_width=True,
                theme=None,
                config={"displayModeBar": False},
            )

    # ==========================================================================
    # TAB 2: ACTION PLAN
    # ==========================================================================
    elif exec_tab == "Action Plan":
        render_hero_panel(
            title="Action Hub com Priorização e Faixa de Investimento",
            subtitle=(
                "As ações são organizadas para execução operacional, com criticidade, "
                "responsável, prazo e estimativa financeira de referência."
            ),
            kicker="Execution Readiness",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Estimativa preliminar do Action Hub",
                purpose=(
                    "O orçamento consolidado usa classificação por palavras-chave técnicas "
                    "e faixas conceituais tipo Classe 5 para orientar decisão inicial."
                ),
                method="Roteamento textual da ação para pacotes CAPEX/OPEX + biblioteca interna AACE/CCPS.",
                references=["AACE Class 5", "CCPS RBPS"],
                assumptions=[
                    "Estimativa conceitual preliminar, sem caráter de proposta comercial nem orçamento executivo.",
                    "Classificação depende da qualidade semântica do texto da ação.",
                    "Faixas devem ser recalibradas à realidade da planta, fornecedor e escopo final.",
                ],
                inputs={
                    "Ações consolidadas": len(action_df_dash) if has_actions else 0,
                    "Critérios": "keyword routing + hierarquia",
                    "Saída": "CAPEX/OPEX + faixa min/P50/máx",
                },
                formula=(
                    "Ação -> pacote técnico -> recurso -> faixa min/P50/máx\n"
                    "Orçamento total = soma das ações abertas"
                ),
                note=(
                    "Use este painel para triagem e priorização. Para CAPEX formal, "
                    "aplicar engenharia de escopo e orçamento detalhado."
                ),
            )

        st.markdown(
            "<div class='panel'><h3>Centro de Comando: Ações de Mitigação (OSHA/CCPS)</h3></div>",
            unsafe_allow_html=True,
        )

        if has_actions:
            col_acao = get_action_col_fn(action_df_dash)
            abertas_df = _build_open_actions_df(action_df_dash)

            capex_qty = _count_equals(abertas_df, "Recurso", "CAPEX")
            opex_qty = _count_equals(abertas_df, "Recurso", "OPEX")

            orcamento_min = _sum_if_exists(abertas_df, "Custo Min (R$)")
            orcamento_p50 = _sum_if_exists(abertas_df, "Custo P50 (R$)")
            orcamento_max = _sum_if_exists(abertas_df, "Custo Máx (R$)")

            col_chart1, col_chart2, col_budget = st.columns([1.15, 1.15, 1.1])

            with col_chart1:
                st.plotly_chart(
                    render_action_donut_fn(action_df_dash),
                    use_container_width=True,
                    theme=None,
                    config={"displayModeBar": False},
                )

            with col_chart2:
                st.plotly_chart(
                    render_action_bar_fn(action_df_dash),
                    use_container_width=True,
                    theme=None,
                    config={"displayModeBar": False},
                )

            with col_budget:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(16,185,129,0.10));
                        border: 1px solid var(--accent-blue);
                        border-radius: 10px;
                        padding: 20px;
                        height: 250px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <div style="color: #9ca3af; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">
                            Orçamento Classe 5 (AACE/CCPS)
                        </div>
                        <div style="color: white; font-size: 1.65rem; font-weight: 800; margin-bottom: 10px;">
                            P50: R$ {orcamento_p50:,.0f}
                        </div>
                        <div style="font-size: 0.82rem; color: #d1d5db; margin-bottom: 16px;">
                            Faixa estimada: R$ {orcamento_min:,.0f} → R$ {orcamento_max:,.0f}
                        </div>
                        <div style="font-size: 0.85rem; color: #d1d5db;">
                            <span style="color:#f59e0b">● CAPEX:</span> {capex_qty} itens
                        </div>
                        <div style="font-size: 0.85rem; color: #d1d5db;">
                            <span style="color:#3b82f6">● OPEX:</span> {opex_qty} itens
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<hr style='border-color: #2a3441;'>", unsafe_allow_html=True)

            col_config = {}
            if "Status" in action_df_dash.columns:
                col_config["Status"] = st.column_config.SelectboxColumn(
                    "Status",
                    options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"],
                    required=True,
                )
            if "Responsável" in action_df_dash.columns:
                col_config["Responsável"] = st.column_config.SelectboxColumn(
                    "Responsável",
                    options=["Engenharia", "Manutenção", "Operação", "HSE"],
                )
            if "Prazo (Dias)" in action_df_dash.columns:
                col_config["Prazo (Dias)"] = st.column_config.NumberColumn(
                    "Prazo",
                    min_value=1,
                    max_value=365,
                    step=1,
                )
            if "Requer MOC?" in action_df_dash.columns:
                col_config["Requer MOC?"] = st.column_config.CheckboxColumn(
                    "Requer MOC?",
                    default=False,
                )
            if "Recurso" in action_df_dash.columns:
                col_config["Recurso"] = st.column_config.TextColumn("Recurso")
            if "Hierarquia NIOSH" in action_df_dash.columns:
                col_config["Hierarquia NIOSH"] = st.column_config.TextColumn(
                    "Hierarquia (Auto)",
                    width="medium",
                )
            if "Pacote AACE" in action_df_dash.columns:
                col_config["Pacote AACE"] = st.column_config.TextColumn(
                    "Pacote AACE",
                    width="medium",
                )
            if "Custo Min (R$)" in action_df_dash.columns:
                col_config["Custo Min (R$)"] = st.column_config.NumberColumn(
                    "Min",
                    format="R$ %.0f",
                )
            if "Custo P50 (R$)" in action_df_dash.columns:
                col_config["Custo P50 (R$)"] = st.column_config.NumberColumn(
                    "P50",
                    format="R$ %.0f",
                )
            if "Custo Máx (R$)" in action_df_dash.columns:
                col_config["Custo Máx (R$)"] = st.column_config.NumberColumn(
                    "Máx",
                    format="R$ %.0f",
                )
            if col_acao in action_df_dash.columns:
                col_config[col_acao] = st.column_config.TextColumn(
                    "Ação Recomendada",
                    width="large",
                )
            if "Criticidade" in action_df_dash.columns:
                col_config["Criticidade"] = st.column_config.TextColumn("Criticidade")

            disabled_cols = []
            for col in [
                col_acao,
                "Recurso",
                "Hierarquia NIOSH",
                "Pacote AACE",
                "Custo Min (R$)",
                "Custo P50 (R$)",
                "Custo Máx (R$)",
                "Criticidade",
            ]:
                if col in action_df_dash.columns:
                    disabled_cols.append(col)

            edited_df = st.data_editor(
                action_df_dash.copy(),
                hide_index=True,
                column_config=col_config,
                disabled=disabled_cols,
                use_container_width=True,
            )

            total = len(edited_df)
            if "Status" in edited_df.columns:
                fechadas = int((edited_df["Status"] == "Fechado").sum())
            else:
                fechadas = 0

            progresso = (fechadas / total) if total > 0 else 0.0
            st.progress(progresso, text=f"Progresso: {fechadas}/{total} ações concluídas")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                st.download_button(
                    label="📥 Baixar Planilha para SAP (CSV)",
                    data=edited_df.to_csv(index=False).encode("utf-8"),
                    file_name="action_plan.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with btn_col2:
                briefing_text = _build_action_briefing(
                    edited_df=edited_df,
                    profile=profile,
                    node_name=st.session_state.current_node_name,
                    action_col=col_acao,
                )
                st.download_button(
                    label="📋 Gerar Briefing de Manutenção (TXT)",
                    data=briefing_text.encode("utf-8"),
                    file_name="ordem_servico.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        else:
            render_success_state(
                title="Nenhuma ação pendente no momento",
                message=(
                    "A consolidação atual não identificou ações abertas de segurança "
                    "de processos para este caso."
                ),
            )

    # ==========================================================================
    # TAB 3: RELATÓRIO AUTOMÁTICO
    # ==========================================================================
    elif exec_tab == "Relatório Automático":
        render_hero_panel(
            title="Relatório Executivo Automatizado",
            subtitle=(
                "Geração rápida de documento consolidado do caso com foco em "
                "comunicação técnica e tomada de decisão."
            ),
            kicker="Reporting",
        )

        st.markdown(
            "<div class='panel'><h3>Gerador de Relatório Executivo</h3></div>",
            unsafe_allow_html=True,
        )

        report_case_name = st.text_input(
            "Nome do Relatório",
            value=_safe_case_name(st.session_state.current_case_name, profile),
        )

        if st.button("Gerar Relatório Completo", type="primary"):
            context = {
                "lopa_result": st.session_state.get("lopa_result"),
                "moc_result": st.session_state.get("moc_result"),
                "pssr_result": st.session_state.get("pssr_result"),
                "reactivity_result": st.session_state.get("reactivity_result"),
                "psi_summary": st.session_state.get("psi_summary"),
                "evidence_summary": st.session_state.get("evidence_summary", {}),
                "evidence_recommendations": st.session_state.get("evidence_recommendations", []),
                "hazop_priorities": st.session_state.get("hazop_priorities", []),
            }

            st.session_state.report_bundle = build_executive_bundle(
                case_name=_safe_case_name(report_case_name, profile),
                profile=profile,
                context=context,
            )
            st.success("Relatório compilado com sucesso.")

        if st.session_state.get("report_bundle"):
            safe_name = _safe_case_name(report_case_name, profile)
            st.download_button(
                label="📥 Baixar Documento (HTML)",
                data=st.session_state.report_bundle["html"],
                file_name=f"{safe_name}.html",
                mime="text/html",
            )

    # ==========================================================================
    # TAB 4: MEUS PROJETOS
    # ==========================================================================
    elif exec_tab == "Meus Projetos":
        render_hero_panel(
            title="Gestão de Projetos e Casos",
            subtitle=(
                "Salve e recupere estudos em andamento para manter continuidade "
                "analítica e rastreabilidade do trabalho."
            ),
            kicker="Project Memory",
        )

        st.markdown("<div class='panel'><h3>Gestão de Projetos</h3></div>", unsafe_allow_html=True)

        col_save, col_load = st.columns(2)

        with col_save:
            case_name = st.text_input(
                "Salvar Projeto Atual Como:",
                value=_safe_case_name(st.session_state.current_case_name, profile),
            )
            if st.button("Salvar Progresso", type="primary"):
                case_name_clean = _safe_case_name(case_name, profile)

                save_case(
                    case_name=case_name_clean,
                    profile=profile,
                    notes="",
                    lopa_result=st.session_state.get("lopa_result"),
                    selected_ipl_names=[],
                    bowtie=bowtie_payload_fn(),
                    moc_result=st.session_state.get("moc_result"),
                    pssr_result=st.session_state.get("pssr_result"),
                    reactivity_result=st.session_state.get("reactivity_result"),
                )
                st.session_state.current_case_name = case_name_clean
                st.success(f"Projeto '{case_name_clean}' salvo com segurança.")

        cases = list_cases()

        with col_load:
            if cases:
                selected_case = st.selectbox(
                    "Carregar Projeto Existente",
                    [c["case_name"] for c in cases],
                )
                if st.button("Carregar Projeto"):
                    loaded = load_case(selected_case)
                    if loaded:
                        apply_loaded_case_fn(loaded)
                        st.rerun()
                    else:
                        st.error("Não foi possível carregar o projeto selecionado.")
            else:
                st.info("Ainda não há projetos salvos.")

        st.markdown("<br>", unsafe_allow_html=True)

        if cases:
            st.markdown(
                "<div class='panel'><h3>Projetos Salvos</h3></div>",
                unsafe_allow_html=True,
            )
            st.dataframe(cases, use_container_width=True, hide_index=True)
        else:
            render_empty_state(
                title="Nenhum projeto salvo ainda",
                message=(
                    "Salve o caso atual para habilitar rastreabilidade, retomada de estudos "
                    "e comparação entre cenários."
                ),
            )
