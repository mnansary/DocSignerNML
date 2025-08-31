from typing import Optional, Any
import uuid
from pydantic import BaseModel
from datetime import datetime


class AuditLogBase(BaseModel):
    document_id: uuid.UUID
    action: str
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[uuid.UUID] = None


class AuditLog(AuditLogBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    timestamp: datetime

    class Config:
        orm_mode = True
