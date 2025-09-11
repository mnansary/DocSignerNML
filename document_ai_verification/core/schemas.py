# document_ai_verification/core/schemas.py

from typing import List, Literal
from pydantic import BaseModel, Field

# Import the definitive PageAuditResult model from the LLM schemas.
# This avoids duplication and ensures consistency between the AI's output
# and the final API report.
from ..ai.llm.schemas import PageAuditResult

# --- Top-Level API Report Schemas ---

# Define the overall status type for the final report.
OverallStatus = Literal["Success", "Failure"]

class VerificationReport(BaseModel):
    """
    The top-level object representing the complete verification report.
    This is the final JSON object that the API will return to the frontend.
    """
    overall_status: OverallStatus = Field(
        ..., 
        description="The final, overall status of the entire document verification."
    )
    nsv_filename: str = Field(
        ..., 
        description="The filename of the non-signed version."
    )
    sv_filename: str = Field(
        ..., 
        description="The filename of the signed version."
    )
    page_count: int = Field(
        ..., 
        description="The total number of pages in the document."
    )
    # The list of page results now directly uses the validated PageAuditResult schema.
    page_results: List[PageAuditResult] = Field(
        ..., 
        description="A list containing the detailed audit results for each page."
    )