from __future__ import annotations

from typing import List

from lexaudit.core.models import CitationSuspect

from .regexes import LEXML_REFERENCE_REGEX


def run_scanner(text: str) -> List[CitationSuspect]:
    """
    Scanner based on regex (Coverage), equivalent to the behavior of version 2.
    - Uses the unified regex compiled from fragments (strict + loose).
    - Maintains the same iteration logic (finditer) of v2.
    - Returns Citation objects with detector="regex".
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    citations: List[CitationSuspect] = []
    for m in LEXML_REFERENCE_REGEX.finditer(text):
        citations.append(
            CitationSuspect(
                suspect_string=m.group(0),
                context_snippet="",
                start=m.start(),
                end=m.end(),
                detector_type="regex",
            )
        )
    # Sort by start for stability
    citations.sort(key=lambda c: (c.start, c.end))
    return citations


__all__ = ["run_scanner"]
