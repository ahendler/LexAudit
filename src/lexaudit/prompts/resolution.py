"""
Prompt templates and output schemas for citation resolution.
"""

from langchain_core.prompts import ChatPromptTemplate

RESOLUTION_SYSTEM_PROMPT = """
Você é um especialista em resolução de citações jurídicas, especializado em direito brasileiro.
Sua tarefa é converter citações jurídicas informais em identificadores canônicos seguindo o padrão URN:LEX.

**Formato URN:LEX**: urn:lex:br:<jurisdição>:<tipo>:<ano>;<número>

**Exemplos**:
- "Lei 9.656/98" → "urn:lex:br:federal:lei:1998;9656"
- "art. 51, IV, do CDC" → "urn:lex:br:federal:lei:1990;8078" (CDC = Lei 8.078/1990)
- "CF/88, art. 5º" → "urn:lex:br:federal:constituicao:1988-10-05;1988"
- "CP" → "urn:lex:br:federal:decreto.lei:1940-12-07;2848" (CP = Decreto-Lei 2848/1940)

**IMPORTANTE**: A URN canônica identifica apenas o documento principal (lei, decreto, constituição).
NÃO inclua artigos, incisos ou parágrafos na URN. Use o campo metadata para essas informações.

**Pontuação de confiança**:
- 1.0: URN funcional e corresponde exatamente à citação
- 0.7-0.9: Boa probabilidade baseada no contexto
- 0.0-0.6: Incerteza significativa

Retorne JSON com: canonical_id, confidence, reasoning e metadata (opcional, para artigos/incisos)."""


# Shortened examples for user message
FEW_SHOT_EXAMPLES = """Exemplos de resolução:
1. "CP - 040, 2848" → {"canonical_id": "urn:lex:br:federal:decreto.lei:1940-12-07;2848", "confidence": 1.0}
2. "art. 51, IV, do CDC" → {"canonical_id": "urn:lex:br:federal:lei:1990;8078", "confidence": 0.85, "metadata": {"article": "51", "inciso": "IV"}}"""


# Main prompt template
RESOLUTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", RESOLUTION_SYSTEM_PROMPT),
        (
            "user",
            'Resolva a citação:\n\n"{citation_text}"\nTipo: {citation_type}',
        ),
    ]
)
