import uuid
from sqlalchemy.orm import Session
from app.models.envelope import Envelope
from app.models.recipient import Recipient # <-- Import Recipient

def get_envelope(db: Session, envelope_id: str) -> Envelope | None:
    """
    Retrieve an envelope from the database by its ID.
    """
    return db.query(Envelope).filter(Envelope.id == envelope_id).first()

def create_envelope(db: Session, *, original_doc_path: str, original_doc_hash: str) -> Envelope:
    """
    Create a new envelope record in the database.
    """
    db_envelope = Envelope(
        id=str(uuid.uuid4()),
        original_doc_path=original_doc_path,
        original_doc_hash=original_doc_hash,
        status="draft"
    )
    db.add(db_envelope)
    db.commit()
    db.refresh(db_envelope)
    return db_envelope

# This is the correct location for this function with the corrected return type
def get_recipients_by_order(db: Session, *, envelope_id: str, order: int) -> list[Recipient]:
    """
    Get all recipients for a specific signing order number.
    """
    return db.query(Recipient).filter(
        Recipient.envelope_id == envelope_id,
        Recipient.signing_order == order
    ).all()