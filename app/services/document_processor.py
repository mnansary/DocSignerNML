import fitz  # PyMuPDF
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Tuple


def generate_golden_master(
    pdf_path: Path,
) -> Tuple[Dict[int, str], Dict[int, Any]]:
    """
    Generates the "Golden Master" for a PDF document.

    This involves creating a hash for each page's image representation and
    extracting a map of all static text and its coordinates.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A tuple containing:
        - A dictionary mapping page numbers to their SHA-256 image hashes.
        - A dictionary mapping page numbers to their extracted text block data.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    page_hashes = {}
    text_map = {}

    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # 1. Generate high-resolution page image and compute hash
        # Using 300 DPI for high resolution, which is standard for printing
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes()
        sha256_hash = hashlib.sha256(img_bytes).hexdigest()
        page_hashes[page_num] = sha256_hash

        # 2. Extract static text and its coordinates
        # 'dict' format provides detailed information including bounding boxes
        page_text_data = page.get_text("dict")
        text_map[page_num] = page_text_data["blocks"]

    doc.close()

    return page_hashes, text_map
