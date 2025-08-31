import numpy as np
import cv2
import pytest

from app.services.verification_engine import _is_change_within_allowed_fields


@pytest.fixture
def base_image():
    """Creates a simple blank white image."""
    return np.full((500, 500, 3), 255, dtype=np.uint8)


def test_change_inside_allowed_field(base_image):
    """
    Tests that a change inside an allowed field is correctly identified as valid.
    """
    # Allowed field is a box from (100, 100) to (200, 200)
    allowed_boxes = [(100, 100, 200, 200)]

    original_img = base_image.copy()
    modified_img = base_image.copy()

    # Create a change (a black square) inside the allowed box
    cv2.rectangle(modified_img, (120, 120), (180, 180), (0, 0, 0), -1)

    diff = cv2.absdiff(original_img, modified_img)

    assert _is_change_within_allowed_fields(diff, allowed_boxes) is True


def test_change_outside_allowed_field(base_image):
    """
    Tests that a change outside any allowed field is correctly identified as invalid.
    """
    # Allowed field is a box from (100, 100) to (200, 200)
    allowed_boxes = [(100, 100, 200, 200)]

    original_img = base_image.copy()
    modified_img = base_image.copy()

    # Create a change (a black square) outside the allowed box
    cv2.rectangle(modified_img, (300, 300), (350, 350), (0, 0, 0), -1)

    diff = cv2.absdiff(original_img, modified_img)

    assert _is_change_within_allowed_fields(diff, allowed_boxes) is False


def test_no_change_passes(base_image):
    """
    Tests that if there is no difference, the check passes.
    """
    allowed_boxes = [(100, 100, 200, 200)]
    diff = cv2.absdiff(base_image, base_image)
    assert _is_change_within_allowed_fields(diff, allowed_boxes) is True
