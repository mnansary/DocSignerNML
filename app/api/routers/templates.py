import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps

router = APIRouter()


@router.post("/", response_model=models.DocumentTemplate)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
):
    """
    Create new document template.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDFs are allowed.",
        )

    # Save the uploaded file
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    file_extension = Path(file.filename).suffix
    saved_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / saved_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    template_in = models.DocumentTemplateCreate(name=name, description=description)
    template = crud.template.create_template(
        db=db, obj_in=template_in, owner_id=current_user.id, filepath=str(file_path)
    )
    return template
