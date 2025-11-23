"""
Citation extraction orchestrator.
"""

import logging
from typing import List, Optional

from .context_snippets import enhance_citation_snippet
from ..core.models import CitationSuspect, ExtractedCitation, IdentifiedCitation
from .detector import CitationDetector
from .identification import CitationIdentifier
from ..config.settings import SETTINGS

logger = logging.getLogger(__name__)


class CitationExtractor:
    """
    High-level orchestrator that coordinates detection and identification stages.
    """

    def __init__(
        self,
        *,
        detector: Optional[CitationDetector] = None,
        identifier: Optional[CitationIdentifier] = None,
    ) -> None:
        self.detector = detector or CitationDetector()
        self.identifier = identifier or CitationIdentifier()

    def extract_from_text(self, text: str) -> List[ExtractedCitation]:
        logger.info("Starting pipeline (text_len=%d)", len(text))

        # Detect suspects
        suspects = self.detector.detect(text)
        logger.info("Detector returned %d suspects", len(suspects))
        if not suspects:
            logger.info("No suspects detected; returning empty result")
            return []

        # Split suspects by type
        regex_suspects = [s for s in suspects if s.detector_type == "regex"]
        linker_detections = [s for s in suspects if s.detector_type == "linker"]
        logger.info(
            "Split suspects: regex=%d linker=%d",
            len(regex_suspects),
            len(linker_detections),
        )
        
        # Apply citation processing limit if configured
        limit = SETTINGS.citations_to_process
        if limit is not None and limit >= 0:
            regex_suspects = regex_suspects[:limit]
            linker_detections = linker_detections[:limit]
            logger.info(
                "Applied limit of %d citations: regex=%d linker=%d",
                limit,
                len(regex_suspects),
                len(linker_detections),
            )
        
        # Identify citations for regex suspects only
        logger.info("Running identification for %d regex suspects", len(regex_suspects))
        identified_regexes = (
            self.identifier.identify_citations(text, regex_suspects)
            if regex_suspects
            else []
        )
        logger.info(
            "Identification complete; %d suspects returned with citations",
            len(identified_regexes),
        )

        # Combine all suspects to normalize: regex (identified) + linker (as is)
        suspects_to_normalize = identified_regexes + linker_detections
        logger.info(
            "Normalizing %d suspects (regex+linker)", len(suspects_to_normalize)
        )

        extracted: List[ExtractedCitation] = []
        for suspect in suspects_to_normalize:
            for citation in suspect.identified_citations or []:
                try:
                    item = self._to_extracted(text, suspect, citation)
                    if item is not None:
                        extracted.append(item)
                except Exception:
                    # Already logged inside _to_extracted
                    continue

        logger.info("Produced %d extracted citations", len(extracted))

        if text and extracted:
            logger.info("Enhancing context snippets for %d citations", len(extracted))
            extracted = [
                enhance_citation_snippet(text, citation) for citation in extracted
            ]

        return extracted

    def _to_extracted(
        self,
        text: str,
        suspect: CitationSuspect,
        citation: IdentifiedCitation,
    ) -> Optional[ExtractedCitation]:
        needle = (citation.identified_string or suspect.suspect_string).strip()
        start_idx, end_idx = None, None

        if needle:
            # tenta localizar próximo do span do suspect (janela pequena), depois global
            window_start = max(0, suspect.start - len(needle))
            window_end = min(len(text), suspect.end + len(needle))
            idx = text.find(needle, window_start, window_end)
            if idx == -1:
                idx = text.find(needle)
            if idx != -1:
                start_idx = idx
                end_idx = idx + len(needle)
            else:
                # fallback: usa o span do suspect
                start_idx = suspect.start
                end_idx = suspect.end

        payload = citation.model_dump()
        payload.update(
            context_snippet=suspect.context_snippet,
            start=start_idx,
            end=end_idx,
        )
        try:
            return ExtractedCitation(**payload)
        except Exception as exc:
            logger.warning("Invalid citation payload skipped: %s", exc)
            return None

    def forward_extracted_citations(
        self,
        raw_citations: List[str],
    ) -> List[ExtractedCitation]:
        """
        Forward already extracted citations (from external source strings).

        Uses the lightweight guess_citation_type helper for classification and stores the string as
        both identified_string and formatted_name. The full string is used as
        context_snippet and positions are unknown (None).
        """
        extracted: List[ExtractedCitation] = []

        for raw in raw_citations or []:
            citation = ExtractedCitation(
                identified_string=raw,
                formatted_name=raw,
                citation_type="unknown",
                confidence=0.0,
                justification="",
                context_snippet=raw,
                start=None,
                end=None,
            )
            extracted.append(citation)

        return extracted
