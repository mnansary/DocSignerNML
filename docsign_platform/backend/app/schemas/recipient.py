from pydantic import BaseModel, EmailStr
from typing import List
from .field import Field # Import the final Field schema

# Base properties
class RecipientBase(BaseModel):
    email: EmailStr
    signing_order: int

# Schema for creating a new recipient
class RecipientCreate(RecipientBase):
    pass

# Schema for returning a recipient from the API
class Recipient(RecipientBase):
    id: int
    status: str
    fields: List[Field] = []

    class Config:
        from_attributes = True