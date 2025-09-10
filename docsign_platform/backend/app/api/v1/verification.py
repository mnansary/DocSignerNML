import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.crud import crud_envelope
from app.schemas.message import Message # Reusable message schema
from app.api import deps
from app.utils.helpers import calculate_sha256

router = APIRouter()

class VerificationResult(Message):
    """Extends the base message to include verification status."""
    is_authentic: bool
    envelope_id: str | None = None
    completed_at: str | None = None


@router.post("/", response_model=VerificationResult)
def verify_document_integrity(
    *,
    db: Session = Depends(deps.get_db),
    # The envelope ID must be sent along with the file in a multipart form
    envelope_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Verifies the integrity of a signed document.
    - User uploads the final PDF and provides its Envelope ID.
    - The API calculates the hash of the uploaded file.
    - It compares this new hash with the 'final_hash' stored in the database.
    - If they match, the document is authentic. If not, it has been altered.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is allowed.")
        
    # Retrieve the original envelope record from the database
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope ID not found in our records.")

    if not envelope.final_hash or envelope.status != "completed":
        raise HTTPException(status_code=400, detail="This envelope has not been completed and cannot be verified yet.")
        
    # To calculate the hash, we must save the uploaded file temporarily
    temp_dir = "backend/storage/temp_verification" # A dedicated temp folder
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file.read())

        # Calculate the hash of the file the user just uploaded
        uploaded_file_hash = calculate_sha256(temp_file_path)
        
    finally:
        # Ensure the temporary file is deleted after hashing
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    # The moment of truth: compare the hashes
    if uploaded_file_hash == envelope.final_hash:
        return {
            "is_authentic": True,
            "message": "Document is authentic and has not been altered since completion.",
            "envelope_id": envelope.id,
            "completed_at": envelope.updated_at.isoformat() if envelope.updated_at else None
        }
    else:
        return {
            "is_authentic": False,
            "message": "Verification Failed: The document has been altered or is not the correct version.",
            "envelope_id": envelope.id,
            "completed_at": envelope.updated_at.isoformat() if envelope.updated_at else None
        }