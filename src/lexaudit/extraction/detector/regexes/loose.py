from __future__ import annotations

# Loose patterns (alto recall) — equivalentes aos de versao2/patterns.py

GENERIC_CF_PATTERN = r"""
(?:
    # CF/88 e variações óbvias
    C\.?\s*F\.?(?:/\d{2,4}|\s*\d{2,4})?
    |
    Constitui[cç][aã]o\s+Federal
    |
    Carta\s+Magna
    |
    Constitui[cç][aã]o\s+Brasileira(?:\s+de\s*(?:19|20)\d{2})?
    |
    # Constituições estaduais por extenso
    Constitui[cç][aã]o\s+(?:do\s+Estado\s+de|do\s+Estado\s+da|do\s+Estado\s+do|Estadual\s+de)\s+[A-Z][\w\s]+
    |
    # Abreviação para Constituição Estadual:
    # CE/SP, CE-RS, CE/MG etc.
    CE\s*[-/]\s*[A-Z]{2}
    |
    # Abreviação comum para Lei Orgânica Municipal:
    # LOM de São Paulo, LOM/SP etc. (tratada aqui como "constitucional" local)
    LOM\s+(?:de|do|da)\s+[A-Z][\w\s]+
    |
    LOM\s*[-/]\s*[A-Z]{2}
    |
    # Constituição genérica (pega muita coisa, mas o scanner é loose mesmo)
    Constitui[cç][aã]o\b
)
"""


GENERIC_ARTICLE_PATTERN = r"""
(?<!\w)                       # início de palavra (evita 'artista', 'cartaz')
(?:arts?\.?|artigo?s?)        # art, art., arts., artigo, artigos
\s*\.?\s*                     # aceita sem espaço e com/sem ponto
\d+[A-Za-z0-9º°\-]*           # 5, 5º, 5-A, 5A
"""


GENERIC_LAW_REFERENCE_PATTERN = r"""
(?:
    Lei(?:\s+(?:Complementar|Municipal|Estadual|Federal))?
    | LC | LCE | LCM | LCP | LD | LDL | MP
)
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*
(?:-\d{1,3})?            # <<< NOVO (ex.: 2.158-35)
(?:/\d{2,4})?
(?:/[A-Z]{2})?
"""


GENERIC_CASE_PATTERN = r"""
(?:AgRg|AgInt|AgIn|AgR|ARE|RE|REsp|AREsp|AI|HC|MS|RMS|ADI|ADPF|ADO|ADC|ACO|EDcl|EDv|Embargos\s+de\s+Declara[cç][aã]o|PET|Rcl|SL|SLS|SS|TP)
\s*
\d{1,9}(?:[\./]\d{1,4})*(?:/[A-Z]{2,3})?
"""

GENERIC_CODE_PATTERN = r"""
C[óo]digo\s+(?:de\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\s]{3,50}
"""

GENERIC_OTHER_ACT_PATTERN = r"""
(?:
    Decreto | Dec\.? | Decr\.?
  | Portaria | Port\.?
  | Resolu[cç][aã]o\s+Normativa
  | Resolu[cç][aã]o | Res\.? | RDC
  | RN(?=\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*\d)
  | Instru[cç][aã]o(?:\s+Normativa)?
  | Instr(?:u[cç][aã]o)?\s+Normativa
  | Orienta[cç][aã]o\s+Normativa
  | Circular
  | Despacho
  | Edital
  | Ato
  | Delibera[cç][aã]o
  | Of[íi]cio
)
(?:\s+(?:[A-Z]{2,10}(?:/[A-Z]{2,10})?|Estadual|Municipal|Federal|Est\.|Mun\.|Fed\.)){0,3}
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
(?:
    \d{1,6}(?:\.\d{3})*
  | \d{1,3}\s*[kK]
)
(?:/\d{2,4})?
(?:/[A-Z]{2})?
(?:\s+(?:do|da|de)\s+[A-Z]{2,10}(?:/[A-Z]{2,10})?)?
"""


GENERIC_LAW_COLLECTION_PATTERN = r"""
(?:Lei|Leis)\s+(?:federais?|municipais?|estaduais?)
"""

GENERIC_SUMULA_ORG_PATTERN = r"""
S[úu]mulas?\s+(?:do|da)\s+(?:STF|STJ|TST|TSE|TRF|CNJ)
"""

