from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from chart_utils import safe_float, render_flammability_envelope
from dense_gas_router import classify_dispersion_mode
from psv_engine import size_psv_gas
from runaway_engine import calculate_tmr_adiabatic
from ui_components import render_hero_panel, render_evidence_panel, metric_card
from ui_formatters import format_identity_df, format_physchem_df


def render_engineering_module(profile, menu_styles: dict):
    eng_tab = option_menu(
        menu_title=None,
        options=["Termodinâmica", "Inertização (NFPA 69)", "Emergências (PSV/Runaway)"],
        icons=["thermometer", "cone-striped", "speedometer2"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    if eng_tab == "Termodinâmica":
        render_hero_panel(
            title="Base de Propriedades e Comportamento do Ativo",
            subtitle="Leitura rápida do composto com foco em risco de processo, propriedades-chave e suporte a decisões de projeto e operação.",
            kicker="Engineering View",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Perfil do composto e classificação de dispersão",
                purpose="Painel de leitura rápida para apoiar engenharia, segurança de processos e resposta inicial sobre o ativo analisado.",
                method="Perfil do composto gerado pelo motor do app + classificação de dispersão por regras internas.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Os dados do composto dependem da qualidade do identificador usado na busca.",
                    "A classificação de dispersão é assistiva e não substitui modelagem formal de dispersão.",
                    "Validação adicional é necessária para estudo QRA ou projeto de mitigação.",
                ],
                inputs={
                    "Ativo": profile.identity.get("name", "—"),
                    "CAS": profile.identity.get("cas", "—"),
                    "Peso molecular": f"{profile.identity.get('molecular_weight', '—')} g/mol",
                    "Confiança do perfil": f"{safe_float(getattr(profile, 'confidence_score', 0)):.0f}%",
                },
                formula="Perfil = identidade + perigos + propriedades\nDispersão = classificação assistida por regras do motor interno",
                note="Use este painel como base de triagem técnica. Para engenharia final, confirmar dados físico-químicos com referência oficial adotada pela empresa.",
            )

        dispersion_mode = classify_dispersion_mode(profile)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(metric_card("Ativo Base", profile.identity.get("name", "—")), unsafe_allow_html=True)
        c2.markdown(metric_card("Peso Molar", f"{profile.identity.get('molecular_weight', '—')} g/mol", mono=True), unsafe_allow_html=True)
        c3.markdown(metric_card("Dispersão", dispersion_mode["label"]), unsafe_allow_html=True)
        c4.markdown(metric_card("Confiança", f"{getattr(profile, 'confidence_score', 0):.0f}%", mono=True), unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            st.markdown("<div class='panel'><h3>Identidade e Perigos GHS</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_identity_df(profile), width="stretch", hide_index=True)
            for hz in profile.hazards:
                st.error(hz)
        with right:
            st.markdown("<div class='panel'><h3>Propriedades Base</h3></div>", unsafe_allow_html=True)
            st.dataframe(format_physchem_df(profile), width="stretch", hide_index=True)

    elif eng_tab == "Inertização (NFPA 69)":
        render_hero_panel(
            title="Envelope de Inflamabilidade e Faixa Operacional de Purga",
            subtitle="Ferramenta visual para raciocínio preliminar de inertização, envelope seguro e margem operacional durante partida e parada.",
            kicker="Explosion Prevention",
        )

        lfl_val = safe_float(profile.limit("LEL_vol", 5.0), 5.0)
        ufl_val = safe_float(profile.limit("UEL_vol", 15.0), 15.0)

        st.markdown("<div class='panel'><h3>⚠️ Envelope de Inflamabilidade & Purga de Reatores</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Calcule a atmosfera segura durante partidas e paradas. Para evitar a mistura explosiva, a concentração de O₂ deve operar abaixo da <b>Limiting Oxygen Concentration (LOC)</b>.</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("#### Parâmetros do Composto")
            lfl = st.number_input("LFL (% Combustível)", value=lfl_val)
            ufl = st.number_input("UFL (% Combustível)", value=ufl_val)
            loc = st.number_input("LOC (% Oxigênio)", value=10.5, help="Concentração limite de O2 segundo NFPA 69")
            st.metric("Margem de Segurança Sugerida (Alarme Alto)", f"O₂ < {loc * 0.6:.1f}%")

        with c2:
            fig_flam = render_flammability_envelope(lfl, ufl, loc)
            st.plotly_chart(fig_flam, use_container_width=True, theme=None, config={"displayModeBar": False})

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Envelope O₂ vs combustível para inertização",
                purpose="Apoiar decisão preliminar sobre faixa segura de operação abaixo da concentração limite de oxidante.",
                method="Representação gráfica simplificada do envelope com LFL, UFL e LOC informados/estimados.",
                references=["NFPA 69"],
                assumptions=[
                    "Modelo visual simplificado para suporte inicial, não substituindo validação detalhada do sistema real.",
                    "LFL, UFL e LOC devem ser confirmados para mistura, temperatura, pressão e diluentes específicos.",
                    "A margem de alarme aqui é conservadora e assistiva.",
                ],
                inputs={
                    "LFL": f"{lfl:.2f} % vol combustível",
                    "UFL": f"{ufl:.2f} % vol combustível",
                    "LOC": f"{loc:.2f} % vol O₂",
                    "Margem sugerida": f"O₂ < {loc*0.6:.2f} %",
                },
                formula="Operação segura preliminar: O₂ < LOC\nMargem interna sugerida no painel: O₂ < 0.6 × LOC",
                note="Use o gráfico para raciocínio preliminar. Em projeto ou autorização operacional, confirmar LOC, estratégia de purga, instrumentação e lógica permissiva.",
            )

    elif eng_tab == "Emergências (PSV/Runaway)":
        render_hero_panel(
            title="Toolkit de Emergências de Processo",
            subtitle="Ferramentas rápidas para sizing preliminar de alívio e leitura inicial de runaway térmico em modo de apoio à decisão.",
            kicker="Emergency Engineering",
        )

        st.markdown("<div class='panel'><h3>Cálculos de Emergência</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Os cálculos abaixo são preliminares e devem ser usados como apoio à triagem de engenharia. Para projeto final, revisar cenários, hipóteses e referência normativa oficial.</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.markdown("#### 🔥 Dimensionamento de Alívio (API 520)")
                with st.popover("⚙️ Configurar Parâmetros da Válvula"):
                    w = st.number_input("Vazão (kg/h)", 10000.0)
                    p = st.number_input("Pressão Setpoint (kPag)", 500.0)
                    t_rel = st.number_input("Temp. no Alívio (°C)", 50.0)

                if st.button("Executar Sizing", use_container_width=True, type="primary"):
                    mw = safe_float(profile.identity.get("molecular_weight", 28.0), 28.0)
                    res = size_psv_gas(w, t_rel, p, 1.0, mw)
                    st.session_state.psv_result = res
                    st.session_state.psv_inputs = {
                        "Vazão": f"{w:.2f} kg/h",
                        "Set pressure": f"{p:.2f} kPag",
                        "Temperatura": f"{t_rel:.2f} °C",
                        "Peso molecular": f"{mw:.2f} g/mol",
                    }
                    st.success(f"Orifício preliminar: **Letra {res['api_letter']}** ({res['api_area_mm2']} mm²)")

            if st.session_state.get("psv_result"):
                res = st.session_state.psv_result
                st.info(f"Resultado armazenado: API Letter **{res['api_letter']}** | Área **{res['api_area_mm2']} mm²**")
                if st.session_state.audit_mode:
                    render_evidence_panel(
                        title="Sizing preliminar de alívio gasoso",
                        purpose="Fornecer leitura rápida do orifício API preliminar para triagem de engenharia.",
                        method="Rotina interna de cálculo para gás com saída em letra/área API.",
                        references=["API 520", "API 521"],
                        assumptions=[
                            "Leitura preliminar para triagem. Não substitui definição completa de cenário de alívio.",
                            "Cenário de contingência, backpressure, propriedades reais e acúmulo devem ser revisados externamente.",
                            "Confirmar unidade, estado do fluido e critério aplicável ao caso real.",
                        ],
                        inputs=st.session_state.get("psv_inputs"),
                        formula="A_orifício = f(vazão, pressão, temperatura, MW, coeficientes e hipótese de gás)",
                        note="Resultado útil para screening inicial. Para projeto final, revisar cenário, fluidodinâmica e exigências normativas detalhadas.",
                    )

        with c2:
            with st.container(border=True):
                st.markdown("#### ⚡ Runaway Térmico (Triagem)")
                with st.popover("⚙️ Configurar Cinética"):
                    t0 = st.number_input("Temp. Processo (°C)", 80.0)
                    ea = st.number_input("Energia Ativação (kJ/mol)", 100.0)

                if st.button("Estimar TMR (Time to Maximum Rate)", use_container_width=True):
                    res = calculate_tmr_adiabatic(t0, ea, 1e12, 1500, 2.5)
                    st.session_state.tmr_result = res
                    st.session_state.tmr_inputs = {
                        "Temperatura inicial": f"{t0:.2f} °C",
                        "Energia de ativação": f"{ea:.2f} kJ/mol",
                        "Modelo": "Triagem adiabática",
                    }
                    st.error(f"Tempo estimado p/ máximo térmico: **{res['tmr_min']:.1f} min**")

            if st.session_state.get("tmr_result"):
                res = st.session_state.tmr_result
                st.warning(f"Resultado armazenado: TMR estimado **{res['tmr_min']:.1f} min**")
                if st.session_state.audit_mode:
                    render_evidence_panel(
                        title="Triagem de runaway térmico",
                        purpose="Estimar rapidamente a severidade temporal de um cenário térmico adiabático para priorização de salvaguardas.",
                        method="Rotina interna de triagem adiabática usando entrada cinética simplificada.",
                        references=["CCPS Guidelines for Chemical Reactivity Evaluation"],
                        assumptions=[
                            "Modelo simplificado para screening, não substitui calorimetria reativa nem estudo dedicado.",
                            "Regime assumido como adiabático de triagem.",
                            "Parâmetros cinéticos informados devem ser tratados como aproximados quando não vierem de ensaio.",
                        ],
                        inputs=st.session_state.get("tmr_inputs"),
                        formula="TMR = f(T0, Ea, parâmetros cinéticos, hipótese adiabática)",
                        note="Use para triagem de severidade. Para decisão de projeto, complementar com dados experimentais e análise térmica formal.",
                    )
