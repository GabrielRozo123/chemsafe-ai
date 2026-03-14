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
    node: str
    parameter: str
    guideword: str
    cause: str
    consequence: str
    safeguards: List[str]
    recommendation: str
    risk_rank: str


@dataclass
class ReportBundle:
    html: bytes
    pdf: bytes
    markdown: bytes
    filename_stem: str
