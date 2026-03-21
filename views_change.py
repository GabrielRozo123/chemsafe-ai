from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from moc_engine import evaluate_moc
from pssr_engine import evaluate_pssr
from ui_components import render_hero_panel, render_evidence_panel


def render_change_module(profile, menu_styles: dict):
    chg_tab = option_menu(
        menu_title=None,
        options=["MOC (Modificação)", "PSSR (Inspeção Pré-Partida)"],
        icons=["arrow-repeat", "check2-square"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    if chg_tab == "MOC (Modificação)":
        render_hero_panel(
            title="Avaliação de Gestão de Mudança",
            subtitle="Classificação inicial de mudança com foco em impacto técnico, proteções afetadas e necessidade de governança adicional.",
            kicker="Management of Change",
        )
        st.markdown("<div class='panel'><h3>🔄 Avaliação de Gestão de Mudança</h3></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            change_type = st.selectbox(
                "Escopo da Mudança",
                ["Mudança química", "Mudança de equipamento", "Mudança de procedimento"],
            )
            impacts = st.multiselect(
                "Áreas Críticas Afetadas",
                ["Química / composição", "Pressão", "Temperatura", "Alívio / PSV"],
            )
        with c2:
            st.write("Fatores Restritivos:")
            p1 = st.checkbox("Mudança de Caráter Temporário")
            p2 = st.checkbox("Bypass ou Override em Sistema de Segurança")

        if st.button("Protocolar MOC para Análise", type="primary"):
            st.session_state.moc_result = evaluate_moc(
                profile,
                change_type,
                impacts,
                "",
                temporary=p1,
                protections_changed=p2,
                bypass_or_override=False,
            )
            st.success("MOC submetido e classificado.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Classificação inicial de MOC",
                purpose="Ajudar a equipe a identificar se a mudança demanda fluxo formal de gestão, revisão de barreiras e governança complementar.",
                method="Triagem assistida por tipo de mudança, impactos críticos e condições restritivas selecionadas.",
                references=["OSHA 1910.119", "CCPS RBPS"],
                assumptions=[
                    "A decisão final de MOC deve seguir o procedimento interno da organização.",
                    "A triagem depende da completude das respostas fornecidas pelo usuário.",
                    "Mudanças complexas podem exigir revisão multidisciplinar adicional.",
                ],
                inputs={
                    "Tipo": change_type,
                    "Impactos": ", ".join(impacts) if impacts else "Nenhum selecionado",
                    "Temporária": "Sim" if p1 else "Não",
                    "Override/bypass": "Sim" if p2 else "Não",
                },
                formula="Mudança + impactos + restrições -> necessidade de governança adicional",
                note="Use a saída como triagem inicial. Abertura formal de MOC deve obedecer o procedimento documentado da empresa.",
            )

    elif chg_tab == "PSSR (Inspeção Pré-Partida)":
        render_hero_panel(
            title="Checklist de Pré-Partida Segura",
            subtitle="Consolide verificações críticas antes de partida ou retorno à operação após modificação relevante.",
            kicker="Pre-Startup Safety Review",
        )
        st.markdown("<div class='panel'><h3>✅ Checklist de Partida Segura</h3></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            d1 = st.checkbox("Construção validada conforme diagrama P&ID")
            d2 = st.checkbox("Procedimentos de emergência revisados e na sala de controle")
        with c2:
            d4 = st.checkbox("Malhas do SIS e PSVs inspecionadas e destravadas")
            d5 = st.checkbox("Matriz de Causa e Efeito validada em TAF (Teste de Aceitação)")

        if st.button("Rodar Assinatura PSSR", type="primary"):
            st.session_state.pssr_result = evaluate_pssr(
                design_ok=d1,
                procedures_ok=d2,
                training_ok=True,
                relief_verified=d4,
                alarms_tested=d5,
                startup_authorized=True,
                pha_or_moc_ok=True,
                mi_ready=True,
                emergency_ready=True,
                scope_label="PSSR",
            )
            st.success("Status operacional emitido.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Checklist PSSR assistido",
                purpose="Apoiar a revisão pré-partida de itens críticos de prontidão operacional.",
                method="Checklist estruturado com foco em construção, procedimentos, proteções e testes de automação.",
                references=["OSHA 1910.119", "CCPS RBPS"],
                assumptions=[
                    "Checklist é assistivo e não substitui a rotina formal da organização.",
                    "Itens não marcados exigem avaliação antes da liberação.",
                    "Pode haver requisitos locais adicionais de engenharia, manutenção e operação.",
                ],
                inputs={
                    "P&ID validado": "Sim" if d1 else "Não",
                    "Procedimentos revisados": "Sim" if d2 else "Não",
                    "SIS/PSVs verificados": "Sim" if d4 else "Não",
                    "C&E validada": "Sim" if d5 else "Não",
                },
                formula="Checklist crítico -> prontidão operacional preliminar",
                note="Use como apoio visual. A autorização de partida deve seguir o fluxo formal de PSSR da planta.",
            )
