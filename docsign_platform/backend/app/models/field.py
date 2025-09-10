from sqlalchemy import Column, Integer, String, Float, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.schemas.enums import FieldTypeEnum

class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    envelope_id = Column(String(36), ForeignKey("envelopes.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), nullable=False)
    
    page_number = Column(Integer, nullable=False)
    
    type = Column(
        Enum(FieldTypeEnum, name="field_type_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    
    # Coordinates are stored as percentages of page dimensions for responsiveness
    x_coord = Column(Float, nullable=False)
    y_coord = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Stores the final input value
    # For signatures, this will be the path to the signature image file.
    # For text fields, it will be the text itself.
    value = Column(Text, nullable=True)

    # Relationships
    envelope = relationship("Envelope", back_populates="fields")
    recipient = relationship("Recipient", back_populates="fields")

