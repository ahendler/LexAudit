"""
Retrieval client for fetching legal documents from official sources.
"""

import logging
import os
import xml.etree.ElementTree as ET
from typing import Optional

import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from ..core.models import ResolvedCitation, RetrievedDocument

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

        # Route to appropriate retriever based on URN pattern
        if canonical_id.startswith("urn:lex:br:"):
            return self._retrieve_from_google(canonical_id)
        else:
            raise NotImplementedError(
                "Retrieval for this citation type is not implemented yet."
            )

    def _retrieve_from_google(self, canonical_id: str) -> Optional[RetrievedDocument]:
        """
        Retrieve document by searching for the URN and fetching from official sources.

        Args:
            canonical_id: URN:LEX identifier

        Returns:
            Retrieved document or None if not found
        """
        logger.info("Searching for: %s", canonical_id)

        # Priority order: planalto.gov.br is best for laws, then normas.leg.br/lexml for URN resolution
        official_domains = [
            "planalto.gov.br",
            "normas.leg.br",
            "lexml.gov.br",
            "in.gov.br",
            "camara.leg.br",
            "senado.leg.br",
        ]

        try:
            # Search using SerpAPI
            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                logger.warning("SERPAPI_API_KEY not set in environment")
                return None

            params = {"q": canonical_id, "api_key": api_key, "num": 10}

            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])

            logger.info("Found %d search results", len(organic_results))
            for i, result in enumerate(organic_results):
                url = result.get("link", "")
                logger.debug("[%d] %s", i + 1, url)

            # Try each official domain in priority order
            for domain in official_domains:
                for result in organic_results:
                    url = result.get("link", "")

                    if domain in url:
                        logger.info("Using official link: %s", url)

                        # Fetch the actual content
                        response = self.session.get(url, timeout=15)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.content, "html.parser")

                        # Remove scripts and styles
                        for element in soup(
                            ["script", "style", "nav", "header", "footer", "aside"]
                        ):
                            element.decompose()

                        # Get text
                        text = soup.get_text(separator="\n", strip=True)
                        title = soup.title.string if soup.title else canonical_id

                        # Skip if content is too short (likely a redirect or error page)
                        if len(text) < 500:
                            logger.warning(
                                "Content too short (%d chars), trying next result...",
                                len(text),
                            )
                            continue

                        logger.info("Retrieved %d characters", len(text))

                        return RetrievedDocument(
                            canonical_id=canonical_id,
                            title=title,
                            full_text=text,
                            source="web_search",
                            metadata={
                                "publication_url": url,
                                "retrieval_method": "serpapi_google_search",
                            },
                        )

            logger.warning("No official links found")
            return None

        except Exception as e:
            logger.error("Error: %s", e)
            return None

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
