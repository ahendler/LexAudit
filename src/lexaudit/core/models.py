"""
Data models for LexAudit pipeline.
"""

from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(Enum):
    """Validation status of a citation."""

    PENDING = "pending"
    CORRECT = "correct"
    OUTDATED = "outdated"
    INCORRECT = "incorrect"
    NON_EXISTENT = "non_existent"


class IdentifiedCitation(BaseModel):
    identified_string: str = Field(
        ...,
        description="The string identified as a citation exactly as it appears in the text",
    )
    formatted_name: str = Field(
        ...,
        description="Formatted, human-friendly name of the cited document (e.g., 'Federal Constitution of 1988')",
    )
    citation_type: str = Field(
        ...,
        description="Descrição livre do tipo de documento (ex.: 'Constituição Federal', 'Lei federal', 'jurisprudência do STJ')",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Identifier confidence score between 0 and 1",
    )
    justification: str = Field(
        default="",
        description="Brief justification by the agent for the identification",
    )


class IdentifiedCitations(BaseModel):
    citations: List[IdentifiedCitation] = Field(
        default_factory=list,
        description="List of identified citations",
    )


class ExtractedCitation(IdentifiedCitation):
    """Identified citation enriched with positional/context metadata.

    This supersedes the previous dataclass-based ExtractedCitation. It keeps the
    textual fields from identification and adds positional/context info.
    """

    context_snippet: str = Field(
        ...,
        description="Full text snippet from which the citation was extracted",
    )
    start: Optional[int] = Field(
        default=None,
        description="Start index of the citation in the original text",
    )
    end: Optional[int] = Field(
        default=None,
        description="End index of the citation in the original text",
    )


class CitationSuspect(BaseModel):
    context_snippet: str = Field(
        ...,
        description="The snippet of the original text where the suspect was detected",
    )
    suspect_string: str = Field(
        ...,
        description="The string detected as a potential citation",
    )
    start: int = Field(
        ...,
        description="Start index of the suspect snippet in the original text",
    )
    end: int = Field(
        ...,
        description="End index of the suspect snippet in the original text",
    )
    detector_type: Literal["linker", "regex"] = Field(
        ..., description="Type of detector that flagged this suspect"
    )
    identified_citations: List[IdentifiedCitation] = Field(
        default_factory=list,
        description="List of identified citations inside this suspect snippet",
    )


class ResolutionOutput(BaseModel):
    """Structured output for citation resolution."""

    canonical_id: str = Field(
        description="Canonical identifier for the legal reference (e.g., 'urn:lex:br:federal:lei:1998;9656')"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1 indicating certainty of the resolution",
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        description="Brief explanation of how the canonical ID was determined"
    )
    metadata: Optional[dict] = Field(
        default=None, description="Additional metadata extracted from the citation"
    )


class ResolvedCitation(BaseModel):
    """Represents a citation with a resolved canonical identifier."""

    extracted_citation: ExtractedCitation
    canonical_id: Optional[str] = None
    resolution_confidence: float = 0.0
    resolution_metadata: Dict[str, Any] = Field(default_factory=dict)

    def __repr__(self):
        return f"ResolvedCitation(id={self.canonical_id}, confidence={self.resolution_confidence})"


class RetrievedDocument(BaseModel):
    """Represents a retrieved legal document."""

    canonical_id: str
    title: str
    full_text: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __repr__(self):
        return f"RetrievedDocument(id={self.canonical_id}, source={self.source})"


class ValidatedCitation(BaseModel):
    """Represents a validated citation with RAG agent results."""

    resolved_citation: ResolvedCitation
    retrieved_document: Optional[RetrievedDocument] = None
    validation_status: ValidationStatus = ValidationStatus.PENDING
    justification: str = ""
    confidence: float = 0.0

    def __repr__(self):
        return f"ValidatedCitation(status={self.validation_status.value}, confidence={self.confidence})"


class DocumentAnalysis(BaseModel):
    """Complete analysis result for a document."""

    document_id: str
    extracted_citations: List[ExtractedCitation] = Field(default_factory=list)
    resolved_citations: List[ResolvedCitation] = Field(default_factory=list)
    validated_citations: List[ValidatedCitation] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __repr__(self):
        return (
            f"DocumentAnalysis(id={self.document_id}, "
            f"citations={len(self.extracted_citations)})"
        )
