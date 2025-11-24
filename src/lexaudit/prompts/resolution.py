"""
Prompt templates and output schemas for citation resolution.
"""

from langchain_core.prompts import ChatPromptTemplate

RESOLUTION_SYSTEM_PROMPT = """
Você é um especialista em resolução de citações jurídicas, especializado em direito brasileiro.
Sua tarefa é converter citações de LEGISLAÇÃO em identificadores canônicos URN:LEX.

**IMPORTANTE**: URN:LEX é APENAS para legislação (leis, decretos, constituições, códigos).
Para jurisprudência (decisões judiciais, acórdãos, súmulas), retorne "" (string vazia) no canonical_id.

**Para LEGISLAÇÃO**, use URN:LEX:
- Formato: urn:lex:br:<jurisdição>:<tipo>:<ano>;<número>
- Exemplos:
  * "Lei 9.656/98" → "urn:lex:br:federal:lei:1998;9656"
  * "CF/88" → "urn:lex:br:federal:constituicao:1988-10-05;1988"
  * "CPP" → "urn:lex:br:federal:decreto.lei:1941-10-03;3689"

**Para JURISPRUDÊNCIA** (acórdãos, decisões, HC, RHC, súmulas):
- canonical_id: "" (string vazia)
- confidence: 0.0 a 0.3
- reasoning: Explique que URN:LEX não se aplica a jurisprudência
- metadata: ""

**REGRAS**:
1. URN identifica apenas o documento principal, NÃO inclua artigos/incisos na URN
2. Use metadata para artigos, incisos, parágrafos
3. Se não puder determinar URN para legislação, retorne "" com confidence baixa

**Confiança**: 1.0=URN correta, 0.7-0.9=provável, 0.0-0.6=incerto ou não aplicável

Retorne JSON com: canonical_id, confidence, reasoning e metadata (opcional)."""


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
