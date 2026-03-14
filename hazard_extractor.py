from __future__ import annotations

from typing import Any, Dict, List

from core.models import HazardScenario
from data.prompts import DOC_EXTRACTOR_SYSTEM, HAZOP_GENERATOR_SYSTEM
from services.ai_client import AIClient


def generate_hazop_from_text(ai: AIClient, process_description: str, equipment: str, operating_context: str) -> List[HazardScenario]:
    payload = ai.ask_json(
        system_prompt=HAZOP_GENERATOR_SYSTEM,
        user_prompt=(
            'Descrição do processo:\n'
            f'{process_description}\n\n'
            f'Equipamento principal: {equipment}\n'
            f'Contexto operacional: {operating_context}\n\n'
            'Gere 8 a 12 cenários HAZOP preliminares.'
        ),
        reasoning=True,
    )
    scenarios: List[HazardScenario] = []
    for item in payload.get('scenarios', []):
        scenarios.append(HazardScenario(
            node=item.get('node', equipment),
            parameter=item.get('parameter', '—'),
            guideword=item.get('guideword', '—'),
            cause=item.get('cause', '—'),
            consequence=item.get('consequence', '—'),
            safeguards=item.get('safeguards', []) or [],
            recommendation=item.get('recommendation', '—'),
            risk_rank=item.get('risk_rank', 'Screening'),
        ))
    return scenarios


def extract_document_insights(ai: AIClient, context_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return ai.ask_json(
        system_prompt=DOC_EXTRACTOR_SYSTEM,
        context_blocks=context_blocks,
        user_prompt=(
            'Extraia um resumo estruturado em JSON com as chaves: '
            'chemicals, equipment, instruments, interlocks, operating_limits, hazards, recommendations.'
        ),
        reasoning=False,
    )
