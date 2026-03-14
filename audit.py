from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from core.config import settings


def append_audit(event_type: str, payload: Dict[str, Any]) -> None:
    line = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'event_type': event_type,
        'payload': payload,
    }
    out = Path(settings.audit_dir) / 'audit_log.jsonl'
    with out.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + '\n')
