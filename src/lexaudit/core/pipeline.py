"""
LexAudit Pipeline - Orchestrates the full validation process.
"""

import logging
from typing import List

from ..extraction.citation_extractor import CitationExtractor
from ..retrieval.resolver import CitationResolver
from ..retrieval.retriever import LegalDocumentRetriever
from ..indexing.document_index import LegalDocumentIndex
from ..indexing.embeddings import get_embeddings
from .models import CitationRetrieval, DocumentAnalysis

logger = logging.getLogger(__name__)


class LexAuditPipeline:
    """
    Main pipeline orchestrator for legal citation validation.

    Pipeline stages:
    1. Extraction: Identify citations in document
    2. Resolution: Convert citations to canonical IDs
    3. Retrieval: Fetch official documents
    3.5. Indexing: Index retrieved documents for RAG
    4. Validation: Compare and validate using RAG agent
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.extractor = CitationExtractor()
        self.resolver = CitationResolver()
        self.retriever = LegalDocumentRetriever()

        # Initialize Indexer with configured embeddings
        try:
            embeddings = get_embeddings()
            self.indexer = LegalDocumentIndex(embeddings)
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings/indexer: {e}")
            self.indexer = None

        # TODO: Initialize validator when validation module is ready
        # self.validator = RAGValidator()

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
        # if not pre_extracted_citations:
        #     # Forward pre-extracted citations (placeholder)
        #     analysis.extracted_citations = self.extractor.forward_extracted_citations(
        #         pre_extracted_citations
        #     )
        # else:
        #     # Extract from text (not implemented yet)
        analysis.extracted_citations = self.extractor.extract_from_text(text)

        logger.info("  -> Extracted %d citations", len(analysis.extracted_citations))

        # STAGE 2: Resolution
        logger.info(
            "[STAGE 2] Resolving citations to canonical IDs... (Only the first 2 citations)"
        )
        # Extract the first two citations as a sample
        sample_citations = analysis.extracted_citations[:2]
        for citation in sample_citations:
            resolved = self.resolver.resolve(citation)
            analysis.resolved_citations.append(resolved)

        logger.info("  -> Resolved %d citations", len(analysis.resolved_citations))
        logger.info("     (showing first 2 resolved citations)")
        for resolved in analysis.resolved_citations:
            logger.info(
                "     - %s -> %s (conf: %.2f)",
                resolved.extracted_citation.formatted_name,
                resolved.canonical_id,
                resolved.resolution_confidence,
            )

        # STAGE 3: Retrieval
        logger.info("[STAGE 3] Retrieving official documents...")
        retrieved_count = 0
        citation_retrievals = []
        for resolved in analysis.resolved_citations:
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
            "  -> Retrieved %d documents (total citations=%d)",
            retrieved_count,
            len(analysis.resolved_citations),
        )

        # STAGE 3.5: Indexing
        if self.indexer:
            logger.info("[STAGE 3.5] Indexing retrieved documents...")
            indexed_count = 0
            # For each citation retrieval
            for retrieval in analysis.citation_retrievals:
                if (
                    retrieval.retrieval_status == "success"
                    and retrieval.retrieved_document
                ):
                    try:
                        self.indexer.index_document(
                            doc_id=retrieval.resolved_citation.canonical_id,
                            full_text=retrieval.retrieved_document.full_text,
                        )
                        indexed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Error indexing document {retrieval.resolved_citation.canonical_id}: {e}"
                        )
            logger.info("  -> Indexed %d documents", indexed_count)
        else:
            logger.warning("[STAGE 3.5] Indexing skipped (indexer not initialized)")

        # STAGE 4: Validation (not implemented yet)
        logger.info("[STAGE 4] Validating citations (NOT IMPLEMENTED YET)...")
        # TODO: Implement validation with RAG agent
        # for resolved, document in zip(analysis.resolved_citations, retrieved_docs):
        #     validated = self.validator.validate(resolved, document)
        #     analysis.validated_citations.append(validated)

        return analysis

    def cleanup(self):
        """Clean up resources (e.g. clear index)."""
        if self.indexer:
            logger.info("Cleaning up indexer resources...")
            self.indexer.clear()

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
