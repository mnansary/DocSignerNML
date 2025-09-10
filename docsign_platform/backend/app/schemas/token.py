from pydantic import BaseModel
from typing import List, Optional
# We will import the Field schema later, so we use a forward reference for now
from .field import Field 
# Add this class to the end of the existing file
from .field import FieldSubmission # Add this import at the top

class SigningData(BaseModel):
    envelope_id: str
    recipient_email: str
    fields: List[Field] # This will contain the fields assigned to this specific signer

class SigningToken(BaseModel):
    token: str
    
class TokenPayload(BaseModel):
    sub: Optional[int] = None


class SubmissionPayload(BaseModel):
    fields: List[FieldSubmission]