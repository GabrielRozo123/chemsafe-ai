from __future__ import annotations

import pandas as pd


def build_risk_register(profile, hazop_priorities, lopa_result=None, dispersion_mode=None):
    rows = []

    for item in hazop_priorities:
        rows.append(
            {
                "Categoria": "HAZOP prioritário",
                "Foco": item.get("focus", ""),
                "Prioridade": item.get("priority", ""),
                "Justificativa": item.get("why", ""),
            }
        )

    for item in profile.routing:
        rows.append(
            {
                "Categoria": "Roteamento de cenários",
                "Foco": item,
                "Prioridade": "Automática",
                "Justificativa": "Derivado do perfil do composto e das propriedades disponíveis.",
            }
        )

    if dispersion_mode:
        rows.append(
            {
                "Categoria": "Modelo de dispersão sugerido",
                "Foco": dispersion_mode.get("label", ""),
                "Prioridade": "Automática",
                "Justificativa": "; ".join(dispersion_mode.get("reasons", [])),
            }
        )

    if lopa_result:
        rows.append(
            {
                "Categoria": "LOPA / SIL",
                "Foco": f"SIL requerido: {lopa_result.get('sil', '—')}",
                "Prioridade": "Cálculo",
                "Justificativa": f"MCF = {lopa_result.get('mcf', 0):.2e}/ano",
            }
        )

    return pd.DataFrame(rows)
