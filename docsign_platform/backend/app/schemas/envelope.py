from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .recipient import Recipient, RecipientCreate
from .field import Field, FieldCreate

# Base properties for an envelope
class EnvelopeBase(BaseModel):
    pass

# Schema for the initial response after a document is uploaded
class EnvelopeCreateResponse(BaseModel):
    id: str

# Schema for the template setup request
# This is what the frontend sends after placing fields
class EnvelopeSetup(BaseModel):
    recipients: List[RecipientCreate]
    fields: List[FieldCreate]

# Main schema for returning a full envelope object from the API
class Envelope(EnvelopeBase):
    id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    recipients: List[Recipient] = []
    
    class Config:
        from_attributes = True