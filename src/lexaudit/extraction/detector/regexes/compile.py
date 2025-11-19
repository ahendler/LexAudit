from __future__ import annotations

import re
from typing import Dict, List, Mapping, Tuple

from .common import COMMON_REGEX_FLAGS
from .strict import (
    CONSTITUTION_PATTERN,
    LAW_LIKE_PATTERN,
    CODE_STATUTE_PATTERN,
    SUMULA_PATTERN,
    JURISPRUDENCE_PATTERN,
    CNJ_NUMBER_PATTERN,
    OTHER_ACT_PATTERN,
    URN_LEXML_PATTERN,
)
from .loose import (
    GENERIC_CF_PATTERN,
    GENERIC_ARTICLE_PATTERN,
    GENERIC_LAW_REFERENCE_PATTERN,
    GENERIC_CASE_PATTERN,
    GENERIC_CODE_PATTERN,
    GENERIC_OTHER_ACT_PATTERN,
    GENERIC_LAW_COLLECTION_PATTERN,
    GENERIC_SUMULA_ORG_PATTERN,
    MP_GENERIC_YEAR_PATTERN,
    IN_ABBR_PATTERN,
    ORG_SIGLA_NUMBER_PATTERN,
    TEMA_RG_PATTERN,
    STJ_RECURSO_REPETITIVO_PATTERN,
    SUMULA_ABBR_PATTERN,
    SUMULA_LIST_NUMBERS_PATTERN,
    SUMULA_GENERIC_TOPIC_PATTERN,
    SUMULA_DIRTY_PATTERN,
    COUNCIL_RESOLUTION_GENERIC_PATTERN,
    REGIMENTO_INTERNO_PATTERN,
    REGIMENTO_SIGLA_PATTERN,
    OTHER_ACT_JOINED_SIGLA_NUM_PATTERN,
    REG_INTERNO_ABBR_PATTERN,
    SUMULA_GENERIC_PATTERN,
    RESOLUTION_GENERIC_ORG_PATTERN,
    PEC_GENERIC_PATTERN,
    PL_GENERIC_PATTERN,
    SUMULA_GENERIC_NEAR_COURT_PATTERN,
    OFFICIAL_MANUAL_PATTERN,
    LEGISLATIVE_PROPOSAL_NUMBER_PATTERN,
    JUDICIAL_DECISION_NUMBER_PATTERN,
    OJ_GENERIC_NEAR_COURT_PATTERN,
    OJ_TST_PATTERN,
    PARECER_ORG_PATTERN,
    PARECER_NUMBER_ORG_SUFFIX_PATTERN,
    NOTE_TECNICA_GENERIC_PATTERN,
    ESTATUTO_SOCIAL_PATTERN,
    REGULAMENTO_INTERNO_PATTERN,
    POLICY_PRIVACY_PATTERN,
    DOCTRINE_CITATION_PATTERN,
    LAW_ALIAS_PATTERN,
    PARECER_GENERIC_ORG_PATTERN,
    NOTA_TECNICA_ABBR_PATTERN,
    EDITAL_GENERIC_PATTERN,
    ESTATUTO_GENERIC_PATTERN,
    # CONSTITUTION_PATTERN, Is also in strict
    ARTICLE_LIST_PATTERN,
)


