"""Motor de leitura de SDS/FISPQ para o ChemSafe Pro.

Fluxo:
1.  ``extract_text_from_sds_pdf``  — pymupdf extrai texto bruto do PDF
2.  ``parse_sds_with_ai``          — LLM retorna JSON estruturado
3.  ``parse_sds_with_regex``        — fallback se IA indisponível
4.  ``merge_sds_into_profile``      — preenche gaps do CompoundProfile

Compatível com SDS em português (FISPQ/NBR 14725) e inglês (GHS/OSHA).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import fitz  # pymupdf — já no requirements.txt
import pandas as pd

from compound_profile import CompoundProfile, PropertyValue
from sds_prompts import (
    SDS_EXTRACTION_SCHEMA,
    SDS_EXTRACTION_SYSTEM,
    SDS_EXTRACTION_USER_TEMPLATE,
)


# ======================================================================
# 1. Extração de texto do PDF
# ======================================================================

def extract_text_from_sds_pdf(file_bytes: bytes, max_pages: int = 20) -> str:
    """Extrai texto de um PDF de SDS/FISPQ via pymupdf.

    Retorna o texto concatenado das primeiras ``max_pages`` páginas,
    com separador por página para contexto do LLM.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: List[str] = []
    for idx, page in enumerate(doc):
        if idx >= max_pages:
            break
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[PÁGINA {idx + 1}]\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages)


# ======================================================================
# 2. Parsing via IA (rota principal)
# ======================================================================

def parse_sds_with_ai(ai_client, sds_text: str) -> Dict[str, Any]:
    """Envia o texto da SDS para o LLM e retorna JSON estruturado.

    Usa ``ai_client.ask_json`` com schema estrito para garantir
    que o retorno segue a estrutura esperada.

    Returns:
        Dict com as seções extraídas ou ``{"error": ...}`` em caso de falha.
    """
    if not getattr(ai_client, "enabled", False):
        return {"error": "openai_disabled", "raw": "OPENAI_API_KEY não configurada"}

    # Limita o texto para caber na context window (~120k chars ≈ 30k tokens)
    truncated = sds_text[:120_000]

    user_prompt = SDS_EXTRACTION_USER_TEMPLATE.format(sds_text=truncated)

    result = ai_client.ask_json(
        user_prompt,
        system_prompt=SDS_EXTRACTION_SYSTEM,
        reasoning=False,
        schema=SDS_EXTRACTION_SCHEMA,
    )

    return result


# ======================================================================
# 3. Parsing via regex (fallback sem IA)
# ======================================================================

def _find_float(patterns: List[str], text: str) -> Optional[float]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except (ValueError, IndexError):
                continue
    return None


def _find_cas(text: str) -> Optional[str]:
    m = re.search(r"\b(\d{2,7}-\d{2}-\d)\b", text)
    return m.group(1) if m else None


def _find_h_statements(text: str) -> List[str]:
    return re.findall(r"(H\d{3}[A-Za-z]?\s*[-—–:]\s*[^\n]{10,80})", text)


