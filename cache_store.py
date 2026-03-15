from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


CACHE_DIR = Path(".chemsafe_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(namespace: str, key: str) -> Path:
    digest = hashlib.sha1(f"{namespace}::{key}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{namespace}_{digest}.json"


def get_cached(namespace: str, key: str, ttl_seconds: int = 86400) -> Optional[Any]:
    path = _cache_path(namespace, key)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    ts = payload.get("_ts", 0)
    if time.time() - ts > ttl_seconds:
        return None

    return payload.get("data")


def set_cached(namespace: str, key: str, data: Any) -> None:
    path = _cache_path(namespace, key)
    payload = {"_ts": time.time(), "data": data}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
