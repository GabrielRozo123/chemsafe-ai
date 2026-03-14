from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from models import HazardScenario
from prompts import DOCUMENT_INSIGHTS_SYSTEM, PREHAZOP_SYSTEM

PREHAZOP_JSON_SCHEMA = {
    "name": "prehazop_payload",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "node": {"type": "string"},
                        "deviation": {"type": "string"},
                        "cause": {"type": "string"},
                        "consequence": {"type": "string"},
                        "safeguards": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "severity": {"type": "string"},
                        "likelihood": {"type": "string"},
                        "risk_rank": {"type": "string"},
                    },
                    "required": [
                        "node",
                        "deviation",
                        "cause",
                        "consequence",
                        "safeguards",
                        "recommendations",
                        "severity",
                        "likelihood",
                        "risk_rank",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["scenarios"],
        "additionalProperties": False,
    },
}

DOC_INSIGHTS_JSON_SCHEMA = {
    "name": "document_insights_payload",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "chemicals": {"type": "array", "items": {"type": "string"}},
            "equipment": {"type": "array", "items": {"type": "string"}},
            "instruments": {"type": "array", "items": {"type": "string"}},
            "safeguards": {"type": "array", "items": {"type": "string"}},
            "operating_limits": {"type": "array", "items": {"type": "string"}},
            "hazards": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "chemicals",
            "equipment",
            "instruments",
            "safeguards",
            "operating_limits",
            "hazards",
            "notes",
        ],
        "additionalProperties": False,
    },
}


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
- considerar cenários de perda de contenção, sobrepressão, runaway, toxic release, incêndio e falhas instrumentadas quando aplicável.
""".strip()

    result = ai_client.ask_json(
        user_prompt,
        system_prompt=PREHAZOP_SYSTEM,
        context_blocks=None,
        reasoning=True,
        schema=PREHAZOP_JSON_SCHEMA,
    )

    if not isinstance(result, dict):
        return []

    raw_items = result.get("scenarios", [])
    if not isinstance(raw_items, list):
        return []

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
                safeguards=item.get("safeguards", []) if isinstance(item.get("safeguards"), list) else [],
                recommendations=item.get("recommendations", []) if isinstance(item.get("recommendations"), list) else [],
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

Retorne JSON com os campos:
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
        schema=DOC_INSIGHTS_JSON_SCHEMA,
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

    if result.get("error"):
        return {
            "chemicals": [],
            "equipment": [],
            "instruments": [],
            "safeguards": [],
            "operating_limits": [],
            "hazards": [],
            "notes": [f"Erro ao extrair insights: {result.get('raw', result.get('error'))}"],
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
