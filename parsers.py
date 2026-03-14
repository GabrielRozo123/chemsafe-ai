from __future__ import annotations

import io
import json
from pathlib import Path
from typing import List, Tuple

import fitz  # type: ignore
import pandas as pd
from docx import Document  # type: ignore


def _read_pdf(file_bytes: bytes) -> List[Tuple[int, str]]:
    doc = fitz.open(stream=file_bytes, filetype='pdf')
    pages = []
    for idx, page in enumerate(doc, start=1):
        pages.append((idx, page.get_text('text')))
    return pages


def _read_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


def _read_spreadsheet(file_bytes: bytes, suffix: str) -> str:
    buffer = io.BytesIO(file_bytes)
    if suffix == '.csv':
        df = pd.read_csv(buffer)
        return df.head(200).to_markdown(index=False)
    sheets = pd.read_excel(buffer, sheet_name=None)
    chunks = []
    for name, df in sheets.items():
        chunks.append(f'# Sheet: {name}\n' + df.head(150).to_markdown(index=False))
    return '\n\n'.join(chunks)


def parse_uploaded_file(uploaded_file) -> List[Tuple[int | None, str]]:
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    payload = uploaded_file.getvalue()
    if suffix == '.pdf':
        return _read_pdf(payload)
    if suffix == '.docx':
        return [(None, _read_docx(payload))]
    if suffix in {'.csv', '.xlsx', '.xls'}:
        return [(None, _read_spreadsheet(payload, suffix))]
    if suffix in {'.txt', '.md', '.py', '.json'}:
        text = payload.decode('utf-8', errors='ignore')
        if suffix == '.json':
            try:
                text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
            except Exception:
                pass
        return [(None, text)]
    return [(None, payload.decode('utf-8', errors='ignore'))]


def split_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    cleaned = ' '.join(text.split())
    if not cleaned:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks
