from pydantic import BaseModel
from typing import Optional

# Base properties shared across all Field schemas
class FieldBase(BaseModel):
    page_number: int
    type: str  # e.g., "signature", "date", "text"
    x_coord: float
    y_coord: float
    width: float
    height: float

# Properties to receive on item creation
class FieldCreate(FieldBase):
    # We use assigneeEmail during setup for easy mapping
    assignee_email: str

# Properties received when a signer submits their data
class FieldUpdate(BaseModel):
    id: int
    value: str # For signatures, this will be a Base64 encoded image string

# Properties to return to a client (includes DB-generated fields)
class Field(FieldBase):
    id: int
    recipient_id: int
    value: Optional[str] = None

    class Config:
        # This allows Pydantic to read data from ORM models
        from_attributes = True

# Add this class to the end of the existing file
class FieldSubmission(BaseModel):
    id: int
    value: str # For signatures, this is a Base64 encoded PNG. For text, it's the string.