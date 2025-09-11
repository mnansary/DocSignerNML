# document_ai_verification/ai/ocr/schemas.py

from typing import List
from pydantic import BaseModel, Field

class OCRDetail(BaseModel):
    """
    Represents a single word or phrase detected by the OCR, including
    its text, bounding polygon, and position.
    """
    poly: List[int] = Field(
        ...,
        description="A list of 8 integers for the four corner points [x1, y1, x2, y2, x3, y3, x4, y4] of the bounding polygon."
    )
    text: str = Field(
        ...,
        description="The transcribed text for that specific polygon."
    )
    line_num: int = Field(
        ...,
        description="The line number the text belongs to in the document."
    )
    word_num: int = Field(
        ...,
        description="The word number within that specific line."
    )

class OCRResponse(BaseModel):
    """
    Represents the full JSON response from the enOCR API.
    """
    status: str = Field(
        ...,
        description="The status of the OCR operation, e.g., 'success'."
    )
    plain_text: str = Field(
        ...,
        description="The full extracted text with newline characters preserving line breaks."
    )
    detailed_data: List[OCRDetail] = Field(
        ...,
        description="A list of objects, each containing detailed information about a transcribed word/phrase."
    )