LAW_ALIAS_PATTERN = r"""
(?:
    # Apelidos comuns de LEI
    Lei\s+de\s+Improbidade(?:\s+Administrativa)?(?:\s+antiga)?
    |
    Lei\s+Anticorrup[cç][aã]o
    |
    Lei\s+de\s+Responsabilidade\s+Fiscal
    |
    # >>> NOVO: Apelidos de MP (ex.: "MP do Bem", "MP da Liberdade Econômica", "MP dos Portos")
    (?:
        (?:MP|Medida\s+Provis[óo]ria)
        \s+(?:da|do|dos|das)\s+
        (?!estado\b|distrito\b|munic[íi]pio\b|minist[ée]rio\b|p[úu]blico\b|procuradoria\b|justi[cç]a\b)
        [A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]*
        (?:\s+
            (?!estado\b|distrito\b|munic[íi]pio\b|minist[ée]rio\b|p[úu]blico\b|procuradoria\b|justi[cç]a\b)
            [A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]*
        ){0,4}
    )
)
"""

MP_GENERIC_YEAR_PATTERN = r"""
(?:
    (?:MP|Medida\s+Provis[óo]ria)
    # Evita confundir com "MP" = Ministério Público etc.
    (?!\s+(?:do|da|dos|das)\s+(?:Estado|Distrito|Munic[íi]pio|Minist[ée]rio|P[úu]blico|Procuradoria|Justi[cç]a)\b)
    (?:\s+[A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]*){0,3}   # ex.: "qualquer", "do Bem", "dos Portos"
    \s+de\s+(?:19|20)\d{2}
)
"""

IN_ABBR_PATTERN = r"""
(?:                                   # Forma 1: IN + ÓRGÃO + (opcional 'nº') + número
    \bIN\b
    (?:\s+(?:[A-Z]{2,10}(?:/[A-Z]{2,10})?))+   # pelo menos 1 sigla: RFB, SRF, ME, ANVISA...
    \s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
    \d{1,6}(?:\.\d{3})*(?:/\d{2,4})?
)
|
(?:                                   # Forma 2: IN + 'nº' + número (sem órgão)
    \bIN\b
    \s*(?:n[ºo°\.]?|n\.|no|nº)\s*
    \d{1,6}(?:\.\d{3})*(?:/\d{2,4})?
)
"""

ORG_SIGLA_NUMBER_PATTERN = r"""
\b(?:RFB|SRF|ANVISA|ANS|ANEEL|ANATEL|ANAC|ANP|ANM|ANTT|ANTAQ|BACEN|BCB|CVM|CMN|SUSEP|PREVIC|IBAMA|INMETRO|MAPA|ME|MF|MTE|MS|MEC|MJ|MJSP|PGFN|CNSP)\b
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*(?:-\d{1,3})?
(?:/\d{2,4})
"""

TEMA_RG_PATTERN = r"""
\bTema\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*\d{1,4}(?:\.\d{3}){0,2}\b
"""

STJ_RECURSO_REPETITIVO_PATTERN = r"""
\b(?:recurso(?:s)?\s+)?repetitivo(?:s)?\s+(?:do|no)\s+STJ\b
"""

SUMULA_ABBR_PATTERN = r"""
\bSum\.?\s*\d{1,3}(?:\s*/\s*(?:STF|STJ|TST|TSE|TRF|CNJ))?\b
"""

# Sim, há problemas. O maior erro é utilizar um quantificador de comprimento variável em lookbehind,
# o que não é permitido no Python (nem em engines que não suportam lookbehind variável).

# Abaixo está uma versão "corrigida": aceitando apenas até 80 caracteres como lookbehind explícito,
# mas extraindo esses 80 caracteres como grupo de captura (ou usando uma âncora alternativa como \b e {0,80} em lookbehind *não* funciona em Python).

# Solução alternativa: usa uma abordagem matching mais permissiva porém compatível.

SUMULA_LIST_NUMBERS_PATTERN = r"""
    \bS[úu]mulas?\b                # "Súmula(s)"
    [^.\n]{0,80}                   # até 80 caracteres antes da lista de números (não inclui ponto ou quebra de linha)
    (?:n[ºo°\.]?\s*)?              # opcional "nº", "n", etc.
    \d{1,3}                        # primeiro número
    (?:\s*(?:,|e)\s*(?:n[ºo°\.]?\s*)?\d{1,3})+   # Mais números separados por vírgula ou "e"
"""

