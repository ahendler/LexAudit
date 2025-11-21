from __future__ import annotations

# Strict patterns (alta precisão) — equivalentes aos de versao2/patterns.py

CONSTITUTION_PATTERN = r"""
(?:
    (?:
        (?:art\.?|artigo)\s+\d+(?:º|°)?
        (?:\s*,?\s*(?:§{1,2}|par(?:[aá]grafo)?|inc\.?|inciso|al[íi]nea)\s*[IVXLCDM0-9]+(?:º|°)?|\s*,?\s*[IVXLCDM]{1,5})*
        \s*(?:da|do|na|no)\s+
    )?
    (?:
        C\.?\s*F\.?(?:/\d{2,4})?
        |
        Constitui[cç][aã]o\s+(?:Federal|da\s+Rep[úu]blica(?:\s+Federativa)?(?:\s+do\s+Brasil)?)
        (?:\s+de\s*(?:19|20)\d{2})?
        |
        Carta\s+Magna
    )
    (?:\s*/\s*(?:19|20)?\d{2})?
)
"""

LAW_LIKE_PATTERN = r"""
(?:
    Lei(?:\s+(?:Complementar|Municipal|Estadual|Federal))?
    |
    Medida\s+Provis[óo]ria
    |
    MP
)
\s*
(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*
(?:/\d{2,4})?
(?:\s*,?\s*de\s*(?:19|20)\d{2})?
(?:\s*\([^)]+\))?
"""

CODE_STATUTE_PATTERN = r"""
(?:
    C[óo]digo\s+(?:Civil|Penal|de\s+Processo\s+Civil|de\s+Processo\s+Penal|
    Tribut[áa]rio\s+Nacional|de\s+Defesa\s+do\s+Consumidor|de\s+Tr[âa]nsito\s+Brasileiro|
    de\s+Processo\s+do\s+Trabalho|de\s+Processo\s+Eleitoral)
    |
    Estatuto\s+(?:da\s+Crian[cç]a\s+e\s+do\s+Adolescente|do\s+Idoso|da\s+Pessoa\s+com\s+Defici[êe]ncia|da\s+Cidade)
    |
    CDC\b
    |
    CPC\b
    |
    CPP\b
    |
    CTN\b
    |
    ECA\b
)
"""

SUMULA_PATTERN = r"""
(?:
    S[úu]mula
    (?:\s+Vinculante)?
    \s*(?:n[ºo°\.]?\s*)?
    \d{1,3}
    (?:\s*(?:/|do\s+)(?:STF|STJ|TST|TSE|TRF|CNJ))?
)
|
(?:SV\s*\d{1,3})
|
(?:Sum\.?\s*\d{1,3}(?:\s*/\s*(?:STF|STJ|TSE|TRF|CNJ))?)
"""


JURISPRUDENCE_PATTERN = r"""
(?:
    # abreviadas (já existiam)
    (?:AgRg|AgInt|AgIn|EDcl|EDv|Embargos\s+de\s+Declara[cç][aã]o)?\s*
    (?:RE|ARE|REsp|AREsp|HC|MS|RMS|ADI|ADPF|ADIn|AO|AOc|AR|RR|RO|AgRE|AgInt|AgRg|AI|AP|EDcl|EDv|Rcl|SL|SLS|Pet)
    \s*(?:n[ºo°\.]?\s*)?\d{1,9}(?:\.\d{3})*(?:/[A-Z]{2,3})?
)
|
(?:
    # NOVO: por extenso
    (?:Recurso\s+Especial|Recurso\s+Extraordin[áa]rio)
    \s*(?:n[ºo°\.]?\s*)?
    \d{1,9}(?:\.\d{3})*(?:/[A-Z]{2,3})?
)
"""


CNJ_NUMBER_PATTERN = r"""
\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b
"""

OTHER_ACT_PATTERN = r"""
(?:
    Decreto | Portaria
  | Resolu[cç][aã]o | Res\.? | RDC
  | Instru[cç][aã]o\s+Normativa
  | Orienta[cç][aã]o\s+Normativa
  | Instru[cç][aã]o | Circular | Delibera[cç][aã]o | Despacho
)
(?:\s+(?:Estadual|Municipal|Federal))?
(?:\s+(?:[A-Z]{2,10}(?:/[A-Z]{2,10})?)){0,3}
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*(?:/\d{2,4})?
(?:\s*,?\s*de\s*(?:19|20)\d{2})?
(?:\s+(?:do|da|de)\s+[A-Z][\w\-/\.]+)?
"""


URN_LEXML_PATTERN = r"""
urn:lex:[^\s,;]+
"""

__all__ = [
    "CONSTITUTION_PATTERN",
    "LAW_LIKE_PATTERN",
    "CODE_STATUTE_PATTERN",
    "SUMULA_PATTERN",
    "JURISPRUDENCE_PATTERN",
    "CNJ_NUMBER_PATTERN",
    "OTHER_ACT_PATTERN",
    "URN_LEXML_PATTERN",
]
