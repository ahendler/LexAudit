"""
Citation resolution module.
Converts textual citations to canonical identifiers (URN:LEX) using LLM.
"""

import logging
from typing import List, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from ..core.models import ExtractedCitation, ResolutionOutput, ResolvedCitation
from ..core.structured_llm import StructuredLLM
from ..prompts.resolution import RESOLUTION_PROMPT


class CitationResolver:
    """
    Resolves extracted citations to canonical identifiers using an LLM.
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the resolver with a LangChain LLM.

        Args:
            llm: Any LangChain-compatible chat model (OpenAI, Anthropic, Ollama, etc.)
            model_name: Model name (used if llm not provided, reads from LLM_MODEL env)
            temperature: Temperature (used if llm not provided, reads from LLM_TEMPERATURE env)
        """
        self.llm_core = StructuredLLM(
            model_name=model_name,
            temperature=temperature,
            chat_model=llm,
        )
        self.model_name = self.llm_core.model_name

    def resolve_batch(
        self, citations: List[ExtractedCitation]
    ) -> List[ResolvedCitation]:
        """
        Resolve multiple citations.

        Args:
            citations: List of extracted citations

        Returns:
            List of resolved citations
        """
        logger = logging.getLogger(__name__)
        logger.info("Resolving %d citations...", len(citations))
        resolved = []

        for idx, citation in enumerate(citations, 1):
            resolved_citation = self.resolve(citation)
            if resolved_citation.canonical_id:
                logger.info(
                    "  [%d/%d] OK %s -> %s (conf: %.2f)",
                    idx,
                    len(citations),
                    citation.formatted_name,
                    resolved_citation.canonical_id,
                    resolved_citation.resolution_confidence,
                )
            else:
                logger.warning(
                    "  [%d/%d] FAILED to resolve '%s'",
                    idx,
                    len(citations),
                    citation.formatted_name,
                )
            resolved.append(resolved_citation)

        return resolved

    def resolve(self, citation: ExtractedCitation) -> ResolvedCitation:
        """
        Resolve a single citation using the LLM.

        Args:
            citation: Citation to resolve

        Returns:
            Resolved citation with canonical ID
        """
        logger = logging.getLogger(__name__)
        ct = citation.citation_type
        values = {
            "citation_text": citation.formatted_name,
            "citation_type": ct,
        }

        # Debug: Log the input values
        logger.debug(
            "Resolution input - text: '%s...' (len=%d), type: '%s'",
            citation.formatted_name[:100],
            len(citation.formatted_name),
            ct,
        )

        # Direct invocation bypasses with_structured_output which has timeout issues
        import json
        import re

        messages = RESOLUTION_PROMPT.format_messages(**values)
        response = self.llm_core.llm.invoke(messages)
        content = response.content

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        parsed = json.loads(content)
        try:
            result = ResolutionOutput.model_validate(parsed)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Resolution output validation failed for '%s': %s. Returning empty resolution.",
                citation.formatted_name,
                exc,
            )
            return ResolvedCitation(
                extracted_citation=citation,
                canonical_id=None,
                resolution_confidence=0.0,
                resolution_metadata={
                    "method": "llm",
                    "model": self.model_name,
                    "error": "validation_failed",
                    "raw_response": content,
                },
            )

        # Create resolved citation
        resolved = ResolvedCitation(
            extracted_citation=citation,
            canonical_id=result.canonical_id,
            resolution_confidence=result.confidence,
            resolution_metadata={
                "method": "llm",
                "model": self.model_name,
                "reasoning": result.reasoning,
                "llm_metadata": result.metadata or {},
            },
        )

        return resolved
