from __future__ import annotations

from .citation_detector import CitationDetector, CitationDetectorMetrics
from .deduplicator import deduplicate
from .linker_adapter import LinkerExecutionError, LinkerParsingError, run_linker
from .pattern_scanner import run_scanner

"""Detector subpackage: regex scanner, linker adapter, and orchestration.

Exports convenience symbols so callers can simply do
`from lexaudit.extraction.detector import CitationDetector`.
"""


__all__ = [
    "CitationDetector",
    "CitationDetectorMetrics",
    "deduplicate",
    "run_scanner",
    "run_linker",
    "LinkerExecutionError",
    "LinkerParsingError",
]
