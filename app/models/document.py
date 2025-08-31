from typing import List, Optional, Any
import uuid
from pydantic import BaseModel
from datetime import datetime


# Document Template Schemas
class DocumentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplate(DocumentTemplateBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    filepath: str

    class Config:
        orm_mode = True


# Document Recipient Schemas
class DocumentRecipientBase(BaseModel):
    email: str


class DocumentRecipientCreate(DocumentRecipientBase):
    pass


class DocumentRecipient(DocumentRecipientBase):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    signed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Document Schemas
class DocumentBase(BaseModel):
    template_id: uuid.UUID
    field_layout: Optional[dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    recipients: List[DocumentRecipientCreate]


class Document(DocumentBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    is_locked: bool
    recipients: List[DocumentRecipient] = []

    class Config:
        orm_mode = True
