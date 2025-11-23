import logging
from typing import Dict, List, Optional, Any
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from lexaudit.config.settings import SETTINGS

logger = logging.getLogger(__name__)

MAX_DOC_CHARS = 3000

class LegalDocumentIndex:
    """
    Manages the indexing of legal documents.
    """

    def __init__(self, embeddings: Embeddings):
        self.small_docs: Dict[str, str] = {}
        self.doc_sizes: Dict[str, int] = {}
        self.embeddings = embeddings  # Store embeddings for reuse
        
        # Initialize Text Splitter for large documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300
        )
        
        # Initialize ChromaDB
        self.large_docs_index = Chroma(
            persist_directory=SETTINGS.chroma_db_path,
            collection_name=SETTINGS.chroma_collection_name,
            embedding_function=self.embeddings
        )
        logger.info("LegalDocumentIndex initialized (ChromaDB path: %s)", SETTINGS.chroma_db_path)
        
        # Ensure clean state on initialization
        self.clear()

    def index_document(
        self, 
        doc_id: str, 
        full_text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Indexes a document. If smaller than MAX_DOC_CHARS, stores in memory.
        If larger, chunks and stores in ChromaDB.
        """
        if not full_text:
            logger.warning("Skipping indexing for empty document: %s", doc_id)
            return

        size = len(full_text)
        self.doc_sizes[doc_id] = size

        if size <= MAX_DOC_CHARS:
            self.small_docs[doc_id] = full_text
            logger.info("Indexed small document in memory: %s (%d chars)", doc_id, size)
        else:
            # Chunking + ChromaDB
            chunks = self.text_splitter.split_text(full_text)
            
            # Prepare metadata for each chunk
            metadatas = []
            for i, _ in enumerate(chunks):
                meta = {"source": doc_id, "chunk_index": i}
                if metadata:
                    meta.update(metadata)
                metadatas.append(meta)
            
            self.large_docs_index.add_texts(texts=chunks, metadatas=metadatas)
            logger.info("Indexed large document in ChromaDB: %s (%d chars, %d chunks)", doc_id, size, len(chunks))

    def search(self, doc_id: str, query: str, k: int = 5) -> List[str]:
        """
        Searches within the specified document.
        
        Args:
            doc_id: The unique identifier of the document (URN).
            query: The search query string.
            k: Number of results to return (for vector search).

        Returns:
            List[str]: A list of text chunks (or the full text for small docs).
        """
        # 1. Check memory (fast path for small docs)
        if doc_id in self.small_docs:
            logger.debug("Searching in small document (memory): %s", doc_id)
            return [self.small_docs[doc_id]]
        
        # 2. Fallback to ChromaDB (for large docs or persisted docs)
        # We don't check doc_sizes anymore to allow searching persisted data
        # even if memory state was lost/restarted.
        logger.debug("Searching in ChromaDB: %s", doc_id)
        results = self.large_docs_index.similarity_search(
             query, 
             k=k, 
             filter={"source": doc_id}
        )
        return [doc.page_content for doc in results]
            
        logger.warning("Document not found for search: %s", doc_id)
        return []

    def clear(self):
        """Clears all indexed documents from memory and ChromaDB."""
        logger.info("Clearing all indexed documents...")
        
        # Clear in-memory small docs
        count_small = len(self.small_docs)
        self.small_docs.clear()
        self.doc_sizes.clear()
        logger.info("  -> Cleared %d small documents from memory", count_small)
        
        # Clear ChromaDB
        try:
            self.large_docs_index.delete_collection()
            
            # Re-initializing to ensure it's ready for new data if needed
            self.large_docs_index = Chroma(
                persist_directory=SETTINGS.chroma_db_path,
                collection_name=SETTINGS.chroma_collection_name,
                embedding_function=self.embeddings
            )
            logger.info("  -> Cleared and re-initialized ChromaDB collection")
        except Exception as e:
            logger.error("Error clearing ChromaDB: %s", e)
