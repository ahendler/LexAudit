"""
Prompt templates for document validation during retrieval.
"""

from langchain_core.prompts import ChatPromptTemplate

RETRIEVED_CITATION_CHECK_SYSTEM_PROMPT = """
Você é um especialista em análise de documentos jurídicos brasileiros.

Sua tarefa é verificar se um documento recuperado corresponde à citação que estamos procurando.

Analise:
1. O documento é sobre a lei/norma citada?
2. O documento contém o artigo/parágrafo específico mencionado (se aplicável)?

Responda com:
- matches: true se o documento corresponde à citação, false caso contrário
- reasoning: explicação breve da sua decisão
- extracted_text: se corresponde, extraia a parte específica mencionada na citação (ex: apenas o artigo citado). Se não há parte específica, deixe vazio. Se aplicável, traga também informações sobre os estado de revogação do artigo.
"""

RETRIEVED_CITATION_CHECK_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", RETRIEVED_CITATION_CHECK_SYSTEM_PROMPT),
        (
            "user",
            """Citação buscada: "{citation_text}"

Documento recuperado:
---
{document_text}
---

O documento corresponde à citação? Extraia a parte específica se aplicável.
Responda em JSON com: matches (boolean), reasoning (string), extracted_text (string).""",
        ),
    ]
)
