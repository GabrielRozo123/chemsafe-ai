from __future__ import annotations

import pandas as pd


def _status_from_bool(ok: bool, partial: bool = False) -> str:
    if ok:
        return "OK"
    if partial:
        return "PARCIAL"
    return "GAP"


def build_psi_readiness_df(profile, lopa_result=None, bowtie=None) -> pd.DataFrame:
    rows = []

    # 1
    identity_ok = bool(
        profile.identity.get("name")
        and profile.identity.get("formula")
        and profile.identity.get("molecular_weight")
    )
    rows.append(
        {
            "Pilar": "Identificação química",
            "Item": "Identidade básica do composto",
            "Status": _status_from_bool(identity_ok),
            "Detalhe": "Nome, fórmula, massa molar e identificadores químicos.",
            "Ação recomendada": "Completar identidade do composto antes do estudo formal." if not identity_ok else "Base mínima disponível.",
        }
    )

    # 2
    flamm_required = profile.flags.get("flammable", False)
    flamm_ok = (
        profile.prop("flash_point_c") is not None
        and profile.prop("lfl_volpct") is not None
        and profile.prop("ufl_volpct") is not None
    ) if flamm_required else True
    rows.append(
        {
            "Pilar": "Dados de perigo",
            "Item": "Pacote de inflamabilidade",
            "Status": _status_from_bool(flamm_ok, partial=flamm_required and not flamm_ok),
            "Detalhe": "Ponto de fulgor, LII e LSI.",
            "Ação recomendada": "Buscar NIST/NIOSH/SDS para fechar inflamabilidade." if not flamm_ok else "Pacote utilizável para screening.",
        }
    )

    # 3
    tox_required = profile.flags.get("toxic_inhalation", False)
    tox_ok = (
        profile.limit("IDLH_ppm") is not None
        or profile.limit("IDLH_mg_m3") is not None
    ) if tox_required else True
    rows.append(
        {
            "Pilar": "Dados de perigo",
            "Item": "Pacote de toxicidade / exposição",
            "Status": _status_from_bool(tox_ok, partial=tox_required and not tox_ok),
            "Detalhe": "IDLH, REL, PEL, ERPG ou limites equivalentes.",
            "Ação recomendada": "Completar limites de exposição e critérios de evacuação." if not tox_ok else "Pacote mínimo disponível.",
        }
    )

    # 4
    compat_ok = bool(profile.storage.get("incompatibilities"))
    rows.append(
        {
            "Pilar": "Reatividade / materiais",
            "Item": "Compatibilidade química",
            "Status": _status_from_bool(compat_ok, partial=not compat_ok),
            "Detalhe": "Incompatibilidades, corrosividade e riscos de mistura.",
            "Ação recomendada": "Adicionar incompatibilidades e materiais compatíveis." if not compat_ok else "Base inicial disponível.",
        }
    )

    # 5
    routing_ok = bool(profile.routing)
    rows.append(
        {
            "Pilar": "Seleção de cenários",
            "Item": "Roteamento de cenários de risco",
            "Status": _status_from_bool(routing_ok),
            "Detalhe": "HAZOP, LOPA, dispersão e fogo alinhados ao perfil do composto.",
            "Ação recomendada": "Revisar cenários prioritários por nó/equipamento." if routing_ok else "Definir cenários principais.",
        }
    )

    # 6
    lopa_ok = bool(lopa_result)
    rows.append(
        {
            "Pilar": "Camadas de proteção",
            "Item": "Avaliação preliminar de LOPA / SIL",
            "Status": _status_from_bool(lopa_ok, partial=not lopa_ok),
            "Detalhe": "Frequência iniciadora, IPLs e SIL requerido.",
            "Ação recomendada": "Executar LOPA preliminar no caso." if not lopa_ok else "LOPA preliminar disponível.",
        }
    )

    # 7
    bowtie_ok = False
    if bowtie:
        bowtie_ok = bool(
            bowtie.get("threats")
            and bowtie.get("barriers_pre")
            and bowtie.get("barriers_mit")
            and bowtie.get("consequences")
        )
    rows.append(
        {
            "Pilar": "Visualização de barreiras",
            "Item": "Bow-Tie do caso",
            "Status": _status_from_bool(bowtie_ok, partial=bool(bowtie)),
            "Detalhe": "Ameaças, top event, barreiras preventivas e mitigadoras.",
            "Ação recomendada": "Editar o Bow-Tie por cenário e consolidar barreiras." if not bowtie_ok else "Bow-Tie inicial disponível.",
        }
    )

    # 8
    pressure_basis_needed = profile.flags.get("pressurized", False)
    pressure_basis_ok = pressure_basis_needed and (
        profile.prop("boiling_point_c") is not None or bool(lopa_result)
    )
    rows.append(
        {
            "Pilar": "Condições operacionais",
            "Item": "Base preliminar de sobrepressão / alívio",
            "Status": _status_from_bool(pressure_basis_ok, partial=pressure_basis_needed and not pressure_basis_ok),
            "Detalhe": "Condições pressurizadas, perda de contenção e necessidade de alívio.",
            "Ação recomendada": "Adicionar base de relief / PSV / bloqueio de linha." if pressure_basis_needed and not pressure_basis_ok else "Screening inicial aceitável.",
        }
    )

    # 9
    process_docs_ok = False
    rows.append(
        {
            "Pilar": "Informação de processo",
            "Item": "PFD/P&ID, inventário, limites e filosofia de controle",
            "Status": _status_from_bool(process_docs_ok, partial=False),
            "Detalhe": "Ainda não integrado diretamente no fluxo do app.",
            "Ação recomendada": "Adicionar documentos e limites operacionais do processo.",
        }
    )

    # 10
    emergency_ok = bowtie_ok or bool(profile.routing)
    rows.append(
        {
            "Pilar": "Resposta e mitigação",
            "Item": "Base inicial de resposta a emergências",
            "Status": _status_from_bool(emergency_ok, partial=not emergency_ok),
            "Detalhe": "Evacuação, mitigação e ações de resposta.",
            "Ação recomendada": "Definir ações operacionais e critérios de resposta." if not emergency_ok else "Estrutura inicial disponível.",
        }
    )

    return pd.DataFrame(rows)


def summarize_psi_readiness(df: pd.DataFrame) -> dict:
    mapping = {"OK": 1.0, "PARCIAL": 0.5, "GAP": 0.0}
    score = 100.0 * df["Status"].map(mapping).fillna(0).mean()

    counts = df["Status"].value_counts().to_dict()
    return {
        "score": score,
        "ok": counts.get("OK", 0),
        "partial": counts.get("PARCIAL", 0),
        "gap": counts.get("GAP", 0),
    }
