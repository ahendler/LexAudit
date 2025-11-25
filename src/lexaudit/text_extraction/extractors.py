"""
Extractors for different file formats.
"""

import logging
from pathlib import Path
from typing import Union

import pypdf
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_txt(file_path: Path) -> str:
    """Extract text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 if utf-8 fails
        logger.warning("UTF-8 decode failed for %s, trying latin-1", file_path)
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    text = []
    try:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        logger.error("Failed to extract text from PDF %s: %s", file_path, e)
        raise


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error("Failed to extract text from DOCX %s: %s", file_path, e)
        raise


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Extracted text content

    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(path)
    elif suffix == ".pdf":
        return extract_text_from_pdf(path)
    elif suffix == ".docx":
        return extract_text_from_docx(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
