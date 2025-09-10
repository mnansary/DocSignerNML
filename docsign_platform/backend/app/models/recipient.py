import secrets
from sqlalchemy import Column, String, Integer, DateTime, func, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)
    envelope_id = Column(String(36), ForeignKey("envelopes.id"), nullable=False)
    
    email = Column(String, nullable=False, index=True)
    signing_order = Column(Integer, default=1, nullable=False)
    
    # A unique, unguessable token for the signing URL
    signing_token = Column(String, unique=True, index=True, default=lambda: secrets.token_urlsafe(32))
    
    status = Column(
        Enum("pending", "viewed", "signed", name="recipient_status_enum"),
        nullable=False,
        default="pending"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    signed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    envelope = relationship("Envelope", back_populates="recipients")
    fields = relationship("Field", back_populates="recipient") # A recipient is assigned many fields