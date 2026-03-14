from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "ChemSafe Pro AI"
    app_version: str = "3.0"

    # Modelos válidos da API atual
    text_model: str = os.getenv("OPENAI_MODEL_TEXT", "gpt-5-mini")
    reasoning_model: str = os.getenv("OPENAI_MODEL_REASONING", "gpt-5")
    embedding_model: str = os.getenv("OPENAI_MODEL_EMBED", "text-embedding-3-large")

    audit_dir: Path = Path(os.getenv("CHEMSAFE_AUDIT_DIR", ".chemsafe_audit"))
    max_context_chunks: int = 8
    chunk_size: int = 1200
    chunk_overlap: int = 200
    company_name: str = "ChemSafe Pro"
    linkedin_url: str = "https://www.linkedin.com/in/gabriel-hernandez-rozo-30751325b"


settings = Settings()
settings.audit_dir.mkdir(parents=True, exist_ok=True)
