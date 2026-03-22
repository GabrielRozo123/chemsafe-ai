from __future__ import annotations

import pandas as pd


def _status_from_bool(ok: bool, partial: bool = False) -> str:
    if ok:
        return "OK"
    if partial:
        return "PARCIAL"
    return "GAP"


def _severity_from_status(status: str, critical: bool = False) -> str:
    if status == "OK":
        return "Baixa"
    if critical:
        return "Crítica"
    if status == "PARCIAL":
        return "Média"
    return "Alta"


def _decision_for_status(status: str, critical: bool, decision: str) -> str:
    if status == "OK":
        return "Não bloqueia"
    if critical:
        return decision
    return f"Restringe: {decision}"


def build_psi_readiness_df(profile, lopa_result=None, bowtie=None) -> pd.DataFrame:
    rows = []

    identity_ok = bool(
        profile.identity.get("name")
        and profile.identity.get("formula")
        and profile.identity.get("molecular_weight")
    )
    status = _status_from_bool(identity_ok)
    rows.append(
        {
            "Pilar": "Chemical PSI",
            "Domínio": "Chemical PSI",
            "Item": "Identidade básica do composto",
            "Status": status,
            "Detalhe": "Nome, fórmula, massa molar e identificadores químicos.",
            "Impacto técnico": "Sem identidade robusta, o caso perde base de screening e de documentação.",
            "Decisão bloqueada": _decision_for_status(status, True, "Aprovação para screening"),
            "Severidade do gap": _severity_from_status(status, critical=True),
            "Tipo de evidência": "live_lookup" if identity_ok else "gap",
            "Hint de fonte": "PubChem / seed local / identidade do caso",
            "Ação recomendada": "Completar identidade do composto antes do estudo formal." if not identity_ok else "Base mínima disponível.",
        }
    )

    flamm_required = profile.flags.get("flammable", False)
    flamm_ok = (
        profile.prop("flash_point_c") is not None
        and profile.prop("lfl_volpct") is not None
        and profile.prop("ufl_volpct") is not None
    ) if flamm_required else True
    status = _status_from_bool(flamm_ok, partial=flamm_required and not flamm_ok)
    rows.append(
        {
            "Pilar": "Chemical PSI",
            "Domínio": "Chemical PSI",
            "Item": "Pacote de inflamabilidade",
            "Status": status,
            "Detalhe": "Ponto de fulgor, LII e LSI.",
            "Impacto técnico": "Compromete envelope de inflamabilidade, ignição e seleção de salvaguardas.",
            "Decisão bloqueada": _decision_for_status(status, True, "HAZOP de ignição / screening de fire and gas"),
            "Severidade do gap": _severity_from_status(status, critical=flamm_required),
            "Tipo de evidência": "derived" if flamm_ok else "gap",
            "Hint de fonte": "NIOSH / SDS / NIST / base interna",
            "Ação recomendada": "Buscar NIST/NIOSH/SDS para fechar inflamabilidade." if not flamm_ok else "Pacote utilizável para screening.",
        }
    )

    tox_required = profile.flags.get("toxic_inhalation", False)
    tox_ok = (
        profile.limit("IDLH_ppm") is not None
        or profile.limit("IDLH_mg_m3") is not None
    ) if tox_required else True
    status = _status_from_bool(tox_ok, partial=tox_required and not tox_ok)
    rows.append(
        {
            "Pilar": "Chemical PSI",
            "Domínio": "Chemical PSI",
            "Item": "Pacote de toxicidade / exposição",
            "Status": status,
            "Detalhe": "IDLH, REL, PEL, ERPG ou limites equivalentes.",
            "Impacto técnico": "Afeta resposta à emergência, evacuação e definição de barreiras de exposição.",
            "Decisão bloqueada": _decision_for_status(status, True, "Screening de dispersão tóxica e resposta a emergência"),
            "Severidade do gap": _severity_from_status(status, critical=tox_required),
            "Tipo de evidência": "derived" if tox_ok else "gap",
            "Hint de fonte": "NIOSH / ACGIH / SDS / critérios de exposição",
            "Ação recomendada": "Completar limites de exposição e critérios de evacuação." if not tox_ok else "Pacote mínimo disponível.",
        }
    )

    compat_ok = bool(profile.storage.get("incompatibilities"))
    status = _status_from_bool(compat_ok, partial=not compat_ok)
    rows.append(
        {
            "Pilar": "Chemical PSI",
            "Domínio": "Chemical PSI",
            "Item": "Compatibilidade química e materiais",
            "Status": status,
            "Detalhe": "Incompatibilidades, corrosividade e riscos de mistura.",
            "Impacto técnico": "Afeta integridade mecânica, segregação operacional e MOC.",
            "Decisão bloqueada": _decision_for_status(status, False, "Definição de materiais e segregação"),
            "Severidade do gap": _severity_from_status(status, critical=False),
            "Tipo de evidência": "derived" if compat_ok else "gap",
            "Hint de fonte": "NIOSH / SDS / histórico de materiais compatíveis",
            "Ação recomendada": "Adicionar incompatibilidades e materiais compatíveis." if not compat_ok else "Base inicial disponível.",
        }
    )

    routing_ok = bool(profile.routing)
    status = _status_from_bool(routing_ok)
    rows.append(
        {
            "Pilar": "Process PSI",
            "Domínio": "Process PSI",
            "Item": "Roteamento de cenários de risco",
            "Status": status,
            "Detalhe": "HAZOP, LOPA, dispersão e fogo alinhados ao perfil do composto.",
            "Impacto técnico": "Sem roteamento, o estudo perde foco e cobertura de cenários prioritários.",
            "Decisão bloqueada": _decision_for_status(status, True, "Kickoff técnico do caso"),
            "Severidade do gap": _severity_from_status(status, critical=True),
            "Tipo de evidência": "derived" if routing_ok else "gap",
            "Hint de fonte": "compound_engine routing",
            "Ação recomendada": "Revisar cenários prioritários por nó/equipamento." if routing_ok else "Definir cenários principais.",
        }
    )

    lopa_ok = bool(lopa_result)
    status = _status_from_bool(lopa_ok, partial=not lopa_ok)
    rows.append(
        {
            "Pilar": "Safeguard PSI",
            "Domínio": "Safeguard PSI",
            "Item": "Avaliação preliminar de LOPA / SIL",
            "Status": status,
            "Detalhe": "Frequência iniciadora, IPLs e SIL requerido.",
            "Impacto técnico": "Sem essa base, é fraca a leitura sobre suficiência de proteção.",
            "Decisão bloqueada": _decision_for_status(status, False, "Aprovação para budgetary study"),
            "Severidade do gap": _severity_from_status(status, critical=False),
            "Tipo de evidência": "derived" if lopa_ok else "gap",
            "Hint de fonte": "lopa_result / workshop de barreiras",
            "Ação recomendada": "Executar LOPA preliminar no caso." if not lopa_ok else "LOPA preliminar disponível.",
        }
    )

    bowtie_ok = False
    if bowtie:
        bowtie_ok = bool(
            bowtie.get("threats")
            and bowtie.get("barriers_pre")
            and bowtie.get("barriers_mit")
            and bowtie.get("consequences")
        )
    status = _status_from_bool(bowtie_ok, partial=bool(bowtie))
    rows.append(
        {
            "Pilar": "Safeguard PSI",
            "Domínio": "Safeguard PSI",
            "Item": "Bow-Tie do caso",
            "Status": status,
            "Detalhe": "Ameaças, top event, barreiras preventivas e mitigadoras.",
            "Impacto técnico": "Sem bow-tie, a comunicação de ameaça-barreira-consequência fica pobre.",
            "Decisão bloqueada": _decision_for_status(status, False, "Workshop de barreiras / revisão multidisciplinar"),
            "Severidade do gap": _severity_from_status(status, critical=False),
            "Tipo de evidência": "derived" if bowtie_ok else "gap",
            "Hint de fonte": "editor bow-tie do caso",
            "Ação recomendada": "Editar o Bow-Tie por cenário e consolidar barreiras." if not bowtie_ok else "Bow-Tie inicial disponível.",
        }
    )

    pressure_basis_needed = profile.flags.get("pressurized", False)
    pressure_basis_ok = pressure_basis_needed and (
        profile.prop("boiling_point_c") is not None or bool(lopa_result)
    )
    status = _status_from_bool(pressure_basis_ok, partial=pressure_basis_needed and not pressure_basis_ok)
    rows.append(
        {
            "Pilar": "Process PSI",
            "Domínio": "Process PSI",
            "Item": "Base preliminar de sobrepressão / alívio",
            "Status": status,
            "Detalhe": "Condições pressurizadas, perda de contenção e necessidade de alívio.",
            "Impacto técnico": "Compromete avaliação de PSV, blocked outlet e fire case.",
            "Decisão bloqueada": _decision_for_status(status, True, "Definição de relief screening"),
            "Severidade do gap": _severity_from_status(status, critical=pressure_basis_needed),
            "Tipo de evidência": "derived" if pressure_basis_ok else "gap",
            "Hint de fonte": "dados de T/P, relief basis, LOPA",
            "Ação recomendada": "Adicionar base de relief / PSV / bloqueio de linha." if pressure_basis_needed and not pressure_basis_ok else "Screening inicial aceitável.",
        }
    )

    process_docs_ok = False
    status = _status_from_bool(process_docs_ok, partial=False)
    rows.append(
        {
            "Pilar": "Process PSI",
            "Domínio": "Process PSI",
            "Item": "PFD/P&ID, inventário, limites e filosofia de controle",
            "Status": status,
            "Detalhe": "Ainda não integrado diretamente no fluxo do app.",
            "Impacto técnico": "Sem contexto de processo, o caso permanece centrado na substância e não no nó.",
            "Decisão bloqueada": _decision_for_status(status, True, "Uso do caso para projeto"),
            "Severidade do gap": _severity_from_status(status, critical=True),
            "Tipo de evidência": "gap",
            "Hint de fonte": "PFD / P&ID / equipment list / control philosophy",
            "Ação recomendada": "Adicionar documentos e limites operacionais do processo.",
        }
    )

    emergency_ok = bowtie_ok or bool(profile.routing)
    status = _status_from_bool(emergency_ok, partial=not emergency_ok)
    rows.append(
        {
            "Pilar": "Emergency PSI",
            "Domínio": "Emergency PSI",
            "Item": "Base inicial de resposta a emergências",
            "Status": status,
            "Detalhe": "Evacuação, mitigação e ações de resposta.",
            "Impacto técnico": "Enfraquece decisão operacional e comunicação de contingência.",
            "Decisão bloqueada": _decision_for_status(status, False, "Briefing operacional / emergência"),
            "Severidade do gap": _severity_from_status(status, critical=False),
            "Tipo de evidência": "derived" if emergency_ok else "gap",
            "Hint de fonte": "routing, bow-tie, plano de resposta",
            "Ação recomendada": "Definir ações operacionais e critérios de resposta." if not emergency_ok else "Estrutura inicial disponível.",
        }
    )

    governance_ok = bool(getattr(profile, "references", [])) and bool(getattr(profile, "source_trace", []))
    status = _status_from_bool(governance_ok, partial=not governance_ok)
    rows.append(
        {
            "Pilar": "Governance PSI",
            "Domínio": "Governance PSI",
            "Item": "Rastreabilidade mínima de fontes",
            "Status": status,
            "Detalhe": "Source trace, referências e confiança do pacote de dados.",
            "Impacto técnico": "Sem rastreabilidade, o caso fica difícil de defender em revisão e auditoria.",
            "Decisão bloqueada": _decision_for_status(status, False, "Aprovação formal do caso"),
            "Severidade do gap": _severity_from_status(status, critical=False),
            "Tipo de evidência": "derived" if governance_ok else "gap",
            "Hint de fonte": "references_registry / source_trace / confidence score",
            "Ação recomendada": "Fechar rastreabilidade mínima por fonte e confiança." if not governance_ok else "Trilha mínima disponível.",
        }
    )

    return pd.DataFrame(rows)


def summarize_psi_readiness(df: pd.DataFrame) -> dict:
    mapping = {"OK": 1.0, "PARCIAL": 0.5, "GAP": 0.0}
    score = 100.0 * df["Status"].map(mapping).fillna(0).mean()

    counts = df["Status"].value_counts().to_dict()
    critical_gaps = int(
        len(
            df[
                (df["Status"] == "GAP")
                & (df["Severidade do gap"].isin(["Crítica", "Alta"]))
            ]
        )
    )

    blocked = sorted(
        {
            x
            for x in df["Decisão bloqueada"].fillna("Não bloqueia").tolist()
            if x != "Não bloqueia"
        }
    )

    domains = (
        df.groupby("Domínio")["Status"]
        .apply(lambda s: round(100.0 * s.map(mapping).fillna(0).mean(), 1))
        .to_dict()
    )

    return {
        "score": round(score, 1),
        "ok": counts.get("OK", 0),
        "partial": counts.get("PARCIAL", 0),
        "gap": counts.get("GAP", 0),
        "critical_gaps": critical_gaps,
        "blocked_decisions": blocked,
        "domain_scores": domains,
    }