SUMULA_GENERIC_TOPIC_PATTERN = r"""
\bS[úu]mula(?:\s+Vinculante)?(?:\s*(?:n[ºo°\.]?\s*)?\d{1,3})?\s+(?:do|sobre)\s+[A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]+
"""
SUMULA_DIRTY_PATTERN = r"""
\b(?:S[úu]m|sum)\.?\s*\d{1,3}
(?:\s*[/\-]?\s*(?:STF|STJ|TST|TSE|TRF|CNJ))?
\b
"""

SUMULA_GENERIC_PATTERN = r"""
\bS[úu]mula(?:\s+Vinculante)?(?:\s*(?:n[ºo°\.]?\s*)?\d{1,3})?\b
"""
# súmulas genéricas próximas de tribunal (sem número)
SUMULA_GENERIC_NEAR_COURT_PATTERN = r"""
\bS[úu]mulas?\b(?=[^\.]{0,80}\b(?:STF|STJ|TST|TSE|TRF|CNJ)\b)
"""


OJ_TST_PATTERN = r"""
(?:
    \bOJ\.?\s*\d{1,4}                       # OJ 191 / OJ191
    (?:\s*[,/ -]?\s*SDI\s*[-–]?\s*(?:I|II|1|2))?  # SDI-1/SDI-2 opcional
    (?:\s*(?:do|da|no|na)\s*)?\s*(?:TST)?\b       # TST opcional agora
)
|
(?:
    \bOrienta[cç][aã]o(?:es|ões)?\s+Jurisprudencial(?:is)?
    (?:\s*(?:n[ºo°\.]?\s*)?\d{1,4})?             # número opcional
    (?:\s+da\s+SDI\s*[-–]?\s*(?:I|II|1|2))?      # SDI-1/2 opcional
    (?:\s+(?:do|da)\s+(?:TST|STJ|STF|TSE|TRF|CNJ))?  # órgão opcional
)
"""


COUNCIL_RESOLUTION_GENERIC_PATTERN = r"""
\bResolu[cç][aã]o\s+do\s+Conselho
\s+(?:Federal|Estadual|Municipal)\s+de\s+
[A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]+
"""
REGIMENTO_INTERNO_PATTERN = r"""
\bRegimento\s+Interno
(?:\s+(?:do|da)\s+[A-Z][\w\s]{2,80})?      # órgão por extenso (STJ, STF, etc.)
(?:\s*\([A-Z]{2,10}\))?                    # sigla entre parênteses (RISTJ)
"""

REGIMENTO_SIGLA_PATTERN = r"""
\bRI(?:STF|STJ|TST|TSE|TRF[1-6])\b
"""

OTHER_ACT_JOINED_SIGLA_NUM_PATTERN = r"""
(?:
    Resolu[cç][aã]o | Res\.? | Decreto | Dec\.? | Decr\.? | Portaria | Port\.? | RDC | RN
)
\s+[A-Z]{2,10}\s*\d{1,6}(?:\.\d{3})*(?:/\d{2,4})?
"""

REG_INTERNO_ABBR_PATTERN = r"""
\bReg(?:imento)?\.?\s+Int(?:\.|erno)?\b
(?:\s+(?:do|da)\s+[A-Z]{2,10})?
"""

RESOLUTION_GENERIC_ORG_PATTERN = r"""
\bResolu[cç](?:[aã]o|[oõ]es)\s+(?:do|da)\s+(?:CNJ|ANS|ANVISA|ANEEL|ANATEL|CVM|BACEN|BCB|CONAMA|CNSP)\b
"""

PEC_GENERIC_PATTERN = r"""
\b(?:PEC|Proposta\s+de\s+Emenda\s+à?\s+Constitui[cç][aã]o)\b
(?:\s+(?:da|do|sobre)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\-]+){0,4})?
"""

PL_GENERIC_PATTERN = r"""
\b(?:PLs?|Projetos?\s+de\s+Lei)\b
"""

# proposições legislativas com número (com/sem espaço): pl4302/98, pec32/20, PL 4.302/1998…
LEGISLATIVE_PROPOSAL_NUMBER_PATTERN = r"""
\b(?:PEC|PL|PLP|PLC|PLN|PLS|PLV|PDL)\s*\d{1,5}(?:\.\d{3})*(?:/\d{2,4})?\b
"""

