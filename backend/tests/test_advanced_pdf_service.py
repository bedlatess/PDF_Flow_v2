from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter

from app.services.advanced_pdf_service import AdvancedPDFService


def test_protect_pdf_adds_open_password(tmp_path: Path):
    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "protected.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with input_path.open("wb") as output_file:
        writer.write(output_file)

    service = AdvancedPDFService()
    service.protect_pdf(
        pdf_path=str(input_path),
        output_path=str(output_path),
        user_password="Secure123",
    )

    protected_reader = PdfReader(str(output_path))
    assert protected_reader.is_encrypted is True
    assert protected_reader.decrypt("wrong-password") == 0
    assert protected_reader.decrypt("Secure123") in (1, 2)
    assert len(protected_reader.pages) == 1
