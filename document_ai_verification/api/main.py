# document_ai_verification/api/main.py

import logging
import json
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

# Import the core service and custom exceptions
from ..core.verification_service import run_verification_workflow
from ..core.exceptions import (
    DocumentVerificationError,
    PageCountMismatchError,
)

# --- Application Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document AI Verification API",
    description="An API to perform a detailed audit and verification of a signed document against its original version.",
    version="2.2.0" # Version bump for streaming fix
)

# --- API Endpoints ---

@app.get("/health", tags=["Health Check"], summary="Check if the API is running")
async def read_root():
    """Confirms that the API server is running."""
    return {"status": "ok", "message": "Document AI Verification API is running."}

async def stream_formatter(generator: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """
    Takes an async generator that yields dictionaries and formats them
    into Server-Sent Event (SSE) strings.
    """
    async for event_dict in generator:
        json_data = json.dumps(event_dict)
        yield f"data: {json_data}\n\n"


@app.post(
    "/verify/", 
    tags=["Verification"],
    summary="[STREAMING] Verify a signed document against its original version"
)
async def verify_documents_stream(
    nsv_file: UploadFile = File(..., description="The original, non-signed PDF document."),
    sv_file: UploadFile = File(..., description="The final, signed PDF document.")
):
    """
    Processes documents and streams a detailed, page-by-page audit report in real-time.
    """
    logger.info(f"Received stream verification request. NSV: '{nsv_file.filename}', SV: '{sv_file.filename}'")
    
    try:
        # --- FIX: Read file contents immediately before the endpoint returns ---
        # This is the crucial step. We consume the UploadFile objects now while they are still open.
        nsv_file_bytes = await nsv_file.read()
        sv_file_bytes = await sv_file.read()
        
        # We also need to preserve the filenames
        nsv_filename = nsv_file.filename
        sv_filename = sv_file.filename

    finally:
        # Ensure files are closed even if reading fails
        await nsv_file.close()
        await sv_file.close()

    # Now, create the generator, passing the raw bytes and filenames, not the UploadFile objects.
    service_generator = run_verification_workflow(
        nsv_file_bytes=nsv_file_bytes,
        nsv_filename=nsv_filename,
        sv_file_bytes=sv_file_bytes,
        sv_filename=sv_filename,
    )
    
    return StreamingResponse(
        stream_formatter(service_generator), 
        media_type="text/event-stream"
    )

# --- Static Files Hosting ---
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")