JUDICIAL_DECISION_NUMBER_PATTERN = r"""
\b(?:STF|STJ|TST|TSE|TRF|CNJ)\s*\d{1,5}(?:\.\d{3})*(?:/\d{2,4})?\b
"""

# manuais oficiais por nome com sigla entre parênteses ou por sigla MCASP
OFFICIAL_MANUAL_PATTERN = r"""
(?:
    \bMCASP\b
  |
    \bManual\s+de\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\s]{3,120}\s*\([A-Z]{2,10}\)
)
"""

OJ_GENERIC_NEAR_COURT_PATTERN = r"""
\bOrienta[cç](?:[aã]o|[oõ]es)\s+Jurisprudenc(?:ial(?:is)?|iais)\b
(?=[^\.]{0,80}\b(?:STF|STJ|TST|TSE|TRF|CNJ)\b)
"""

OJ_TST_PATTERN = r"""
(?:
    \bOJ[-\.\s]?\s*\d{1,4}                      # OJ-191 / OJ 191 / OJ191
    (?:\s*[,/ -]?\s*SDI\s*[-–]?\s*(?:I|II|1|2))?
    (?:\s*(?:do|da|no|na)\s*)?\s*(?:TST)?\b
)
|
(?:
    \bOrienta[cç][aã]o(?:es|ões)?\s+Jurisprudencial(?:is)?
    (?:\s*(?:n[ºo°\.]?\s*)?\d{1,4})?
    (?:\s+da\s+SDI\s*[-–]?\s*(?:I|II|1|2))?
    (?:\s+(?:do|da)\s+(?:TST|STJ|STF|TSE|TRF|CNJ))?
)
"""

PARECER_ORG_PATTERN = r"""
\bParecer
\s+[A-Z]{2,10}(?:/[A-Z]{2,10}){0,3}
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*(?:/\d{2,4})\b
"""

PARECER_NUMBER_ORG_SUFFIX_PATTERN = r"""
\bParecer
\s*(?:n[ºo°\.]?|n\.|no|nº)?\s*
\d{1,6}(?:\.\d{3})*(?:/\d{2,4})
\s*[-–]?\s*
[A-Z]{2,10}(?:/[A-Z]{2,10}){0,3}\b
"""

NOTE_TECNICA_GENERIC_PATTERN = r"""
\bnota\s+t[eé]cnica(?:\s+(?:do|da|de)\s+(?:CNJ|ANS|ANVISA|ANEEL|ANATEL|CVM|BACEN|BCB|IBAMA|MAPA|RFB|PGFN|AG[êe]ncia\s+Reguladora))?
\b
"""

ESTATUTO_SOCIAL_PATTERN = r"""
\bEstatuto\s+Social\b
(?:\s+(?:da|do)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\s\.&\-]{1,80})?
"""
REGULAMENTO_INTERNO_PATTERN = r"""
\bRegulamento\s+Interno\b
(?:\s+(?:de|do|da)\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\s\.&\-]{1,80})?
"""

POLICY_PRIVACY_PATTERN = r"""
\bPol[ií]tica\s+de\s+Privacidade\b
"""

DOCTRINE_CITATION_PATTERN = r"""
(?:
    \b(?:Fredie\s+)?Didier(?:\s+Jr\.?)?\b
  |
    \bCurso\s+de\s+Direito\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\w\s]{3,60}\b
)
"""

LAW_ALIAS_PATTERN = r"""
(?:
    Lei\s+de\s+Improbidade(?:\s+Administrativa)?(?:\s+antiga)?
  | Lei\s+Anticorrup[cç][aã]o
  | Lei\s+de\s+Responsabilidade\s+Fiscal
  | Lei\s+(?:Geral\s+de\s+)?Licita[cç][oõ]es           # <<< NOVO
  |
    (?:
        (?:MP|Medida\s+Provis[óo]ria)
        \s+(?:da|do|dos|das)\s+
        (?!estado\b|distrito\b|munic[íi]pio\b|minist[ée]rio\b|p[úu]blico\b|procuradoria\b|justi[cç]a\b)
        [A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]*
        (?:\s+(?!estado\b|distrito\b|munic[íi]pio\b|minist[ée]rio\b|p[úu]blico\b|procuradoria\b|justi[cç]a\b)
            [A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\-]*){0,4}
    )
)
"""

PARECER_GENERIC_ORG_PATTERN = r"""
\bParecer\s+(?:do|da|de)\s+[A-Z]{2,10}(?:/[A-Z]{2,10}){0,3}\b
"""

