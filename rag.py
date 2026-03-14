from __future__ import annotations

import math
import re
import uuid
from typing import Iterable, List, Optional

import numpy as np

from core.config import settings
from core.models import DocumentChunk, RetrievedChunk
from services.ai_client import AIClient
from services.parsers import parse_uploaded_file, split_text


class LocalKnowledgeBase:
    def __init__(self, ai: Optional[AIClient] = None) -> None:
        self.ai = ai or AIClient()
        self.chunks: List[DocumentChunk] = []
        self._has_embeddings = False

    def ingest_streamlit_uploads(self, uploads: Iterable) -> int:
        added = 0
        new_chunks: List[DocumentChunk] = []
        for upload in uploads:
            pages = parse_uploaded_file(upload)
            for page_no, text in pages:
                for idx, chunk_text in enumerate(split_text(text, settings.chunk_size, settings.chunk_overlap), start=1):
                    chunk = DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        source_name=upload.name,
                        source_type=upload.type or 'document',
                        page=page_no,
                        text=chunk_text,
                        metadata={'chunk_no': idx},
                    )
                    new_chunks.append(chunk)
                    added += 1
        if new_chunks and self.ai.enabled:
            try:
                embeddings = self.ai.embed([c.text for c in new_chunks])
                for chunk, emb in zip(new_chunks, embeddings):
                    chunk.embedding = emb
                self._has_embeddings = True
            except Exception:
                self._has_embeddings = False
        self.chunks.extend(new_chunks)
        return added

    def search(self, query: str, top_k: int = 6) -> List[RetrievedChunk]:
        if not self.chunks:
            return []
        if self._has_embeddings and self.ai.enabled:
            try:
                q_emb = np.array(self.ai.embed([query])[0], dtype=float)
                scored = []
                for chunk in self.chunks:
                    if not chunk.embedding:
                        continue
                    c_emb = np.array(chunk.embedding, dtype=float)
                    denom = np.linalg.norm(q_emb) * np.linalg.norm(c_emb)
                    score = float(np.dot(q_emb, c_emb) / denom) if denom else 0.0
                    scored.append(RetrievedChunk(chunk=chunk, score=score, match_reason='semantic'))
                scored.sort(key=lambda x: x.score, reverse=True)
                return scored[:top_k]
            except Exception:
                pass
        q_terms = set(re.findall(r'[\w\-]+', query.lower()))
        scored = []
        for chunk in self.chunks:
            terms = set(re.findall(r'[\w\-]+', chunk.text.lower()))
            overlap = len(q_terms & terms)
            norm = math.sqrt(max(len(q_terms), 1) * max(len(terms), 1))
            score = overlap / norm if norm else 0.0
            scored.append(RetrievedChunk(chunk=chunk, score=score, match_reason='lexical'))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
