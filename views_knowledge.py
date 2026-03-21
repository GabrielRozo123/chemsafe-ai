from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from historical_engine import get_relevant_historical_cases
from ui_components import render_hero_panel, render_evidence_panel
from ui_states import render_empty_state


def render_knowledge_module(profile, menu_styles: dict, norms_db: list[dict]):
    kb_tab = option_menu(
        menu_title=None,
        options=["Normas e Referências", "Incidentes Históricos"],
        icons=["journal-text", "clock-history"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    if kb_tab == "Normas e Referências":
        render_hero_panel(
            title="Biblioteca Curada de Normas e Referências",
            subtitle="Consulta rápida a fundamentos técnicos relevantes para engenharia e segurança de processos. Validar sempre a edição vigente oficial antes de uso formal.",
            kicker="Knowledge Base",
        )

        st.markdown(
            "<div class='note-card'><strong>Importante:</strong> esta é uma base curada interna no app para acelerar consulta. Antes de usar em auditoria, projeto ou aprovação formal, confirme a edição oficial vigente com a fonte publicadora da norma.</div>",
            unsafe_allow_html=True,
        )

        c_search, c_filter, c_area = st.columns([2.2, 1, 1.2])
        search_term = c_search.text_input(
            "🔍 Buscar por código, título ou palavra-chave...",
            placeholder="Ex: API 520, HAZOP, SIS...",
        )
        tag_filter = c_filter.selectbox("Entidade", ["Todos", "API", "OSHA", "IEC", "NFPA", "CCPS", "AACE"])
        area_filter = c_area.selectbox("Área", ["Todas"] + sorted(list({n["area"] for n in norms_db})))

        filtered_normas = []
        for n in norms_db:
            s = search_term.lower().strip()
            matches_search = (
                s in n["id"].lower()
                or s in n["title"].lower()
                or s in n["desc"].lower()
                or s in n["application"].lower()
            ) if s else True
            matches_tag = (tag_filter == "Todos" or n["tag"] == tag_filter)
            matches_area = (area_filter == "Todas" or n["area"] == area_filter)
            if matches_search and matches_tag and matches_area:
                filtered_normas.append(n)

        cols = st.columns(2)
        for idx, norma in enumerate(filtered_normas):
            with cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="doc-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span style="color:#9ca3af; font-size:0.8rem; font-weight:700;">{norma['tag']}</span>
                            <span class="doc-tag">{norma['area']}</span>
                        </div>
                        <span class="doc-title">{norma['id']} — {norma['title']}</span>
                        <p class="doc-desc"><strong>Escopo:</strong> {norma['desc']}</p>
                        <p class="doc-desc"><strong>Aplicação típica:</strong> {norma['application']}</p>
                        <p class="doc-desc"><strong>Nota:</strong> {norma['status_note']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Base interna de normas do app",
                purpose="Permitir consulta rápida e estruturada de referências técnicas relevantes ao fluxo do software.",
                method="Biblioteca local curada embutida no app com tags, área, escopo e aplicação típica.",
                references=[n["id"] for n in filtered_normas[:6]] if filtered_normas else ["CCPS RBPS"],
                assumptions=[
                    "A base não é uma sincronização automática com publishers ou bases regulatórias oficiais.",
                    "A edição vigente deve ser confirmada externamente antes de uso formal.",
                    "A biblioteca foi desenhada para apoio de engenharia e não para substituir gestão documental corporativa.",
                ],
                inputs={
                    "Itens exibidos": len(filtered_normas),
                    "Filtro entidade": tag_filter,
                    "Filtro área": area_filter,
                    "Busca": search_term or "Sem filtro textual",
                },
                formula="Consulta = filtro textual + entidade + área",
                note="Esta biblioteca melhora velocidade e padronização da consulta. Para compliance formal, integrar futuramente com gestão documental oficial da empresa.",
            )

    elif kb_tab == "Incidentes Históricos":
        render_hero_panel(
            title="Incidentes Históricos e Lições Aprendidas",
            subtitle="Contextualize o risco do ativo com eventos históricos relacionados para enriquecer discussão de barreiras, consequências e governança.",
            kicker="Lessons Learned",
        )

        st.markdown("<div class='panel'><h3>📚 Banco de Incidentes e Lições Aprendidas</h3></div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='color: #9ca3af; margin-bottom: 30px;'>Filtrando falhas históricas globais relacionadas à substância <b>{profile.identity.get('name')}</b>.</p>",
            unsafe_allow_html=True,
        )

        relevant_cases = get_relevant_historical_cases(profile)
        if relevant_cases:
            timeline_html = "<div class='history-timeline'>"
            for case in relevant_cases:
                timeline_html += f"""
                <div class='history-item'>
                    <div style='color: #3b82f6; font-weight: 700; font-size: 1.1rem;'>{case['ano']}</div>
                    <div style='font-size: 1.2rem; font-weight: 600; color: #f3f4f6; margin-top: 5px;'>{case['evento']}</div>
                    <div style='background: rgba(30,41,59,0.5); padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 3px solid #f59e0b;'>
                        <strong style='color: #f59e0b; font-size: 0.85rem; text-transform: uppercase;'>Mecanismo de Falha</strong><br>
                        <span style='color: #d1d5db; font-size: 0.95rem; line-height: 1.5;'>{case['mecanismo']}</span>
                    </div>
                </div>
                """
            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.info(f"Nenhum incidente catastrófico catalogado especificamente para {profile.identity.get('name')} na base curada atual.")

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Incidentes históricos relacionados ao ativo",
                purpose="Apoiar análise de lições aprendidas e enriquecer discussão sobre falhas, mecanismos e barreiras relevantes.",
                method="Consulta à base curada interna de incidentes relacionados ao perfil do composto.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Base histórica depende da cobertura interna disponível no projeto.",
                    "Ausência de caso não significa ausência de risco.",
                    "Os eventos exibidos devem ser usados para aprendizado e contextualização, não como substituto de análise local.",
                ],
                inputs={
                    "Ativo": profile.identity.get("name", "—"),
                    "Casos encontrados": len(relevant_cases) if relevant_cases else 0,
                    "Base": "Curada interna",
                },
                formula="Composto/perfil -> busca de casos históricos relacionados",
                note="Os incidentes enriquecem a discussão de risco, mas não substituem estudo específico da instalação.",
            )
