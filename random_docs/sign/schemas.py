# document_ai_verification/ai/sign/schemas.py

from typing import List
from pydantic import BaseModel, Field

class SignatureDetection(BaseModel):
    """
    Represents a single detected signature with its bounding box
    and the model's confidence in the detection.
    """
    box: List[float] = Field(
        ...,
        description="A list of 4 floats representing the bounding box in [x1, y1, x2, y2] format."
    )
    confidence: float = Field(
        ...,
        description="The model's confidence score for the detection, from 0.0 to 1.0."
    )

class SignatureDetectionResponse(BaseModel):
    """
    Represents the full JSON response from the Signature Detection API.
    """
    request_id: str = Field(
        ...,
        description="A unique identifier for this specific request."
    )
    detection_count: int = Field(
        ...,
        description="The total number of signatures found."
    )
    detections: List[SignatureDetection] = Field(
        ...,
        description="A list of detection objects."
    )