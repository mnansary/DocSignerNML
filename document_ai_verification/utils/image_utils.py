# document_ai_verification/utils/image_utils.py

import cv2
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def find_difference_bboxes_direct(img1: np.ndarray, img2: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Finds the bounding boxes of differences between two images.
    """
    if img1 is None or img2 is None:
        return []
    
    # Convert to grayscale for more reliable difference detection
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Add a small padding for better visibility
        padding = 5
        bounding_boxes.append((x-padding, y-padding, x + w + padding, y + h + padding))
    return bounding_boxes

def generate_difference_images(
    original_img: np.ndarray,
    signed_img: np.ndarray,
    bboxes: List[Tuple[int, int, int, int]],
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    Generates two images with colored bounding boxes indicating differences.
    - Original image gets GREEN boxes.
    - Signed image gets RED boxes.

    Args:
        original_img: The original page image.
        signed_img: The signed page image.
        bboxes: A list of bounding box tuples (x1, y1, x2, y2).
        output_dir: The directory to save the new images in.

    Returns:
        A tuple containing the paths to the (original_diff_image, signed_diff_image).
    """
    output_dir.mkdir(exist_ok=True) # Ensure the output directory exists
    
    # --- Define colors (BGR format) ---
    green = (0, 255, 0)
    red = (0, 0, 255)
    thickness = 2

    # --- Process Original Image (Green Boxes) ---
    original_with_boxes = original_img.copy()
    for (x1, y1, x2, y2) in bboxes:
        cv2.rectangle(original_with_boxes, (x1, y1), (x2, y2), green, thickness)
    original_output_path = output_dir / "diff_original.png"
    cv2.imwrite(str(original_output_path), original_with_boxes)
    logger.info(f"Saved original difference image to {original_output_path}")

    # --- Process Signed Image (Red Boxes) ---
    signed_with_boxes = signed_img.copy()
    for (x1, y1, x2, y2) in bboxes:
        cv2.rectangle(signed_with_boxes, (x1, y1), (x2, y2), red, thickness)
    signed_output_path = output_dir / "diff_signed.png"
    cv2.imwrite(str(signed_output_path), signed_with_boxes)
    logger.info(f"Saved signed difference image to {signed_output_path}")
    
    return (original_output_path, signed_output_path)


def analyze_page_meta_from_image(nsv_img: np.ndarray, sv_img: np.ndarray) -> Dict:
    """
    Analyzes and updates page metadata based on image comparison.
    Returns a dictionary with the analysis results.
    """
    analysis = {}
    if nsv_img is None or sv_img is None:
        analysis["source_match"] = False
        analysis["content_match"] = False
        analysis["difference_bboxes"] = []
        return analysis
    
    # Ensure images have the same dimensions for accurate comparison
    resized_sv_img = sv_img
    if nsv_img.shape != sv_img.shape:
        h, w, _ = nsv_img.shape
        resized_sv_img = cv2.resize(sv_img, (w, h))
        analysis["source_match"] = False
    else:
        analysis["source_match"] = True
    
    difference = cv2.subtract(nsv_img, resized_sv_img)
    b, g, r = cv2.split(difference)
    
    if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
        analysis["content_match"] = True
        analysis["difference_bboxes"] = []
    else:
        analysis["content_match"] = False
        analysis["difference_bboxes"] = find_difference_bboxes_direct(nsv_img, resized_sv_img)
        
    return analysis