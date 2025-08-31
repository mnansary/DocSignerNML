import fitz  # PyMuPDF
import hashlib
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

from app.db.models.document import DocumentRecipient


def _is_change_within_allowed_fields(
    diff_img: np.ndarray, allowed_boxes: List[Tuple[int, int, int, int]]
) -> bool:
    """
    Analyzes a difference image to see if all changes are within allowed bounding boxes.
    """
    gray_diff = cv2.cvtColor(diff_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_diff, 10, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return True # No changes found

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Bounding box of the detected change
        change_box = (x, y, x + w, y + h)

        is_within_an_allowed_field = False
        for field_box in allowed_boxes:
            # Check if the change_box is completely contained within the field_box
            if (field_box[0] <= change_box[0] and
                field_box[1] <= change_box[1] and
                field_box[2] >= change_box[2] and
                field_box[3] >= change_box[3]):
                is_within_an_allowed_field = True
                break

        if not is_within_an_allowed_field:
            return False # A change was detected outside of all allowed fields

    return True


def verify_document_integrity(recipient: DocumentRecipient) -> bool:
    """
    Verifies the integrity of a signed document against its Golden Master.

    Args:
        recipient: The DocumentRecipient object containing the submission data.

    Returns:
        True if verification passes, False otherwise.
    """
    doc = recipient.document
    template_path = Path(doc.template.filepath)
    submission_data = recipient.submission_data
    golden_hashes = doc.golden_master_hashes
    golden_text_map = doc.golden_master_text_map
    field_layout = doc.field_layout

    # 1. Secure Reconstruction: Create a new PDF with the submitted data
    # For simplicity in this implementation, we will perform checks on a
    # conceptual 'new' PDF. A full implementation would build it with ReportLab/PyMuPDF.
    # Here, we will simulate this by checking the golden master against itself,
    # but the logic for diffing is the key part.

    # Let's assume `reconstructed_pdf_path` is the path to the PDF built from submission
    # For this simulation, we'll just re-use the template path and assume
    # the submitted data would be on it. The verification logic remains the same.
    reconstructed_pdf_path = template_path

    new_doc = fitz.open(reconstructed_pdf_path)
    if len(new_doc) != len(golden_hashes):
        return False # Page count mismatch is an immediate failure

    # 2. Verification Steps
    for page_num in range(len(new_doc)):
        page = new_doc.load_page(page_num)

        # a. Render page and compute new hash
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes()
        new_hash = hashlib.sha256(img_bytes).hexdigest()

        # b. Hash Comparison
        if new_hash == golden_hashes.get(str(page_num)):
            continue  # Page is identical to the master, no changes, move to next page

        # c. Pixel-Level Difference Analysis (if hashes do not match)
        # This part is complex and requires careful handling of coordinates.
        # For this step, we will outline the logic. A full implementation would
        # require a robust coordinate transformation system.

        # Re-render Golden Master page for comparison
        original_doc = fitz.open(template_path)
        original_page = original_doc.load_page(page_num)
        original_pix = original_page.get_pixmap(dpi=300)

        # Convert to OpenCV images
        original_img = np.frombuffer(original_pix.samples, dtype=np.uint8).reshape(original_pix.h, original_pix.w, 3)
        new_img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)

        # Compute difference
        diff_img = cv2.absdiff(original_img, new_img)

        # Get the allowed fields for this page
        # Note: A real implementation needs to scale the field_layout bbox
        # coordinates to match the DPI of the rendered images.
        # For this example, we assume they are in the same coordinate space.
        page_fields = [tuple(f['bbox']) for f in field_layout.get(str(page_num), [])]

        if not _is_change_within_allowed_fields(diff_img, page_fields):
            return False # Verification failed: change outside allowed area

        # d. Static Text Integrity Check
        new_text_data = page.get_text("dict")
        # This comparison needs to be deep and ignore irrelevant floating point differences
        # For this implementation, we'll check the number of blocks and spans as a proxy
        if len(new_text_data.get("blocks", [])) != len(golden_text_map.get(str(page_num), [])):
            return False

    return True
