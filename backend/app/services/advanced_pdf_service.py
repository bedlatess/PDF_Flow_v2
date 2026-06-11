"""
Advanced PDF features: Digital signatures, watermarks, form filling, annotations
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import io
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import (
        ArrayObject,
        BooleanObject,
        DictionaryObject,
        FloatObject,
        NameObject,
        NumberObject,
        TextStringObject,
    )
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import Color
    from reportlab.lib.utils import ImageReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class AdvancedPDFService:
    """Service for advanced PDF operations"""

    def __init__(self):
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 and reportlab not installed")

    # ============================================================================
    # Watermark
    # ============================================================================

    def add_watermark(
        self,
        pdf_path: str,
        output_path: str,
        watermark_text: str,
        opacity: float = 0.3,
        rotation: int = 45,
        font_size: int = 40,
        color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
        position: str = 'center'
    ) -> str:
        """
        Add text watermark to PDF

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            watermark_text: Text to use as watermark
            opacity: Watermark opacity (0.0-1.0)
            rotation: Rotation angle in degrees
            font_size: Font size
            color: RGB color tuple (0.0-1.0 for each)
            position: Position ('center', 'diagonal', 'top', 'bottom')

        Returns:
            Path to output PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Create watermark
        watermark_pdf = self._create_watermark(
            watermark_text,
            opacity,
            rotation,
            font_size,
            color,
            position,
            reader.pages[0].mediabox.width,
            reader.pages[0].mediabox.height
        )

        # Apply watermark to each page
        watermark_reader = PdfReader(watermark_pdf)
        watermark_page = watermark_reader.pages[0]

        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)

        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    def _create_watermark(
        self,
        text: str,
        opacity: float,
        rotation: int,
        font_size: int,
        color: Tuple[float, float, float],
        position: str,
        page_width: float,
        page_height: float
    ) -> io.BytesIO:
        """Create watermark PDF overlay"""
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # Set transparency
        c.setFillColorRGB(color[0], color[1], color[2], alpha=opacity)
        c.setFont("Helvetica-Bold", font_size)

        # Calculate position
        if position == 'center':
            x = page_width / 2
            y = page_height / 2
        elif position == 'diagonal':
            x = page_width / 2
            y = page_height / 2
        elif position == 'top':
            x = page_width / 2
            y = page_height - 50
            rotation = 0
        elif position == 'bottom':
            x = page_width / 2
            y = 50
            rotation = 0
        else:
            x = page_width / 2
            y = page_height / 2

        # Draw text
        c.saveState()
        c.translate(x, y)
        c.rotate(rotation)
        text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
        c.drawString(-text_width / 2, 0, text)
        c.restoreState()

        c.save()
        packet.seek(0)
        return packet

    # ============================================================================
    # Form Filling
    # ============================================================================

    def fill_form(
        self,
        pdf_path: str,
        output_path: str,
        field_data: Dict[str, str]
    ) -> str:
        """
        Fill PDF form fields

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            field_data: Dictionary of field names and values

        Returns:
            Path to output PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Check if PDF has form fields
        if "/AcroForm" not in reader.trailer["/Root"]:
            raise ValueError("PDF does not contain form fields")

        writer.append(reader)
        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
            writer._root_object["/AcroForm"].update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_data)

        # Write output
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    def get_form_fields(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract form field names and types from PDF

        Args:
            pdf_path: PDF file path

        Returns:
            Dictionary of field names and their properties
        """
        reader = PdfReader(pdf_path)

        if "/AcroForm" not in reader.trailer["/Root"]:
            return {}

        fields = {}

        try:
            form = reader.trailer["/Root"]["/AcroForm"]
            if "/Fields" in form:
                for field in form["/Fields"]:
                    field_obj = field.get_object()
                    if "/T" in field_obj:
                        field_name = field_obj["/T"]
                        field_type = field_obj.get("/FT", "Unknown")
                        field_value = field_obj.get("/V", "")

                        fields[str(field_name)] = {
                            "name": str(field_name),
                            "type": self._normalize_form_field_type(str(field_type)),
                            "default_value": str(field_value) if field_value else "",
                            "required": False,
                            "options": [],
                        }
        except Exception as e:
            print(f"Error extracting form fields: {e}")

        return fields

    def _normalize_form_field_type(self, raw_type: str) -> str:
        """Map PDF field names to frontend field types."""
        field_type = raw_type.replace("/", "").lower()
        if field_type in {"btn", "checkbox"}:
            return "checkbox"
        if field_type in {"ch", "choice"}:
            return "dropdown"
        return "text"

    # ============================================================================
    # Annotations
    # ============================================================================

    def add_text_annotation(
        self,
        pdf_path: str,
        output_path: str,
        page_number: int,
        text: str,
        x: float,
        y: float,
        width: float = 200,
        height: float = 100
    ) -> str:
        """
        Add text annotation to PDF page

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            page_number: Page number (0-indexed)
            text: Annotation text
            x, y: Position on page
            width, height: Annotation box size

        Returns:
            Path to output PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i == page_number:
                # Add annotation
                annotation = DictionaryObject({
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/FreeText"),
                    NameObject("/Contents"): TextStringObject(text),
                    NameObject("/Rect"): ArrayObject([
                        FloatObject(x),
                        FloatObject(y),
                        FloatObject(x + width),
                        FloatObject(y + height),
                    ]),
                    NameObject("/C"): ArrayObject([FloatObject(1), FloatObject(1), FloatObject(0)]),
                    NameObject("/DA"): TextStringObject("/Helv 12 Tf 0 0 0 rg"),
                    NameObject("/F"): NumberObject(4),
                })

                self._append_annotation(page, annotation)

            writer.add_page(page)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    def add_highlight(
        self,
        pdf_path: str,
        output_path: str,
        page_number: int,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Tuple[float, float, float] = (1, 1, 0)  # Yellow
    ) -> str:
        """
        Add highlight annotation to PDF

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            page_number: Page number (0-indexed)
            x, y: Position
            width, height: Highlight box size
            color: RGB color (0-1)

        Returns:
            Path to output PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i == page_number:
                # Add highlight annotation
                annotation = DictionaryObject({
                    NameObject("/Type"): NameObject("/Annot"),
                    NameObject("/Subtype"): NameObject("/Highlight"),
                    NameObject("/Rect"): ArrayObject([
                        FloatObject(x),
                        FloatObject(y),
                        FloatObject(x + width),
                        FloatObject(y + height),
                    ]),
                    NameObject("/C"): ArrayObject([FloatObject(value) for value in color]),
                    NameObject("/QuadPoints"): ArrayObject([
                        FloatObject(x),
                        FloatObject(y + height),
                        FloatObject(x + width),
                        FloatObject(y + height),
                        FloatObject(x),
                        FloatObject(y),
                        FloatObject(x + width),
                        FloatObject(y),
                    ]),
                    NameObject("/F"): NumberObject(4),
                })

                self._append_annotation(page, annotation)

            writer.add_page(page)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    # ============================================================================
    # Digital Signature (Placeholder)
    # ============================================================================

    def add_signature_field(
        self,
        pdf_path: str,
        output_path: str,
        page_number: int,
        x: float,
        y: float,
        width: float = 200,
        height: float = 50,
        field_name: str = "Signature"
    ) -> str:
        """
        Add signature field to PDF

        Note: This adds a visual signature field.
        Actual digital signatures require cryptographic libraries.

        Args:
            pdf_path: Input PDF path
            output_path: Output PDF path
            page_number: Page number (0-indexed)
            x, y: Position
            width, height: Field size
            field_name: Signature field name

        Returns:
            Path to output PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i == page_number:
                # Add signature field (visual placeholder)
                # Note: Real digital signatures need endesive or pyHanko
                annotation = {
                    "/Type": "/Annot",
                    "/Subtype": "/Widget",
                    "/FT": "/Sig",
                    "/T": field_name,
                    "/Rect": [x, y, x + width, y + height],
                    "/F": 4,  # Print flag
                }

                if "/Annots" in page:
                    page["/Annots"].append(annotation)
                else:
                    page["/Annots"] = [annotation]

            writer.add_page(page)

        with open(output_path, 'wb') as output_file:
            writer.write(output_file)

        return output_path

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_page_dimensions(self, pdf_path: str, page_number: int = 0) -> Dict[str, float]:
        """Get page dimensions"""
        reader = PdfReader(pdf_path)
        page = reader.pages[page_number]

        return {
            'width': float(page.mediabox.width),
            'height': float(page.mediabox.height)
        }

    def _append_annotation(self, page: Any, annotation: DictionaryObject) -> None:
        """Append an annotation using valid PDF object containers."""
        if "/Annots" in page:
            annotations = page["/Annots"]
            try:
                annotations = annotations.get_object()
            except AttributeError:
                pass
            annotations.append(annotation)
        else:
            page[NameObject("/Annots")] = ArrayObject([annotation])


# Singleton instance
_advanced_pdf_service: Optional[AdvancedPDFService] = None


def get_advanced_pdf_service() -> AdvancedPDFService:
    """Get or create advanced PDF service singleton"""
    global _advanced_pdf_service
    if _advanced_pdf_service is None:
        _advanced_pdf_service = AdvancedPDFService()
    return _advanced_pdf_service
