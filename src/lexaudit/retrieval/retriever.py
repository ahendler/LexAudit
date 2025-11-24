"""
Retrieval client for fetching legal documents from official sources.
"""

import hashlib
import json
import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional

import requests
import trafilatura
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from ..core.models import ResolvedCitation, RetrievedDocument
from ..core.structured_llm import StructuredLLM
from ..prompts.retrieved_citation_check import RETRIEVED_CITATION_CHECK_PROMPT
from .retrieved_citation_check import RetrievedCitationCheck

logger = logging.getLogger(__name__)


class LegalDocumentRetriever:
    """
    Retrieves legal documents from official sources using LexML SRU API.

    Based on the SRU (Search/Retrieval via URL) standard.
    Documentation: http://www.loc.gov/standards/sru/
    """

    LEXML_SRU_BASE = "https://www.lexml.gov.br/busca/SRU"

    def __init__(self):
        """Initialize the retriever."""
        self.session = requests.Session()
        self.llm = StructuredLLM()
        # Set browser-like headers to avoid being blocked by government sites
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        # Pages cache directory (stores mapping URL -> RetrievedDocument as JSON)
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        self.pages_cache_dir = os.path.join(repo_root, "data", "retrieved_pages")
        os.makedirs(self.pages_cache_dir, exist_ok=True)

    def retrieve(
        self, resolved_citation: ResolvedCitation
    ) -> Optional[RetrievedDocument]:
        """
        Retrieve the full document for a resolved citation.

        Args:
            resolved_citation: Citation with canonical identifier

        Returns:
            Retrieved document or None if not found
        """
        if not resolved_citation.canonical_id:
            return None

        canonical_id = resolved_citation.canonical_id
        # Use the raw citation text for searching (better Google results)
        raw_citation = resolved_citation.extracted_citation.identified_string

        # Route to appropriate retriever based on URN pattern
        if canonical_id.startswith("urn:lex:br:"):
            return self._retrieve_from_google(canonical_id, raw_citation)
        else:
            raise NotImplementedError(
                "Retrieval for this citation type is not implemented yet."
            )

    def _retrieve_from_google(
        self, canonical_id: str, raw_citation: str
    ) -> Optional[RetrievedDocument]:
        """Retrieve document by searching and fetching from official sources."""
        logger.info("Searching for: %s (URN: %s)", raw_citation, canonical_id)

        # Search for URLs
        urls = self._search_google(raw_citation)
        if not urls:
            return None

        # Try each URL in priority order
        official_domains = [
            "planalto.gov.br",
            "normas.leg.br",
            "lexml.gov.br",
            "in.gov.br",
            "camara.leg.br",
            "senado.leg.br",
        ]

        for domain in official_domains:
            for url in urls:
                if domain in url:
                    doc = self._fetch_and_extract(url, canonical_id, raw_citation)
                    if doc:
                        return doc

        logger.warning("No official content retrieved")
        return None

    def _search_google(self, query: str) -> list[str]:
        """Search Google and return list of URLs."""
        try:
            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                logger.warning("SERPAPI_API_KEY not set")
                return []

            search = GoogleSearch({"q": query, "api_key": api_key, "num": 10})
            results = search.get_dict().get("organic_results", [])
            urls = [r.get("link", "") for r in results if r.get("link")]
            logger.info("Found %d search results", len(urls))
            return urls
        except Exception as e:
            logger.error("Search failed: %s", e)
            return []

    def _fetch_and_extract(
        self, url: str, canonical_id: str, raw_citation: str = ""
    ) -> Optional[RetrievedDocument]:
        """Fetch URL and extract main content using Trafilatura."""
        logger.info("Trying: %s", url)

        # Check cache
        cached = self._load_cached_page(url)
        if cached:
            logger.info("Cache hit")
            return cached

        # Fetch and extract
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Preprocess HTML to mark strikethrough content
            html_content = self._preprocess_strikethrough(response.content)

            # Extract main content with Trafilatura
            # favor_recall=True prioritizes capturing more content over precision
            text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_recall=True,
            )

            if not text or len(text) < 500:
                logger.warning("Content too short (%d chars)", len(text) if text else 0)
                return None

            # Post-process: merge adjacent revoked sections in extracted text
            text = self._merge_adjacent_revoked(text)

            # Check if document matches citation
            # if not self._check_retrieved_citation(
            #     text, raw_citation, canonical_id, url
            # ):
            #     logger.warning("Retrieved citation check failed, trying next result")
            #     return None

            # Extract title
            metadata = trafilatura.extract_metadata(response.content)
            title = metadata.title if metadata and metadata.title else canonical_id

            logger.info("Retrieved %d characters", len(text))

            doc = RetrievedDocument(
                canonical_id=canonical_id,
                title=title.strip(),
                full_text=f"{url}\n\n{text}",
                source="web_search",
                metadata={"publication_url": url, "retrieval_method": "trafilatura"},
            )

            self._save_cached_page(url, doc)
            return doc

        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return None

    def _preprocess_strikethrough(self, html_content: bytes) -> str:
        """Preprocess HTML to mark strikethrough content with special markers."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all strike/s/del tags and unwrap them with markers
        strike_tags = soup.find_all(["strike", "s", "del"])
        logger.debug(f"Found {len(strike_tags)} strikethrough tags")

        for i, tag in enumerate(strike_tags):
            preview = tag.get_text()[:100].replace("\n", " ")
            logger.debug(f"Strike tag {i + 1}: {preview}...")

            # Insert marker before the tag content
            marker_before = soup.new_string("<REVOGADO_INICIO>")
            tag.insert_before(marker_before)

            # Insert marker after the tag content
            marker_after = soup.new_string("<REVOGADO_FIM>")
            tag.insert_after(marker_after)

            # Unwrap the tag (keep content, remove the tag itself)
            tag.unwrap()

        return str(soup)

    def _merge_adjacent_revoked(self, text: str) -> str:
        """Merge adjacent revoked sections separated by short content."""
        import re

        # Pattern: <REVOGADO_FIM> followed by short content, then <REVOGADO_INICIO>
        # Captures: whitespace, newlines, bullets (-, *, •), and short text (< 4 chars)
        def should_merge(match):
            separator = match.group(1)
            # Strip whitespace and common bullet characters
            cleaned = separator.strip().lstrip("-*•")
            # If what remains is very short (< 4 chars), merge the sections
            if len(cleaned) < 4:
                return "\n"  # Replace with single newline
            return match.group(0)  # Keep as is

        # Match end tag, separator content, and start tag
        # Allow for bullets, whitespace, and short strings
        merged = re.sub(
            r"<REVOGADO_FIM>([^<]{0,20})<REVOGADO_INICIO>", should_merge, text
        )

        return merged

    def _check_retrieved_citation(
        self, text: str, raw_citation: str, canonical_id: str, url: str
    ) -> bool:
        """Check that retrieved document matches the citation using LLM."""
        if not self.llm.available:
            logger.error("LLM not available, skipping check")
            return True  # Skip check if LLM not configured

        try:
            # Send full document text for checking
            check_result = self.llm.invoke(
                RETRIEVED_CITATION_CHECK_PROMPT,
                {
                    "citation_text": raw_citation,
                    "canonical_id": canonical_id,
                    "document_text": text,
                },
                RetrievedCitationCheck,
            )
            logger.info(
                "Retrieved citation check: %s - %s",
                "MATCH" if check_result.matches else "NO MATCH",
                check_result.reasoning,
            )
            if check_result.extracted_text:
                logger.info(
                    "Extracted specific part (%d chars): %s...",
                    len(check_result.extracted_text),
                    check_result.extracted_text,
                )
            return check_result.matches
        except Exception as e:
            logger.warning("Citation check failed: %s. Accepting document.", e)
            return True  # Accept on error

    # Pages cache helpers
    def _cache_file_path(self, url: str) -> str:
        """Return a filesystem-safe cache file path for a given URL."""
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return os.path.join(self.pages_cache_dir, f"{key}.json")

    def _load_cached_page(self, url: str) -> Optional[RetrievedDocument]:
        """Load a cached RetrievedDocument for a given URL if present."""
        path = self._cache_file_path(url)
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct RetrievedDocument
        return RetrievedDocument(**data)

    def _save_cached_page(self, url: str, doc: RetrievedDocument) -> None:
        """Save a RetrievedDocument to the pages cache."""
        path = self._cache_file_path(url)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(doc.dict(), f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)

    # NOT WORKING YET
    def _retrieve_from_lexml_api(
        self, canonical_id: str
    ) -> Optional[RetrievedDocument]:
        """
        Retrieve document metadata from LexML using SRU API.

        Args:
            canonical_id: URN:LEX identifier (e.g., urn:lex:br:federal:lei:1998;9656)

        Returns:
            Retrieved document or None if not found
        """
        # Build CQL query for exact URN match
        query = f'urn="{canonical_id}"'

        # Build SRU API URL
        params = {
            "operation": "searchRetrieve",
            "version": "1.1",
            "query": query,
            "startRecord": "1",
            "maximumRecords": "1",
        }

        logger.info("Querying LexML API for: %s", canonical_id)

        response = self.session.get(self.LEXML_SRU_BASE, params=params, timeout=10)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)

        # Define namespaces
        ns = {
            "srw": "http://www.loc.gov/zing/srw/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "lexml": "http://www.lexml.gov.br/elementSet",
        }

        # Check if we got results
        num_records = root.find(".//srw:numberOfRecords", ns)
        if num_records is None or int(num_records.text) == 0:
            logger.warning("No results found for %s", canonical_id)
            return None

        # Extract record data
        record = root.find(".//srw:record", ns)
        if record is None:
            return None

        # Extract metadata
        title_elem = record.find(".//dc:title", ns)
        title = title_elem.text if title_elem is not None else canonical_id

        description_elem = record.find(".//dc:description", ns)
        description = description_elem.text if description_elem is not None else ""

        # Extract publication links
        identifier_elems = record.findall(".//dc:identifier", ns)
        publication_url = None

        for identifier in identifier_elems:
            if identifier.text and "planalto.gov.br" in identifier.text:
                publication_url = identifier.text
                break
            elif identifier.text and (
                "camara.leg.br" in identifier.text
                or "senado.leg.br" in identifier.text
                or "in.gov.br" in identifier.text
            ):
                if not publication_url:
                    publication_url = identifier.text

        # Build result
        full_text = f"{title}\n\n{description}" if description else title

        logger.info("Found document: %s...", title[:60])

        # Save to file for debugging
        with open("retrieved_document.txt", "w", encoding="utf-8") as f:
            f.write(full_text)

        return RetrievedDocument(
            canonical_id=canonical_id,
            title=title,
            full_text=full_text,
            source="lexml_api",
            metadata={
                "publication_url": publication_url,
                "retrieval_method": "lexml_sru_api",
                "description": description,
            },
        )
