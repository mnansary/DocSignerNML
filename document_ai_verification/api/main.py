# document_ai_verification/api/main.py

import logging
import logging
from pathlib import Path # <--- Import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles # <--- Import StaticFiles
from pydantic import ValidationError

# Import the core service and custom exceptions
from ..core.verification_service import run_verification_workflow
from ..core.exceptions import (
    DocumentVerificationError,
    PageCountMismatchError,
)
from ..core.schemas import VerificationReport # Import the response model

# --- Application Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document AI Verification API",
    description="An API to perform a detailed audit and verification of a signed document against its original version.",
    version="2.0.0" # Version bump for new features
)

# --- API Endpoints ---

@app.get("/health", tags=["Health Check"], summary="Check if the API is running")
async def read_root():
    """Confirms that the API server is running."""
    return {"status": "ok", "message": "Document AI Verification API is running."}


@app.post(
    "/verify/", 
    tags=["Verification"],
    summary="Verify a signed document against its original version",
    # Use the Pydantic model to automatically generate response documentation
    response_model=VerificationReport 
)
async def verify_documents(
    nsv_file: UploadFile = File(..., description="The original, non-signed PDF document."),
    sv_file: UploadFile = File(..., description="The final, signed PDF document.")
):
    """
    Processes a non-signed document (NSV) and a signed document (SV) to perform a detailed, page-by-page audit.

    **On Success (HTTP 200):**
    - Returns a comprehensive `VerificationReport` JSON object detailing the status of every page, required inputs, and any detected content discrepancies.

    **On Failure:**
    - **HTTP 400 (Bad Request):** Raised for fundamental validation errors, like page count mismatches.
    - **HTTP 500 (Internal Server Error):** Raised for unexpected processing errors, such as AI model failures or file conversion issues.
    """
    logger.info(f"Received verification request. NSV: '{nsv_file.filename}', SV: '{sv_file.filename}'")

    try:
        # The service now returns the Pydantic report object directly
        report = await run_verification_workflow(nsv_file=nsv_file, sv_file=sv_file)
        
        # FastAPI will automatically serialize the Pydantic model to JSON
        logger.info(f"Verification for '{nsv_file.filename}' completed with status: {report.overall_status}")
        return report

    # --- Specific Error Handling ---
    except PageCountMismatchError as e:
        logger.warning(f"Verification failed due to page count mismatch: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
        
    except DocumentVerificationError as e:
        # This is a catch-all for our other custom errors
        logger.error(f"A document verification error occurred: {e.message}")
        # We return a 500 here because it's an unexpected failure in our defined logic
        raise HTTPException(status_code=500, detail=f"Processing Error: {e.message}")

    except ValidationError as e:
        # This can happen if an AI model returns malformed JSON that Pydantic can't parse
        logger.error(f"Pydantic validation error, likely from AI model output: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Failed to process the AI model's response.")
        
    # --- Generic Error Handling ---
    except Exception as e:
        logger.exception("An unexpected internal server error occurred.")
        raise HTTPException(status_code=500, detail="Internal Server Error: An unexpected error occurred during processing.")
    

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")