NOTA_TECNICA_ABBR_PATTERN = r"""
\bN\.?\s*T\.?\b
(?:\s+(?:do|da|de)\s+(?:ANVISA|ANS|ANEEL|ANATEL|CNJ|RFB|PGFN|BACEN|BCB))?
"""

EDITAL_GENERIC_PATTERN = r"""
\bEdital\b
(?:\s+(?:de|do|da)\s+[A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\s\-]{1,80})?
"""

ESTATUTO_GENERIC_PATTERN = r"""
\bEstatuto\b
(?:\s+(?:do|da)\s+[A-Za-zÁÉÍÓÚÂÊÔÃÕÇà-ú][\w\s\-]{1,80})?
"""

CONSTITUTION_PATTERN = r"""
(?:
    (?:
        C\.?\s*F\.?(?:/\d{2,4}|\s*\d{2,4})?   # aceita CF/88 e CF88
        |
        Constitui[cç][aã]o\s+(?:Federal|da\s+Rep[úu]blica(?:\s+Federativa)?(?:\s+do\s+Brasil)?)
        (?:\s+de\s*(?:19|20)\d{2})?
        |
        Carta\s+Magna
    )
    (?:\s*/\s*(?:19|20)?\d{2})?
)
"""

ARTICLE_LIST_PATTERN = r"""
\barts?\.?\s*\d+[A-Za-z0-9º°\-]*
(?:\s*,\s*\d+[A-Za-z0-9º°\-]*)*
(?:\s+e\s+\d+[A-Za-z0-9º°\-]*)?
"""


__all__ = [
    "GENERIC_CF_PATTERN",
    "GENERIC_ARTICLE_PATTERN",
    "GENERIC_LAW_REFERENCE_PATTERN",
    "GENERIC_CASE_PATTERN",
    "GENERIC_CODE_PATTERN",
    "GENERIC_OTHER_ACT_PATTERN",
    "GENERIC_LAW_COLLECTION_PATTERN",
    "GENERIC_SUMULA_ORG_PATTERN",
    "LAW_ALIAS_PATTERN",
    "MP_GENERIC_YEAR_PATTERN",
    "IN_ABBR_PATTERN",
    "ORG_SIGLA_NUMBER_PATTERN",
    "TEMA_RG_PATTERN",
    "STJ_RECURSO_REPETITIVO_PATTERN",
    "SUMULA_ABBR_PATTERN",
    "SUMULA_LIST_NUMBERS_PATTERN",
    "SUMULA_GENERIC_TOPIC_PATTERN",
    "SUMULA_DIRTY_PATTERN",
    "OJ_TST_PATTERN",
    "COUNCIL_RESOLUTION_GENERIC_PATTERN",
    "REGIMENTO_INTERNO_PATTERN",
    "REGIMENTO_SIGLA_PATTERN",
    "OTHER_ACT_JOINED_SIGLA_NUM_PATTERN",
    "REG_INTERNO_ABBR_PATTERN",
    "SUMULA_GENERIC_PATTERN",
    "RESOLUTION_GENERIC_ORG_PATTERN",
    "PEC_GENERIC_PATTERN",
    "PL_GENERIC_PATTERN",
    "SUMULA_GENERIC_NEAR_COURT_PATTERN",
    "LEGISLATIVE_PROPOSAL_NUMBER_PATTERN",
    "JUDICIAL_DECISION_NUMBER_PATTERN",
    "OFFICIAL_MANUAL_PATTERN",
    "OJ_GENERIC_NEAR_COURT_PATTERN",
    "OJ_TST_PATTERN",
    "PARECER_ORG_PATTERN",
    "PARECER_NUMBER_ORG_SUFFIX_PATTERN",
    "NOTE_TECNICA_GENERIC_PATTERN",
    "ESTATUTO_SOCIAL_PATTERN",
    "REGULAMENTO_INTERNO_PATTERN",
    "POLICY_PRIVACY_PATTERN",
    "DOCTRINE_CITATION_PATTERN",
    "LAW_ALIAS_PATTERN",
    "PARECER_GENERIC_ORG_PATTERN",
    "NOTA_TECNICA_ABBR_PATTERN",
    "EDITAL_GENERIC_PATTERN",
    "ESTATUTO_GENERIC_PATTERN",
    "CONSTITUTION_PATTERN",
    "ARTICLE_LIST_PATTERN",
]
