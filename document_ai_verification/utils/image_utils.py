import cv2
import numpy as np
from typing import Dict, List, Tuple

def find_difference_bboxes_direct(img1: np.ndarray, img2: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Finds the bounding boxes of differences between two images.
    """
    if img1 is None or img2 is None:
        return []
    
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, x + w, y + h))
    return bounding_boxes

def analyze_page_meta_from_image(nsv_img: str, sv_img: str, page_meta: Dict) -> Dict:
    """
    Analyzes and updates page metadata based on image comparison.
    """

    if nsv_img is None or sv_img is None:
        page_meta["source"] = "error"
        page_meta["content"] = "not_matching"
        page_meta["difference"] = []
        return page_meta
    
    hs, ws, _ = nsv_img.shape
    sv_img_resized = cv2.resize(sv_img, (ws, hs))
    
    if nsv_img.shape == sv_img.shape:
        page_meta["source"] = "matching"
    else:
        page_meta["source"] = "not_matching"
    
    difference = cv2.subtract(nsv_img, sv_img_resized)
    b, g, r = cv2.split(difference)
    
    if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
        page_meta["content"] = "matching"
        page_meta["difference"] = []
    else:
        page_meta["content"] = "not_matching"
        page_meta["difference"] = find_difference_bboxes_direct(nsv_img, sv_img_resized)
        
    return page_meta