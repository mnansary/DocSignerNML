import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models, services
from app.api import deps

router = APIRouter()


@router.post("/", response_model=models.Document)
def create_document(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    document_in: models.DocumentCreate,
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Create a new document from a template.
    The user defines the fillable fields and signature slots here.
    """
    template = crud.template.get_template(db, template_id=document_in.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    document = crud.document.create_with_owner(
        db=db, obj_in=document_in, owner_id=current_user.id
    )

    # Audit log
    crud.audit.create_audit_log(
        db=db,
        obj_in=models.AuditLogCreate(
            document_id=document.id,
            user_id=current_user.id,
            action="document_created",
            ip_address=request.client.host,
        ),
    )

    return document


@router.post("/{document_id}/lock", response_model=models.Document)
def lock_document_for_signing(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    document_id: uuid.UUID,
    current_user: models.User = Depends(deps.get_current_user),
):
    """
    Lock the document and generate the Golden Master record.
    This is the final step before sending to the signer.
    """
    doc = crud.document.get(db, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if doc.is_locked:
        raise HTTPException(status_code=400, detail="Document is already locked")

    # Get the template filepath
    template_path = Path(doc.template.filepath)

    # Generate Golden Master assets
    page_hashes, text_map = services.document_processor.generate_golden_master(
        template_path
    )

    # Update the document with the generated data
    update_data = {
        "golden_master_hashes": page_hashes,
        "golden_master_text_map": text_map,
        "is_locked": True,
    }
    updated_doc = crud.document.update(db=db, db_obj=doc, obj_in=update_data)

    # Audit log
    crud.audit.create_audit_log(
        db=db,
        obj_in=models.AuditLogCreate(
            document_id=updated_doc.id,
            user_id=current_user.id,
            action="document_locked",
            ip_address=request.client.host,
        ),
    )

    return updated_doc
