from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Optional

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import settings


@dataclass
class KnowledgeChunk:
    text: str
    source_name: str
    page: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchHit:
    chunk: KnowledgeChunk
    score: float
    match_reason: str


class LocalKnowledgeBase:
    def __init__(self, ai_client: Any) -> None:
        self.ai = ai_client
        self.chunks: List[KnowledgeChunk] = []

    # ------------------------------------------------------------------
    # ingest
    # ------------------------------------------------------------------
    def ingest_streamlit_uploads(self, uploads: Iterable[Any]) -> int:
        added = 0
        for upload in uploads:
            try:
                text = self._extract_text_from_upload(upload)
                if not text.strip():
                    continue
                new_chunks = self._chunk_document(text, upload.name)
                self._attach_embeddings_if_available(new_chunks)
                self.chunks.extend(new_chunks)
                added += len(new_chunks)
            except Exception:
                # segue sem quebrar o app
                continue
        return added

    def _extract_text_from_upload(self, upload: Any) -> str:
        suffix = Path(upload.name).suffix.lower()
        data = upload.read()

        if suffix in {".txt", ".md", ".json"}:
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1", errors="ignore")

        if suffix == ".csv":
            try:
                import pandas as pd
                from io import StringIO

                text = data.decode("utf-8", errors="ignore")
                df = pd.read_csv(StringIO(text))
                return df.to_csv(index=False)
            except Exception:
                return data.decode("utf-8", errors="ignore")

        if suffix in {".xlsx", ".xls"}:
            try:
                import pandas as pd
                from io import BytesIO

                xls = pd.ExcelFile(BytesIO(data))
                blocks = []
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    blocks.append(f"[SHEET] {sheet}\n{df.to_csv(index=False)}")
                return "\n\n".join(blocks)
            except Exception:
                return ""

        if suffix == ".pdf":
            # tenta pypdf
            try:
                from io import BytesIO
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(data))
                pages = []
                for i, page in enumerate(reader.pages, start=1):
                    try:
                        txt = page.extract_text() or ""
                    except Exception:
                        txt = ""
                    if txt.strip():
                        pages.append(f"[PAGE {i}]\n{txt}")
                return "\n\n".join(pages)
            except Exception:
                return ""

        if suffix == ".docx":
            try:
                from io import BytesIO
                from docx import Document

                doc = Document(BytesIO(data))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                return "\n".join(paragraphs)
            except Exception:
                return ""

        # fallback bruto
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _chunk_document(self, text: str, source_name: str) -> List[KnowledgeChunk]:
        clean = self._normalize_text(text)
        if not clean:
            return []

        chunk_size = max(300, int(settings.chunk_size))
        overlap = max(0, int(settings.chunk_overlap))
        step = max(1, chunk_size - overlap)

        chunks: List[KnowledgeChunk] = []
        for start in range(0, len(clean), step):
            end = start + chunk_size
            piece = clean[start:end].strip()
            if not piece:
                continue

            page = None
            m = re.search(r"\[PAGE\s+(\d+)\]", piece)
            if m:
                page = int(m.group(1))

            chunks.append(
                KnowledgeChunk(
                    text=piece,
                    source_name=source_name,
                    page=page,
                )
            )

        return chunks

    def _attach_embeddings_if_available(self, chunks: List[KnowledgeChunk]) -> None:
        if not chunks:
            return
        if not getattr(self.ai, "enabled", False):
            return

        try:
            texts = [c.text[:8000] for c in chunks]
            vectors = self.ai.embed(texts)
            for c, v in zip(chunks, vectors):
                c.embedding = v
        except Exception:
            # fallback lexical se embeddings falharem
            return

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: int = 6) -> List[SearchHit]:
        if not query.strip() or not self.chunks:
            return []

        use_embeddings = getattr(self.ai, "enabled", False) and any(c.embedding is not None for c in self.chunks)

        if use_embeddings:
            try:
                q_vec = self.ai.embed([query])[0]
                hits = self._vector_search(q_vec, query, top_k)
                if hits:
                    return hits
            except Exception:
                pass

        return self._lexical_search(query, top_k)

    def _vector_search(self, query_vec: List[float], query: str, top_k: int) -> List[SearchHit]:
        scored: List[SearchHit] = []
        q_tokens = self._tokenize(query)

        for chunk in self.chunks:
            if chunk.embedding is None:
                continue
            sim = self._cosine_similarity(query_vec, chunk.embedding)
            lex_bonus = self._token_overlap_score(q_tokens, self._tokenize(chunk.text))
            score = 0.85 * sim + 0.15 * lex_bonus
            if score > 0:
                scored.append(
                    SearchHit(
                        chunk=chunk,
                        score=score,
                        match_reason="vector+lexical",
                    )
                )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def _lexical_search(self, query: str, top_k: int) -> List[SearchHit]:
        q_tokens = self._tokenize(query)
        scored: List[SearchHit] = []

        for chunk in self.chunks:
            c_tokens = self._tokenize(chunk.text)
            score = self._token_overlap_score(q_tokens, c_tokens)
            if score > 0:
                scored.append(
                    SearchHit(
                        chunk=chunk,
                        score=score,
                        match_reason="lexical",
                    )
                )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    # ------------------------------------------------------------------
    # utils
    # ------------------------------------------------------------------
    def _normalize_text(self, text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r"[a-zà-úA-ZÀ-Ú0-9_\-/\.]+", text)
        return [t for t in tokens if len(t) > 1]

    def _token_overlap_score(self, q_tokens: List[str], c_tokens: List[str]) -> float:
        if not q_tokens or not c_tokens:
            return 0.0
        q_set = set(q_tokens)
        c_set = set(c_tokens)
        inter = len(q_set & c_set)
        if inter == 0:
            return 0.0
        return inter / math.sqrt(len(q_set) * len(c_set))

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
