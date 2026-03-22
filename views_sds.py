"""View do leitor de SDS/FISPQ.

Integra-se como sub-tab no módulo de Engenharia ou pode ser chamado
de qualquer lugar via ``render_sds_upload_panel(profile)``.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sds_reader import (
    build_merge_summary,
    extract_text_from_sds_pdf,
    merge_sds_into_profile,
    parse_sds_with_ai,
    parse_sds_with_regex,
    sds_data_to_review_df,
)
from ui_components import metric_card, render_evidence_panel, render_hero_panel


def _get_ai_client():
    """Obtém o AIClient de forma lazy (só instancia se necessário)."""
    try:
        from ai_client import AIClient

        if "ai_client" not in st.session_state:
            st.session_state.ai_client = AIClient()
        return st.session_state.ai_client
    except Exception:
        return None


def _ai_is_available() -> bool:
    """Verifica se a integração com IA está disponível."""
    client = _get_ai_client()
    return client is not None and getattr(client, "enabled", False)


def render_sds_upload_panel(profile):
    """Renderiza o painel completo de upload e leitura de SDS/FISPQ."""
    render_hero_panel(
        title="Leitor Inteligente de SDS / FISPQ",
        subtitle=(
            "Faça upload de uma Safety Data Sheet em PDF e o motor extrai "
            "automaticamente propriedades, limites de exposição, perigos GHS "
            "e incompatibilidades — preenchendo os gaps do perfil do composto."
        ),
        kicker="Document Intelligence",
    )

    # ------------------------------------------------------------------
    # Evidências (modo auditoria)
    # ------------------------------------------------------------------
    if st.session_state.get("audit_mode"):
        render_evidence_panel(
            title="Extração estruturada de SDS/FISPQ",
            purpose=(
                "Automatizar a leitura de Safety Data Sheets para acelerar a "
                "preparação de estudos e eliminar transcrição manual de dados."
            ),
            method=(
                "Rota padrão: extração por padrões (regex) para campos críticos de process safety — "
                "funciona sem custo e sem API key. "
                "Rota opcional (IA): LLM com JSON schema estrito para extração mais completa das seções 2, 5, 8, 9 e 10."
            ),
            references=["ABNT NBR 14725-4", "GHS Rev.10", "OSHA 29 CFR 1910.1200"],
            assumptions=[
                "A extração depende da qualidade do texto do PDF (PDFs escaneados podem exigir OCR prévio).",
                "Dados extraídos devem ser revisados pelo usuário antes do merge.",
                "A SDS é um documento do fabricante — confirmar com fonte oficial quando necessário.",
                "O merge preenche gaps e não sobrescreve dados curados existentes (exceto se solicitado).",
            ],
            inputs={
                "Formato aceito": "PDF (SDS/FISPQ)",
                "Seções extraídas": "2, 5, 8, 9, 10 (IA) | CAS, flash, LFL, IDLH, TLV, H-codes (regex)",
                "Motor padrão": "Regex (gratuito)",
            },
            formula="PDF → texto → regex ou LLM → JSON estruturado → revisão → merge no perfil",
            note=(
                "Use para acelerar preparação de workshops. Para dados regulatórios "
                "finais, confirmar com a SDS original assinada pelo fabricante."
            ),
        )

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------
    st.markdown(
        "<div class='panel'><h3>📄 Upload de SDS / FISPQ</h3></div>",
        unsafe_allow_html=True,
    )

    col_upload, col_info = st.columns([2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Arraste ou selecione a SDS em PDF",
            type=["pdf"],
            key="sds_file_uploader",
            help="Aceita SDS em português (FISPQ/NBR 14725) ou inglês (OSHA/GHS).",
        )

    with col_info:
        st.markdown(
            """
            <div class='note-card'>
            <strong>Dados extraídos automaticamente:</strong><br>
            • Identidade (nome, CAS, fórmula, PM)<br>
            • Físico-química (Sec. 9)<br>
            • Limites de exposição (Sec. 8)<br>
            • Perigos GHS e NFPA (Sec. 2)<br>
            • Incompatibilidades (Sec. 10)<br>
            • Combate a incêndio (Sec. 5)
            </div>
            """,
            unsafe_allow_html=True,
        )

    if uploaded_file is None:
        return

    # ------------------------------------------------------------------
    # Extração de texto
    # ------------------------------------------------------------------
    file_bytes = uploaded_file.getvalue()

    with st.spinner("Extraindo texto do PDF..."):
        sds_text = extract_text_from_sds_pdf(file_bytes)

    if not sds_text.strip():
        st.error(
            "Não foi possível extrair texto deste PDF. "
            "Pode ser um PDF escaneado (imagem). Tente um PDF com texto selecionável."
        )
        return

    # Preview do texto extraído
    with st.expander(f"📝 Texto bruto extraído ({len(sds_text):,} caracteres)", expanded=False):
        st.text_area(
            "Texto da SDS",
            value=sds_text[:5000] + ("\n\n[... truncado para preview ...]" if len(sds_text) > 5000 else ""),
            height=250,
            disabled=True,
            label_visibility="collapsed",
        )

    # ------------------------------------------------------------------
    # Seleção do motor de extração
    # ------------------------------------------------------------------
    st.markdown("---")
    ai_available = _ai_is_available()

    col_btn, col_toggle = st.columns([3, 1.5])

    with col_toggle:
        if ai_available:
            use_ai = st.toggle(
                "🤖 Usar IA (extração avançada)",
                value=False,
                help="Habilita extração por LLM para cobertura mais completa. Consome créditos da API OpenAI.",
            )
        else:
            use_ai = False
            st.toggle(
                "🤖 Usar IA (extração avançada)",
                value=False,
                disabled=True,
                help="Requer OPENAI_API_KEY configurada nos Secrets do Streamlit.",
            )
            st.caption("🔒 Requer API key · [Como configurar](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)")
    with col_btn:
        btn_label = "🔬 Extrair dados da SDS" + (" com IA" if use_ai else " (gratuito)")
        run_extraction = st.button(btn_label, type="primary", use_container_width=True)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    if run_extraction:
        if use_ai and ai_available:
            with st.spinner("Analisando SDS com inteligência artificial..."):
                ai_client = _get_ai_client()
                sds_data = parse_sds_with_ai(ai_client, sds_text)

            if sds_data.get("error"):
                st.warning(
                    f"Erro na extração por IA: {sds_data.get('raw', sds_data.get('error'))}. "
                    "Usando fallback por padrões..."
                )
                sds_data = parse_sds_with_regex(sds_text)
                st.session_state.sds_extraction_mode = "Regex (fallback)"
            else:
                st.session_state.sds_extraction_mode = "IA"
        else:
            with st.spinner("Analisando SDS com extração por padrões..."):
                sds_data = parse_sds_with_regex(sds_text)
            st.session_state.sds_extraction_mode = "Regex"

        st.session_state.sds_extracted_data = sds_data

    # ------------------------------------------------------------------
    # Revisão dos dados extraídos
    # ------------------------------------------------------------------
    sds_data = st.session_state.get("sds_extracted_data")
    if sds_data is None or sds_data.get("error"):
        return

    extraction_mode = st.session_state.get("sds_extraction_mode", "—")
    notes = sds_data.get("extraction_notes", [])

    # KPIs da extração
    physchem = sds_data.get("physchem", {})
    exposure = sds_data.get("exposure_limits", {})
    n_physchem = sum(1 for v in physchem.values() if v is not None)
    n_exposure = sum(1 for v in exposure.values() if v is not None)
    n_hazards = len(sds_data.get("hazards", {}).get("ghs_h_statements", []))
    n_incompat = len(sds_data.get("reactivity", {}).get("incompatibilities", []))

    st.markdown(
        "<div class='panel'><h3>📊 Resultado da Extração</h3></div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        mode_color = "risk-green" if "IA" in extraction_mode else "risk-blue"
        st.markdown(metric_card("Motor", extraction_mode, mode_color), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Físico-química", f"{n_physchem} campos", "risk-blue", mono=True), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Exposição", f"{n_exposure} limites", "risk-amber", mono=True), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Perigos GHS", f"{n_hazards}", "risk-red", mono=True), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card("Incompatib.", f"{n_incompat}", "risk-violet", mono=True), unsafe_allow_html=True)

    # Notas de extração
    if notes:
        for note in notes:
            st.info(f"📌 {note}")

    # Tabela de revisão
    review_df = sds_data_to_review_df(sds_data)
    if not review_df.empty:
        st.markdown("**Revise os dados extraídos antes de aplicar ao perfil:**")
        st.dataframe(
            review_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seção": st.column_config.TextColumn("Seção", width="small"),
                "Campo": st.column_config.TextColumn("Campo", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="large"),
                "Unidade": st.column_config.TextColumn("Unidade", width="small"),
            },
        )
    else:
        st.warning("Nenhum dado estruturado extraído. Tente uma SDS com mais informações textuais.")
        return

    # ------------------------------------------------------------------
    # Merge no perfil
    # ------------------------------------------------------------------
    st.markdown("---")
    col_merge, col_option = st.columns([3, 1])

    with col_option:
        overwrite = st.checkbox(
            "Sobrescrever dados existentes",
            value=False,
            help="Se marcado, valores da SDS substituem os atuais. Se desmarcado, preenche apenas gaps.",
        )

    with col_merge:
        if st.button(
            "✅ Aplicar dados da SDS ao perfil do composto",
            type="primary",
            use_container_width=True,
        ):
            updated_profile, changes = merge_sds_into_profile(
                profile, sds_data, overwrite=overwrite
            )

            st.session_state.profile = updated_profile
            st.session_state.sds_merge_changes = changes

            summary = build_merge_summary(changes)
            if summary["total"] > 0:
                st.success(
                    f"Perfil atualizado: {summary['preenchidos']} campos preenchidos, "
                    f"{summary['atualizados']} atualizados, {summary['adicionados']} adicionados."
                )
            else:
                st.info("Nenhuma mudança aplicada — o perfil já continha todos os dados extraídos.")

    # ------------------------------------------------------------------
    # Log de mudanças
    # ------------------------------------------------------------------
    changes = st.session_state.get("sds_merge_changes")
    if changes:
        with st.expander("📋 Log detalhado de mudanças aplicadas", expanded=False):
            st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # Download do JSON extraído (para auditoria)
    # ------------------------------------------------------------------
    import json

    st.download_button(
        "📥 Baixar extração bruta (JSON)",
        json.dumps(sds_data, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="sds_extraction.json",
        mime="application/json",
    )
