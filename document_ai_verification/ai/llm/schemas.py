# document_ai_verification/ai/llm/schemas.py

from typing import List, Literal
from pydantic import BaseModel, Field

# ===================================================================
# SECTION 1: Schemas for the Initial NSV Analysis
# ===================================================================

class RequiredInput(BaseModel):
    """
    Represents a single input field identified in the non-signed document.
    """
    input_type: str = Field(..., description="The type of input required (e.g., 'signature', 'date', 'full_name').")
    marker_text: str = Field(..., description="The unique text label that identifies the input field.")
    description: str = Field(..., description="A brief, human-readable explanation of what is required.")

class PageInputAnalysis(BaseModel):
    """
    The complete analysis of a single NSV page, listing all required inputs.
    This is the target schema for the 'get_ns_document_analysis_prompt'.
    """
    required_inputs: List[RequiredInput] = Field(default_factory=list)

# ===================================================================
# SECTION 2: Schema for VLLM-based OCR
# ===================================================================

class VllmOcrResult(BaseModel):
    """
    Represents the structured Markdown content extracted from a scanned image.
    This is the target schema for the 'get_vllm_ocr_prompt'.
    """
    markdown_content: str = Field(..., description="The full text content of the image, formatted as clean Markdown.")

# ===================================================================
# SECTION 3: Schemas for the Final Multi-Modal Audit
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