from __future__ import annotations

import logging
import subprocess
from html.parser import HTMLParser
from time import perf_counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

from lexaudit.config.settings import SETTINGS
from lexaudit.core.models import CitationSuspect, IdentifiedCitation

logger = logging.getLogger(__name__)


class LinkerExecutionError(RuntimeError):
    """Error executing the Linker external command."""


class LinkerParsingError(RuntimeError):
    """Error parsing the decorated HTML returned by the Linker."""


def _build_linker_args(
    *,
    command: Optional[Sequence[str]] = None,
    output_format: str = "html",
    context: str = SETTINGS.linker_context,
    extra_args: Optional[Sequence[str]] = None,
) -> List[str]:
    flag = {"html": "--html", "xml": "--xml"}.get(output_format.lower())
    if flag is None:
        raise ValueError(f"Unsupported linker output format: {output_format}")
    args = list(command) if command is not None else list(SETTINGS.linker_cmd)
    args = args + ["--text", flag, f"--contexto={context}"]
    if extra_args:
        args.extend(extra_args)
    return args


def _run_linker(
    text: str,
    *,
    command: Optional[Sequence[str]] = None,
    output_format: str = "html",
    context: str = SETTINGS.linker_context,
    timeout: Optional[float] = SETTINGS.linker_timeout,
) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    args = _build_linker_args(
        command=command,
        output_format=output_format,
        context=context,
    )
    logger.info("Executando Linker: %s", " ".join(args[:3] + ["..."]))
    try:
        t0 = perf_counter()
        completed = subprocess.run(
            args,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        dt = perf_counter() - t0
    except FileNotFoundError as exc:
        raise LinkerExecutionError(f"Linker command not found: {args[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise LinkerExecutionError("Linker command timed out") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")
        raise LinkerExecutionError(
            f"Linker exited with code {completed.returncode}: {stderr.strip()}"
        )
    logger.info(
        "Linker concluído em %.3fs (exit=%s, bytes=%d)",
        dt,
        completed.returncode,
        len(completed.stdout),
    )
    return completed.stdout.decode("utf-8")


def _has_linker_class(attrs: Dict[str, str]) -> bool:
    classes = attrs.get("class", "")
    return any(token == "lexmlurnlink" for token in classes.split())


class _LinkerHTMLParser(HTMLParser):
    """Parser to map anchors from the Linker back to the original text."""

    def __init__(self, original_text: str):
        super().__init__(convert_charrefs=True)
        self._original = original_text
        self._cursor = 0
        self._anchor_stack: List[Dict[str, Any]] = []
        self.references: List[Tuple[int, int]] = []

    def handle_starttag(self, tag: str, attrs_list):
        if tag.lower() != "a":
            return
        attrs = dict(attrs_list)
        if not _has_linker_class(attrs):
            return
        self._anchor_stack.append({"attrs": attrs, "segments": []})

    def handle_data(self, data: str):
        if not data:
            return
        start = self._align_to_original(data)
        end = start + len(data)
        if self._anchor_stack:
            self._anchor_stack[-1]["segments"].append((start, end))

    def handle_endtag(self, tag: str):
        if tag.lower() != "a" or not self._anchor_stack:
            return
        anchor = self._anchor_stack.pop()
        segments = anchor["segments"]
        if not segments:
            return
        start = segments[0][0]
        end = segments[-1][1]
        self.references.append((start, end))

    def close(self):
        super().close()
        if self._cursor > len(self._original):
            raise LinkerParsingError(
                "Decorated output diverges from original text; cannot map spans."
            )
        # We don't require _cursor == len(original); the Linker may not wrap the final
        if self._anchor_stack:
            raise LinkerParsingError("Unbalanced <a> tags in Linker output")

    def _align_to_original(self, data: str) -> int:
        # Trivial case: the next chunk is exactly at the cursor
        if self._original.startswith(data, self._cursor):
            start = self._cursor
        else:
            # Search forward from the cursor
            idx = self._original.find(data, self._cursor)
            if idx == -1:
                raise LinkerParsingError(
                    "Could not align decorated segment with original text"
                )
            start = idx
        self._cursor = start + len(data)
        return start


def run_linker(
    text: str,
    *,
    command: Optional[Sequence[str]] = None,
    context: str = SETTINGS.linker_context,
    output_format: str = "html",
    timeout: Optional[float] = SETTINGS.linker_timeout,
) -> List[CitationSuspect]:
    """
    Executes the official Linker (via CLI) over 'text' and returns citations with spans.
    - Uses <a class="lexmlurnlink"> from the generated HTML to recover offsets.
    - Returns Pydantic Citation objects with detector="linker".
    """
    decorated = _run_linker(
        text,
        command=command,
        output_format=output_format,
        context=context,
        timeout=timeout,
    )
    parser = _LinkerHTMLParser(text)
    parser.feed(decorated)
    parser.close()
    citations: List[CitationSuspect] = []
    for start, end in parser.references:
        snippet = ""
        suspect_text = text[start:end]
        citations.append(
            CitationSuspect(
                suspect_string=suspect_text,
                context_snippet=snippet,
                start=start,
                end=end,
                detector_type="linker",
                identified_citations=[  # List of identified citations that match this suspect
                    IdentifiedCitation(
                        identified_string=suspect_text,
                        formatted_name=suspect_text,
                        citation_type="unknown",
                        confidence=1.0,
                        justification="linker",
                    )
                ],
            )
        )
    return citations


__all__ = ["run_linker", "LinkerExecutionError", "LinkerParsingError"]
