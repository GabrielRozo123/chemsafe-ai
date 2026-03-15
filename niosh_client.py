from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from cache_store import get_cached, set_cached


BASE = "https://www.cdc.gov/niosh/npg/"


def _normalize(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
        .replace(" ", "")
        .replace("-", "")
    )


def _safe_get_text(url: str, timeout: int = 10) -> str:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""


def _resolve_entry_url(name: str, cas: str = "") -> Optional[str]:
    if not name:
        return None

    first = _normalize(name)[:1]
    if not first or not first.isalpha():
        return None

    index_url = f"{BASE}npgsyn-{first}.html"
    html = _safe_get_text(index_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    target = _normalize(name)

    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not re.search(r"npgd\d+\.html", href):
            continue

        label = a.get_text(" ", strip=True)
        row_text = a.parent.get_text(" ", strip=True) if a.parent else label
        candidates.append((label, row_text, urljoin(index_url, href)))

    # 1) match CAS in row
    if cas:
        for label, row_text, url in candidates:
            if cas in row_text:
                return url

    # 2) exact normalized label
    for label, _, url in candidates:
        if _normalize(label).replace("*", "") == target:
            return url

    # 3) substring fallback
    for label, _, url in candidates:
        if target in _normalize(label):
            return url

    return None


def _f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def _mmhg_to_kpa(v: float) -> float:
    return v * 0.133322


def _extract_float(patterns: list[str], text: str) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                continue
    return None


def _extract_block(text: str, start: str, ends: list[str]) -> str:
    s = re.search(start, text, flags=re.IGNORECASE)
    if not s:
        return ""
    sub = text[s.end():]
    end_positions = []
    for e in ends:
        m = re.search(e, sub, flags=re.IGNORECASE)
        if m:
            end_positions.append(m.start())
    cut = min(end_positions) if end_positions else len(sub)
    return sub[:cut].strip()


def fetch_niosh_record(name: str = "", cas: str = "") -> Dict[str, Any]:
    cache_key = f"{name}|{cas}"
    cached = get_cached("niosh", cache_key, ttl_seconds=7 * 24 * 3600)
    if cached is not None:
        return cached

    entry_url = _resolve_entry_url(name, cas)
    if not entry_url:
        result = {}
        set_cached("niosh", cache_key, result)
        return result

    html = _safe_get_text(entry_url)
    if not html:
        result = {}
        set_cached("niosh", cache_key, result)
        return result

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"[ \t]+", " ", text)

    idlh_ppm = _extract_float(
        [
            r"IDLH\s+(?:Ca\s+)?\[?([0-9.]+)\s*ppm\]?",
        ],
        text,
    )

    rel_twa_ppm = _extract_float(
        [
            r"NIOSH REL.*?TWA\s+([0-9.]+)\s*ppm",
        ],
        text,
    )

    rel_st_ppm = _extract_float(
        [
            r"NIOSH REL.*?ST\s+([0-9.]+)\s*ppm",
        ],
        text,
    )

    osha_pel_twa_ppm = _extract_float(
        [
            r"OSHA PEL.*?TWA\s+([0-9.]+)\s*ppm",
        ],
        text,
    )

    mw = _extract_float(
        [r"Molecular Weight\s+([0-9.]+)"],
        text,
    )

    bp_f = _extract_float(
        [r"Boiling Point\s+([\-0-9.]+)\s*°?F"],
        text,
    )
    bp_c = _f_to_c(bp_f) if bp_f is not None else None

    flash_f = _extract_float(
        [r"Flash Point\s+(?:\([^)]+\)\s*)?([\-0-9.]+)\s*°?F"],
        text,
    )
    flash_c = _f_to_c(flash_f) if flash_f is not None else None

    vp_mmhg = _extract_float(
        [r"Vapor Pressure\s+([0-9.]+)\s*mmHg"],
        text,
    )
    vapor_pressure_kpa = _mmhg_to_kpa(vp_mmhg) if vp_mmhg is not None else None

    lel = _extract_float([r"Lower Explosive Limit\s+([0-9.]+)\s*%"], text)
    uel = _extract_float([r"Upper Explosive Limit\s+([0-9.]+)\s*%"], text)

    incompat_block = _extract_block(
        text,
        r"Incompatibilities\s*&\s*Reactivities",
        [
            r"Exposure Routes",
            r"Symptoms",
            r"Personal Protection",
            r"First Aid",
            r"Respirator Recommendations",
        ],
    )

    incompatibilities = []
    if incompat_block:
        cleaned = incompat_block.replace(";", ",")
        for item in [x.strip() for x in cleaned.split(",") if x.strip()]:
            incompatibilities.append(item)

    result = {
        "entry_url": entry_url,
        "molecular_weight": mw,
        "boiling_point_c": bp_c,
        "flash_point_c": flash_c,
        "vapor_pressure_kpa": vapor_pressure_kpa,
        "lfl_volpct": lel,
        "ufl_volpct": uel,
        "IDLH_ppm": idlh_ppm,
        "REL_TWA_ppm": rel_twa_ppm,
        "REL_ST_ppm": rel_st_ppm,
        "OSHA_PEL_TWA_ppm": osha_pel_twa_ppm,
        "incompatibilities": incompatibilities,
        "source": "NIOSH Pocket Guide",
    }

    set_cached("niosh", cache_key, result)
    return result
