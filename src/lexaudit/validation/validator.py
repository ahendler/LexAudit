"""
RAGValidator - Main validator class using multi-agent LangGraph workflow.
"""

import logging

from ..core.models import CitationRetrieval, ValidatedCitation, ValidationStatus
from ..indexing.document_index import LegalDocumentIndex
from .graph import build_validation_graph

logger = logging.getLogger(__name__)


class RAGValidator:
    """
    Multi-agent citation validator using LangGraph.

    Uses a triage agent to handle simple cases and multi-agent debate
    for complex legal interpretation questions.
    """

    def __init__(self, indexer: LegalDocumentIndex):
        """
        Initialize the validator.

        Args:
            indexer: The LegalDocumentIndex for querying official documents
        """
        self.indexer = indexer
        try:
            self.graph = build_validation_graph(indexer)
            logger.info("RAGValidator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to build validation graph: {e}")
            self.graph = None

    def validate(self, citation_retrieval: CitationRetrieval) -> ValidatedCitation:
        """
        Validate a citation using the multi-agent workflow.

        Args:
            citation_retrieval: The citation retrieval result from Stage 3

        Returns:
            ValidatedCitation with status, justification, and discussion history
        """
        if not self.graph:
            logger.error("Validation graph not available")
            return self._create_error_validation(
                citation_retrieval, "Validation graph not initialized"
            )

        try:
            # Prepare initial state
            initial_state = {
                "citation_retrieval": citation_retrieval,
                "triage_result": None,
                "discussion_history": [],
                "round_counter": 0,
                "final_validation": None,
            }

            # Invoke graph with retry logic
            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"Validating citation: {citation_retrieval.resolved_citation.canonical_id} "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    result = self.graph.invoke(initial_state)

                    # Extract final validation
                    final_validation = result.get("final_validation")

                    if final_validation:
                        logger.info(
                            f"Validation complete: {final_validation.validation_status.value}"
                        )
                        return final_validation
                    else:
                        raise ValueError("No final validation produced by graph")

                except Exception as e:
                    last_error = e
                    logger.warning(f"Validation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        logger.info("Retrying...")
                    continue

            # All retries failed
            logger.error(f"All validation attempts failed: {last_error}")
            return self._create_error_validation(
                citation_retrieval, f"Validation failed after retries: {str(last_error)}"
            )

        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}", exc_info=True)
            return self._create_error_validation(
                citation_retrieval, f"Unexpected error: {str(e)}"
            )

    def _create_error_validation(
        self, citation_retrieval: CitationRetrieval, error_message: str
    ) -> ValidatedCitation:
        """
        Create a fallback ValidatedCitation when validation fails.

        Args:
            citation_retrieval: The citation retrieval result
            error_message: Error description

        Returns:
            ValidatedCitation with PENDING status and error message
        """
        return ValidatedCitation(
            resolved_citation=citation_retrieval.resolved_citation,
            retrieved_document=citation_retrieval.retrieved_document,
            validation_status=ValidationStatus.PENDING,
            justification=f"Erro na validação: {error_message}",
            confidence=0.0,
            discussion_messages=[],
        )
