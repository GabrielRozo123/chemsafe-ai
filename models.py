from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocumentChunk:
    chunk_id: str
    source_name: str
    source_type: str
    page: Optional[int]
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float
    match_reason: str


@dataclass
class CopilotAnswer:
    answer: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw: Optional[Any] = None


@dataclass
class HazardScenario:
    """Cenário de perigo gerado por IA ou por motor determinístico.

    NOTA: os campos foram alinhados com o schema JSON usado em
    ``hazard_extractor.generate_hazop_from_text`` e com o prompt
    ``PREHAZOP_JSON_SCHEMA``.  Os nomes antigos (parameter, guideword,
    recommendation singular) foram substituídos pelos que o código
    efetivamente produz.
    """

    node: str
    deviation: str
    cause: str
    consequence: str
    safeguards: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    severity: str = "Medium"
    likelihood: str = "Medium"
    risk_rank: str = "Médio"


@dataclass
class ReportBundle:
    html: bytes
    pdf: bytes
    markdown: bytes
    filename_stem: str
