import os
import fitz # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

# Corrected, more specific imports
from app.crud import crud_envelope, crud_recipient, crud_field, crud_audit_trail
from app.schemas.envelope import EnvelopeCreateResponse, EnvelopeSetup
from app.schemas.message import Message
from app.api import deps
from app.core.config import settings
from app.utils.helpers import calculate_sha256
from app.tasks.send_email import send_signing_request_email
# Add this import at the top of the file
from fastapi.responses import FileResponse

router = APIRouter()

# Add 'async' to the function definition
@router.post("/", response_model=EnvelopeCreateResponse)
async def create_envelope(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...)
):
    """
    Upload a new PDF document to create an envelope.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is allowed.")

    originals_dir = os.path.join(settings.STORAGE_BASE_PATH, "originals")
    os.makedirs(originals_dir, exist_ok=True)
    
    # In a real app, use a UUID for the filename to prevent overwrites
    file_path = os.path.join(originals_dir, file.filename)
    
    # Use 'async with' and 'await' to handle the file content
    with open(file_path, "wb") as buffer:
        content = await file.read() # <-- Use await here
        buffer.write(content)

    file_hash = calculate_sha256(file_path)
    envelope = crud_envelope.create_envelope(db=db, original_doc_path=file_path, original_doc_hash=file_hash)
    
    return {"id": envelope.id}


@router.get("/{envelope_id}/preview/{page_num}", response_class=Response)
def get_envelope_page_preview(
    envelope_id: str,
    page_num: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get a PNG image preview of a specific page of a document.
    """
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope not found")
        
    try:
        doc = fitz.open(envelope.original_doc_path)
        if page_num < 1 or page_num > len(doc):
             raise HTTPException(status_code=404, detail="Page number out of range")
        
        page = doc.load_page(page_num - 1)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        return Response(content=img_bytes, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render page preview: {str(e)}")


@router.post("/{envelope_id}/setup", response_model=Message)
def setup_envelope_template(
    envelope_id: str,
    *,
    db: Session = Depends(deps.get_db),
    setup_data: EnvelopeSetup
):
    """
    Configure an envelope with recipients and fields.
    """
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope not found")

    if envelope.status != "draft":
        raise HTTPException(status_code=400, detail="Envelope has already been configured and sent.")

    # 1. Create recipient objects and add them to the session
    recipient_map = {}
    for recipient_in in setup_data.recipients:
        recipient = crud_recipient.create_recipient(db=db, obj_in=recipient_in, envelope_id=envelope_id)
        recipient_map[recipient.email] = recipient

    # 2. Flush the session to the database.
    # This sends the INSERT for recipients and populates their IDs,
    # but does NOT commit the transaction yet.
    db.flush()

    # 3. Now that recipient.id is populated, create the fields
    for field_in in setup_data.fields:
        recipient = recipient_map.get(field_in.assignee_email)
        if not recipient:
            # This check is now even more important
            raise HTTPException(status_code=400, detail=f"Recipient with email {field_in.assignee_email} not found.")
        
        # At this point, recipient.id is guaranteed to have a value
        crud_field.create_field(db=db, obj_in=field_in, envelope_id=envelope_id, recipient_id=recipient.id)

    # 4. Finally, commit the entire transaction (recipients and fields)
    db.commit()
    return {"message": "Envelope template configured successfully."}


@router.post("/{envelope_id}/send", response_model=Message)
def send_envelope_for_signing(
    envelope_id: str,
    *,
    db: Session = Depends(deps.get_db),
    request: Request
):
    """
    Initiates the signing process for an envelope.
    """
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope not found")
    if envelope.status != "draft":
        raise HTTPException(status_code=400, detail="Envelope has already been sent.")

    recipients_to_notify = crud_envelope.get_recipients_by_order(db=db, envelope_id=envelope_id, order=1)
    if not recipients_to_notify:
        raise HTTPException(status_code=400, detail="No recipients configured for this envelope.")

    envelope.status = "sent"
    crud_audit_trail.create_audit_log(db=db, envelope_id=envelope_id, event="Envelope Sent")

    for recipient in recipients_to_notify:
        # Construct the link reliably to avoid missing slashes
        signing_link = f"{request.url.scheme}://{request.url.netloc}/sign.html?token={recipient.signing_token}"

        send_signing_request_email(recipient.email, signing_link)

        crud_audit_trail.create_audit_log(
            db=db,
            envelope_id=envelope_id,
            event=f"Sent to {recipient.email}"
        )

    db.commit()
    return {"message": "Envelope has been sent for signing."}




# Add this entire function to the envelopes.py file
@router.get("/{envelope_id}/download", response_class=FileResponse)
def download_original_document(
    envelope_id: str,
    db: Session = Depends(deps.get_db)
):
    """
    Allows the client to download the original, unaltered PDF document.
    This is used by the frontend to get the page count with PDF.js.
    """
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope or not os.path.exists(envelope.original_doc_path):
        raise HTTPException(status_code=404, detail="Document not found.")
    
    return FileResponse(envelope.original_doc_path, media_type='application/pdf', filename=os.path.basename(envelope.original_doc_path))