def _f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def parse_sds_with_regex(sds_text: str) -> Dict[str, Any]:
    """Extração baseada em regex para os campos mais comuns.

    Não é tão completa quanto a rota por IA, mas funciona sem API key
    e captura os dados mais críticos para process safety.
    """
    txt = sds_text

    # --- Identidade ---
    cas = _find_cas(txt)

    # --- Físico-química ---
    flash_c = _find_float(
        [
            r"(?:flash\s*point|ponto\s*de\s*fulgor)[:\s]*([-\d.,]+)\s*°?\s*C",
            r"(?:flash\s*point|ponto\s*de\s*fulgor)[:\s]*([-\d.,]+)\s*°?\s*F",
        ],
        txt,
    )
    # Se achou em °F, converter
    if flash_c is None:
        flash_f = _find_float(
            [r"(?:flash\s*point|ponto\s*de\s*fulgor)[:\s]*([-\d.,]+)\s*°?\s*F"],
            txt,
        )
        if flash_f is not None:
            flash_c = _f_to_c(flash_f)

    bp_c = _find_float(
        [
            r"(?:boiling\s*point|ponto\s*de\s*ebuli)[^:]*[:\s]*([-\d.,]+)\s*°?\s*C",
        ],
        txt,
    )

    ait_c = _find_float(
        [
            r"(?:auto[- ]?ignition|temperatura\s*de\s*autoigni)[^:]*[:\s]*([-\d.,]+)\s*°?\s*C",
        ],
        txt,
    )

    lfl = _find_float(
        [
            r"(?:lower\s*(?:explosive|flammab)|LFL|LIE|LEL|limite\s*inferior)[^:]*[:\s]*([\d.,]+)\s*%",
        ],
        txt,
    )

    ufl = _find_float(
        [
            r"(?:upper\s*(?:explosive|flammab)|UFL|LSE|UEL|limite\s*superior)[^:]*[:\s]*([\d.,]+)\s*%",
        ],
        txt,
    )

    vp = _find_float(
        [
            r"(?:vapor\s*pressure|press[ãa]o\s*de\s*vapor)[^:]*[:\s]*([\d.,]+)\s*(?:kPa|hPa)",
            r"(?:vapor\s*pressure|press[ãa]o\s*de\s*vapor)[^:]*[:\s]*([\d.,]+)\s*mmHg",
        ],
        txt,
    )

    density = _find_float(
        [
            r"(?:density|densidade)[^:]*[:\s]*([\d.,]+)\s*(?:g/cm|g/mL|kg/L)",
        ],
        txt,
    )

    # --- Exposição ---
    idlh_ppm = _find_float([r"IDLH[:\s]*([\d.,]+)\s*ppm"], txt)
    tlv_twa = _find_float([r"(?:TLV[- ]?TWA|TWA)[:\s]*([\d.,]+)\s*ppm"], txt)

    # --- H-statements ---
    h_statements = _find_h_statements(txt)

    # --- Incompatibilidades ---
    incompat_block = ""
    m = re.search(
        r"(?:incompatib|materiais?\s*a\s*evitar|substâncias?\s*incomp)[^:]*[:](.*?)(?:Seç[ãa]o|Section|\d{1,2}\.\s)",
        txt,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        incompat_block = m.group(1).strip()

    incompatibilities = []
    if incompat_block:
        for item in re.split(r"[;,\n•·\-]", incompat_block):
            clean = item.strip()
            if len(clean) > 3 and len(clean) < 120:
                incompatibilities.append(clean)

    return {
        "identity": {
            "product_name": None,
            "chemical_name": None,
            "cas": cas,
            "formula": None,
            "molecular_weight": None,
            "synonyms": [],
        },
        "hazards": {
            "ghs_h_statements": h_statements[:15],
            "signal_word": None,
            "ghs_pictograms": [],
        },
        "nfpa": {"health": None, "fire": None, "reactivity": None, "special": None},
        "physchem": {
            "flash_point_c": flash_c,
            "boiling_point_c": bp_c,
            "melting_point_c": None,
            "autoignition_c": ait_c,
            "lfl_volpct": lfl,
            "ufl_volpct": ufl,
            "vapor_pressure_kpa_20c": vp,
            "density_liquid_g_cm3": density,
            "vapor_density_air": None,
            "ph": None,
            "solubility_water": None,
        },
        "exposure_limits": {
            "idlh_ppm": idlh_ppm,
            "idlh_mg_m3": None,
            "tlv_twa_ppm": tlv_twa,
            "tlv_stel_ppm": None,
            "tlv_stel_mg_m3": None,
            "rel_twa_ppm": None,
            "osha_pel_twa_ppm": None,
            "erpg_2_ppm": None,
            "erpg_3_ppm": None,
        },
        "reactivity": {
            "incompatibilities": incompatibilities[:10],
            "hazardous_decomposition": [],
            "conditions_to_avoid": [],
            "stability_notes": None,
        },
        "firefighting": {
            "suitable_extinguishing": [],
            "unsuitable_extinguishing": [],
            "special_hazards": None,
        },
        "extraction_confidence": "baixa",
        "extraction_notes": [
            "Extração por regex (IA indisponível). Dados parciais — revisar manualmente.",
        ],
    }


# ======================================================================
# 4. Merge com CompoundProfile existente
# ======================================================================

_PHYSCHEM_MAP = {
    "flash_point_c": ("°C", "flash_point_c"),
    "boiling_point_c": ("°C", "boiling_point_c"),
    "melting_point_c": ("°C", "melting_point_c"),
    "autoignition_c": ("°C", "autoignition_c"),
    "lfl_volpct": ("%vol", "lfl_volpct"),
    "ufl_volpct": ("%vol", "ufl_volpct"),
    "vapor_pressure_kpa_20c": ("kPa", "vapor_pressure_kpa_20c"),
    "density_liquid_g_cm3": ("g/cm3", "density_liquid_g_cm3"),
    "vapor_density_air": ("air=1", "vapor_density_air"),
}

_EXPOSURE_MAP = {
    "idlh_ppm": ("ppm", "IDLH_ppm"),
    "idlh_mg_m3": ("mg/m3", "IDLH_mg_m3"),
    "tlv_twa_ppm": ("ppm", "TLV_TWA_ppm"),
    "tlv_stel_ppm": ("ppm", "TLV_STEL_ppm"),
    "tlv_stel_mg_m3": ("mg/m3", "TLV_STEL_mg_m3"),
    "rel_twa_ppm": ("ppm", "REL_TWA_ppm"),
    "osha_pel_twa_ppm": ("ppm", "OSHA_PEL_TWA_ppm"),
    "erpg_2_ppm": ("ppm", "ERPG_2_ppm"),
    "erpg_3_ppm": ("ppm", "ERPG_3_ppm"),
}


def merge_sds_into_profile(
    profile: CompoundProfile,
    sds_data: Dict[str, Any],
    *,
    overwrite: bool = False,
) -> tuple[CompoundProfile, list[dict]]:
    """Preenche gaps do perfil com dados extraídos da SDS.

    Args:
        profile: Perfil atual do composto.
        sds_data: Dicionário retornado por ``parse_sds_with_ai`` ou ``parse_sds_with_regex``.
        overwrite: Se True, sobrescreve valores existentes. Se False (padrão),
            preenche apenas campos faltantes (None ou "").

    Returns:
        Tuple de (profile atualizado, lista de mudanças aplicadas).
    """
    changes: list[dict] = []
    source_label = "SDS Upload"
    confidence_label = "document"

    # --- Physchem ---
    physchem = sds_data.get("physchem", {})
    for sds_key, (unit, profile_key) in _PHYSCHEM_MAP.items():
        value = physchem.get(sds_key)
        if value is None:
            continue

        existing = profile.prop(profile_key)
        if existing is not None and not overwrite:
            continue

        profile.physchem[profile_key] = PropertyValue(
            value=value, unit=unit, source=source_label, confidence=confidence_label
        )
        changes.append({
            "Campo": profile_key,
            "Valor anterior": existing,
            "Valor SDS": value,
            "Unidade": unit,
            "Ação": "Atualizado" if existing is not None else "Preenchido",
        })

    # --- Exposure limits ---
    exposure = sds_data.get("exposure_limits", {})
    for sds_key, (unit, profile_key) in _EXPOSURE_MAP.items():
        value = exposure.get(sds_key)
        if value is None:
            continue

        existing = profile.limit(profile_key)
        if existing is not None and not overwrite:
            continue

        profile.exposure_limits[profile_key] = PropertyValue(
            value=value, unit=unit, source=source_label, confidence=confidence_label
        )
        changes.append({
            "Campo": profile_key,
            "Valor anterior": existing,
            "Valor SDS": value,
            "Unidade": unit,
            "Ação": "Atualizado" if existing is not None else "Preenchido",
        })

    # --- Hazards (H-statements) ---
    h_statements = sds_data.get("hazards", {}).get("ghs_h_statements", [])
    if h_statements:
        existing_codes = {h.split(" ")[0] for h in profile.hazards}
        new_hazards = [h for h in h_statements if h.split(" ")[0] not in existing_codes]
        if new_hazards:
            profile.hazards.extend(new_hazards)
            changes.append({
                "Campo": "hazards",
                "Valor anterior": f"{len(profile.hazards) - len(new_hazards)} H-statements",
                "Valor SDS": f"+{len(new_hazards)} novos",
                "Unidade": "—",
                "Ação": "Adicionado",
            })

    # --- NFPA ---
    nfpa = sds_data.get("nfpa", {})
    for key in ["health", "fire", "reactivity", "special"]:
        value = nfpa.get(key)
        if value is None:
            continue
        existing = profile.nfpa.get(key)
        if existing not in [None, 0, ""] and not overwrite:
            continue
        profile.nfpa[key] = value
        if existing != value:
            changes.append({
                "Campo": f"nfpa.{key}",
                "Valor anterior": existing,
                "Valor SDS": value,
                "Unidade": "—",
                "Ação": "Atualizado" if existing not in [None, 0, ""] else "Preenchido",
            })

    # --- Incompatibilidades ---
    new_incompat = sds_data.get("reactivity", {}).get("incompatibilities", [])
    if new_incompat:
        existing_set = set(
            x.lower() for x in profile.storage.get("incompatibilities", [])
        )
        added = [x for x in new_incompat if x.lower() not in existing_set]
        if added:
            current = profile.storage.get("incompatibilities", [])
            profile.storage["incompatibilities"] = current + added
            changes.append({
                "Campo": "incompatibilities",
                "Valor anterior": f"{len(current)} itens",
                "Valor SDS": f"+{len(added)} novos",
                "Unidade": "—",
                "Ação": "Adicionado",
            })

    # --- Source trace ---
    profile.source_trace.append({
        "field": "sds_upload",
        "source": source_label,
    })

    return profile, changes


# ======================================================================
# 5. Helpers de visualização
# ======================================================================

def sds_data_to_review_df(sds_data: Dict[str, Any]) -> pd.DataFrame:
    """Converte o JSON extraído em um DataFrame legível para revisão."""
    rows = []

    identity = sds_data.get("identity", {})
    for key, label in [
        ("product_name", "Nome do produto"),
        ("chemical_name", "Nome químico"),
        ("cas", "CAS"),
        ("formula", "Fórmula"),
        ("molecular_weight", "Massa molar"),
    ]:
        value = identity.get(key)
        if value is not None:
            rows.append({"Seção": "Identidade", "Campo": label, "Valor": str(value), "Unidade": ""})

    physchem = sds_data.get("physchem", {})
    labels_physchem = {
        "flash_point_c": ("Ponto de fulgor", "°C"),
        "boiling_point_c": ("Ponto de ebulição", "°C"),
        "melting_point_c": ("Ponto de fusão", "°C"),
        "autoignition_c": ("Autoignição", "°C"),
        "lfl_volpct": ("LII", "%vol"),
        "ufl_volpct": ("LSI", "%vol"),
        "vapor_pressure_kpa_20c": ("Pressão de vapor", "kPa"),
        "density_liquid_g_cm3": ("Densidade", "g/cm³"),
        "vapor_density_air": ("Dens. vapor (ar=1)", "—"),
    }
    for key, (label, unit) in labels_physchem.items():
        value = physchem.get(key)
        if value is not None:
            rows.append({"Seção": "Físico-química", "Campo": label, "Valor": str(value), "Unidade": unit})

    exposure = sds_data.get("exposure_limits", {})
    labels_exp = {
        "idlh_ppm": ("IDLH", "ppm"),
        "idlh_mg_m3": ("IDLH", "mg/m³"),
        "tlv_twa_ppm": ("TLV-TWA", "ppm"),
        "tlv_stel_ppm": ("TLV-STEL", "ppm"),
        "rel_twa_ppm": ("REL-TWA", "ppm"),
        "osha_pel_twa_ppm": ("OSHA PEL-TWA", "ppm"),
        "erpg_2_ppm": ("ERPG-2", "ppm"),
        "erpg_3_ppm": ("ERPG-3", "ppm"),
    }
    for key, (label, unit) in labels_exp.items():
        value = exposure.get(key)
        if value is not None:
            rows.append({"Seção": "Exposição", "Campo": label, "Valor": str(value), "Unidade": unit})

    hazards = sds_data.get("hazards", {})
    for h in hazards.get("ghs_h_statements", []):
        rows.append({"Seção": "Perigos GHS", "Campo": "H-statement", "Valor": h, "Unidade": ""})

    incompat = sds_data.get("reactivity", {}).get("incompatibilities", [])
    for item in incompat:
        rows.append({"Seção": "Reatividade", "Campo": "Incompatibilidade", "Valor": item, "Unidade": ""})

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Seção", "Campo", "Valor", "Unidade"])


def build_merge_summary(changes: list[dict]) -> dict:
    """Gera resumo do merge para exibição no UI."""
    if not changes:
        return {"total": 0, "preenchidos": 0, "atualizados": 0, "adicionados": 0}

    return {
        "total": len(changes),
        "preenchidos": sum(1 for c in changes if c["Ação"] == "Preenchido"),
        "atualizados": sum(1 for c in changes if c["Ação"] == "Atualizado"),
        "adicionados": sum(1 for c in changes if c["Ação"] == "Adicionado"),
    }
