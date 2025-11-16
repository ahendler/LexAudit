from __future__ import annotations

"""Detector subpackage: regex scanner, linker adapter, and orchestration.

Exports convenience symbols so callers can simply do
`from lexaudit.extraction.detector import CitationDetector`.
"""

from .citation_detector import CitationDetector, CitationDetectorMetrics
from .deduplicator import deduplicate
from .pattern_scanner import run_scanner
from .linker_adapter import (
    run_linker,
    LinkerExecutionError,
    LinkerParsingError,
)

__all__ = [
    "CitationDetector",
    "CitationDetectorMetrics",
    "deduplicate",
    "run_scanner",
    "run_linker",
    "LinkerExecutionError",
    "LinkerParsingError",
]
