from __future__ import annotations

from typing import Optional, Tuple


_HARD_PUNCT = {".", "!", "?"}
_SOFT_PUNCT = {";", ":"}
_ABBREVIATIONS = {
    # Common legal abbreviations in PT-BR that end with dot and should not split sentences
    "art.",
    "arts.",
    "inc.",
    "incs.",
    "al.",
    "n.",
    "nº",
    "no.",
    "vol.",
    "v.",
    "vs.",
}


def _is_decimal_point(text: str, i: int) -> bool:
    if i < 0 or i >= len(text) or text[i] != ".":
        return False
    prev_c = text[i - 1] if i - 1 >= 0 else ""
    next_c = text[i + 1] if i + 1 < len(text) else ""
    return prev_c.isdigit() and next_c.isdigit()


def _looks_like_abbreviation(text: str, i: int) -> bool:
    """Return True if a '.' at position i seems to close a known abbreviation."""
    if i < 0 or i >= len(text) or text[i] != ".":
        return False
    # Grab token ending at '.'
    j = i - 1
    while j >= 0 and not text[j].isspace():
        j -= 1
    token = text[j + 1 : i + 1].lower()
    return token in _ABBREVIATIONS


def _is_hard_break(text: str, i: int) -> bool:
    c = text[i]
    if c in _HARD_PUNCT:
        if c == "." and (
            _is_decimal_point(text, i) or _looks_like_abbreviation(text, i)
        ):
            return False
        return True
    # Paragraph break (double newline) – treat the second as a hard break
    if c == "\n" and i - 1 >= 0 and text[i - 1] == "\n":
        return True
    return False


def _is_soft_break(text: str, i: int) -> bool:
    c = text[i]
    if c in _SOFT_PUNCT:
        return True
    if c == "\n":  # single newline as soft break
        if not (i - 1 >= 0 and text[i - 1] == "\n"):
            return True
    return False


def find_left_boundary(
    text: str,
    anchor: int,
    *,
    min_chars: int = 120,
    max_backtrack: Optional[int] = 600,
) -> int:
    if not text:
        return 0
    n = len(text)
    anchor = max(0, min(anchor, n))
    target = max(0, anchor - max(0, min_chars))
    floor = max(0, anchor - max_backtrack) if max_backtrack else 0

    best_soft = None
    i = target
    while i >= floor:
        if _is_hard_break(text, i):
            return i + 1
        if best_soft is None and _is_soft_break(text, i):
            best_soft = i + 1
        i -= 1
    if best_soft is not None:
        return best_soft
    return floor


def find_right_boundary(
    text: str,
    anchor: int,
    *,
    min_chars: int = 120,
    max_ahead: Optional[int] = 600,
) -> int:
    if not text:
        return 0
    n = len(text)
    anchor = max(0, min(anchor, n))
    target = min(n, anchor + max(0, min_chars))
    ceil = min(n, anchor + max_ahead) if max_ahead else n

    best_soft = None
    i = target
    while i < ceil:
        if _is_hard_break(text, i):
            return i + 1
        if best_soft is None and _is_soft_break(text, i):
            best_soft = i + 1
        i += 1
    if best_soft is not None:
        return best_soft
    return ceil


def build_sentence_bounded_range(
    text: str,
    start: int,
    end: int,
    *,
    min_chars: int = 120,
    max_chars: Optional[int] = 600,
    lock_left: bool = False,
    lock_right: bool = False,
) -> Tuple[int, int]:
    if not text:
        return (0, 0)
    n = len(text)
    start = max(0, min(start, n))
    end = max(0, min(end, n))
    if start > end:
        start, end = end, start

    left = (
        start
        if lock_left
        else find_left_boundary(
            text, start, min_chars=min_chars, max_backtrack=max_chars
        )
    )
    right = (
        end
        if lock_right
        else find_right_boundary(text, end, min_chars=min_chars, max_ahead=max_chars)
    )
    left = min(left, start)
    right = max(right, end)
    return (left, right)


def choose_split_without_overlap(
    text: str,
    left_min: int,
    right_max: int,
    *,
    prefer_rightmost: bool = True,
) -> int:
    left_min = max(0, left_min)
    right_max = max(left_min, right_max)
    segment = text[left_min:right_max]
    best_hard = None
    best_soft = None
    for offset, _ in enumerate(segment):
        i = left_min + offset
        if _is_hard_break(text, i):
            best_hard = i + 1
        elif best_soft is None and _is_soft_break(text, i):
            best_soft = i + 1
    if best_hard is not None:
        return best_hard
    if best_soft is not None:
        return best_soft
    mid = (left_min + right_max) // 2
    j = mid
    while j > left_min:
        if text[j].isspace():
            return j
        j -= 1
    return right_max


__all__ = [
    "find_left_boundary",
    "find_right_boundary",
    "build_sentence_bounded_range",
    "choose_split_without_overlap",
]
