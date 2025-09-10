import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.crud import crud_envelope
from app.schemas.message import Message
from app.api import deps
from app.utils.helpers import calculate_sha256

router = APIRouter()

class VerificationResult(Message):
    is_authentic: bool
    envelope_id: str | None = None
    completed_at: str | None = None

# Add 'async' to the function definition
@router.post("/", response_model=VerificationResult)
async def verify_document_integrity(
    *,
    db: Session = Depends(deps.get_db),
    envelope_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Verifies the integrity of a signed document.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is allowed.")
        
    envelope = crud_envelope.get_envelope(db=db, envelope_id=envelope_id)
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope ID not found in our records.")

    if not envelope.final_hash or envelope.status != "completed":
        raise HTTPException(status_code=400, detail="This envelope has not been completed and cannot be verified yet.")
        
    # Use an absolute path for the temporary directory for reliability
    temp_dir = os.path.abspath(os.path.join("backend/storage", "temp_verification"))
    os.makedirs(temp_dir, exist_ok=True)
    # Use a unique name to avoid conflicts if multiple users verify at once
    temp_file_path = os.path.join(temp_dir, f"verify_{envelope_id}_{file.filename}")
    
    try:
        # Use 'async with' and 'await' to handle the file content
        with open(temp_file_path, "wb") as buffer:
            content = await file.read() # <-- Use await here
            buffer.write(content)

        uploaded_file_hash = calculate_sha256(temp_file_path)
        
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
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