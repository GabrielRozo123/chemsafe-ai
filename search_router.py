from __future__ import annotations

import unicodedata


PT_EN_ALIASES = {
    "agua": "water",
    "água": "water",
    "amonia": "ammonia",
    "amônia": "ammonia",
    "acido sulfurico": "sulfuric acid",
    "ácido sulfúrico": "sulfuric acid",
    "acido cloridrico": "hydrochloric acid",
    "ácido clorídrico": "hydrochloric acid",
    "acido nitrico": "nitric acid",
    "ácido nítrico": "nitric acid",
    "acido acetico": "acetic acid",
    "ácido acético": "acetic acid",
    "etanol": "ethanol",
    "metanol": "methanol",
    "acetona": "acetone",
    "tolueno": "toluene",
    "benzeno": "benzene",
    "metano": "methane",
    "etano": "ethane",
    "propano": "propane",
    "butano": "butane",
    "hexano": "hexane",
    "heptano": "heptane",
    "etileno": "ethylene",
    "propileno": "propylene",
    "amida formica": "formamide",
    "formaldeido": "formaldehyde",
    "formaldeído": "formaldehyde",
    "amina": "amine",
}


def normalize_query(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


def expand_search_candidates(query: str) -> list[str]:
    q = normalize_query(query)
    if not q:
        return []

    candidates = []
    seen = set()

    def add(x: str):
        x = (x or "").strip()
        if not x:
            return
        key = x.lower()
        if key not in seen:
            seen.add(key)
            candidates.append(x)

    add(query.strip())
    add(q)
    add(q.replace("-", ""))
    add(q.replace(" ", ""))
    add(q.upper().replace(" ", ""))

    translated = PT_EN_ALIASES.get(q)
    if translated:
        add(translated)
        add(translated.title())

    # fórmulas químicas simples
    if all(ch.isalnum() for ch in q.replace(" ", "")):
        add(q.upper().replace(" ", ""))

    return candidates
