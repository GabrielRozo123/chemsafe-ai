from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from cache_store import get_cached, set_cached


def _cas_to_nist_id(cas: str) -> str:
    return "C" + cas.replace("-", "").strip()


def _safe_get_text(url: str, timeout: int = 10) -> str:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""


def _find_first_record_url_by_name(name: str) -> Optional[str]:
    search_url = f"https://webbook.nist.gov/cgi/cbook.cgi?Name={quote_plus(name)}&Units=SI"
    html = _safe_get_text(search_url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "cgi/cbook.cgi?ID=" in href:
            if href.startswith("http"):
                return href
            return f"https://webbook.nist.gov{href}"
    return None


def _extract_float(patterns: list[str], text: str) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                continue
    return None


def _convert_pressure_to_kpa(value: float, unit: str) -> float:
    u = unit.lower().replace(" ", "")
    if u in {"kpa"}:
        return value
    if u in {"pa"}:
        return value / 1000.0
    if u in {"mmhg", "torr"}:
        return value * 0.133322
    if u in {"bar"}:
        return value * 100.0
    return value


def fetch_nist_record(name: str = "", cas: str = "") -> Dict[str, Any]:
    cache_key = f"{name}|{cas}"
    cached = get_cached("nist", cache_key, ttl_seconds=7 * 24 * 3600)
    if cached is not None:
        return cached

    url = None
    if cas:
        url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID={_cas_to_nist_id(cas)}&Units=SI"
    elif name:
        url = _find_first_record_url_by_name(name)

    if not url:
        result = {}
        set_cached("nist", cache_key, result)
        return result

    html = _safe_get_text(url)
    if not html:
        result = {}
        set_cached("nist", cache_key, result)
        return result

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    bp_c = _extract_float(
        [
            r"Boiling point\s*([\-+]?\d+(?:\.\d+)?)\s*°C",
            r"Tboil\s*([\-+]?\d+(?:\.\d+)?)\s*°C",
        ],
        text,
    )

    mp_c = _extract_float(
        [
            r"Melting point\s*([\-+]?\d+(?:\.\d+)?)\s*°C",
            r"Tfus\s*([\-+]?\d+(?:\.\d+)?)\s*°C",
        ],
        text,
    )

    vp_match = re.search(
        r"Vapor pressure\s*([\-+]?\d+(?:\.\d+)?)\s*(Pa|kPa|bar|mmHg|mm Hg|torr)",
        text,
        flags=re.IGNORECASE,
    )
    vapor_pressure_kpa = None
    if vp_match:
        try:
            vapor_pressure_kpa = _convert_pressure_to_kpa(float(vp_match.group(1)), vp_match.group(2))
        except Exception:
            vapor_pressure_kpa = None

    result = {
        "entry_url": url,
        "boiling_point_c": bp_c,
        "melting_point_c": mp_c,
        "vapor_pressure_kpa": vapor_pressure_kpa,
        "source": "NIST WebBook",
    }
    set_cached("nist", cache_key, result)
    return result
