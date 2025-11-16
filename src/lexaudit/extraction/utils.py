from __future__ import annotations

from ..core.models import CitationCategory


def guess_citation_type(raw_text: str) -> CitationCategory:
    """
    Very lightweight heuristic to classify citations when we only have the raw
    string (e.g., in forward_extracted_citations).

    Prioritizes jurisprudência (incluindo súmulas, precedentes etc.) and defaults
    to legislação. Keep in sync com as categorias aceitas.
    """
    normalized = (raw_text or "").lower()

    sumula_tokens = [
        "súmula",
        "sumula",
        " súm.",
        " súm ",
        "oj ",
        "orientação jurisprudencial",
        "enunciado",
    ]
    jurisprudence_tokens = [
        "resp",
        "recurso",
        "re ",
        "are",
        "agrg",
        "agint",
        "hc",
        "ms",
        "adi",
        "adpf",
        "rcl",
        "rr",
        "ro ",
        "acórdão",
        "precedente",
        "stj",
        "stf",
        "tribunal",
    ]
    if any(token in normalized for token in sumula_tokens + jurisprudence_tokens):
        return "jurisprudência"

    return "legislação"


__all__ = ["guess_citation_type", "CitationCategory"]
