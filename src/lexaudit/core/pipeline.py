"""
LexAudit Pipeline - Orchestrates the full validation process.
"""
from typing import List
from .models import DocumentAnalysis
from ..extraction.citation_extractor import CitationExtractor
from ..retrieval.resolver import CitationResolver
from ..retrieval.retriever import LegalDocumentRetriever


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
        # TODO: Initialize validator when validation module is ready
        # self.validator = RAGValidator()

    def process_document(self, document_id: str, text: str = "",
                         pre_extracted_citations: List[str] = None) -> DocumentAnalysis:
        """
        Process a document through the full pipeline.

        Args:
            document_id: Unique identifier for the document
            text: Full text of the document (optional if pre_extracted_citations provided)
            pre_extracted_citations: Pre-extracted citations to forward (optional)

        Returns:
            Complete document analysis
        """
        analysis = DocumentAnalysis(
            document_id=document_id,
            metadata={}
        )

        # STAGE 1: Extraction
        print(f"[STAGE 1] Extracting citations from document {document_id}...")
        if pre_extracted_citations:
            # Forward pre-extracted citations (placeholder)
            analysis.extracted_citations = self.extractor.forward_extracted_citations(
                pre_extracted_citations
            )
        else:
            # Extract from text (not implemented yet)
            analysis.extracted_citations = self.extractor.extract_from_text(
                text)

        print(f"  -> Extracted {len(analysis.extracted_citations)} citations")

        # STAGE 2: Resolution
        print("[STAGE 2] Resolving citations to canonical IDs...")
        # Extract the first two citations as a sample
        sample_citations = analysis.extracted_citations[:2]
        for citation in sample_citations:
            resolved = self.resolver.resolve(citation)
            analysis.resolved_citations.append(resolved)

        print(f"  -> Resolved {len(analysis.resolved_citations)} citations")
        print("     (showing first 2 resolved citations)")
        for resolved in analysis.resolved_citations:
            print(
                f"     - {resolved.extracted_citation.formatted_name} -> {resolved.canonical_id} (conf: {resolved.resolution_confidence:.2f})"
            )

        # STAGE 3: Retrieval
        print("[STAGE 3] Retrieving official documents...")
        retrieved_count = 0
        for resolved in analysis.resolved_citations:
            document = self.retriever.retrieve(resolved)
            if document:
                retrieved_count += 1
                # TODO: Store document for validation stage

        print(f"  -> Retrieved {retrieved_count} documents")

        # STAGE 4: Validation (not implemented yet)
        print("[STAGE 4] Validating citations (NOT IMPLEMENTED YET)...")
        # TODO: Implement validation with RAG agent
        # for resolved, document in zip(analysis.resolved_citations, retrieved_docs):
        #     validated = self.validator.validate(resolved, document)
        #     analysis.validated_citations.append(validated)

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
            doc_id = doc.get('id', 'unknown')
            citations = doc.get('citations', [])

            analysis = self.process_document(
                document_id=doc_id,
                pre_extracted_citations=citations
            )
            results.append(analysis)

        return results
