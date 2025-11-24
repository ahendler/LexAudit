"""
Citation validator orchestrating triage and multi-agent debate.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.models import (
    CitationRetrieval,
    ValidatedCitation,
    ValidationStatus,
    ValidationOutput,
    DebateOutput,
)
from .triage_agent import TriageAgent
from .debate_graph import DebateGraph

logger = logging.getLogger(__name__)


class CitationValidator:
    """
    Orchestrates citation validation through triage and optional multi-agent debate.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize validator components."""
        self.triage_agent = TriageAgent()
        self.debate_graph = DebateGraph()
        self.output_dir = output_dir or Path("data/validation_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_outputs: List[ValidationOutput] = []

    def validate(self, citation_retrieval: CitationRetrieval) -> ValidatedCitation:
        """
        Validate a single citation through triage and optional debate.

        Args:
            citation_retrieval: Citation with retrieved document

        Returns:
            ValidatedCitation with final status and justification

        Raises:
            Exception: If validation fails (intentional crash)
        """
        resolved = citation_retrieval.resolved_citation
        extracted = resolved.extracted_citation

        triage_decision = self.triage_agent.analyze(citation_retrieval)

        debate_output_data = None

        if not triage_decision.needs_discussion:
            status = self._map_status(triage_decision.preliminary_status)

            logger.info(
                "  -> Triage decision final: %s (confidence=%.2f)",
                status.value,
                triage_decision.confidence,
            )

            final_status = status.value
            final_confidence = triage_decision.confidence
            final_justification = triage_decision.reasoning

        else:
            logger.info(
                "  -> Triage requires debate (confidence=%.2f)",
                triage_decision.confidence,
            )

            debate_decision = self.debate_graph.run_debate(citation_retrieval)

            status = self._map_status(debate_decision["validation_status"])

            logger.info(
                "  -> Debate decision final: %s (confidence=%.2f)",
                status.value,
                debate_decision["confidence"],
            )

            final_status = status.value
            final_confidence = debate_decision["confidence"]
            final_justification = debate_decision["justification"]

            debate_output_data = DebateOutput(
                validation_status=debate_decision["validation_status"],
                confidence=debate_decision["confidence"],
                justification=debate_decision["justification"],
                consensus_level=debate_decision["consensus_level"],
                verifier_arguments=debate_decision.get("verifier_arguments", []),
            )

        validation_output = ValidationOutput(
            citation_reference=extracted.formatted_name,
            citation_context=extracted.context_snippet or "",
            canonical_id=resolved.canonical_id,
            triage_decision=triage_decision,
            debate_output=debate_output_data,
            final_status=final_status,
            final_confidence=final_confidence,
            final_justification=final_justification,
        )

        self.validation_outputs.append(validation_output)

        return ValidatedCitation(
            resolved_citation=resolved,
            retrieved_document=citation_retrieval.retrieved_document,
            validation_status=status,
            justification=final_justification,
            confidence=final_confidence,
        )

    def validate_batch(
        self, citation_retrievals: List[CitationRetrieval], document_id: str = "unknown"
    ) -> List[ValidatedCitation]:
        """
        Validate multiple citations.

        Args:
            citation_retrievals: List of citations with retrieved documents
            document_id: Document identifier for output file naming

        Returns:
            List of validated citations
        """
        self.validation_outputs = []
        validated = []

        for retrieval in citation_retrievals:
            validated_citation = self.validate(retrieval)
            validated.append(validated_citation)

        self._save_outputs(document_id)

        return validated

    def _save_outputs(self, document_id: str):
        """
        Save validation outputs to JSON file.

        Args:
            document_id: Document identifier for file naming
        """
        if not self.validation_outputs:
            logger.warning("No validation outputs to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{document_id}_{timestamp}.json"
        filepath = self.output_dir / filename

        output_data = {
            "document_id": document_id,
            "timestamp": timestamp,
            "total_citations": len(self.validation_outputs),
            "validations": [output.model_dump() for output in self.validation_outputs],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info("  -> Saved validation outputs to: %s", filepath)

    @staticmethod
    def _map_status(status_str: str) -> ValidationStatus:
        """
        Map string status to ValidationStatus enum.

        Args:
            status_str: Status string from agent

        Returns:
            ValidationStatus enum value
        """
        status_map = {
            "correct": ValidationStatus.CORRECT,
            "outdated": ValidationStatus.OUTDATED,
            "incorrect": ValidationStatus.INCORRECT,
            "non_existent": ValidationStatus.NON_EXISTENT,
            "pending": ValidationStatus.PENDING,
        }
        return status_map.get(status_str.lower(), ValidationStatus.PENDING)