# Mapeamento de chaves → padrões, idêntico ao de versao2/patterns.py
REFERENCE_PATTERN_SPECS: Dict[str, str] = {
    "constitution": CONSTITUTION_PATTERN,
    "law_or_code": LAW_LIKE_PATTERN,
    "code_name": CODE_STATUTE_PATTERN,
    "sumula": SUMULA_PATTERN,
    "jurisprudence": JURISPRUDENCE_PATTERN,
    "cnj_number": CNJ_NUMBER_PATTERN,
    "other_act": OTHER_ACT_PATTERN,
    "law_alias": LAW_ALIAS_PATTERN,
    "generic_constitution": GENERIC_CF_PATTERN,
    "generic_article": GENERIC_ARTICLE_PATTERN,
    "generic_law_number": GENERIC_LAW_REFERENCE_PATTERN,
    "generic_law_collection": GENERIC_LAW_COLLECTION_PATTERN,
    "generic_case": GENERIC_CASE_PATTERN,
    "generic_code_name": GENERIC_CODE_PATTERN,
    "generic_other_act": GENERIC_OTHER_ACT_PATTERN,
    "generic_sumula_org": GENERIC_SUMULA_ORG_PATTERN,
    "urn_reference": URN_LEXML_PATTERN,
    "mp_generic_year": MP_GENERIC_YEAR_PATTERN,
    "in_abbr": IN_ABBR_PATTERN,
    "org_sigla_number": ORG_SIGLA_NUMBER_PATTERN,
    "tema_rg": TEMA_RG_PATTERN,
    "stj_recurso_repetitivo": STJ_RECURSO_REPETITIVO_PATTERN,
    "sumula_abbr": SUMULA_ABBR_PATTERN,
    "sumula_list_numbers": SUMULA_LIST_NUMBERS_PATTERN,
    "sumula_generic_topic": SUMULA_GENERIC_TOPIC_PATTERN,
    "sumula_dirty": SUMULA_DIRTY_PATTERN,
    "oj_tst": OJ_TST_PATTERN,
    "council_resolution_generic": COUNCIL_RESOLUTION_GENERIC_PATTERN,
    "sumula_generic": SUMULA_GENERIC_PATTERN,
    "resolution_generic_org": RESOLUTION_GENERIC_ORG_PATTERN,
    "regimento_interno": REGIMENTO_INTERNO_PATTERN,
    "regimento_sigla": REGIMENTO_SIGLA_PATTERN,
    "reg_interno_abbr": REG_INTERNO_ABBR_PATTERN,
    "other_act_joined_sigla_num": OTHER_ACT_JOINED_SIGLA_NUM_PATTERN,
    "pec_generic": PEC_GENERIC_PATTERN,
    "pl_generic": PL_GENERIC_PATTERN,
    "legislative_proposal_number": LEGISLATIVE_PROPOSAL_NUMBER_PATTERN,
    "sumula_generic_near_court": SUMULA_GENERIC_NEAR_COURT_PATTERN,
    "judicial_decision_number": JUDICIAL_DECISION_NUMBER_PATTERN,
    "official_manual": OFFICIAL_MANUAL_PATTERN,
    "oj_generic_near_court": OJ_GENERIC_NEAR_COURT_PATTERN,
    "parecer_org": PARECER_ORG_PATTERN,
    "parecer_number_org_suffix": PARECER_NUMBER_ORG_SUFFIX_PATTERN,
    "note_tecnica_generic": NOTE_TECNICA_GENERIC_PATTERN,
    "estatuto_social": ESTATUTO_SOCIAL_PATTERN,
    "regulamento_interno": REGULAMENTO_INTERNO_PATTERN,
    "policy_privacy": POLICY_PRIVACY_PATTERN,
    "doctrine_citation": DOCTRINE_CITATION_PATTERN,
    "parecer_generic_org": PARECER_GENERIC_ORG_PATTERN,
    "nota_tecnica_abbr": NOTA_TECNICA_ABBR_PATTERN,
    "edital_generic": EDITAL_GENERIC_PATTERN,
    "estatuto_generic": ESTATUTO_GENERIC_PATTERN,
    "article_list": ARTICLE_LIST_PATTERN,
}


def _compile_pattern_groups(
    groups: Mapping[str, Dict[str, str]],
) -> Tuple[re.Pattern[str], Dict[str, Dict[str, str]]]:
    pattern_fragments: List[str] = []
    metadata: Dict[str, Dict[str, str]] = {}

    for confidence, specs in groups.items():
        for label, pattern in specs.items():
            group_name = f"{confidence}__{label}"
            pattern_fragments.append(f"(?P<{group_name}>{pattern})")
            metadata[group_name] = {"category": label, "confidence": confidence}

    combined_pattern = re.compile(
        "|\n".join(pattern_fragments),
        flags=COMMON_REGEX_FLAGS,
    )
    return combined_pattern, metadata


REFERENCE_REGEX, REFERENCE_GROUP_METADATA = _compile_pattern_groups(
    {"reference": REFERENCE_PATTERN_SPECS}
)

# Aliases de compatibilidade com a versão 2
LEXML_REFERENCE_REGEX = REFERENCE_REGEX
GROUP_METADATA = REFERENCE_GROUP_METADATA

__all__ = [
    "COMMON_REGEX_FLAGS",
    "REFERENCE_PATTERN_SPECS",
    "REFERENCE_REGEX",
    "REFERENCE_GROUP_METADATA",
    "LEXML_REFERENCE_REGEX",
    "GROUP_METADATA",
]
