from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from lexaudit.config.settings import SETTINGS
from lexaudit.core.models import CitationSuspect

from .snippets import build_sentence_bounded_range


def _overlaps(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """Return True if half-open ranges a and b overlap.

    Ranges are interpreted as [start, end), consistent with Python slicing.
    """
    (a0, a1), (b0, b1) = a, b
    return (a0 < b1) and (b0 < a1)


@dataclass
class _Cluster:
    """Internal structure to group nearby suspects and compute one snippet.

    - prelim_left/right: preliminary sentence-bounded window used for grouping.
    - cov_start/end: minimal coverage that must be contained by the final snippet
      (union of member spans).
    - snip_start/end: final snippet bounds (computed later).
    - rep: chosen representative suspect for this cluster.
    """

    members: List[CitationSuspect] = field(default_factory=list)
    prelim_left: int = 0
    prelim_right: int = 0
    cov_start: int = 0
    cov_end: int = 0
    snip_start: int = 0
    snip_end: int = 0
    rep: Optional[CitationSuspect] = None


def _filter_regex_overlapping_linker(
    linkers: List[CitationSuspect], regexes: List[CitationSuspect]
) -> List[CitationSuspect]:
    """Drop regex suspects whose span overlaps any linker span."""
    linker_spans = [(c.start, c.end) for c in linkers]
    kept: List[CitationSuspect] = []
    for c in regexes:
        span = (c.start, c.end)
        if not any(_overlaps(span, s) for s in linker_spans):
            kept.append(c)
    return kept


def _preliminary_window(
    text: str,
    s: CitationSuspect,
    *,
    min_chars: int,
    max_chars: Optional[int],
) -> Tuple[int, int]:
    """Sentence-aware preliminary window for one suspect span."""
    left, right = build_sentence_bounded_range(
        text,
        s.start,
        s.end,
        min_chars=min_chars,
        max_chars=max_chars,
        lock_left=False,
        lock_right=False,
    )
    return left, right


def _build_clusters(windows: List[Tuple[int, int, CitationSuspect]]) -> List[_Cluster]:
    """
    Groups citation suspects into clusters based on overlapping preliminary windows.

    Args:
        windows: A list of tuples (window_left, window_right, suspect), where window_left and window_right
                 define the sentence-bounded window for that suspect.

    Returns:
        A list of _Cluster objects, each containing suspects whose sentence windows overlap.
    """
    clusters: List[_Cluster] = []

    # Sort windows by their starting position, then by end for stable order.
    for window_left, window_right, suspect in sorted(
        windows, key=lambda w: (w[0], w[1])
    ):
        # If there are no clusters yet or this window doesn't overlap the last cluster, start a new one.
        if not clusters or window_left > clusters[-1].prelim_right:
            clusters.append(
                _Cluster(
                    members=[suspect],
                    prelim_left=window_left,
                    prelim_right=window_right,
                    cov_start=suspect.start,
                    cov_end=suspect.end,
                )
            )
        else:
            # Merge into the last cluster: expand its window and coverage as needed.
            current = clusters[-1]
            current.members.append(suspect)
            current.prelim_right = max(current.prelim_right, window_right)
            current.cov_start = min(current.cov_start, suspect.start)
            current.cov_end = max(current.cov_end, suspect.end)

    return clusters


def _has_left_linker_anchor(cl: _Cluster) -> bool:
    return any(
        m.detector_type == "linker" and m.start == cl.cov_start for m in cl.members
    )


def _has_right_linker_anchor(cl: _Cluster) -> bool:
    return any(m.detector_type == "linker" and m.end == cl.cov_end for m in cl.members)


def _compute_cluster_snippet_range(
    text: str,
    cl: _Cluster,
    *,
    min_chars: int,
    max_chars: Optional[int],
    prefer_linker_edges: bool,
) -> Tuple[int, int]:
    """Compute the final snippet range for a cluster, honoring linker anchors."""
    lock_left = prefer_linker_edges and _has_left_linker_anchor(cl)
    lock_right = prefer_linker_edges and _has_right_linker_anchor(cl)
    s_left, s_right = build_sentence_bounded_range(
        text,
        cl.cov_start,
        cl.cov_end,
        min_chars=min_chars,
        max_chars=max_chars,
        lock_left=lock_left,
        lock_right=lock_right,
    )
    return s_left, s_right


def _choose_representative(cl: _Cluster) -> CitationSuspect:
    """Prefer a linker suspect; otherwise the earliest by start/end."""
    linkers = [m for m in cl.members if m.detector_type == "linker"]
    return (
        min(linkers, key=lambda m: (m.start, m.end))
        if linkers
        else min(cl.members, key=lambda m: (m.start, m.end))
    )


def _reconcile_adjacent_clusters(
    clusters: List[_Cluster],
    text: str,
    *,
    min_chars: int,
    max_chars: Optional[int],
    prefer_linker_edges: bool,
) -> List[_Cluster]:
    """Ensure no overlap between final snippet ranges; merge if coverage overlaps.

    - If two cluster snippets overlap and the coverage intervals also overlap,
      merge them and recompute snippet and representative.
    - Otherwise, trim the left cluster's snip_end so it ends at or before the
      right cluster's snip_start, but never before its coverage end.
    """
    i = 1
    while i < len(clusters):
        prev = clusters[i - 1]
        curr = clusters[i]
        if prev.snip_end <= curr.snip_start:
            i += 1
            continue
        # Coverage overlap → merge clusters
        if prev.cov_end > curr.cov_start:
            merged = _Cluster(
                members=prev.members + curr.members,
                prelim_left=min(prev.prelim_left, curr.prelim_left),
                prelim_right=max(prev.prelim_right, curr.prelim_right),
                cov_start=min(prev.cov_start, curr.cov_start),
                cov_end=max(prev.cov_end, curr.cov_end),
            )
            merged.snip_start, merged.snip_end = _compute_cluster_snippet_range(
                text,
                merged,
                min_chars=min_chars,
                max_chars=max_chars,
                prefer_linker_edges=prefer_linker_edges,
            )
            merged.rep = _choose_representative(merged)
            clusters[i - 1 : i + 1] = [merged]
            # do not increment i; re-check with new neighbor
            continue
        # No coverage overlap → trim previous snippet to avoid overlap
        prev.snip_end = max(prev.cov_end, min(prev.snip_end, curr.snip_start))
        i += 1
    return clusters


def deduplicate(
    text: str,
    linker_citations: List[CitationSuspect],
    regex_citations: List[CitationSuspect],
    *,
    snippet_min_chars: int = getattr(SETTINGS, "snippet_min_chars", 120),
    snippet_max_chars: Optional[int] = getattr(SETTINGS, "snippet_max_chars", 600),
    prefer_linker_edges: bool = getattr(SETTINGS, "prefer_linker_edges", True),
) -> List[CitationSuspect]:
    """
    Multi-stage deduplication and snippet building.

    Steps:
    1) Remove regex suspects that overlap any linker suspect (keep linker).
    2) Compute sentence-aware preliminary windows for remaining suspects.
    3) Build clusters by merging overlapping preliminary windows.
    4) For each cluster, compute a final snippet range and choose a representative
       (prefer linker, else earliest).
    5) Reconcile adjacent clusters to avoid snippet overlap; merge when coverage overlaps.

    Returns representatives with snippet in `context_snippet`, sorted by start.

    Note: proximity is determined by overlap of sentence windows rather than a
    fixed gap threshold.
    """
    # 1) Sort inputs for stability and drop regex overlapping linker spans
    link_sorted = sorted(linker_citations, key=lambda c: (c.start, c.end))
    regex_sorted = sorted(regex_citations, key=lambda c: (c.start, c.end))
    regex_kept = _filter_regex_overlapping_linker(link_sorted, regex_sorted)

    # 2) Build preliminary windows
    windows: List[Tuple[int, int, CitationSuspect]] = []
    for s in link_sorted + regex_kept:
        w_left, w_right = _preliminary_window(
            text, s, min_chars=snippet_min_chars, max_chars=snippet_max_chars
        )
        windows.append((w_left, w_right, s))

    # 3) Cluster by overlapping windows
    clusters = _build_clusters(windows)

    # 4) Compute snippet range + representative for each cluster
    for cl in clusters:
        cl.snip_start, cl.snip_end = _compute_cluster_snippet_range(
            text,
            cl,
            min_chars=snippet_min_chars,
            max_chars=snippet_max_chars,
            prefer_linker_edges=prefer_linker_edges,
        )
        cl.rep = _choose_representative(cl)

    # 5) Ensure no overlap among final snippets
    clusters = _reconcile_adjacent_clusters(
        clusters,
        text,
        min_chars=snippet_min_chars,
        max_chars=snippet_max_chars,
        prefer_linker_edges=prefer_linker_edges,
    )

    # Build return: representatives with updated context_snippet
    final_items: List[CitationSuspect] = []
    for cl in clusters:
        rep = cl.rep  # type: ignore[assignment]
        if rep is None:
            # Shouldn't happen, but be defensive
            rep = _choose_representative(cl)
        rep.context_snippet = text[cl.snip_start : cl.snip_end].strip()
        final_items.append(rep)

    final_items.sort(key=lambda c: (c.start, c.end))
    return final_items


__all__ = ["deduplicate"]
