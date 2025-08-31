from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps

router = APIRouter()


@router.get("/{signing_token}")
def get_signing_document_data(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    signing_token: str,
):
    """
    Get the necessary data to render a document for signing.
    This is what the signer's UI would call first.
    """
    recipient = crud.document.get_recipient_by_token(db, token=signing_token)

    if not recipient:
        raise HTTPException(status_code=404, detail="Signing link is not valid")

    if datetime.utcnow() > recipient.token_expires_at:
        raise HTTPException(status_code=400, detail="Signing link has expired")

    if recipient.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"This document's status is '{recipient.status}'"
        )

    # Log the view event
    crud.audit.create_audit_log(
        db=db,
        obj_in=models.AuditLogCreate(
            document_id=recipient.document.id,
            action="document_viewed",
            ip_address=request.client.host,
            details={"signer_email": recipient.email},
        ),
    )

    # Return the data needed for the signing UI
    return {
        "document_id": recipient.document.id,
        "template_filepath": recipient.document.template.filepath,
        "field_layout": recipient.document.field_layout,
    }


from app import services


@router.post("/{signing_token}")
def submit_signed_document(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    signing_token: str,
    submission_in: models.signing.SigningSubmission,
):
    """
    Submit the signer's data (filled fields and signature).
    This triggers the verification process.
    """
    recipient = crud.document.get_recipient_by_token(db, token=signing_token)

    if not recipient:
        raise HTTPException(status_code=404, detail="Signing link is not valid")

    if datetime.utcnow() > recipient.token_expires_at:
        raise HTTPException(status_code=400, detail="Signing link has expired")

    if recipient.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"This document's status is '{recipient.status}'"
        )

    # Store the submitted data and update status
    recipient.submission_data = submission_in.submission_data
    recipient.signed_at = datetime.utcnow()
    recipient.status = "submitted"  # Mark as submitted before verification
    db.commit()

    crud.audit.create_audit_log(
        db=db,
        obj_in=models.AuditLogCreate(
            document_id=recipient.document.id,
            action="document_submitted",
            ip_address=request.client.host,
            details={"signer_email": recipient.email},
        ),
    )

    # Trigger the deterministic verification engine
    verification_passed = services.verification_engine.verify_document_integrity(
        recipient=recipient
    )

    if verification_passed:
        recipient.status = "verification_passed"
        message = "Document submitted and verified successfully."
        action = "verification_passed"
    else:
        recipient.status = "verification_failed"
        message = "Document submission failed verification."
        action = "verification_failed"

    db.commit()

    crud.audit.create_audit_log(
        db=db,
        obj_in=models.AuditLogCreate(
            document_id=recipient.document.id,
            action=action,
            ip_address=request.client.host,
            details={"signer_email": recipient.email},
        ),
    )

    return {"message": message, "verification_status": recipient.status}
