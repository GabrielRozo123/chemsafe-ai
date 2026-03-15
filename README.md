# ChemSafe Pro Deterministic

Plataforma Streamlit para **segurança de processo orientada por propriedades químicas, bases públicas e lógica determinística**, desenvolvida para apoiar engenheiros de processo e engenheiros de segurança de processo em atividades de screening, priorização de cenários e estruturação inicial de estudos.

A arquitetura atual combina:

- **base local curada** para compostos prioritários de segurança de processo;
- **lookup universal** via bases públicas;
- **motor determinístico** para HAZOP, LOPA, PSI/PSM readiness e screening de consequências;
- **visualização técnica** com Bow-Tie, matrizes, comparadores e registro de riscos.

---

## O que esta versão já entrega

- Busca de compostos por:
  - nome em português
  - nome em inglês
  - CAS
  - fórmula química

- Perfil químico integrado com:
  - identidade e descritores
  - propriedades físico-químicas
  - limites de exposição
  - incompatibilidades
  - links oficiais para consulta

- **Hazard fingerprint** com roteamento automático de cenários

- **HAZOP orientado por propriedades**
  - prioridades automáticas por composto
  - worksheet HAZOP base
  - matriz de risco inicial
  - registro inicial de riscos

- **Bow-Tie editável**
  - modo **Executivo**
  - modo **Técnico**

- **LOPA / SIL preliminar**
  - seleção de IPLs
  - cálculo de MCF
  - indicação de SIL requerido
  - panorama das camadas de proteção

- **PSI / PSM Readiness**
  - score de prontidão
  - checklist por pilar
  - cobertura por pilar
  - ações prioritárias

- **Consequências**
  - screening de dispersão
  - screening de pool fire
  - roteamento entre dispersão gaussiana e abordagem conservadora para gás denso

- **Comparador entre compostos**
  - propriedades lado a lado
  - leitura rápida das diferenças de risco

- **Persistência de casos**
  - salvar caso
  - carregar caso
  - manter Bow-Tie, notas e resultados

---

## Arquitetura

```mermaid
flowchart TD
    UI[Streamlit UI] --> CE[Compound Engine]
    CE --> SEED[Base local curada]
    CE --> PUB[PubChem]
    CE --> NIST[NIST WebBook]
    CE --> NIOSH[NIOSH Pocket Guide]

    UI --> HAZOP[HAZOP Engine]
    UI --> LOPA[LOPA / SIL Engine]
    UI --> CONS[Consequence Screening]
    UI --> PSI[PSI / PSM Readiness]
    UI --> BOW[Bow-Tie Editor]
    UI --> COMP[Compound Comparator]
    UI --> CASES[Case Store]

    CE --> VIS[Risk Visuals]
    HAZOP --> VIS
    LOPA --> VIS
    PSI --> VIS
    BOW --> VIS
