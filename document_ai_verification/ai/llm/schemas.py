# document_ai_verification/ai/llm/schemas.py

from typing import List, Literal
from pydantic import BaseModel, Field

# ===================================================================
# SECTION 1: Schemas for the Initial NSV Analysis
# ===================================================================


class RequiredInput(BaseModel):
    """
    Represents a single input field identified in the non-signed document that requires user input.
    """
    input_type: str = Field(..., description="The type of input required (e.g., 'signature', 'date', 'full_name').")
    marker_text: str = Field(..., description="The unique text label that identifies the input field.")
    description: str = Field(..., description="A brief, human-readable explanation of what is required.")

class PrefilledInput(BaseModel):
    """
    Represents a single prefilled field identified in the non-signed document.
    """
    input_type: str = Field(..., description="The type of input (e.g., 'signature', 'date', 'full_name').")
    marker_text: str = Field(..., description="The unique text label that identifies the field.")
    value: str = Field(..., description="The filled value, or 'SIGNED' for signatures, 'CHECKED' for checkboxes, etc.")

class PageHolisticAnalysis(BaseModel):
    """
    The holistic analysis of a single NSV page, listing required inputs, prefilled fields, and a summary.
    This is the target schema for the 'get_ns_document_analysis_prompt_holistic'.
    """
    required_inputs: List[RequiredInput] = Field(default_factory=list)
    prefilled_inputs: List[PrefilledInput] = Field(default_factory=list)
    summary: str = Field(..., description="A short summary of the prefilled and required fields, e.g., 'No fields are filled' or 'One party filled name, date, and signature; other party fields are blank.'")



# ===================================================================
# SECTION 2: Schemas for the Final Multi-Modal Audit
# ===================================================================
# These models define the structure for the most complex LLM call, the final page audit.

# Define literal types for status fields to enforce consistency in the LLM's output.
PageStatus = Literal["Verified", "Input Missing", "Content Mismatch", "Input Missing and Content Mismatch"]

class AuditedInput(BaseModel):
    """
    Represents the audit result for a single required input field.
    """
    input_type: str = Field(..., description="The type of input that was required.")
    marker_text: str = Field(..., description="The text label identifying the input field.")
    is_fulfilled: bool = Field(..., description="True if the input was fulfilled, False if missing.")
    audit_notes: str = Field(..., description="The AI's notes supporting its fulfillment decision.")

class AuditedContentDifference(BaseModel):
    """
    Represents a detected unauthorized change in the static content.
    """
    nsv_text: str = Field(..., description="The original text snippet from the NSV.")
    sv_text: str = Field(..., description="The corresponding altered text snippet from the SV.")
    description: str = Field(..., description="A concise explanation of the unauthorized change.")

class PageAuditResult(BaseModel):
    """
    The complete audit results for a single document page.
    This is the target schema for the 'get_multimodal_audit_prompt'.
    """
    page_number: int = Field(..., description="The page number being audited (1-indexed).")
    page_status: PageStatus = Field(..., description="The overall status of the page based on the audit.")
    required_inputs: List[AuditedInput] = Field(default_factory=list)
    content_differences: List[AuditedContentDifference] = Field(default_factory=list)