from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Dict, List, Optional

from lexaudit.config.settings import SETTINGS
from lexaudit.core.models import CitationSuspect, IdentifiedCitation
from lexaudit.core.structured_llm import IdentifierLLM

logger = logging.getLogger(__name__)


class CitationIdentifier:
    """
    Identifier stage that normalizes suspects into structured citations.

    Expect to receive only non-linker suspects. The caller is responsible for
    separating linker outputs (which can be passed-through upstream).
    """

    def __init__(
        self,
        *,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        enable_review: bool = True,
    ) -> None:
        self.llm_service = IdentifierLLM(model_name=model_name, temperature=temperature)
        self.model_name = self.llm_service.model_name
        # Review config
        self.enable_review = enable_review
        logger.info(
            "[Identifier] LLM configured: provider=%s model=%s available=%s",
            getattr(SETTINGS, "llm_provider", "unknown"),
            self.model_name,
            self.llm_service.available,
        )

    def identify_citations(
        self,
        text: str,
        suspects: List[CitationSuspect],
    ) -> List[CitationSuspect]:
        """
        Runs the identification agent (and the reviewer, if enabled) for
        each suspect and returns the list with identified_citations filled in.
        """
        if not suspects:
            return []

        processed: List[CitationSuspect] = []
        logger.info(
            "Starting identification for %d suspects (review=%s)",
            len(suspects),
            self.enable_review,
        )
        for suspect in suspects:
            t0 = perf_counter()
            logger.info(
                "Identifying suspect span=(%d,%d) len=%d",
                suspect.start,
                suspect.end,
                len(suspect.context_snippet or ""),
            )
            identified_suspect = self._run_identifier_agent(suspect)
            if self.enable_review and identified_suspect.identified_citations:
                identified_suspect = self._run_reviewer_agent(identified_suspect)
            dt = perf_counter() - t0
            logger.info(
                "Finished suspect (%d citations) in %.2fs",
                len(identified_suspect.identified_citations or []),
                dt,
            )
            processed.append(identified_suspect)

        logger.info("Completed identification stage")
        return processed

    def _run_identifier_agent(self, suspect: CitationSuspect) -> CitationSuspect:
        if not self.llm_service.available:
            suspect.identified_citations = []
            logger.warning("LLM unavailable; skipping identification")
            return suspect
        try:
            logger.info("Invoking LLM identify (model=%s)", self.model_name)
            output = self.llm_service.identify(suspect.context_snippet)
            built: List[IdentifiedCitation] = []
            for item in output.citations:
                try:
                    built.append(
                        self._build_identified(
                            identified_string=getattr(item, "identified_string", "")
                            or suspect.suspect_string,
                            formatted_name=getattr(item, "formatted_name", "")
                            or suspect.suspect_string,
                            citation_type=getattr(item, "citation_type", None),
                            confidence=getattr(item, "confidence", 1.0),
                            justification=getattr(item, "justification", ""),
                        )
                    )
                except Exception as exc:
                    logger.warning("Skipping invalid citation item: %s", exc)
            # Log raw structured result
            try:
                logger.info(
                    "LLM identify output: %s...",
                    output.model_dump_json(ensure_ascii=False)[:100],
                )
            except Exception:
                logger.info(
                    "LLM identify produced %d items",
                    len(getattr(output, "citations", []) or []),
                )
            suspect.identified_citations = built
            return suspect
        except Exception as exc:
            logger.warning("Identifier LLM failed: %s", exc)
            suspect.identified_citations = []
            return suspect

    def _run_reviewer_agent(self, suspect: CitationSuspect) -> CitationSuspect:
        if not self.llm_service.available or not suspect.identified_citations:
            return suspect
        proposals_json = json.dumps(
            [ic.model_dump() for ic in suspect.identified_citations], ensure_ascii=False
        )
        try:
            logger.info(
                "Invoking LLM review (model=%s) with %d proposals",
                self.model_name,
                len(suspect.identified_citations),
            )
            logger.info("Proposals JSON: %s", proposals_json)
            reviewed_output = self.llm_service.review(
                suspect.context_snippet,
                proposals_json,
            )
            reviewed_list: List[IdentifiedCitation] = list(
                reviewed_output.citations or []
            )
            try:
                logger.info(
                    "LLM review output: %s",
                    reviewed_output.model_dump_json(ensure_ascii=False),
                )
            except Exception:
                logger.info(
                    "LLM review produced %d items",
                    len(reviewed_list),
                )
            if reviewed_list:
                suspect.identified_citations = reviewed_list
            return suspect
        except Exception as exc:
            logger.warning("Reviewer step failed: %s", exc)
            return suspect

    def _build_identified(
        self,
        *,
        identified_string: Optional[str] = None,
        formatted_name: str,
        citation_type: Optional[str] = None,
        confidence: Optional[float] = None,
        justification: Optional[str] = None,
    ) -> IdentifiedCitation:
        # determined identified_string
        identified_string_value = (
            identified_string if identified_string is not None else formatted_name
        )

        payload: Dict[str, object] = {
            "formatted_name": formatted_name,
            "identified_string": identified_string_value,
        }
        if citation_type is None or str(citation_type).strip() == "":
            # Enforce presence early; downstream models expect a descriptive string
            raise ValueError("citation_type must be provided")
        payload["citation_type"] = citation_type
        if confidence is not None:
            payload["confidence"] = confidence
        if justification is not None:
            payload["justification"] = justification

        return IdentifiedCitation(**payload)


__all__ = ["CitationIdentifier"]
