from sqlalchemy.orm import Session
from app.models.recipient import Recipient
from app.schemas.recipient import RecipientCreate
# Add this function to the existing file
from datetime import datetime

def create_recipient(db: Session, *, obj_in: RecipientCreate, envelope_id: str) -> Recipient:
    """
    Create a new recipient for a given envelope.

    Args:
        db: The database session.
        obj_in: Pydantic schema with recipient data (email, signing_order).
        envelope_id: The ID of the envelope this recipient belongs to.

    Returns:
        The newly created Recipient object.
    """
    db_recipient = Recipient(
        **obj_in.model_dump(),
        envelope_id=envelope_id
    )
    db.add(db_recipient)
    # We will commit once all recipients and fields are added in the API layer.
    # db.commit() 
    # db.refresh(db_recipient)
    return db_recipient

def get_recipient_by_email(db: Session, *, envelope_id: str, email: str) -> Recipient | None:
    """
    Find a recipient by their email within a specific envelope.
    This is useful for linking fields to the correct recipient ID.
    """
    return db.query(Recipient).filter(Recipient.envelope_id == envelope_id, Recipient.email == email).first()

# Add this function to the existing file
def get_recipient_by_token(db: Session, *, token: str) -> Recipient | None:
    """
    Find a recipient by their unique signing token.
    """
    return db.query(Recipient).filter(Recipient.signing_token == token).first()



def update_recipient_status(db: Session, *, recipient_id: int, status: str) -> Recipient | None:
    """
    Updates the status of a recipient and sets the signed_at timestamp if applicable.
    """
    db_recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if db_recipient:
        db_recipient.status = status
        if status == "signed":
            db_recipient.signed_at = datetime.utcnow()
        db.add(db_recipient)
    return db_recipient