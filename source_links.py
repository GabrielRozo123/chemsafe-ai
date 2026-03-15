from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus


def _cas_to_nist_id(cas: str) -> str:
    return "C" + cas.replace("-", "").strip()


def build_official_source_links(profile: Any) -> List[Dict[str, str]]:
    name = profile.identity.get("preferred_name") or profile.identity.get("name") or ""
    cas = profile.identity.get("cas") or ""
    cid = profile.identity.get("pubchem_cid")

    name_q = quote_plus(name) if name else ""
    cas_q = quote_plus(cas) if cas else ""

    links: List[Dict[str, str]] = []

    if cid:
        links.append(
            {
                "source": "PubChem",
                "purpose": "Identidade química, sinônimos, descritores e metadados públicos",
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            }
        )
    else:
        links.append(
            {
                "source": "PubChem",
                "purpose": "Identidade química, sinônimos, descritores e metadados públicos",
                "url": "https://pubchem.ncbi.nlm.nih.gov/",
            }
        )

    if cas:
        links.append(
            {
                "source": "NIST Chemistry WebBook",
                "purpose": "Propriedades termodinâmicas e termofísicas",
                "url": f"https://webbook.nist.gov/cgi/cbook.cgi?ID={_cas_to_nist_id(cas)}&Units=SI",
            }
        )
    else:
        links.append(
            {
                "source": "NIST Chemistry WebBook",
                "purpose": "Propriedades termodinâmicas e termofísicas",
                "url": "https://webbook.nist.gov/",
            }
        )

    links.append(
        {
            "source": "NIOSH Pocket Guide",
            "purpose": "IDLH, REL, PEL, propriedades, incompatibilidades e higiene ocupacional",
            "url": "https://www.cdc.gov/niosh/npg/default.html",
        }
    )

    links.append(
        {
            "source": "CAMEO Chemicals",
            "purpose": "Reatividade química, resposta emergencial e hazards de mistura",
            "url": "https://cameochemicals.noaa.gov/",
        }
    )

    links.append(
        {
            "source": "EPA CompTox",
            "purpose": "Exposure, hazard e dados químicos ampliados",
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

    if name_q or cas_q:
        links.append(
            {
                "source": "Busca web técnica",
                "purpose": "Apoio rápido para pesquisa manual em bases oficiais",
                "url": f"https://www.google.com/search?q={quote_plus(name + ' ' + cas + ' site:cdc.gov OR site:webbook.nist.gov OR site:cameochemicals.noaa.gov')}",
            }
        )

    return links
