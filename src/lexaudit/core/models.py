"""
Data models for LexAudit pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class CitationType(Enum):
    """Type of legal citation."""
    LEGISLATION = "legislation"
    JURISPRUDENCE = "jurisprudence"


class ValidationStatus(Enum):
    """Validation status of a citation."""
    PENDING = "pending"
    CORRECT = "correct"
    OUTDATED = "outdated"
    INCORRECT = "incorrect"
    NON_EXISTENT = "non_existent"


@dataclass
class ExtractedCitation:
    """Represents an extracted legal citation."""
    raw_text: str
    citation_type: CitationType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"ExtractedCitation(type={self.citation_type.value}, text='{self.raw_text[:50]}...')"


@dataclass
class ResolvedCitation:
    """Represents a citation with a resolved canonical identifier."""
    extracted_citation: ExtractedCitation
    canonical_id: Optional[str] = None
    resolution_confidence: float = 0.0
    resolution_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"ResolvedCitation(id={self.canonical_id}, confidence={self.resolution_confidence})"


@dataclass
class RetrievedDocument:
    """Represents a retrieved legal document."""
    canonical_id: str
    title: str
    full_text: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"RetrievedDocument(id={self.canonical_id}, source={self.source})"


@dataclass
class ValidatedCitation:
    """Represents a validated citation with RAG agent results."""
    resolved_citation: ResolvedCitation
    retrieved_document: Optional[RetrievedDocument] = None
    validation_status: ValidationStatus = ValidationStatus.PENDING
    justification: str = ""
    confidence: float = 0.0
    
    def __repr__(self):
        return f"ValidatedCitation(status={self.validation_status.value}, confidence={self.confidence})"


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a document."""
    document_id: str
    extracted_citations: List[ExtractedCitation] = field(default_factory=list)
    resolved_citations: List[ResolvedCitation] = field(default_factory=list)
    validated_citations: List[ValidatedCitation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return (f"DocumentAnalysis(id={self.document_id}, "
                f"citations={len(self.extracted_citations)})")
