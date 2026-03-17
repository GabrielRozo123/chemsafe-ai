from __future__ import annotations

import unicodedata
import re

# Dicionário expandido para a indústria de processos
PT_EN_ALIASES = {
    "agua": "water", "água": "water",
    "amonia": "ammonia", "amônia": "ammonia",
    "acido sulfurico": "sulfuric acid", "ácido sulfúrico": "sulfuric acid",
    "acido cloridrico": "hydrochloric acid", "ácido clorídrico": "hydrochloric acid",
    "acido nitrico": "nitric acid", "ácido nítrico": "nitric acid",
    "acido acetico": "acetic acid", "ácido acético": "acetic acid",
    "soda caustica": "sodium hydroxide", "soda cáustica": "sodium hydroxide",
    "hidroxido de sodio": "sodium hydroxide", "hidróxido de sódio": "sodium hydroxide",
    "hipoclorito de sodio": "sodium hypochlorite", "hipoclorito de sódio": "sodium hypochlorite",
    "etanol": "ethanol", "alcool etilico": "ethanol", "álcool etílico": "ethanol",
    "metanol": "methanol", "acetona": "acetone", "propanona": "acetone",
    "tolueno": "toluene", "benzeno": "benzene", "xileno": "xylene",
    "metano": "methane", "etano": "ethane", "propano": "propane", "butano": "butane",
    "hexano": "hexane", "heptano": "heptane", "etileno": "ethylene", "propileno": "propylene",
    "amida formica": "formamide", "formaldeido": "formaldehyde", "formaldeído": "formaldehyde",
    "amina": "amine", "cloro": "chlorine", "gas cloro": "chlorine", "gás cloro": "chlorine",
    "hidrogenio": "hydrogen", "hidrogênio": "hydrogen", "oxigenio": "oxygen", "oxigênio": "oxygen"
}

def normalize_query(text: str) -> str:
    text = (text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())

def expand_search_candidates(query: str) -> list[str]:
    q_original = (query or "").strip()
    if not q_original:
        return[]

    # 1. ATALHO INTELIGENTE: É um número CAS? (Ex: 7664-41-7)
    # Se for CAS, não traduzimos, mandamos direto para a API para busca exata e rápida.
    if re.match(r'^\d{2,7}-\d{2}-\d$', q_original):
        return [q_original]

    q = normalize_query(q_original)
    candidates =[]
    seen = set()

    def add(x: str):
        x = (x or "").strip()
        if not x: return
        key = x.lower()
        if key not in seen:
            seen.add(key)
            candidates.append(x)

    add(q_original)
    add(q)
    add(q.replace("-", ""))
    
    # 2. Tradução inteligente
    translated = PT_EN_ALIASES.get(q)
    if translated:
        add(translated)
        add(translated.title())

    # 3. Fórmulas químicas simples (Ex: H2SO4, NaOH)
    if all(ch.isalnum() for ch in q.replace(" ", "")):
        add(q.upper().replace(" ", ""))

    return candidates
