from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from models import HazardScenario
from prompts import DOCUMENT_INSIGHTS_SYSTEM, PREHAZOP_SYSTEM


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def generate_hazop_from_text(
    ai_client,
    process_description: str,
    equipment: str,
    operating_context: str = "",
) -> List[HazardScenario]:
    if not getattr(ai_client, "enabled", False):
        return []

    user_prompt = f"""
Gere um pré-HAZOP técnico para o seguinte caso.

Equipamento / nó:
{equipment}

Descrição do processo:
{process_description}

Contexto operacional:
{operating_context}

Requisitos:
- retornar cenários tecnicamente plausíveis para segurança de processo;
- incluir desvio, causa, consequência, salvaguardas existentes e recomendação;
- priorizar linguagem de engenharia química / process safety;
- considerar cenários de perda de contenção, sobrepressão, runaway, toxic release, incêndio e falhas instrumentadas quando aplicável;
- responder em JSON válido.
""".strip()

    result = ai_client.ask_json(
        user_prompt,
        system_prompt=PREHAZOP_SYSTEM,
        context_blocks=None,
        reasoning=True,
    )

    raw_items = []
    if isinstance(result, dict):
        if isinstance(result.get("scenarios"), list):
            raw_items = result["scenarios"]
        elif isinstance(result.get("hazop"), list):
            raw_items = result["hazop"]
        elif isinstance(result.get("items"), list):
            raw_items = result["items"]

    scenarios: List[HazardScenario] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        scenarios.append(
            HazardScenario(
                node=item.get("node", equipment),
                deviation=item.get("deviation", "Desvio não informado"),
                cause=item.get("cause", "Causa não informada"),
                consequence=item.get("consequence", "Consequência não informada"),
                safeguards=_safe_list(item.get("safeguards")),
                recommendations=_safe_list(item.get("recommendations")),
                severity=str(item.get("severity", "Medium")),
                likelihood=str(item.get("likelihood", "Medium")),
                risk_rank=str(item.get("risk_rank", "Médio")),
            )
        )

    return scenarios


def extract_document_insights(
    ai_client,
    context_blocks: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    if not getattr(ai_client, "enabled", False):
        return {
            "chemicals": [],
            "equipment": [],
            "instruments": [],
            "safeguards": [],
            "operating_limits": [],
            "hazards": [],
            "notes": ["Integração OpenAI indisponível."],
        }

    user_prompt = """
Extraia insights de segurança de processo a partir do contexto documental.

Retorne JSON válido com os campos:
- chemicals
- equipment
- instruments
- safeguards
- operating_limits
- hazards
- notes

Regras:
- consolidar duplicatas;
- manter linguagem técnica;
- priorizar informações úteis para HAZOP, LOPA, Bow-Tie e consequence analysis;
- não inventar dados fora do contexto recebido.
""".strip()

    result = ai_client.ask_json(
        user_prompt,
        system_prompt=DOCUMENT_INSIGHTS_SYSTEM,
        context_blocks=context_blocks,
        reasoning=False,
    )

    if not isinstance(result, dict):
        return {
            "chemicals": [],
            "equipment": [],
            "instruments": [],
            "safeguards": [],
            "operating_limits": [],
            "hazards": [],
            "notes": ["Falha ao interpretar a saída do modelo."],
        }

    return {
        "chemicals": _safe_list(result.get("chemicals")),
        "equipment": _safe_list(result.get("equipment")),
        "instruments": _safe_list(result.get("instruments")),
        "safeguards": _safe_list(result.get("safeguards")),
        "operating_limits": _safe_list(result.get("operating_limits")),
        "hazards": _safe_list(result.get("hazards")),
        "notes": _safe_list(result.get("notes")),
    }
