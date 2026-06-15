"""Shared text extraction helpers for PDF conversion tools."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader


class TextPDFError(ValueError):
    """User-facing error for text-based PDF extraction."""


def extract_text_pdf_pages(
    *,
    input_path: str,
    min_text_chars: int,
    max_pages: int,
    product_label: str,
) -> tuple[Path, list[str], int]:
    """Extract normalized page text and reject scan-like PDFs."""

    source = Path(input_path)
    try:
        reader = PdfReader(str(source))
    except Exception as exc:
        raise TextPDFError(f"This PDF could not be opened. Try a readable text-based PDF.") from exc

    if reader.is_encrypted:
        raise TextPDFError(f"Encrypted PDFs are not supported in {product_label}.")

    page_count = len(reader.pages)
    if page_count == 0:
        raise TextPDFError("This PDF has no pages to convert.")
    if page_count > max_pages:
        raise TextPDFError(f"{product_label} supports up to {max_pages} pages.")

    page_texts: list[str] = []
    total_chars = 0
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        normalized = normalize_page_text(text)
        page_texts.append(normalized)
        total_chars += len(normalized.strip())

    if total_chars < min_text_chars:
        raise TextPDFError(
            "This looks like a scanned or image-based PDF. Use OCR PDF first, then convert the recognized text."
        )

    return source, page_texts, total_chars


def normalize_page_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
