"""
Triage agent for citation validation.
"""

import logging
from typing import Dict, Any

from ..core.structured_llm import StructuredLLM
from ..core.models import CitationRetrieval, TriageDecision
from ..prompts.validation import TRIAGE_PROMPT

logger = logging.getLogger(__name__)


class TriageAgent:
    """
    Triage agent that decides if a citation can be validated autonomously
    or requires multi-agent discussion.
    """

    def __init__(self):
        """Initialize triage agent with structured LLM."""
        self.llm = StructuredLLM()

    def analyze(self, citation_retrieval: CitationRetrieval) -> TriageDecision:
        """
        Analyze a citation and decide if it needs multi-agent discussion.

        Args:
            citation_retrieval: Citation with retrieved document

        Returns:
            TriageDecision with needs_discussion flag and preliminary status

        Raises:
            Exception: If triage analysis fails (intentional crash)
        """
        resolved = citation_retrieval.resolved_citation
        retrieved_doc = citation_retrieval.retrieved_document
        extracted_citation = resolved.extracted_citation

        citation_context = extracted_citation.context_snippet or ""
        citation_reference = extracted_citation.formatted_name
        retrieval_status = citation_retrieval.retrieval_status

        official_text = (
            retrieved_doc.full_text if retrieved_doc else "DOCUMENTO NÃO RECUPERADO"
        )
        extracted_section = (
            retrieved_doc.metadata.get("extracted_text", "Não disponível")
            if retrieved_doc
            else "Não disponível"
        )

        values: Dict[str, Any] = {
            "citation_context": citation_context,
            "citation_reference": citation_reference,
            "official_text": official_text[:5000],  # Limit to avoid token overflow
            "extracted_section": extracted_section,
            "retrieval_status": retrieval_status,
        }

        logger.info(
            "Triage analyzing citation: %s (retrieval_status=%s)",
            citation_reference,
            retrieval_status,
        )

        decision = self.llm.invoke(TRIAGE_PROMPT, values, TriageDecision)

        logger.info(
            "  -> Decision: needs_discussion=%s, status=%s, confidence=%.2f",
            decision.needs_discussion,
            decision.preliminary_status,
            decision.confidence,
        )

        return decision
