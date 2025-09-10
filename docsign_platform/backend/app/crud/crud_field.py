from sqlalchemy.orm import Session
from app.models.field import Field
from app.schemas.field import FieldCreate

def create_field(db: Session, *, obj_in: FieldCreate, envelope_id: str, recipient_id: int) -> Field:
    """
    Create a new field and associate it with an envelope and a recipient.

    Args:
        db: The database session.
        obj_in: Pydantic schema with field data (page, type, coordinates).
        envelope_id: The ID of the parent envelope.
        recipient_id: The ID of the recipient assigned to this field.

    Returns:
        The newly created Field object.
    """
    # Create a dictionary from the Pydantic model, excluding the assignee_email
    # which is not part of the database model.
    field_data = obj_in.model_dump(exclude={"assignee_email"})
    
    db_field = Field(
        **field_data,
        envelope_id=envelope_id,
        recipient_id=recipient_id
    )
    db.add(db_field)
    # Similar to recipients, we will commit once all fields are added.
    # db.commit()
    # db.refresh(db_field)
    return db_field

# Add this function to the existing file
def update_field_value(db: Session, *, field_id: int, value: str) -> Field | None:
    """
    Updates the value of a specific field.
    """
    db_field = db.query(Field).filter(Field.id == field_id).first()
    if db_field:
        db_field.value = value
        db.add(db_field)
    return db_field