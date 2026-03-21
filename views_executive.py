from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from case_store import list_cases, load_case, save_case
from executive_report import build_executive_bundle
from ui_components import render_hero_panel, render_evidence_panel, metric_card
from ui_states import render_empty_state, render_success_state


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

    if exec_tab == "Dashboard Global":
        render_hero_panel(
            title="Cockpit Executivo de Segurança de Processos",
            subtitle="Visão consolidada da prontidão do caso, gaps críticos e ações abertas para acelerar decisão com governança técnica.",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="KPIs executivos do caso",
                purpose="Este painel consolida prontidão, gaps críticos e pendências para leitura gerencial rápida com foco em PSM e execução.",
                method="Agregação interna de readiness do caso + plano de ação consolidado + criticidade registrada.",
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
                formula="CRI = função consolidada do caso\nGaps críticos = contagem de ações com criticidade Alta/Crítica\nPendências = total de ações abertas/consolidadas",
                note="Painel executivo voltado a priorização. Para aprovação de investimento ou aceite de risco, complementar com revisão técnica formal.",
            )

        st.markdown("<div class='panel'><h3>KPIs Executivos</h3></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("Maturidade Global", f"{cri_data['index']}%", cri_data["color_class"], mono=True), unsafe_allow_html=True)
        c2.markdown(metric_card("Ações Pendentes", str(num_acoes_pendentes), "risk-amber" if num_acoes_pendentes > 0 else "risk-green", mono=True), unsafe_allow_html=True)
        c3.markdown(metric_card("Gaps Críticos", str(gaps_criticos), "risk-red" if gaps_criticos > 0 else "risk-green", mono=True), unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Índice de Prontidão do Caso (CRI)</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_gauge_fn(cri_data["index"], cri_data["band"]), use_container_width=True, theme=None, config={"displayModeBar": False})
        with right:
            st.markdown("<div class='panel'><h3>Distribuição por Pilares</h3></div>", unsafe_allow_html=True)
            st.plotly_chart(render_modern_radar_fn(cri_data), use_container_width=True, theme=None, config={"displayModeBar": False})

    elif exec_tab == "Action Plan":
        render_hero_panel(
            title="Action Hub com Priorização e Faixa de Investimento",
            subtitle="As ações são organizadas para execução operacional, com criticidade, responsável, prazo e estimativa financeira de referência.",
            kicker="Execution Readiness",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Estimativa preliminar do Action Hub",
                purpose="O orçamento consolidado usa classificação por palavras-chave técnicas e faixas conceituais tipo Classe 5 para orientar decisão inicial.",
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
                formula="Ação -> pacote técnico -> recurso -> faixa min/P50/máx\nOrçamento total = soma das ações abertas",
                note="Use este painel para triagem e priorização. Para CAPEX formal, aplicar engenharia de escopo e orçamento detalhado.",
            )

        st.markdown("<div class='panel'><h3>Centro de Comando: Ações de Mitigação (OSHA/CCPS)</h3></div>", unsafe_allow_html=True)

        if has_actions:
            col_acao = get_action_col_fn(action_df_dash)
            abertas_df = action_df_dash[action_df_dash["Status"] != "Fechado"].copy()

            capex_qty = int((abertas_df["Recurso"] == "CAPEX").sum()) if "Recurso" in abertas_df.columns else 0
            opex_qty = int((abertas_df["Recurso"] == "OPEX").sum()) if "Recurso" in abertas_df.columns else 0

            orcamento_min = float(abertas_df["Custo Min (R$)"].sum()) if "Custo Min (R$)" in abertas_df.columns else 0.0
            orcamento_p50 = float(abertas_df["Custo P50 (R$)"].sum()) if "Custo P50 (R$)" in abertas_df.columns else 0.0
            orcamento_max = float(abertas_df["Custo Máx (R$)"].sum()) if "Custo Máx (R$)" in abertas_df.columns else 0.0

            col_chart1, col_chart2, col_budget = st.columns([1.15, 1.15, 1.1])
            with col_chart1:
                st.plotly_chart(render_action_donut_fn(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
            with col_chart2:
                st.plotly_chart(render_action_bar_fn(action_df_dash), use_container_width=True, theme=None, config={"displayModeBar": False})
            with col_budget:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(16,185,129,0.10)); border: 1px solid var(--accent-blue); border-radius: 10px; padding: 20px; height: 250px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="color: #9ca3af; font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 5px;">Orçamento Classe 5 (AACE/CCPS)</div>
                        <div style="color: white; font-size: 1.65rem; font-weight: 800; margin-bottom: 10px;">P50: R$ {orcamento_p50:,.0f}</div>
                        <div style="font-size: 0.82rem; color: #d1d5db; margin-bottom: 16px;">Faixa estimada: R$ {orcamento_min:,.0f} → R$ {orcamento_max:,.0f}</div>
                        <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#f59e0b">● CAPEX:</span> {capex_qty} itens</div>
                        <div style="font-size: 0.85rem; color: #d1d5db;"><span style="color:#3b82f6">● OPEX:</span> {opex_qty} itens</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("<hr style='border-color: #2a3441;'>", unsafe_allow_html=True)

            col_config = {
                "Status": st.column_config.SelectboxColumn("Status", options=["Aberto", "Em Andamento", "Aguardando Verba", "Fechado"], required=True),
                "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Engenharia", "Manutenção", "Operação", "HSE"]),
                "Prazo (Dias)": st.column_config.NumberColumn("Prazo", min_value=1, max_value=365, step=1),
                "Requer MOC?": st.column_config.CheckboxColumn("Requer MOC?", default=False),
                "Recurso": st.column_config.TextColumn("Recurso"),
                "Hierarquia NIOSH": st.column_config.TextColumn("Hierarquia (Auto)", width="medium"),
                "Pacote AACE": st.column_config.TextColumn("Pacote AACE", width="medium"),
                "Custo Min (R$)": st.column_config.NumberColumn("Min", format="R$ %.0f"),
                "Custo P50 (R$)": st.column_config.NumberColumn("P50", format="R$ %.0f"),
                "Custo Máx (R$)": st.column_config.NumberColumn("Máx", format="R$ %.0f"),
                col_acao: st.column_config.TextColumn("Ação Recomendada", width="large"),
            }
            if "Criticidade" in action_df_dash.columns:
                col_config["Criticidade"] = st.column_config.TextColumn("Criticidade")

            disabled_cols = [col_acao, "Recurso", "Hierarquia NIOSH", "Pacote AACE", "Custo Min (R$)", "Custo P50 (R$)", "Custo Máx (R$)"]
            if "Criticidade" in action_df_dash.columns:
                disabled_cols.append("Criticidade")

            edited_df = st.data_editor(
                action_df_dash,
                width="stretch",
                hide_index=True,
                column_config=col_config,
                disabled=disabled_cols,
            )

            fechadas = len(edited_df[edited_df["Status"] == "Fechado"])
            total = len(edited_df)
            st.progress(fechadas / total if total > 0 else 0.0, text=f"Progresso: {fechadas}/{total} ações concluídas")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button(
                    "📥 Baixar Planilha para SAP (CSV)",
                    edited_df.to_csv(index=False).encode("utf-8"),
                    "action_plan.csv",
                    "text/csv",
                    use_container_width=True,
                )

            with btn_col2:
                briefing_text = (
                    f"ORDEM DE SERVIÇO - SEGURANÇA DE PROCESSOS\n"
                    f"Ativo: {profile.identity.get('name')}\n"
                    f"Topologia: {st.session_state.current_node_name}\n"
                    + "=" * 50
                    + "\n\n"
                )
                for resp in edited_df[edited_df["Status"] != "Fechado"]["Responsável"].unique():
                    briefing_text += f"[EQUIPE: {resp.upper()}]\n"
                    acoes_resp = edited_df[(edited_df["Status"] != "Fechado") & (edited_df["Responsável"] == resp)]
                    for _, row in acoes_resp.iterrows():
                        crit = row.get("Criticidade", "Normal")
                        briefing_text += f"- [{crit}] {row[col_acao]} (Prazo: {row['Prazo (Dias)']} dias)\n"
                    briefing_text += "\n"

                st.download_button(
                    "📋 Gerar Briefing de Manutenção (TXT)",
                    briefing_text.encode("utf-8"),
                    "ordem_servico.txt",
                    "text/plain",
                    use_container_width=True,
                )
                else:
            render_success_state(
                title="Nenhuma ação pendente no momento",
                message="A consolidação atual não identificou ações abertas de segurança de processos para este caso.",
            )

    elif exec_tab == "Relatório Automático":
        render_hero_panel(
            title="Relatório Executivo Automatizado",
            subtitle="Geração rápida de documento consolidado do caso com foco em comunicação técnica e tomada de decisão.",
            kicker="Reporting",
        )
        st.markdown("<div class='panel'><h3>Gerador de Relatório Executivo</h3></div>", unsafe_allow_html=True)
        report_case_name = st.text_input("Nome do Relatório", value=st.session_state.current_case_name or profile.identity.get("name", "Caso"))
        if st.button("Gerar Relatório Completo", type="primary"):
            st.session_state.report_bundle = build_executive_bundle(
                case_name=report_case_name,
                profile=profile,
                context={"lopa_result": st.session_state.get("lopa_result")},
            )
            st.success("Relatório Compilado!")
        if st.session_state.get("report_bundle"):
            st.download_button("📥 Baixar Documento (HTML)", st.session_state.report_bundle["html"], file_name=f"{report_case_name}.html")

    elif exec_tab == "Meus Projetos":
        render_hero_panel(
            title="Gestão de Projetos e Casos",
            subtitle="Salve e recupere estudos em andamento para manter continuidade analítica e rastreabilidade do trabalho.",
            kicker="Project Memory",
        )
        st.markdown("<div class='panel'><h3>Gestão de Projetos</h3></div>", unsafe_allow_html=True)
        col_save, col_load = st.columns(2)
        with col_save:
            case_name = st.text_input("Salvar Projeto Atual Como:")
            if st.button("Salvar Progresso", type="primary"):
                save_case(case_name, profile, "", st.session_state.get("lopa_result"), [], bowtie_payload_fn(), None, None, None)
                st.session_state.current_case_name = case_name
                st.success("Salvo com segurança!")
        cases = list_cases()
        if cases:
            with col_load:
                selected_case = st.selectbox("Carregar Projeto Existente", [c["case_name"] for c in cases])
                if st.button("Carregar Projeto"):
                    apply_loaded_case_fn(load_case(selected_case))
                    st.rerun()
