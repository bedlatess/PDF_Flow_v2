"""PDF to Word MVP conversion helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from fastapi import HTTPException, status

from app.domains.files.pdf_text import TextPDFError, extract_text_pdf_pages


PDF_TO_WORD_MIN_TEXT_CHARS = 40
PDF_TO_WORD_MAX_PAGES = 80


class PDFToWordError(TextPDFError):
    """User-facing conversion error for PDF to Word Beta."""


def convert_text_pdf_to_docx(
    *,
    input_path: str,
    output_path: str,
    insert_page_breaks: bool = True,
) -> dict:
    """Extract readable text from a text-based PDF and write a simple DOCX."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        source, page_texts, total_chars = extract_text_pdf_pages(
            input_path=input_path,
            min_text_chars=PDF_TO_WORD_MIN_TEXT_CHARS,
            max_pages=PDF_TO_WORD_MAX_PAGES,
            product_label="PDF to Word Beta",
        )
    except TextPDFError as exc:
        raise PDFToWordError(str(exc)) from exc

    page_count = len(page_texts)

    document = Document()
    document.core_properties.title = source.stem
    document.add_heading(source.stem or "Converted PDF", level=1)

    paragraph_count = 0
    for page_index, text in enumerate(page_texts):
        if page_index > 0 and insert_page_breaks:
            document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

        if page_count > 1:
            document.add_paragraph(f"Page {page_index + 1}", style="Intense Quote")

        for block in _split_blocks(text):
            _append_block(document, block)
            paragraph_count += 1

    document.save(str(output))

    return {
        "success": True,
        "output_path": str(output),
        "file_size": os.path.getsize(output),
        "page_count": page_count,
        "paragraph_count": paragraph_count,
        "extracted_characters": total_chars,
    }


def validate_pdf_to_word_upload(file_id: str, filename: str | None) -> None:
    """Reject obviously non-PDF inputs before queueing."""

    if not file_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_id is required")

    if filename and not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF to Word Beta only accepts PDF files.",
        )


def user_facing_pdf_to_word_error(exc: Exception) -> str:
    """Return a short error message suitable for task status and history."""

    if isinstance(exc, PDFToWordError):
        return str(exc)
    message = str(exc).splitlines()[0].strip()
    return message[:240] if message else "PDF to Word conversion failed."


def _split_blocks(text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if blocks:
        return blocks
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def _append_block(document: Document, block: str) -> None:
    compact = " ".join(line.strip() for line in block.splitlines() if line.strip())
    if not compact:
        return

    if _looks_like_heading(compact):
        document.add_heading(compact, level=2)
        return

    document.add_paragraph(compact)


def _looks_like_heading(text: str) -> bool:
    if len(text) > 96 or text.endswith((".", ",", ";", ":")):
        return False
    if re.match(r"^(\d+(\.\d+)*|[IVXLC]+)\s+[\w(]", text):
        return True
    letters = [char for char in text if char.isalpha()]
    return bool(letters) and len(letters) >= 4 and sum(char.isupper() for char in letters) / len(letters) > 0.75
