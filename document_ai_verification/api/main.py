# document_ai_verification/api/main.py

import logging
import json
import shutil # Import shutil for the background task
from pathlib import Path
from typing import AsyncGenerator
import asyncio

# --- Import BackgroundTasks ---
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from ..core.verification_service import run_verification_workflow
from ..core.exceptions import DocumentVerificationError, PageCountMismatchError
from ..utils.config_loader import load_settings
# --- Import the handler class itself ---
from ..utils.file_utils import TemporaryFileHandler

# --- Application Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document AI Verification API",
    description="An API to perform a detailed audit and verification of a signed document against its original version.",
    version="2.4.0" # Version bump for background tasks
)

CONFIG = load_settings()['config']
TEMP_DIR_BASE = Path(CONFIG['application']['temp_storage_path'])


# --- Background Task Function for Cleanup ---
async def cleanup_temp_dir(path: Path, delay_seconds: int):
    """Waits for a specified time and then deletes the temporary directory."""
    await asyncio.sleep(delay_seconds)
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            logger.info(f"Background task successfully cleaned up temporary directory: {path}")
    except OSError as e:
        logger.error(f"Background task failed to clean up temporary directory {path}: {e}")


# --- API Endpoints ---
# --- FIX: Full definition of the /health endpoint ---
@app.get("/health", tags=["Health Check"], summary="Check if the API is running")
async def read_root():
    """Confirms that the API server is running."""
    return {"status": "ok", "message": "Document AI Verification API is running."}


# --- FIX: Full definition of the /temp endpoint ---
@app.get("/temp/{request_id}/{file_path:path}", tags=["Utilities"])
async def get_temp_file(request_id: str, file_path: str):
    """
    Serves a temporary file generated during the verification process.
    Includes a security check to prevent accessing files outside the temp directory.
    """
    try:
        base_path = TEMP_DIR_BASE.resolve()
        full_path = (base_path / request_id / file_path).resolve()

        if not str(full_path).startswith(str(base_path)):
            logger.warning(f"Forbidden access attempt: {full_path}")
            raise HTTPException(status_code=403, detail="Forbidden: Access denied.")

        if not full_path.is_file():
            logger.error(f"Temp file not found: {full_path}")
            raise HTTPException(status_code=404, detail="File not found.")

        return FileResponse(full_path)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error serving temp file '{file_path}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


async def stream_formatter(generator: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """
    Takes an async generator that yields dictionaries and formats them
    into Server-Sent Event (SSE) strings.
    """
    async for event_dict in generator:
        json_data = json.dumps(event_dict)
        yield f"data: {json_data}\n\n"


@app.post("/verify/", tags=["Verification"])
async def verify_documents_stream(
    background_tasks: BackgroundTasks,
    nsv_file: UploadFile = File(...),
    sv_file: UploadFile = File(...)
):
    """
    Processes documents, streams results, and schedules a background task for cleanup.
    """
    logger.info(f"Received stream verification request. NSV: '{nsv_file.filename}', SV: '{sv_file.filename}'")
    
    handler = TemporaryFileHandler(base_path=str(TEMP_DIR_BASE))
    handler.setup()

    try:
        nsv_file_bytes = await nsv_file.read()
        sv_file_bytes = await sv_file.read()
        nsv_filename = nsv_file.filename
        sv_filename = sv_file.filename
    finally:
        await nsv_file.close()
        await sv_file.close()

    cleanup_delay = CONFIG['application'].get('temp_storage_cleanup_delay_seconds', 600)
    background_tasks.add_task(cleanup_temp_dir, handler.temp_dir, delay_seconds=cleanup_delay)

    service_generator = run_verification_workflow(
        handler=handler,
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