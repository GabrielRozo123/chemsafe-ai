from __future__ import annotations

import pandas as pd

from risk_taxonomy import ACTION_COLUMN_ALIASES, ACTION_VALUE_MAPPINGS, AACE_CLASS5_LIBRARY


def get_action_col(df):
    if not isinstance(df, pd.DataFrame) or df.empty or len(df.columns) == 0:
        return "Ação Recomendada"

    possible_names = [
        "Ação Recomendada",
        "Ação",
        "Recomendação",
        "Ações",
        "Descrição",
        "Ação Requerida",
    ]
    for name in possible_names:
        if name in df.columns:
            return name

    excluded = [
        "Origem",
        "Criticidade",
        "Status",
        "Responsável",
        "Prazo",
        "Prazo (Dias)",
        "Recurso",
        "Hierarquia NIOSH",
        "Requer MOC?",
        "Pacote AACE",
        "Custo Min (R$)",
        "Custo P50 (R$)",
        "Custo Máx (R$)",
    ]
    for col in df.columns:
        if col not in excluded:
            return col
    return df.columns[-1]


def normalize_whitespace(value):
    if not isinstance(value, str):
        return value
    import re
    value = value.replace("\xa0", " ")
    value = value.replace("Â\xa0", " ")
    value = value.replace("Â ", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def translate_value(value, mapping):
    if not isinstance(value, str):
        return value
    key = normalize_whitespace(value).lower()
    return mapping.get(key, normalize_whitespace(value))


def sanitize_and_translate_action_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        return df

    out = df.copy()
    out.columns = [normalize_whitespace(col) for col in out.columns]

    rename_map = {}
    for col in out.columns:
        col_key = normalize_whitespace(col).lower()
        if col_key in ACTION_COLUMN_ALIASES:
            rename_map[col] = ACTION_COLUMN_ALIASES[col_key]
    out = out.rename(columns=rename_map)

    for col in out.select_dtypes(include="object").columns:
        out[col] = out[col].apply(normalize_whitespace)

    for col, mapping in ACTION_VALUE_MAPPINGS.items():
        if col in out.columns:
            out[col] = out[col].apply(lambda x: translate_value(x, mapping))

    if "Requer MOC?" in out.columns:
        out["Requer MOC?"] = out["Requer MOC?"].apply(
            lambda x: x if isinstance(x, bool) else str(x).strip().lower() in {"true", "1", "yes", "sim", "y"}
        )

    return out


def classify_hierarchy(action_text):
    text = normalize_whitespace(action_text).lower()
    if any(word in text for word in ["eliminar", "substituir"]):
        return "Eliminação/Substituição"
    if any(
        word in text
        for word in [
            "sis",
            "sif",
            "esd",
            "clp",
            "plc",
            "válvula",
            "valvula",
            "psv",
            "alarme",
            "sensor",
            "detector",
            "intertravamento",
            "bloqueio",
        ]
    ):
        return "Engenharia (Hardware)"
    if any(
        word in text
        for word in [
            "treinar",
            "treinamento",
            "procedimento",
            "instrução",
            "instrucao",
            "revisar",
            "checklist",
        ]
    ):
        return "Administrativo (Procedimento)"
    return "Mitigação (Emergência)"


def estimate_action_cost(action_text: str, hierarchy: str) -> dict:
    text = normalize_whitespace(action_text).lower()
    hierarchy = normalize_whitespace(hierarchy).lower()

    for rule in AACE_CLASS5_LIBRARY:
        if any(keyword in text for keyword in rule["keywords"]):
            return {
                "Recurso": rule["resource"],
                "Pacote AACE": rule["label"],
                "Custo Min (R$)": rule["min"],
                "Custo P50 (R$)": rule["p50"],
                "Custo Máx (R$)": rule["max"],
            }

    if "engenharia" in hierarchy or "eliminação" in hierarchy:
        return {
            "Recurso": "CAPEX",
            "Pacote AACE": "Hardware Genérico",
            "Custo Min (R$)": 25000.0,
            "Custo P50 (R$)": 60000.0,
            "Custo Máx (R$)": 140000.0,
        }

    return {
        "Recurso": "OPEX",
        "Pacote AACE": "Ação Administrativa Genérica",
        "Custo Min (R$)": 2500.0,
        "Custo P50 (R$)": 7000.0,
        "Custo Máx (R$)": 16000.0,
    }


def enrich_action_plan_df(df: pd.DataFrame) -> pd.DataFrame:
    out = sanitize_and_translate_action_df(df)
    if not isinstance(out, pd.DataFrame) or out.empty:
        return out

    col_acao = get_action_col(out)

    if "Status" not in out.columns:
        out["Status"] = "Aberto"
    if "Responsável" not in out.columns:
        out["Responsável"] = "Engenharia"
    if "Prazo (Dias)" not in out.columns:
        out["Prazo (Dias)"] = 30
    if "Requer MOC?" not in out.columns:
        out["Requer MOC?"] = False
    if "Criticidade" not in out.columns:
        out["Criticidade"] = "Média"

    out["Hierarquia NIOSH"] = out[col_acao].apply(classify_hierarchy)

    cost_df = out.apply(
        lambda row: estimate_action_cost(row[col_acao], row.get("Hierarquia NIOSH", "")),
        axis=1,
        result_type="expand",
    )
    for col in cost_df.columns:
        out[col] = cost_df[col]

    return out
