from __future__ import annotations

import pandas as pd
import streamlit as st
import graphviz
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from ui_states import render_empty_state

from ce_matrix_engine import generate_ce_matrix_from_hazop
from pid_engine import EQUIPMENT_PARAMETERS, generate_hazop_from_topology, process_bulk_pid_nodes
from ui_components import render_hero_panel, render_evidence_panel


def render_risk_module(
    profile,
    menu_styles: dict,
    is_valid_df_fn,
):
    risk_tab = option_menu(
        menu_title=None,
        options=["HAZOP Builder", "Verificação SIL (IEC)", "QRA Social"],
        icons=["diagram-3", "shield-check", "activity"],
        default_index=0,
        orientation="horizontal",
        styles=menu_styles,
    )

    if risk_tab == "HAZOP Builder":
        render_hero_panel(
            title="HAZOP Builder com Topologia Assistida",
            subtitle="Estruture nós, desvios, causas, consequências e salvaguardas em uma experiência mais legível para workshop técnico.",
            kicker="Risk Study Workspace",
        )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Geração assistida de matriz HAZOP",
                purpose="Suportar workshops e pré-estruturação do estudo com base na topologia selecionada.",
                method="Mapeamento assistido de equipamentos/linhas para cenários HAZOP e matriz de desvios.",
                references=["IEC 61882"],
                assumptions=[
                    "A saída é assistiva e não substitui workshop formal com equipe multidisciplinar.",
                    "A qualidade da matriz depende da topologia e dos equipamentos selecionados.",
                    "Salvaguardas e recomendações exigem revisão humana antes de congelamento.",
                ],
                inputs={
                    "Nó atual": st.session_state.current_node_name,
                    "Modo": "Grafo / processamento em lote",
                    "Saída": "Matriz HAZOP + C&E assistida",
                },
                formula="Topologia + tipo de equipamento -> cenários de desvio -> causas/consequências/salvaguardas",
                note="Use a geração como ponto de partida de estudo. A consolidação final deve ocorrer em sessão HAZOP validada.",
            )

        st.markdown("<div class='panel'><h3>Geração Inteligente de P&ID e HAZOP</h3></div>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Nó Único (Grafo)", "Lote Múltiplos Nós (CSV)"])

        with t1:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.session_state.current_node_name = st.text_input(
                    "Identificação do Nó",
                    value=st.session_state.current_node_name,
                )
            with col2:
                selected_equipment = st.multiselect(
                    "Equipamentos e Linhas (Em Ordem)",
                    options=list(EQUIPMENT_PARAMETERS.keys()),
                    default=[
                        "Tanque de Armazenamento Atmosférico",
                        "Tubulação / Linha de Transferência",
                        "Bomba Centrífuga",
                    ],
                )

            if selected_equipment:
                dot = graphviz.Digraph()
                dot.attr(rankdir="LR", bgcolor="transparent")
                dot.attr(
                    "node",
                    shape="box",
                    style="filled",
                    fillcolor="#1e293b",
                    color="#3b82f6",
                    fontcolor="white",
                    fontname="Inter",
                    penwidth="2",
                )
                dot.attr("edge", color="#9ca3af", penwidth="2")
                for i, eq in enumerate(selected_equipment):
                    dot.node(str(i), eq)
                    if i > 0:
                        dot.edge(str(i - 1), str(i))
                st.graphviz_chart(dot, use_container_width=True)

            if st.button("🚀 Consolidar Topologia em HAZOP", type="primary"):
                st.session_state.pid_hazop_matrix = generate_hazop_from_topology(
                    st.session_state.current_node_name,
                    selected_equipment,
                    profile,
                )
                st.success("Grafo processado! As pendências de mitigação foram enviadas ao Action Hub.")

        with t2:
            st.markdown(
                "<div class='note-card'>Importe a Equipment List extraída do seu CAD (Nó, Equipamento).</div>",
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])
            if uploaded_file is not None:
                df_bulk = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                if st.button("⚡ Executar Processamento em Lote", type="primary"):
                    bulk_results = process_bulk_pid_nodes(df_bulk, profile)
                    if bulk_results:
                        st.session_state.pid_hazop_matrix = bulk_results
                        st.success(f"{len(bulk_results)} cenários gerados para a fábrica inteira.")

        if st.session_state.get("pid_hazop_matrix"):
            st.markdown("<br><hr>", unsafe_allow_html=True)
            df_hazop = pd.DataFrame(st.session_state.pid_hazop_matrix)

            with st.expander("📋 Estudo HAZOP (IEC 61882)", expanded=True):
                view_mode = st.radio(
                    "Modo de Leitura:",
                    ["🗂️ Cards (Discussão de Reunião)", "📊 Tabela Otimizada (Text Wrap)"],
                    horizontal=True,
                    label_visibility="collapsed",
                )
                st.markdown("<br>", unsafe_allow_html=True)

                if "Cards" in view_mode:
                    for _, row in df_hazop.iterrows():
                        st.markdown(
                            f"""
                            <div style="background-color: rgba(30, 41, 59, 0.4); border: 1px solid #374151; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                    <span style="color: #9ca3af; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">{row['Nó']}</span>
                                    <span style="background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 600;">{row['Palavra-Guia']} {row['Parâmetro']}</span>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
                                    <div><strong style="color: #f87171; font-size: 0.9rem;">⚠️ Causa:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Causa']}</span></div>
                                    <div><strong style="color: #f87171; font-size: 0.9rem;">💥 Consequência:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Consequência']}</span></div>
                                </div>
                                <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 10px; border-radius: 6px;">
                                    <strong style="color: #34d399; font-size: 0.9rem;">🛡️ Salvaguardas:</strong><br><span style="color: #d1d5db; font-size: 0.95rem;">{row['Salvaguarda Atual']}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.dataframe(
                        df_hazop,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "Nó": st.column_config.TextColumn("Nó", width="medium"),
                            "Causa": st.column_config.TextColumn("Causa", width="large"),
                            "Consequência": st.column_config.TextColumn("Consequência", width="large"),
                            "Salvaguarda Atual": st.column_config.TextColumn("Salvaguarda", width="medium"),
                        },
                    )
                st.download_button(
                    "📥 Exportar CSV",
                    df_hazop.to_csv(index=False).encode("utf-8"),
                    "hazop_export.csv",
                    "text/csv",
                )

            with st.expander("🔀 Matriz Causa e Efeito p/ Automação (IEC 61511)", expanded=False):
                df_ce = generate_ce_matrix_from_hazop(st.session_state.pid_hazop_matrix)
                if is_valid_df_fn(df_ce):
                    st.dataframe(df_ce, width="stretch", hide_index=True)
                    st.download_button(
                        "📥 Exportar C&E",
                        df_ce.to_csv(index=False).encode("utf-8"),
                        "ce_matrix.csv",
                        "text/csv",
                    )
                                else:
                    render_empty_state(
                        title="Nenhuma matriz Causa & Efeito deduzida",
                        message="Os cenários atuais ainda não geraram uma arquitetura de trip/intertravamento clara para exportação.",
                        icon="🧩",
                    )

    elif risk_tab == "Verificação SIL (IEC)":
        render_hero_panel(
            title="Verificação Paramétrica de SIL / PFDavg",
            subtitle="Leitura rápida da robustez da arquitetura de intertravamento com base em hipótese simplificada de falha perigosa e intervalo de teste.",
            kicker="Functional Safety",
        )

        st.markdown("<div class='panel'><h3>🖲️ Análise de Arquitetura de Intertravamento (IEC 61511)</h3></div>", unsafe_allow_html=True)
        st.markdown("<div class='note-card'>Cálculo paramétrico da Probabilidade Média de Falha sob Demanda (PFDavg) garantindo leitura preliminar da malha SIF.</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            arq = st.selectbox("Arquitetura de Sensores/Válvulas", ["1oo1 (Simplex)", "1oo2 (Redundante)", "2oo3 (Votação)"])
            lambda_du = st.number_input("Taxa de Falha Perigosa (λdu) - falhas/hora", 1e-6, format="%.2e")
            ti_meses = st.number_input("Intervalo de Teste (Proof Test - Meses)", 12)
            ti_horas = ti_meses * 730

        with col2:
            st.markdown("#### Memorial de Cálculo (IEC)")
            if "1oo1" in arq:
                formula = r"PFD_{avg} = \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
                pfd_avg = lambda_du * (ti_horas / 2)
            elif "1oo2" in arq:
                formula = r"PFD_{avg} \approx \frac{(\lambda_{DU} \times TI)^2}{3} + \beta \times \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
                st.caption("*Assumindo fator de causa comum (β) = 10%*")
                pfd_avg = (((lambda_du * ti_horas) ** 2) / 3) + (0.10 * lambda_du * (ti_horas / 2))
            else:
                formula = r"PFD_{avg} \approx (\lambda_{DU} \times TI)^2 + \beta \times \lambda_{DU} \times \frac{TI}{2}"
                st.latex(formula)
                st.caption("*Assumindo fator de causa comum (β) = 10%*")
                pfd_avg = ((lambda_du * ti_horas) ** 2) + (0.10 * lambda_du * (ti_horas / 2))

            sil = "SIL 3" if pfd_avg < 1e-3 else "SIL 2" if pfd_avg < 1e-2 else "SIL 1" if pfd_avg < 1e-1 else "Não Classificado"

            st.markdown(
                f"""
                <div style='background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:8px; padding:15px; margin-top:20px; text-align:center;'>
                    <span style='color:#9ca3af; font-size:0.8rem; text-transform:uppercase;'>Resultado Final (PFDavg)</span><br>
                    <span style='color:white; font-size:2.5rem; font-weight:800;'>{pfd_avg:.2e}</span><br>
                    <span style='color:#10b981; font-size:1.2rem; font-weight:700;'>Alcança {sil}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Verificação paramétrica de PFDavg",
                purpose="Oferecer leitura preliminar de atendimento SIL sob hipóteses simplificadas de arquitetura, falha perigosa e intervalo de teste.",
                method="Equações simplificadas por arquitetura 1oo1, 1oo2 e 2oo3 com hipótese de β = 10% em redundância.",
                references=["IEC 61511"],
                assumptions=[
                    "Leitura preliminar. Não substitui cálculo SIL verification formal.",
                    "Assume β fixo de 10% nos casos redundantes.",
                    "Não contempla todos os fatores reais de proof test coverage, bypass, repair, diagnostics e common cause detalhado.",
                ],
                inputs={
                    "Arquitetura": arq,
                    "λDU": f"{lambda_du:.2e} falhas/h",
                    "Proof test interval": f"{ti_meses} meses",
                    "TI": f"{ti_horas} h",
                    "Resultado": f"{pfd_avg:.2e} ({sil})",
                },
                formula=formula,
                note="Painel útil para screening e comparações. Para especificação de SIF, conduzir cálculo formal conforme procedimento da organização.",
            )

    elif risk_tab == "QRA Social":
        render_hero_panel(
            title="Curva F-N de Risco Social",
            subtitle="Visualização ilustrativa para posicionamento preliminar do risco social frente a envelopes de tolerabilidade.",
            kicker="Risk Communication",
        )

        st.markdown("<div class='panel'><h3>Curva F-N de Risco Social</h3></div>", unsafe_allow_html=True)
        fig_fn = go.Figure()
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-4, 1e-5, 1e-6], name="Limite Tolerável", line=dict(color="red", dash="dash")))
        fig_fn.add_trace(go.Scatter(x=[1, 10, 100], y=[1e-5, 1e-6, 1e-7], name="Limite Desprezível", line=dict(color="green", dash="dash")))
        fig_fn.add_trace(go.Scatter(x=[10], y=[2e-5], mode="markers+text", text=["Risco Planta"], textposition="top center", marker=dict(size=12, color="white")))
        fig_fn.update_layout(
            xaxis_type="log",
            yaxis_type="log",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#9ca3af",
            height=400,
        )
        st.plotly_chart(fig_fn, use_container_width=True, theme=None)

        if st.session_state.audit_mode:
            render_evidence_panel(
                title="Curva F-N ilustrativa",
                purpose="Apoiar comunicação preliminar de risco social de forma visual e executiva.",
                method="Gráfico ilustrativo com envelopes de tolerabilidade e ponto representativo da planta.",
                references=["CCPS RBPS"],
                assumptions=[
                    "Gráfico atual é ilustrativo e não resulta de um QRA quantitativo completo.",
                    "Não usar para licenciamento, aceite formal de risco ou justificativa regulatória.",
                    "Exige modelagem quantitativa formal para aplicação decisória robusta.",
                ],
                inputs={
                    "Escala": "Log-log",
                    "Limites": "Tolerável / Desprezível",
                    "Status": "Demonstrativo",
                },
                formula="F(N) vs N em escala logarítmica",
                note="Painel intencionalmente didático. Para uso formal, substituir por resultados oriundos de QRA quantitativo real.",
            )
