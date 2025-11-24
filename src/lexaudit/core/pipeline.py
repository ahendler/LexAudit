"""
LexAudit Pipeline - Orchestrates the full validation process.
"""

import logging
from typing import List

from ..extraction.citation_extractor import CitationExtractor
from ..retrieval.resolver import CitationResolver
from ..retrieval.retriever import LegalDocumentRetriever
from ..validation.validator import CitationValidator
from .models import CitationRetrieval, DocumentAnalysis
from ..config.settings import SETTINGS

logger = logging.getLogger(__name__)


class LexAuditPipeline:
    """
    Main pipeline orchestrator for legal citation validation.

    Pipeline stages:
    1. Extraction: Identify citations in document
    2. Resolution: Convert citations to canonical IDs
    3. Retrieval: Fetch official documents
    4. Validation: Compare and validate using RAG agent
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.extractor = CitationExtractor()
        self.resolver = CitationResolver()
        self.retriever = LegalDocumentRetriever()
        self.validator = CitationValidator()

    def process_document(
        self,
        document_id: str,
        text: str = "",
        pre_extracted_citations: List[str] = None,
    ) -> DocumentAnalysis:
        """
        Process a document through the full pipeline.

        Args:
            document_id: Unique identifier for the document
            text: Full text of the document (optional if pre_extracted_citations provided)
            pre_extracted_citations: Pre-extracted citations to forward (optional)

        Returns:
            Complete document analysis
        """
        analysis = DocumentAnalysis(document_id=document_id, metadata={})

        # STAGE 1: Extraction
        logger.info("[STAGE 1] Extracting citations from document %s...", document_id)

        analysis.extracted_citations = self.extractor.extract_from_text(text)

        logger.info("  -> Extracted %d citations", len(analysis.extracted_citations))

        # STAGE 2: Resolution
        limit = SETTINGS.citations_to_process
        sample_citations = (
            analysis.extracted_citations[:limit]
            if (limit is not None and limit >= 0)
            else analysis.extracted_citations
        )
        logger.info(
            "[STAGE 2] Resolving citations to canonical IDs (%s)...",
            f"limit: {limit} citations"
            if limit is not None and limit >= 0
            else f"all {len(sample_citations)} citations",
        )

        for idx, citation in enumerate(sample_citations, 1):
            logger.info(
                "  [%d/%d] Resolving: '%s' (type: %s)",
                idx,
                len(sample_citations),
                citation.formatted_name,
                citation.citation_type,
            )
            resolved = self.resolver.resolve(citation)
            analysis.resolved_citations.append(resolved)

        logger.info("  -> Resolved %d citations", len(analysis.resolved_citations))
        for resolved in analysis.resolved_citations[:3]:
            logger.info(
                "     - %s -> %s (conf: %.2f)",
                resolved.extracted_citation.formatted_name,
                resolved.canonical_id,
                resolved.resolution_confidence,
            )

        # Filter citations with valid URN:LEX identifiers
        citations_with_urn = [
            r for r in analysis.resolved_citations
            if r.canonical_id and r.canonical_id.startswith("urn:lex:br:")
        ]
        skipped_count = len(analysis.resolved_citations) - len(citations_with_urn)
        if skipped_count > 0:
            logger.info(
                "  -> Skipping %d citation(s) without valid URN:LEX identifier",
                skipped_count,
            )

        # STAGE 3: Retrieval
        logger.info(
            "[STAGE 3] Retrieving official documents for %d citation(s)...",
            len(citations_with_urn),
        )
        retrieved_count = 0
        citation_retrievals = []
        for resolved in citations_with_urn:
            document = self.retriever.retrieve(resolved)
            status = "success" if document else "not_found"
            if status == "success":
                retrieved_count += 1

            retrieval = CitationRetrieval(
                resolved_citation=resolved,
                retrieved_document=document,
                retrieval_status=status,
                retrieval_metadata={},
            )
            citation_retrievals.append(retrieval)
        analysis.citation_retrievals = citation_retrievals
        analysis.metadata["citation_retrievals"] = citation_retrievals

        logger.info(
            "  -> Retrieved %d documents (attempted=%d, skipped=%d, total=%d)",
            retrieved_count,
            len(citations_with_urn),
            skipped_count,
            len(analysis.resolved_citations),
        )

        # STAGE 4: Validation
        logger.info("[STAGE 4] Validating citations...")

        analysis.validated_citations = self.validator.validate_batch(
            analysis.citation_retrievals, document_id=document_id
        )

        logger.info(
            "  -> Validated %d citations",
            len(analysis.validated_citations),
        )
        for validated in analysis.validated_citations[:3]:
            logger.info(
                "     - %s -> %s (conf: %.2f)",
                validated.resolved_citation.extracted_citation.formatted_name,
                validated.validation_status.value,
                validated.confidence,
            )

        return analysis

    def process_batch(self, documents: List[dict]) -> List[DocumentAnalysis]:
        """
        Process multiple documents.

        Args:
            documents: List of document dicts with 'id' and 'citations' keys

        Returns:
            List of document analyses
        """
        results = []

        for doc in documents:
            doc_id = doc.get("id", "unknown")
            citations = doc.get("citations", [])

            analysis = self.process_document(
                document_id=doc_id, pre_extracted_citations=citations
            )
            results.append(analysis)

        return results
