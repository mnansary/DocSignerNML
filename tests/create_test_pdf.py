from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path


def generate_test_pdf():
    """
    Generates a simple, one-page PDF for testing purposes.
    """
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    pdf_path = assets_dir / "test_template.pdf"

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter

    # Add some static text
    c.drawString(72, height - 72, "This is a test document for the signing platform.")
    c.drawString(72, height - 96, "It contains static text that must not change.")

    # This text will be inside a "field" in some tests
    c.drawString(100, 500, "Signer Name:")

    c.save()
    print(f"Test PDF created at {pdf_path}")


if __name__ == "__main__":
    generate_test_pdf()
