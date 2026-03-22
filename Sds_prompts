"""Prompts e schemas JSON para extração estruturada de SDS/FISPQ.

O schema segue o formato ``json_schema`` da API OpenAI Responses,
compatível com o método ``ai_client.ask_json(schema=...)``.
"""
from __future__ import annotations

SDS_EXTRACTION_SYSTEM = """
Você é um especialista em leitura de Safety Data Sheets (SDS / FISPQ).

Sua função é extrair dados estruturados de segurança de processo a partir
do texto bruto de uma SDS.

Regras obrigatórias:
- Responder APENAS com o JSON solicitado, sem markdown nem explicações.
- Extrair valores numéricos puros (sem texto explicativo no campo de valor).
- Se um dado não estiver presente na SDS, usar null (não inventar).
- Para faixas (ex: "1.2 - 7.8 %"), usar o primeiro valor como lfl e o segundo como ufl.
- Converter unidades quando necessário:
  - °F → °C: (F - 32) × 5/9
  - mmHg → kPa: mmHg × 0.13332
  - mg/m³ pode ficar em mg/m³ (registrar a unidade)
  - ppm fica em ppm
- Incompatibilidades devem ser uma lista de strings curtas e técnicas.
- H-statements devem incluir código e texto (ex: "H225 — Líquido e vapor altamente inflamáveis").
- NFPA: extrair os 4 campos (health, fire, reactivity, special) como inteiros.
""".strip()

SDS_EXTRACTION_USER_TEMPLATE = """
Extraia os dados de segurança de processo da SDS/FISPQ abaixo.

--- INÍCIO DO TEXTO DA SDS ---
{sds_text}
--- FIM DO TEXTO DA SDS ---

Retorne um JSON com a estrutura especificada.
Campos não encontrados devem ser null.
""".strip()

SDS_EXTRACTION_SCHEMA = {
    "name": "sds_extraction_payload",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "identity": {
                "type": "object",
                "properties": {
                    "product_name": {"type": ["string", "null"]},
                    "chemical_name": {"type": ["string", "null"]},
                    "cas": {"type": ["string", "null"]},
                    "formula": {"type": ["string", "null"]},
                    "molecular_weight": {"type": ["number", "null"]},
                    "synonyms": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "product_name",
                    "chemical_name",
                    "cas",
                    "formula",
                    "molecular_weight",
                    "synonyms",
                ],
                "additionalProperties": False,
            },
            "hazards": {
                "type": "object",
                "properties": {
                    "ghs_h_statements": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "signal_word": {"type": ["string", "null"]},
                    "ghs_pictograms": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["ghs_h_statements", "signal_word", "ghs_pictograms"],
                "additionalProperties": False,
            },
            "nfpa": {
                "type": "object",
                "properties": {
                    "health": {"type": ["integer", "null"]},
                    "fire": {"type": ["integer", "null"]},
                    "reactivity": {"type": ["integer", "null"]},
                    "special": {"type": ["string", "null"]},
                },
                "required": ["health", "fire", "reactivity", "special"],
                "additionalProperties": False,
            },
            "physchem": {
                "type": "object",
                "properties": {
                    "flash_point_c": {"type": ["number", "null"]},
                    "boiling_point_c": {"type": ["number", "null"]},
                    "melting_point_c": {"type": ["number", "null"]},
                    "autoignition_c": {"type": ["number", "null"]},
                    "lfl_volpct": {"type": ["number", "null"]},
                    "ufl_volpct": {"type": ["number", "null"]},
                    "vapor_pressure_kpa_20c": {"type": ["number", "null"]},
                    "density_liquid_g_cm3": {"type": ["number", "null"]},
                    "vapor_density_air": {"type": ["number", "null"]},
                    "ph": {"type": ["string", "null"]},
                    "solubility_water": {"type": ["string", "null"]},
                },
                "required": [
                    "flash_point_c",
                    "boiling_point_c",
                    "melting_point_c",
                    "autoignition_c",
                    "lfl_volpct",
                    "ufl_volpct",
                    "vapor_pressure_kpa_20c",
                    "density_liquid_g_cm3",
                    "vapor_density_air",
                    "ph",
                    "solubility_water",
                ],
                "additionalProperties": False,
            },
            "exposure_limits": {
                "type": "object",
                "properties": {
                    "idlh_ppm": {"type": ["number", "null"]},
                    "idlh_mg_m3": {"type": ["number", "null"]},
                    "tlv_twa_ppm": {"type": ["number", "null"]},
                    "tlv_stel_ppm": {"type": ["number", "null"]},
                    "tlv_stel_mg_m3": {"type": ["number", "null"]},
                    "rel_twa_ppm": {"type": ["number", "null"]},
                    "osha_pel_twa_ppm": {"type": ["number", "null"]},
                    "erpg_2_ppm": {"type": ["number", "null"]},
                    "erpg_3_ppm": {"type": ["number", "null"]},
                },
                "required": [
                    "idlh_ppm",
                    "idlh_mg_m3",
                    "tlv_twa_ppm",
                    "tlv_stel_ppm",
                    "tlv_stel_mg_m3",
                    "rel_twa_ppm",
                    "osha_pel_twa_ppm",
                    "erpg_2_ppm",
                    "erpg_3_ppm",
                ],
                "additionalProperties": False,
            },
            "reactivity": {
                "type": "object",
                "properties": {
                    "incompatibilities": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "hazardous_decomposition": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "conditions_to_avoid": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "stability_notes": {"type": ["string", "null"]},
                },
                "required": [
                    "incompatibilities",
                    "hazardous_decomposition",
                    "conditions_to_avoid",
                    "stability_notes",
                ],
                "additionalProperties": False,
            },
            "firefighting": {
                "type": "object",
                "properties": {
                    "suitable_extinguishing": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "unsuitable_extinguishing": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "special_hazards": {"type": ["string", "null"]},
                },
                "required": [
                    "suitable_extinguishing",
                    "unsuitable_extinguishing",
                    "special_hazards",
                ],
                "additionalProperties": False,
            },
            "extraction_confidence": {
                "type": "string",
                "enum": ["alta", "media", "baixa"],
            },
            "extraction_notes": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "identity",
            "hazards",
            "nfpa",
            "physchem",
            "exposure_limits",
            "reactivity",
            "firefighting",
            "extraction_confidence",
            "extraction_notes",
        ],
        "additionalProperties": False,
    },
}
