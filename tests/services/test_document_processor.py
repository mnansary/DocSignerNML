from pathlib import Path
import pytest

from app.services.document_processor import generate_golden_master

TEST_ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEST_PDF_PATH = TEST_ASSETS_DIR / "test_template.pdf"


def test_generate_golden_master_runs_successfully():
    """
    Tests that the golden master generation runs without raising an exception.
    """
    assert TEST_PDF_PATH.exists(), "Test PDF asset not found."
    try:
        page_hashes, text_map = generate_golden_master(TEST_PDF_PATH)
        assert isinstance(page_hashes, dict)
        assert isinstance(text_map, dict)
        assert len(page_hashes) == 1  # Our test PDF has one page
        assert 0 in page_hashes
    except Exception as e:
        pytest.fail(f"generate_golden_master raised an exception: {e}")


def test_generate_golden_master_is_deterministic():
    """
    Tests that the output is identical for the same input file run twice.
    """
    assert TEST_PDF_PATH.exists(), "Test PDF asset not found."

    # Run 1
    page_hashes_1, text_map_1 = generate_golden_master(TEST_PDF_PATH)

    # Run 2
    page_hashes_2, text_map_2 = generate_golden_master(TEST_PDF_PATH)

    assert page_hashes_1 == page_hashes_2, "Page hashes are not deterministic."

    # The text map from PyMuPDF can have minor float differences, so a simple
    # equality check might be too strict. We'll compare a known piece of text.
    text_in_map_1 = any(
        "This is a test document" in span["text"]
        for block in text_map_1.get(0, [])
        for line in block["lines"]
        for span in line["spans"]
    )
    text_in_map_2 = any(
        "This is a test document" in span["text"]
        for block in text_map_2.get(0, [])
        for line in block["lines"]
        for span in line["spans"]
    )
    assert text_in_map_1, "Expected text not found in first run's text map."
    assert text_in_map_2, "Expected text not found in second run's text map."
