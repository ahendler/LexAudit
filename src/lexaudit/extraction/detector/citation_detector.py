from __future__ import annotations

import logging
from time import perf_counter
from typing import Dict, List, Optional, Sequence, Tuple

from config.settings import SETTINGS
from lexaudit.core.models import CitationSuspect

from .deduplicator import deduplicate
from .linker_adapter import (
    LinkerExecutionError,
    LinkerParsingError,
    run_linker,
)
from .pattern_scanner import run_scanner

logger = logging.getLogger(__name__)


CitationDetectorMetrics = Dict[str, float]


class CitationDetector:
    """
    High-level detector that orchestrates the linker adapter, regex scanner and
    deduplication heuristics to surface high-quality citation suspects.
    """

    def __init__(
        self,
        *,
        use_linker: bool = True,
        linker_cmd: Optional[Sequence[str]] = None,
        context: str = SETTINGS.linker_context,
        timeout: Optional[float] = SETTINGS.linker_timeout,
        max_gap: int = SETTINGS.dedup_gap_l2,
    ) -> None:
        self._use_linker = use_linker
        self._context = context
        self._timeout = timeout
        self._max_gap = max_gap
        self._linker_cmd = list(linker_cmd) if linker_cmd is not None else list(SETTINGS.linker_cmd)

    def detect(
        self,
        text: str,
        *,
        use_linker: Optional[bool] = None,
        linker_cmd: Optional[Sequence[str]] = None,
        context: Optional[str] = None,
        timeout: Optional[float] = None,
        max_gap: Optional[int] = None,
    ) -> List[CitationSuspect]:
        suspects, _ = self.detect_with_metrics(
            text,
            use_linker=use_linker,
            linker_cmd=linker_cmd,
            context=context,
            timeout=timeout,
            max_gap=max_gap,
        )
        return suspects

    def detect_with_metrics(
        self,
        text: str,
        *,
        use_linker: Optional[bool] = None,
        linker_cmd: Optional[Sequence[str]] = None,
        context: Optional[str] = None,
        timeout: Optional[float] = None,
        max_gap: Optional[int] = None,
    ) -> Tuple[List[CitationSuspect], CitationDetectorMetrics]:
        """
        Run the multi-stage detector and return both suspects and execution metrics.

        The method mirrors the previous functional implementation but gives the caller
        fine-grained overrides while keeping sane defaults configured at init time.
        """
        resolved_use_linker = self._use_linker if use_linker is None else use_linker
        resolved_context = self._context if context is None else context
        resolved_timeout = self._timeout if timeout is None else timeout
        resolved_max_gap = self._max_gap if max_gap is None else max_gap
        resolved_linker_cmd = list(self._linker_cmd if linker_cmd is None else linker_cmd)

        t0 = perf_counter()
        logger.info(
            "Starting detection: use_linker=%s context=%s max_gap=%s",
            resolved_use_linker,
            resolved_context,
            resolved_max_gap,
        )

        linker_citations: List[CitationSuspect] = []
        t_linker = 0.0
        if resolved_use_linker:
            tl0 = perf_counter()
            try:
                linker_citations = run_linker(
                    text,
                    command=resolved_linker_cmd,
                    context=resolved_context,
                    timeout=resolved_timeout,
                )
            except (LinkerExecutionError, LinkerParsingError):
                # Fallback silencioso para apenas regex
                linker_citations = []
            finally:
                t_linker = perf_counter() - tl0
                logger.info(
                    "Precision(Linker): %d references in %.3fs",
                    len(linker_citations),
                    t_linker,
                )

        ts0 = perf_counter()
        regex_citations: List[CitationSuspect] = run_scanner(text)
        t_scanner = perf_counter() - ts0
        logger.info(
            "Coverage(Regex): %d references in %.3fs",
            len(regex_citations),
            t_scanner,
        )

        td0 = perf_counter()
        final = deduplicate(
            text,
            linker_citations,
            regex_citations,
            max_gap=resolved_max_gap,
        )
        t_dedup = perf_counter() - td0
        t_total = perf_counter() - t0
        logger.info(
            "Deduplication: %d final references in %.3fs (total=%.3fs)",
            len(final),
            t_dedup,
            t_total,
        )

        metrics: CitationDetectorMetrics = {
            "duration_linker_s": t_linker,
            "duration_scanner_s": t_scanner,
            "duration_dedup_s": t_dedup,
            "duration_total_s": t_total,
            "num_l1": float(len(linker_citations)),
            "num_l2": float(len(regex_citations)),
            "num_final": float(len(final)),
        }
        return final, metrics


__all__ = [
    "CitationDetector",
    "CitationDetectorMetrics",
]
