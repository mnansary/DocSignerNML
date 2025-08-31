import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    filepath = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="templates")
    documents = relationship("Document", back_populates="template")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    field_layout = Column(JSON)  # To store sender-defined field layout
    golden_master_hashes = Column(JSON)  # To store page hashes
    golden_master_text_map = Column(JSON) # To store static text map
    created_at = Column(DateTime, default=func.now())
    is_locked = Column(Boolean, default=False)

    owner = relationship("User", back_populates="documents")
    template = relationship("DocumentTemplate", back_populates="documents")
    recipients = relationship("DocumentRecipient", back_populates="document")


class DocumentRecipient(Base):
    __tablename__ = "document_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    email = Column(String, nullable=False)
    signing_token = Column(String, unique=True, index=True)
    token_expires_at = Column(DateTime)
    signed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # e.g., pending, viewed, signed
    submission_data = Column(JSON, nullable=True)  # To store signer's input

    document = relationship("Document", back_populates="recipients")
