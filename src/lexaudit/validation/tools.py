"""
Tools for validation agents - Vector DB queries.
"""

import logging
from typing import List

from langchain_core.tools import tool

from ..indexing.document_index import LegalDocumentIndex

logger = logging.getLogger(__name__)


def create_query_tool(indexer: LegalDocumentIndex):
    """
    Create a query tool bound to a specific indexer instance.

    Args:
        indexer: The LegalDocumentIndex instance to query

    Returns:
        A LangChain tool that agents can use to query documents
    """

    @tool
    def query_document_tool(canonical_id: str, query: str, k: int = 3) -> List[str]:
        """Query the official legal document by canonical_id. Returns relevant text chunks.

        Use this tool to search for specific information within the official legal document.
        The tool performs semantic search and returns the most relevant text passages.

        Args:
            canonical_id: The canonical identifier (URN:LEX) of the document to query
            query: Natural language query describing what you're looking for
            k: Number of relevant chunks to return (default: 3)

        Returns:
            List of relevant text chunks from the document, or empty list if document not found
        """
        try:
            logger.debug(
                f"Vector DB query: doc_id={canonical_id}, query='{query[:50]}...', k={k}"
            )
            results = indexer.search(doc_id=canonical_id, query=query, k=k)
            logger.debug(f"Query returned {len(results)} chunks")
            return results
        except Exception as e:
            logger.error(f"Error querying document {canonical_id}: {e}")
            return []

    return query_document_tool
