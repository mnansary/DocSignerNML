# document_ai_verification/core/verification_service.py

import logging
from pathlib import Path
import json
from typing import Dict, Any, List, Tuple, AsyncGenerator

from fastapi import UploadFile # This can be removed or kept for type hinting if preferred
# Import all our custom modules
from ..utils.config_loader import load_settings
from ..utils.file_utils import TemporaryFileHandler
from ..ai.llm.client import LLMService
from ..ai.llm.prompts import (
    get_ns_document_analysis_prompt_holistic,
    get_multimodal_audit_prompt,
)
from ..ai.llm.schemas import (
    PageHolisticAnalysis,
    PageAuditResult
)
from .exceptions import PageCountMismatchError, ContentMismatchError, DocumentVerificationError
from .schemas import (
    VerificationReport,
)

# --- Setup ---
logger = logging.getLogger(__name__)

APP_SETTINGS = load_settings()
SECRETS = APP_SETTINGS['secrets']
CONFIG = APP_SETTINGS['config']

LLM_CLIENT = LLMService(
    api_key=SECRETS['llm_api_key'],
    model=SECRETS['llm_model_name'],
    base_url=SECRETS['llm_api_url'],
    max_context_tokens=CONFIG['ai_services']['llm'].get('max_context_tokens', 64000)
)

def _save_debug_json(data: Any, filename: str, output_path: Path):
    """Saves data to a JSON file, handling Pydantic models correctly."""
    filepath = output_path / filename
    try:
        def json_converter(o):
            if hasattr(o, 'model_dump'):
                return o.model_dump()
            return f"<<non-serializable: {type(o).__name__}>>"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=json_converter)
        logger.info(f"Saved debug data to: {filepath}")
    except Exception as e:
        logger.error(f"Could not save debug file {filepath}. Error: {e}")


# --- FIX: Update function signature to accept bytes and filenames ---
async def run_verification_workflow(
    nsv_file_bytes: bytes, 
    nsv_filename: str, 
    sv_file_bytes: bytes, 
    sv_filename: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrates the verification workflow from file bytes, yielding progress.
    """
    handler = TemporaryFileHandler(base_path=CONFIG['application']['temp_storage_path'])
    
    try:
        handler.setup()

        yield {"type": "status_update", "message": f"Temporary workspace created. Request ID: {handler.request_id}"}

        debug_output_path = Path(handler.temp_dir) / "debug_outputs"
        debug_output_path.mkdir(exist_ok=True)
        logger.info(f"Debug outputs will be saved in: {debug_output_path}")

        # --- FIX: Save the files from bytes instead of UploadFile objects ---
        yield {"type": "status_update", "message": f"Saving original document: {nsv_filename}"}
        nsv_path = handler.save_bytes_as_file(nsv_file_bytes, nsv_filename)

        yield {"type": "status_update", "message": f"Saving signed document: {sv_filename}"}
        sv_path = handler.save_bytes_as_file(sv_file_bytes, sv_filename)

        # --- From this point on, the logic is identical as it works with file paths ---

        yield {"type": "status_update", "message": "Extracting pages from original document..."}
        nsv_page_bundles = handler.extract_content_per_page(nsv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])

        yield {"type": "status_update", "message": "Extracting pages from signed document..."}
        sv_page_bundles = handler.extract_content_per_page(sv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        _save_debug_json(nsv_page_bundles, "step_1_nsv_page_bundles.json", debug_output_path)
        _save_debug_json(sv_page_bundles, "step_1_sv_page_bundles.json", debug_output_path)

        if len(nsv_page_bundles) != len(sv_page_bundles):
            raise PageCountMismatchError(f"NSV has {len(nsv_page_bundles)} pages, SV has {len(sv_page_bundles)} pages.")

        yield {"type": "status_update", "message": f"Found {len(nsv_page_bundles)} pages. Starting Stage 1: Requirement Analysis..."}
        
        requirements_map: Dict[int, PageHolisticAnalysis] = {}
        for page_bundle in nsv_page_bundles:
            page_num = page_bundle['page_num']
            page_img = page_bundle["image_path"]
            
            yield {"type": "status_update", "message": f"Analyzing requirements for Page {page_num}..."}

            prompt = get_ns_document_analysis_prompt_holistic(page_bundle['markdown_text'])
            page_req_result = LLM_CLIENT.invoke_vision_structured(
                prompt=prompt, image_path=page_img, response_model=PageHolisticAnalysis
            )
            requirements_map[page_num] = page_req_result

            # --- FIX: Manually add page_number to the result payload ---
            result_payload = page_req_result.model_dump()
            result_payload['page_number'] = page_num
            
            # --- Yield the structured result for the frontend ---
            yield {
                "type": "process_step_result",
                "data": {
                    "stage_id": "requirement_analysis",
                    "stage_title": "Stage 1: Requirement Analysis",
                    "result": result_payload
                }
            }
            
        
        _save_debug_json(requirements_map, "step_2_requirements_map.json", debug_output_path)
        yield {"type": "status_update", "message": "Stage 1 analysis complete."}
        
        yield {
            "type": "workflow_complete",
            "data": {
                "final_status": "Success",
                "message": "All planned stages have finished."
            }
        }
            
    except (PageCountMismatchError, DocumentVerificationError) as e:
        logger.error(f"A known document processing error occurred: {e}")
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        logger.exception("An unexpected error occurred during the verification workflow.")
        yield {"type": "error", "message": f"An unexpected server error occurred. Please check system logs."}
    finally:
        handler.cleanup()