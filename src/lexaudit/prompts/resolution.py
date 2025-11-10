"""
Prompt templates and output schemas for citation resolution.
"""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional


class ResolutionOutput(BaseModel):
    """Structured output for citation resolution."""
    canonical_id: str = Field(
        description="Canonical identifier for the legal reference (e.g., 'urn:lex:br:federal:lei:1998;9656' or 'REsp-1234567')"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1 indicating certainty of the resolution",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of how the canonical ID was determined"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata extracted from the citation"
    )


# System prompt for the resolution task
RESOLUTION_SYSTEM_PROMPT = """You are a legal citation resolution expert specialized in Brazilian law.

Your task is to convert informal legal citations into canonical identifiers following these standards:

1. **For Legislation (Laws, Decrees, Constitutions)**:
   - Use URN:LEX format when possible: urn:lex:br:<jurisdiction>:<type>:<year>;<number>
   - Examples:
     * "Lei 9.656/98" → "urn:lex:br:federal:lei:1998;9656"
     * "Decreto 3.048/99" → "urn:lex:br:federal:decreto:1999;3048"
     * "CF/88, art. 5º" → "urn:lex:br:constituicao.federal:1988"

2. **For Jurisprudence (Court decisions)**:
   - Use standardized case identifiers
   - Examples:
     * "REsp 1.234.567" → "REsp-1234567"
     * "AgInt no AREsp 123.456" → "AgInt-AREsp-123456"

3. **Confidence scoring**:
   - 1.0: Clear, complete citation with all necessary information
   - 0.7-0.9: Most information present, minor ambiguity
   - 0.5-0.7: Significant ambiguity or missing information
   - < 0.5: Very incomplete or unclear citation

Return your response as a JSON object with: canonical_id, confidence, reasoning, and optional metadata."""


# Few-shot examples
FEW_SHOT_EXAMPLES = """
## Example 1:
Citation: "Lei n. 9.656/1998"
Output: {
  "canonical_id": "urn:lex:br:federal:lei:1998;9656",
  "confidence": 1.0,
  "reasoning": "Complete legislation reference with law number and year. Standard URN:LEX format applied.",
  "metadata": {"type": "lei", "number": "9656", "year": "1998", "jurisdiction": "federal"}
}

## Example 2:
Citation: "REsp 1.889.704/SP"
Output: {
  "canonical_id": "REsp-1889704",
  "confidence": 0.95,
  "reasoning": "Standard STJ special appeal format. State information (SP) noted but not required in canonical ID.",
  "metadata": {"type": "recurso_especial", "number": "1889704", "state": "SP", "court": "STJ"}
}

## Example 3:
Citation: "art. 51, IV, do CDC"
Output: {
  "canonical_id": "urn:lex:br:federal:lei:1990;8078:art.51;inc.4",
  "confidence": 0.85,
  "reasoning": "CDC refers to Lei 8.078/1990 (Código de Defesa do Consumidor). Article and item clearly specified.",
  "metadata": {"type": "lei", "number": "8078", "year": "1990", "article": "51", "inciso": "IV", "common_name": "CDC"}
}

## Example 4:
Citation: "CF/88, art. 5º, XI"
Output: {
  "canonical_id": "urn:lex:br:constituicao.federal:1988:art.5;inc.11",
  "confidence": 0.95,
  "reasoning": "Constitutional reference with article and inciso clearly identified. Roman numeral XI converted to 11.",
  "metadata": {"type": "constituicao", "year": "1988", "article": "5", "inciso": "XI"}
}

## Example 5:
Citation: "Lei 9.961/2000"
Output: {
  "canonical_id": "urn:lex:br:federal:lei:2000;9961",
  "confidence": 1.0,
  "reasoning": "Complete and unambiguous legislation reference. Federal law with number and year.",
  "metadata": {"type": "lei", "number": "9961", "year": "2000", "jurisdiction": "federal"}
}
"""


# Main prompt template
RESOLUTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", RESOLUTION_SYSTEM_PROMPT),
    ("user", "{examples}\n\nNow resolve this citation:\n\nCitation: \"{citation_text}\"\nType: {citation_type}\n\nProvide your response as a JSON object.")
])
