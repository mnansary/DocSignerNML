import uuid
from sqlalchemy import Column, String, DateTime, func, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base

class Envelope(Base):
    __tablename__ = "envelopes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    status = Column(
        Enum("draft", "sent", "completed", "voided", name="envelope_status_enum"),
        nullable=False,
        default="draft"
    )

    original_doc_path = Column(String, nullable=False)
    original_doc_hash = Column(String, nullable=False)
    signed_doc_path = Column(String, nullable=True)
    final_hash = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # This tells SQLAlchemy that an Envelope can have many recipients and fields.
    # The 'cascade="all, delete-orphan"' means if an envelope is deleted,
    # all its associated recipients and fields are also deleted.
    recipients = relationship("Recipient", back_populates="envelope", cascade="all, delete-orphan")
    fields = relationship("Field", back_populates="envelope", cascade="all, delete-orphan")
    audit_trails = relationship("AuditTrail", back_populates="envelope", cascade="all, delete-orphan")