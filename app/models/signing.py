from typing import Dict, Any
from pydantic import BaseModel


class SigningSubmission(BaseModel):
    """
    Represents the data submitted by a signer.
    The keys are the field IDs defined in the document's field_layout,
    and the values are the signer's inputs.
    """
    submission_data: Dict[str, Any]
