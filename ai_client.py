from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

from core.config import settings
from core.models import CopilotAnswer
from data.prompts import COPILOT_SYSTEM
from services.audit import append_audit


class AIClient:
    def __init__(self) -> None:
        self.enabled = bool(os.getenv('OPENAI_API_KEY')) and OpenAI is not None
        self.client = OpenAI() if self.enabled else None

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text
        parts: List[str] = []
        for item in getattr(response, 'output', []) or []:
            for content in getattr(item, 'content', []) or []:
                text = getattr(content, 'text', None)
                if text:
                    parts.append(text)
        return '\n'.join(parts).strip()

    def ask(self, user_prompt: str, *, system_prompt: Optional[str] = None, context_blocks: Optional[Iterable[Dict[str, Any]]] = None, json_mode: bool = False, reasoning: bool = False) -> CopilotAnswer:
        if not self.enabled:
            return CopilotAnswer(
                answer='Integração OpenAI indisponível. Defina OPENAI_API_KEY para habilitar o copiloto, o gerador de HAZOP por IA e o redator de relatórios.',
                warnings=['OPENAI_API_KEY não configurada'],
            )

        blocks = []
        if system_prompt or COPILOT_SYSTEM:
            blocks.append({'role': 'system', 'content': [{'type': 'input_text', 'text': system_prompt or COPILOT_SYSTEM}]})

        if context_blocks:
            context_text = []
            for idx, block in enumerate(context_blocks, start=1):
                context_text.append(f"[CTX-{idx}] {block.get('source', 'fonte')}\n{block.get('text', '')}")
            blocks.append({'role': 'user', 'content': [{'type': 'input_text', 'text': 'Contexto documental:\n\n' + '\n\n'.join(context_text)}]})

        blocks.append({'role': 'user', 'content': [{'type': 'input_text', 'text': user_prompt}]})

        kwargs: Dict[str, Any] = {
            'model': settings.reasoning_model if reasoning else settings.text_model,
            'input': blocks,
        }
        if json_mode:
            kwargs['text'] = {'format': {'type': 'json_object'}}

        response = self.client.responses.create(**kwargs)
        answer = self._extract_text(response)
        append_audit('llm_call', {
            'model': kwargs['model'],
            'json_mode': json_mode,
            'system_prompt': (system_prompt or COPILOT_SYSTEM)[:500],
            'user_prompt': user_prompt[:2000],
            'answer_preview': answer[:1500],
        })
        return CopilotAnswer(answer=answer, raw=response)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.enabled:
            raise RuntimeError('OPENAI_API_KEY não configurada')
        response = self.client.embeddings.create(model=settings.embedding_model, input=texts)
        return [item.embedding for item in response.data]

    def ask_json(self, user_prompt: str, *, system_prompt: str, context_blocks: Optional[Iterable[Dict[str, Any]]] = None, reasoning: bool = False) -> Dict[str, Any]:
        result = self.ask(user_prompt, system_prompt=system_prompt, context_blocks=context_blocks, json_mode=True, reasoning=reasoning)
        try:
            return json.loads(result.answer)
        except json.JSONDecodeError:
            return {'error': 'invalid_json', 'raw': result.answer}
