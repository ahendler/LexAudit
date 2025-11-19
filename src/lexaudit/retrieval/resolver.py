"""
Citation resolution module.
Converts textual citations to canonical identifiers (URN:LEX) using LLM.
"""

from typing import Optional, List
import logging
from langchain_core.language_models.chat_models import BaseChatModel

from ..core.models import ExtractedCitation, ResolvedCitation, ResolutionOutput
from ..core.structured_llm import StructuredLLM
from ..prompts.resolution import RESOLUTION_PROMPT, FEW_SHOT_EXAMPLES


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
        ct = citation.citation_type
        values = {
            "examples": FEW_SHOT_EXAMPLES,
            "citation_text": citation.formatted_name,
            "citation_type": ct,
        }

        result = self.llm_core.invoke(
            RESOLUTION_PROMPT,
            values,
            ResolutionOutput,
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
