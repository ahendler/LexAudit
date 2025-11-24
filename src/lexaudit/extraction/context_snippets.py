"""
Helpers for building expanded context snippets around citations.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from lexaudit.extraction.detector.snippets import _is_hard_break
from lexaudit.core.models import ExtractedCitation


def _paragraphs_from_blank_lines(text: str) -> List[Tuple[int, int]]:
    """
    Paragraphs delimited by blank lines (two or more newlines, optionally with
    whitespace in between).
    """
    ranges: List[Tuple[int, int]] = []
    last = 0

    for match in re.finditer(r"\n\s*\n+", text):
        start = match.start()
        if start > last:
            ranges.append((last, start))
        last = match.end()

    if last < len(text):
        ranges.append((last, len(text)))

    if not ranges:
        ranges.append((0, len(text)))

    return ranges


def _paragraphs_from_sentences(
    text: str, sentences_per_paragraph: int = 5
) -> List[Tuple[int, int]]:
    """
    Build paragraph ranges by grouping sentences when the text has no explicit
    paragraph breaks.

    A "sentence" here termina em ponto final ou equivalentes ('.', '!', '?'),
    usando a mesma heurística do detector para não confundir números e
    abreviações com fim de frase.
    """
    if not text:
        return [(0, 0)]

    # Find sentence boundaries (end indices, half-open ranges)
    bounds: List[int] = []
    for i in range(len(text)):
        if _is_hard_break(text, i):
            bounds.append(i + 1)

    if not bounds or bounds[-1] < len(text):
        bounds.append(len(text))

    # Build sentence ranges
    sentences: List[Tuple[int, int]] = []
    prev = 0
    for end in bounds:
        if end > prev:
            sentences.append((prev, end))
            prev = end

    if not sentences:
        return [(0, len(text))]

    # Group sentences in chunks of N as paragraphs
    paragraphs: List[Tuple[int, int]] = []
    n = len(sentences)
    step = max(1, sentences_per_paragraph)
    idx = 0
    while idx < n:
        group = sentences[idx : idx + step]
        p_start = group[0][0]
        p_end = group[-1][1]
        paragraphs.append((p_start, p_end))
        idx += step

    return paragraphs


def _paragraph_ranges(text: str) -> List[Tuple[int, int]]:
    """
    Return a list of (start, end) indices for paragraphs in ``text``.

    - Se houver quebras explícitas de parágrafo (linhas em branco: ``\\n\\n``),
      usamos essas fronteiras.
    - Se não houver nenhuma quebra de linha no texto, construímos parágrafos
      agrupando 5 períodos (frases) por parágrafo, usando a mesma heurística do
      detector para ponto final/abreviações/números.
    """
    if not text:
        return [(0, 0)]

    if "\n" in text:
        return _paragraphs_from_blank_lines(text)

    # Texto "corridão" sem quebras: derivar parágrafos a partir de períodos
    return _paragraphs_from_sentences(text, sentences_per_paragraph=5)


def build_three_paragraph_snippet(
    text: str,
    start: Optional[int],
    end: Optional[int] = None,
) -> str:
    """
    Build a snippet containing the paragraph where ``start`` occurs, plus the
    immediate previous and next paragraphs (when available).
    """
    if not text:
        return ""

    if start is None:
        return text.strip()

    start = max(0, min(start, len(text)))
    paragraphs = _paragraph_ranges(text)
    center_idx = len(paragraphs) - 1

    for idx, (p_start, p_end) in enumerate(paragraphs):
        if p_start <= start < p_end or (
            start == len(text) and p_start <= start <= p_end
        ):
            center_idx = idx
            break

    indices: List[int] = []
    if center_idx - 1 >= 0:
        indices.append(center_idx - 1)
    indices.append(center_idx)
    if center_idx + 1 < len(paragraphs):
        indices.append(center_idx + 1)

    pieces: List[str] = []
    for idx in indices:
        p_start, p_end = paragraphs[idx]
        segment = text[p_start:p_end].strip("\n")
        if segment:
            pieces.append(segment.strip())

    return "\n\n".join(pieces).strip()


def enhance_citation_snippet(
    full_text: str,
    citation: ExtractedCitation,
) -> ExtractedCitation:
    """
    Expand ``citation.context_snippet`` to include three paragraphs around the
    citation span.
    """
    if not full_text or citation.start is None:
        return citation

    expanded = build_three_paragraph_snippet(
        full_text,
        citation.start,
        citation.end,
    )
    if expanded:
        citation.context_snippet = expanded
    return citation


__all__ = ["build_three_paragraph_snippet", "enhance_citation_snippet"]
