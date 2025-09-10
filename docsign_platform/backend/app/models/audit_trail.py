from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class AuditTrail(Base):
    __tablename__ = "audit_trails"

    id = Column(Integer, primary_key=True, index=True)
    envelope_id = Column(String(36), ForeignKey("envelopes.id"), nullable=False)
    
    # Example events: 'Envelope Created', 'Sent to signer1@email.com', 'Viewed by signer1@email.com',
    # 'Signed by signer1@email.com', 'Envelope Completed'
    event = Column(String, nullable=False)
    
    ip_address = Column(String, nullable=True) # Logged on view/sign events
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    envelope = relationship("Envelope", back_populates="audit_trails")