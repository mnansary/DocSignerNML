import uuid
from sqlalchemy.orm import Session

from app.db.models.document import DocumentTemplate
from app.models.document import DocumentTemplateCreate


def create_template(
    db: Session, *, obj_in: DocumentTemplateCreate, owner_id: uuid.UUID, filepath: str
) -> DocumentTemplate:
    """
    Creates a new document template.
    """
    db_obj = DocumentTemplate(
        name=obj_in.name,
        description=obj_in.description,
        owner_id=owner_id,
        filepath=filepath,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_template(db: Session, *, template_id: uuid.UUID) -> DocumentTemplate | None:
    """
    Gets a document template by its ID.
    """
    return db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()
