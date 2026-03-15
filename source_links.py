from __future__ import annotations

from typing import Any, Dict, List


def _cas_to_nist_id(cas: str) -> str:
    return "C" + cas.replace("-", "").strip()


def build_official_source_links(profile: Any) -> List[Dict[str, str]]:
    name = profile.identity.get("preferred_name") or profile.identity.get("name") or ""
    cas = profile.identity.get("cas") or ""
    cid = profile.identity.get("pubchem_cid")

    links: List[Dict[str, str]] = []

    if cid:
        links.append(
            {
                "source": "PubChem",
                "purpose": "Identidade, descritores e metadados públicos",
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            }
        )
    else:
        links.append(
            {
                "source": "PubChem",
                "purpose": "Identidade, descritores e metadados públicos",
                "url": "https://pubchem.ncbi.nlm.nih.gov/",
            }
        )

    if cas:
        links.append(
            {
                "source": "NIST Chemistry WebBook",
                "purpose": "Termodinâmica, vapor pressure e propriedades termofísicas",
                "url": f"https://webbook.nist.gov/cgi/cbook.cgi?ID={_cas_to_nist_id(cas)}&Units=SI",
            }
        )
    else:
        links.append(
            {
                "source": "NIST Chemistry WebBook",
                "purpose": "Termodinâmica, vapor pressure e propriedades termofísicas",
                "url": "https://webbook.nist.gov/",
            }
        )

    links.append(
        {
            "source": "NIOSH Pocket Guide",
            "purpose": "IDLH, REL, PEL, incompatibilidades e higiene ocupacional",
            "url": "https://www.cdc.gov/niosh/npg/default.html",
        }
    )
    links.append(
        {
            "source": "CAMEO Chemicals",
            "purpose": "Resposta emergencial e reatividade química",
            "url": "https://cameochemicals.noaa.gov/",
        }
    )
    links.append(
        {
            "source": "EPA CompTox Dashboard",
            "purpose": "Hazard, exposure e dados químicos ampliados",
            "url": "https://comptox.epa.gov/dashboard",
        }
    )
    links.append(
        {
            "source": "ECHA Substance Information",
            "purpose": "Classificação, rotulagem e informação regulatória",
            "url": "https://echa.europa.eu/substance-information/",
        }
    )

    return links
