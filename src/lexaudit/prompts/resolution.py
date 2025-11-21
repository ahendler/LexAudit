"""
Prompt templates and output schemas for citation resolution.
"""

from langchain_core.prompts import ChatPromptTemplate

# TODO: Refinar few-shot examples e prompt
RESOLUTION_SYSTEM_PROMPT = """
Você é um especialista em resolução de citações jurídicas, especializado em direito brasileiro.
Sua tarefa é converter citações jurídicas informais em identificadores canônicos seguindo o padrão:

**Legislação (Leis, Decretos, Constituições)**:
  - Use o formato URN:LEX : urn:lex:br:<jurisdição>:<tipo>:<ano>;<número>
  - Exemplos:
    * "Lei 9.656/98" → "urn:lex:br:federal:lei:1998;9656"
    * "Decreto 3.048/99" → "urn:lex:br:federal:decreto:1999;3048"
    * "CF/88, art. 5º" → "urn:lex:br:federal:constituicao:1988-10-05;1988"

**Pontuação de confiança**:
  - 1.0: A URN é funcional e corresponde exatamente à citação fornecida
  - 0.0 até 0.9: Indica a probabilidade da urn estar correta com base na citação fornecida

Retorne sua resposta como um objeto JSON com: canonical_id, confidence, reasoning e metadata opcional."""


# Exemplos few-shot
FEW_SHOT_EXAMPLES = """
# Exemplos corretos
## Exemplo 1:
Citação: "CP - 040, 2848"
Saída: {
  "canonical_id": "urn:lex:br:federal:decreto.lei:1940-12-07;2848",
  "confidence": 1.0,
  "reasoning": "Referência legislativa completa com número e ano da lei. Necessário adicionar data para identificação do código penal.",
  "metadata": {"type": "decreto.lei", "number": "2848", "year": "1940", "jurisdiction": "federal"}
}

## Exemplo 2:
Citação: "art. 51, IV, do CDC"
Saída: {
  "canonical_id": "urn:lex:br:federal:lei:1990;8078",
  "confidence": 0.85,
  "reasoning": "CDC refere-se à Lei 8.078/1990 (Código de Defesa do Consumidor). Artigo e inciso claramente especificados.",
  "metadata": {"type": "lei", "number": "8078", "year": "1990", "article": "51", "inciso": "IV", "common_name": "CDC"}
}

## Exemplo 3:
Citação: "CF/88, art. 5º, XI"
Saída: {
  "canonical_id": "urn:lex:br:federal:constituicao:1988-10-05;1988",
  "confidence": 0.95,
  "reasoning": "Referência constitucional com artigo e inciso claramente identificados. O número romano XI convertido para 11.",
  "metadata": {"type": "constituicao", "year": "1988", "article": "5", "inciso": "XI"}
}

# Exemplos incorretos
## Exemplo 1:
Citação: "CF/88, art. 5º, XI"
Saída: {
  "canonical_id": "urn:lex:br:federal:constituicao:1988-10-05;1988;art.5;inc.XI", -- INCORRETO: Artigo e inciso não devem ser incluídos na URN canônica
  "confidence": 0.95,
  "reasoning": "Referência constitucional com artigo e inciso claramente identificados. O número romano XI convertido para 11.",
  "metadata": {"type": "constituicao", "year": "1988", "article": "5", "inciso": "XI"}
}
"""


# Main prompt template
RESOLUTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", RESOLUTION_SYSTEM_PROMPT),
        (
            "user",
            '{examples}\n\nAgora resolva a seguinte citação:\n\n"{citation_text}"\nTipo: {citation_type}\n\nResponda com um objeto JSON.',
        ),
    ]
)
