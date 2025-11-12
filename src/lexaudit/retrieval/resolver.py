"""
Citation resolution module.
Converts textual citations to canonical identifiers (URN:LEX) using LLM.
"""
from typing import Optional, List
import json
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser

from ..core.models import ExtractedCitation, ResolvedCitation
from ..core.llm_config import create_llm
from ..prompts.resolution import (
    RESOLUTION_PROMPT,
    ResolutionOutput,
    FEW_SHOT_EXAMPLES
)


class CitationResolver:
    """
    Resolves extracted citations to canonical identifiers using an LLM.
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize the resolver with a LangChain LLM.

        Args:
            llm: Any LangChain-compatible chat model (OpenAI, Anthropic, Ollama, etc.)
            model_name: Model name (used if llm not provided, reads from LLM_MODEL env)
            temperature: Temperature (used if llm not provided, reads from LLM_TEMPERATURE env)
        """
        if llm:
            self.llm = llm
            self.model_name = getattr(llm, 'model_name', 'custom')
        else:
            self.llm = create_llm(model_name=model_name, temperature=temperature)
            self.model_name = model_name or "default"

        self.parser = JsonOutputParser(pydantic_object=ResolutionOutput)

    def resolve_batch(self, citations: List[ExtractedCitation]) -> List[ResolvedCitation]:
        """
        Resolve multiple citations.

        Args:
            citations: List of extracted citations

        Returns:
            List of resolved citations
        """
        print(f"[RESOLVER] Resolving {len(citations)} citations...")
        resolved = []

        for idx, citation in enumerate(citations, 1):
            resolved_citation = self.resolve(citation)
            if resolved_citation.canonical_id:
                print(f"  [{idx}/{len(citations)}] OK {citation.raw_text} -> {resolved_citation.canonical_id} (conf: {resolved_citation.resolution_confidence:.2f})")
            else:
                print(
                    f"  [{idx}/{len(citations)}] FAILED to resolve '{citation.raw_text}'")
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
        # Format the prompt
        prompt = RESOLUTION_PROMPT.format_messages(
            examples=FEW_SHOT_EXAMPLES,
            citation_text=citation.raw_text,
            citation_type=citation.citation_type or "unknown"
        )

        # Call LLM
        response = self.llm.invoke(prompt)

        # Parse the response
        try:
            result = self.parser.parse(response.content)
        except Exception as e:
            raise ValueError(
                f"Failed to parse LLM response: {response.content}") from e

        # Create resolved citation
        resolved = ResolvedCitation(
            extracted_citation=citation,
            canonical_id=result["canonical_id"],
            resolution_confidence=result["confidence"],
            resolution_metadata={
                "method": "llm",
                "model": self.model_name,
                "reasoning": result["reasoning"],
                "llm_metadata": result.get("metadata", {})
            }
        )

        return resolved
