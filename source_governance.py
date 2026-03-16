from __future__ import annotations

import pandas as pd


SOURCE_CLASS = {
    "local_seed": "curado",
    "PubChem": "oficial",
    "PubChem PUG REST": "oficial",
    "NIST WebBook": "oficial",
    "NIOSH Pocket Guide": "oficial",
}


def _link_map(profile) -> dict:
    mapping = {}
    for item in profile.storage.get("official_links", []):
        mapping[item["source"]] = item["url"]
    return mapping


def _usage_label(source: str, confidence: str) -> str:
    src = (source or "").strip()
    conf = (confidence or "").strip()

    if src in ["NIST WebBook", "NIOSH Pocket Guide"]:
        return "screening + apoio técnico"
    if src in ["PubChem", "PubChem PUG REST"]:
        return "identidade / apoio técnico"
    if src == "local_seed" and conf == "seed":
        return "screening curado"
    return "revisar manualmente"


def _append_row(rows: list[dict], grupo: str, campo: str, valor, unidade: str, fonte: str, status: str, link: str):
    rows.append(
        {
            "Grupo": grupo,
            "Campo": campo,
            "Valor": valor,
            "Unidade": unidade,
            "Fonte": fonte,
            "Classe da fonte": SOURCE_CLASS.get(fonte, "revisar"),
            "Status": status,
            "Adequação": _usage_label(fonte, status),
            "Link oficial": link,
        }
    )


def build_evidence_ledger_df(profile) -> pd.DataFrame:
    rows = []
    links = _link_map(profile)

    # Identidade
    identity_source = "PubChem" if profile.identity.get("pubchem_cid") else "local_seed"
    identity_status = "live" if identity_source == "PubChem" else "seed"
    for key in ["name", "preferred_name", "cas", "formula", "molecular_weight", "pubchem_cid", "iupac_name", "inchikey"]:
        value = profile.identity.get(key)
        if value not in [None, ""]:
            _append_row(
                rows,
                "Identidade",
                key,
                value,
                "" if key != "molecular_weight" else "g/mol",
                identity_source,
                identity_status,
                links.get("PubChem", ""),
            )

    # Physchem
    for key, item in profile.physchem.items():
        _append_row(
            rows,
            "Físico-química",
            key,
            item.value,
            item.unit,
            item.source,
            item.confidence,
            links.get(item.source, ""),
        )

    # Exposure
    for key, item in profile.exposure_limits.items():
        _append_row(
            rows,
            "Exposição",
            key,
            item.value,
            item.unit,
            item.source,
            item.confidence,
            links.get(item.source, ""),
        )

    return pd.DataFrame(rows)


def summarize_evidence(profile) -> dict:
    df = build_evidence_ledger_df(profile)
    if df.empty:
        return {
            "linhas": 0,
            "oficial": 0,
            "curado": 0,
            "revisar": 0,
            "com_link": 0,
        }

    classes = df["Classe da fonte"].value_counts().to_dict()
    return {
        "linhas": len(df),
        "oficial": classes.get("oficial", 0),
        "curado": classes.get("curado", 0),
        "revisar": classes.get("revisar", 0),
        "com_link": int((df["Link oficial"].astype(str).str.len() > 0).sum()),
    }


def build_source_recommendations(profile) -> list[str]:
    recs = []

    if profile.flags.get("toxic_inhalation") and profile.limit("IDLH_ppm") is None and profile.limit("IDLH_mg_m3") is None:
        recs.append("Fechar IDLH/limites ocupacionais em fonte oficial antes de usar para decisão de resposta.")

    if profile.flags.get("flammable") and profile.prop("flash_point_c") is None:
        recs.append("Fechar ponto de fulgor em fonte oficial antes de consolidar screening de inflamabilidade.")

    if profile.flags.get("pressurized") and profile.prop("boiling_point_c") is None:
        recs.append("Fechar base de ebulição/volatilidade para suportar cenários de perda de contenção.")

    if not profile.storage.get("official_links"):
        recs.append("Adicionar links oficiais para permitir verificação externa e atualização futura.")

    if not recs:
        recs.append("Pacote atual apresenta rastreabilidade inicial adequada para screening.")

    return recs
