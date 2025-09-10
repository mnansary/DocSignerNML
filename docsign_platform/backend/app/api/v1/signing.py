from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime # Import datetime

# Corrected, more specific imports
from app.crud import crud_recipient, crud_audit_trail
from app.schemas.token import SigningData
from app.crud import crud_field, crud_envelope
from app.schemas.token import SubmissionPayload
from app.services.pdf_processor import save_signature_image
from app.tasks.send_email import send_signing_request_email # Ensure this is imported
from app.api import deps
from app.schemas.message import Message

router = APIRouter()

@router.get("/{token}", response_model=SigningData)
def get_signing_data(
    token: str,
    *,
    db: Session = Depends(deps.get_db),
    request: Request # Add request to get IP
):
    """
    Retrieves the necessary data for a signer to view and sign the document.
    """
    recipient = crud_recipient.get_recipient_by_token(db=db, token=token)
    if not recipient or not recipient.envelope:
        raise HTTPException(status_code=404, detail="Invalid signing token.")

    if recipient.status == "signed":
         raise HTTPException(status_code=400, detail="Document has already been signed by this recipient.")

    # Log the 'viewed' event only the first time
    if recipient.status == "pending":
        recipient.status = "viewed"
        recipient.viewed_at = datetime.utcnow() # Assuming you add this field to the model
        crud_audit_trail.create_audit_log(
            db=db,
            envelope_id=recipient.envelope_id,
            event=f"Viewed by {recipient.email}",
            ip_address=request.client.host
        )
        db.commit()
        db.refresh(recipient)

    return {
        "envelope_id": recipient.envelope.id,
        "recipient_email": recipient.email,
        "fields": recipient.fields,
    }


# Add this endpoint to the end of the file
# Add these imports at the top of the file:


@router.post("/{token}", response_model=Message)
def submit_signed_fields(
    token: str,
    *,
    db: Session = Depends(deps.get_db),
    submission: SubmissionPayload,
    request: Request
):
    """
    Accepts the signer's inputs (signatures, text fields) and processes them.
    """
    recipient = crud_recipient.get_recipient_by_token(db=db, token=token)
    if not recipient or recipient.status != "viewed":
        raise HTTPException(status_code=404, detail="Invalid token or signing session.")

    envelope = recipient.envelope

    # Process each submitted field
    for field_sub in submission.fields:
        field_model = db.query(crud_field.Field).get(field_sub.id)
        # Security check: ensure the field belongs to this recipient
        if not field_model or field_model.recipient_id != recipient.id:
            raise HTTPException(status_code=403, detail=f"Not authorized to update field ID {field_sub.id}")

        value_to_save = field_sub.value
        if field_model.type in ["signature", "initial"]:
            # If it's a signature, save the image and store the path
            try:
                value_to_save = save_signature_image(field_sub.value)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        crud_field.update_field_value(db=db, field_id=field_sub.id, value=value_to_save)

    # Update recipient status to 'signed' and log the event
    crud_recipient.update_recipient_status(db=db, recipient_id=recipient.id, status="signed")
    crud_audit_trail.create_audit_log(
        db=db,
        envelope_id=envelope.id,
        event=f"Signed by {recipient.email}",
        ip_address=request.client.host
    )

    # --- Post-Signing Logic ---
    next_order = recipient.signing_order + 1
    next_recipients = crud_envelope.get_recipients_by_order(db=db, envelope_id=envelope.id, order=next_order)

    if next_recipients:
        # There are more signers, so notify them
        for next_recipient in next_recipients:
            base_url = str(request.base_url).rstrip('/')
            signing_link = f"{base_url}sign.html?token={next_recipient.signing_token}"
            send_signing_request_email(next_recipient.email, signing_link)
            crud_audit_trail.create_audit_log(
                db=db, envelope_id=envelope.id, event=f"Sent to {next_recipient.email}"
            )
    else:
        # This was the last signer, the envelope is now ready for processing.
        envelope.status = "completed"
        crud_audit_trail.create_audit_log(db=db, envelope_id=envelope.id, event="Envelope Completed")
        
        # Trigger the background task to finalize the document.
        # .delay() is the standard way to call a Celery task.
        from app.tasks.finalize_document import finalize_envelope_task
        finalize_envelope_task.delay(envelope.id)

    db.commit()

    return {"message": "Document successfully signed. Thank you."}