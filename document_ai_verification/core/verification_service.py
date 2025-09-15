import asyncio
import logging
from pathlib import Path
import json
from typing import Dict, Any, List, Tuple, AsyncGenerator

# --- Import your new image utils ---
from ..utils.image_utils import analyze_page_meta_from_image, generate_difference_images
from ..utils.text_utils import get_structured_diff_json
import cv2

# Import all other custom modules
from ..utils.config_loader import load_settings
from ..utils.file_utils import TemporaryFileHandler
from ..ai.llm.client import LLMService
from ..ai.llm.prompts import (
    get_ns_document_analysis_prompt_holistic,
    get_multimodal_audit_prompt
)
from ..ai.llm.schemas import (
    PageHolisticAnalysis,
    PageAuditResult,
    AuditedInput
)
from ..ai.ocr.client import extract_text_from_image, OcrAPIError
from .exceptions import PageCountMismatchError, ContentMismatchError, DocumentVerificationError
from .schemas import VerificationReport


# --- Setup ---
logger = logging.getLogger(__name__)
APP_SETTINGS = load_settings()
SECRETS = APP_SETTINGS['secrets']
CONFIG = APP_SETTINGS['config']
LLM_CLIENT = LLMService(
    api_key=SECRETS['llm_api_key'],
    model=SECRETS['llm_model_name'],
    base_url=SECRETS['llm_api_url'],
    max_context_tokens=CONFIG['ai_services']['llm'].get('max_context_tokens', 64000),
    max_img_height=CONFIG['ai_services']['llm'].get('max_img_height')
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


# --- MODIFIED: Function now accepts the handler and has no try/finally block ---
async def run_verification_workflow(
    handler: TemporaryFileHandler, # <-- Accepts the handler object
    nsv_file_bytes: bytes, 
    nsv_filename: str, 
    sv_file_bytes: bytes, 
    sv_filename: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Orchestrates the verification workflow using a pre-existing temp file handler.
    Cleanup is managed by the calling API endpoint's background task.
    """
    try:
        # The handler is already set up, so we can use it immediately.
        yield {"type": "status_update", "message": f"Processing with Request ID: {handler.request_id}"}
        await asyncio.sleep(0.01)
        
        debug_output_path = Path(handler.temp_dir) / "debug_outputs"
        debug_output_path.mkdir(exist_ok=True)

        yield {"type": "status_update", "message": f"Saving original document: {nsv_filename}"}
        await asyncio.sleep(0.01)
        nsv_path = handler.save_bytes_as_file(nsv_file_bytes, nsv_filename)

        yield {"type": "status_update", "message": f"Saving signed document: {sv_filename}"}
        await asyncio.sleep(0.01)
        sv_path = handler.save_bytes_as_file(sv_file_bytes, sv_filename)

        yield {"type": "status_update", "message": "Extracting pages from original document..."}
        await asyncio.sleep(0.01)
        nsv_page_bundles = handler.extract_content_per_page(nsv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])

        yield {"type": "status_update", "message": "Extracting pages from signed document..."}
        await asyncio.sleep(0.01)
        sv_page_bundles = handler.extract_content_per_page(sv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        _save_debug_json(nsv_page_bundles, "step_1_nsv_page_bundles.json", debug_output_path)
        _save_debug_json(sv_page_bundles, "step_1_sv_page_bundles.json", debug_output_path)

        # MODIFIED: Instead of raising an error, yield a failure message and stop.
        if len(nsv_page_bundles) != len(sv_page_bundles):
            error_message = f"Page count mismatch: Original document has {len(nsv_page_bundles)} pages, while the signed document has {len(sv_page_bundles)} pages."
            logger.error(error_message)
            yield {
                "type": "verification_failed",
                "data": { "final_status": "Failure", "message": error_message }
            }
            return # Stop the generator

        yield {"type": "status_update", "message": f"Found {len(nsv_page_bundles)} pages. Starting Stage 1: Requirement Analysis..."}
        await asyncio.sleep(0.01)
        
        requirements_map: Dict[int, PageHolisticAnalysis] = {}
        for page_bundle in nsv_page_bundles:
            page_num = page_bundle['page_num']
            page_img = page_bundle["image_path"]
            
            yield {"type": "status_update", "message": f"Analyzing requirements for Page {page_num}..."}
            await asyncio.sleep(0.01)
            try:
                prompt = get_ns_document_analysis_prompt_holistic(page_bundle['markdown_text'])
                page_req_result = LLM_CLIENT.invoke_vision_structured(prompt=prompt, image_path=page_img, response_model=PageHolisticAnalysis)
                requirements_map[page_num] = page_req_result
            except Exception as e:    
                logger.error(f"Error analyzing page {page_num}: {e}", exc_info=True)
                yield {"type": "error", "message": "Server Critical Error during requirement analysis. Please Try Again Later. (GPU Overload)"}
                return # Stop the generator
            
            result_payload = page_req_result.model_dump()
            result_payload['page_number'] = page_num
            
            yield { "type": "process_step_result", "data": { "stage_id": "requirement_analysis", "stage_title": "Stage 1: Requirement Analysis", "result": result_payload } }
            await asyncio.sleep(0.01)
        
        _save_debug_json(requirements_map, "step_2_requirements_map.json", debug_output_path)
        yield {"type": "status_update", "message": "Stage 1 analysis complete."}
        await asyncio.sleep(0.01)

        # --- Stage 2: Page-by-Page Content Verification ---
        yield {"type": "status_update", "message": "Starting Stage 2: Content Verification..."}
        await asyncio.sleep(0.01)

        for page_num in range(1, len(nsv_page_bundles) + 1):
            yield {"type": "status_update", "message": f"Verifying content for Page {page_num}..."}
            await asyncio.sleep(0.01)
            content_type=None

            page_requirements = requirements_map.get(page_num)
            nsv_bundle = nsv_page_bundles[page_num - 1]
            sv_bundle = sv_page_bundles[page_num - 1]

            nsv_image_path = nsv_bundle['image_path']
            sv_image_path = sv_bundle['image_path']
            sv_markdown = sv_bundle['markdown_text']
            nsv_markdown = nsv_bundle['markdown_text']
                
            nsv_img = cv2.imread(str(nsv_image_path))
            sv_img = cv2.imread(str(sv_image_path))

            
            result_payload = {
                "page_number": page_num,
                "content_match": None, # Will be set later
                "summary": "",
                "original_diff_url": None,
                "signed_diff_url": None,
            }
                
            if not sv_markdown or not sv_markdown.strip():
                yield {"type": "status_update", "message": f"Signed page {page_num} is scanned. Using OCR..."}
                await asyncio.sleep(0.01)
                content_type="scanned"
                try:
                    # NOTE: This part is simplified for brevity as content is not used later
                    sv_content=extract_text_from_image(sv_image_path, api_url=SECRETS['ocr_url'])
                    nsv_content=extract_text_from_image(nsv_image_path, api_url=SECRETS['ocr_url'])
                except OcrAPIError:
                    logger.warning(f"OCR processing failed for page {page_num}. Content analysis may be limited.")
                    yield {"type": "error", "message": f"AI model failed during audit of page {page_num}. Please try again. (GPU Overload)."}
                    return
            else:
                content_type="Digital"
                sv_content = sv_markdown
                nsv_content = nsv_markdown

            content_diff=get_structured_diff_json(nsv_content,sv_content)
            _save_debug_json({"nsv_content": nsv_content, "sv_content": sv_content,"difference":content_diff}, f"step_3_audit_input_{page_num}.json", debug_output_path)


            # --- NEW: Short-circuit logic for when no textual differences are found ---
            if not content_diff or content_diff == '[]':
                yield {"type": "status_update", "message": f"No textual changes detected on Page {page_num}. Assessing based on requirements..."}
                await asyncio.sleep(0.01)

                # BRANCH 1: No changes AND no inputs were required. This page is verified.
                if not page_requirements or not page_requirements.required_inputs:
                    result_payload["content_match"] = True
                    result_payload["verification_status"] = "Verified"
                    result_payload["summary"] = "Verified. No textual changes were detected on this static page."
                    
                    # Yield the result for Stage 2 and continue
                    yield {
                        "type": "process_step_result",
                        "data": {
                            "stage_id": "content_verification",
                            "stage_title": "Stage 2: Content Verification",
                            "result": result_payload
                        }
                    }
                    await asyncio.sleep(0.01)
                    continue # Success for this page, move to the next one.

                # BRANCH 2: No changes BUT inputs WERE required. This is a definitive failure.
                else:
                    failure_message = f"Audit failed on page {page_num}: Document is unchanged, but inputs were required."
                    yield {"type": "status_update", "message": failure_message}
                    await asyncio.sleep(0.01)

                    # Manually construct the audit result without calling the LLM
                    unfulfilled_inputs = [
                        AuditedInput(
                            input_type=req.input_type,
                            marker_text=req.marker_text,
                            is_fulfilled=False,
                            audit_notes="Verification failed. The document content is identical to the original, so this required input was not fulfilled."
                        ) for req in page_requirements.required_inputs
                    ]
                    
                    manual_audit_result = PageAuditResult(
                        page_number=page_num,
                        page_status="Input Missing",
                        required_inputs=unfulfilled_inputs,
                        content_differences=[]
                    )

                    # Yield the manually created audit result
                    yield {
                        "type": "process_step_result",
                        "data": {
                            "stage_id": "multimodal_audit",
                            "stage_title": "Stage 3: Multi-Modal Audit",
                            "result": manual_audit_result.model_dump()
                        }
                    }
                    await asyncio.sleep(0.01)
                    
                    # Yield the final failure message and stop the entire workflow
                    yield {"type": "verification_failed", "data": {"final_status": "Failure", "message": failure_message}}
                    return


            # --- EXISTING LOGIC (WRAPPED IN ELSE): Only run if there ARE content differences ---
            else:
                # BRANCH 1: Page was supposed to be static (no inputs), but changes were found.
                if page_requirements and not page_requirements.required_inputs and content_type=="Digital":
                    analysis_result = analyze_page_meta_from_image(nsv_img, sv_img)
                    result_payload["content_match"] = analysis_result["content_match"]

                    if not analysis_result["content_match"]:
                        result_payload["verification_status"] = "Discrepancy-Found"
                        bboxes = analysis_result["difference_bboxes"]
                        summary_message = f"Unauthorized visual change detected in {len(bboxes)} area(s) on a page that should be static."
                        result_payload["summary"] = summary_message
                        
                        diff_output_dir = handler.temp_dir / f"page_{page_num:02d}_diffs"
                        try:
                            original_diff_path, signed_diff_path = generate_difference_images(
                                original_img=nsv_img, signed_img=sv_img, bboxes=bboxes, output_dir=diff_output_dir
                            )
                            result_payload["original_diff_url"] = f"/temp/{handler.request_id}/{original_diff_path.relative_to(handler.temp_dir)}"
                            result_payload["signed_diff_url"] = f"/temp/{handler.request_id}/{signed_diff_path.relative_to(handler.temp_dir)}"
                        except Exception as e:
                            logger.error(f"Failed to generate difference images for page {page_num}: {e}")
                        
                        yield { "type": "process_step_result", "data": { "stage_id": "content_verification", "stage_title": "Stage 2: Content Verification", "result": result_payload } }
                        await asyncio.sleep(0.01)
                        yield { "type": "verification_failed", "data": { "final_status": "Failure", "message": f"Verification failed: {summary_message}" } }
                        return

                    else:
                        result_payload["verification_status"] = "Verified"
                        result_payload["summary"] = "Verified. No visual differences were detected on this static page."

                # BRANCH 2: Page was dynamic (inputs required), and changes were found. Audit them.
                else:
                    yield {"type": "status_update", "message": f"Starting multi-modal audit for Page {page_num}..."}
                    await asyncio.sleep(0.01)
                    
                    prompt = get_multimodal_audit_prompt(
                        content_difference=content_diff,
                        required_inputs_analysis=page_requirements.model_dump(),
                        page_number=page_num
                    )

                    try:
                        audit_result = LLM_CLIENT.invoke_image_compare_structured(
                            prompt=prompt,
                            image_path_1=nsv_image_path,
                            image_path_2=sv_image_path,
                            response_model=PageAuditResult
                        )
                        _save_debug_json(audit_result, f"step_3_audit_result_page_{page_num}.json", debug_output_path)

                    except Exception as e:
                        logger.error(f"Critical error during multi-modal audit for page {page_num}: {e}", exc_info=True)
                        yield {"type": "error", "message": f"AI model failed during audit of page {page_num}. Please try again. (GPU Overload)."}
                        return

                    yield {
                        "type": "process_step_result",
                        "data": {
                            "stage_id": "multimodal_audit",
                            "stage_title": "Stage 3: Multi-Modal Audit",
                            "result": audit_result.model_dump()
                        }
                    }
                    await asyncio.sleep(0.01)

                    if audit_result.page_status != "Verified":
                        failure_message = f"Audit failed on page {page_num}. Status: '{audit_result.page_status}'"
                        yield {"type": "verification_failed", "data": {"final_status": "Failure", "message": failure_message}}
                        return
        
        yield { "type": "workflow_complete", "data": { "final_status": "Success", "message": "All planned stages have finished." } }
        await asyncio.sleep(0.01)
            
    # MODIFIED: Removed handled exceptions from this block
    except DocumentVerificationError as e:
        logger.error(f"A known document processing error occurred: {e}")
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        logger.exception("An unexpected error occurred during the verification workflow.")
        yield {"type": "error", "message": f"An unexpected server error occurred. Please check system logs."}