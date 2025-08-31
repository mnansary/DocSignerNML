import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models.document import Document, DocumentRecipient
from app.models.document import DocumentCreate

# A reasonable expiration time for signing links, e.g., 7 days
SIGNING_LINK_EXPIRATION_DAYS = 7


def get(db: Session, *, document_id: uuid.UUID) -> Document | None:
    """
    Gets a document by its ID.
    """
    return db.query(Document).filter(Document.id == document_id).first()


def get_recipient_by_token(db: Session, *, token: str) -> DocumentRecipient | None:
    """
    Gets a document recipient by their signing token.
    """
    return db.query(DocumentRecipient).filter(DocumentRecipient.signing_token == token).first()


def create_with_owner(
    db: Session, *, obj_in: DocumentCreate, owner_id: uuid.UUID
) -> Document:
    """
    Creates a new document with an owner and generates secure signing tokens for recipients.
    """
    db_obj = Document(
        template_id=obj_in.template_id,
        owner_id=owner_id,
        field_layout=obj_in.field_layout,
    )
    db.add(db_obj)
    db.commit()

    # Create recipient records
    for recipient in obj_in.recipients:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=SIGNING_LINK_EXPIRATION_DAYS)
        db_recipient = DocumentRecipient(
            document_id=db_obj.id,
            email=recipient.email,
            signing_token=token,
            token_expires_at=expires_at,
        )
        db.add(db_recipient)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Document, obj_in: dict) -> Document:
    """
    Updates a document.
    """
    for field, value in obj_in.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
