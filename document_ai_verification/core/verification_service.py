# document_ai_verification/core/verification_service.py

import logging
from pathlib import Path
import json
from typing import Dict, Any, List

from fastapi import UploadFile
import cv2
# Import all our custom modules
from ..utils.config_loader import load_settings
from ..utils.image_utils import analyze_page_meta_from_image
from ..utils.file_utils import TemporaryFileHandler
from ..ai.llm.client import LLMService
from ..ai.llm.prompts import (
    get_ns_document_analysis_prompt_holistic,
    get_multimodal_audit_prompt,
)
# --- FIX 1: Import the correct schemas ---
from ..ai.llm.schemas import (
    PageHolisticAnalysis,
    PageAuditResult  # <-- Import the correct class
)
from ..ai.ocr.client import extract_text_from_image, OcrAPIError
from .exceptions import PageCountMismatchError,ContentMismatchError
# --- FIX 2: Only import VerificationReport from core schemas ---
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

# --- ADDITION: Helper function to save debug JSON files ---
def _save_debug_json(data: Any, filename: str, output_path: Path):
    """Saves data to a JSON file, handling Pydantic models correctly."""
    filepath = output_path / filename
    try:
        # A simple converter to handle Pydantic models and other non-serializable types
        def json_converter(o):
            if hasattr(o, 'model_dump'):
                return o.model_dump()
            return f"<<non-serializable: {type(o).__name__}>>"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=json_converter)
        logger.info(f"Saved debug data to: {filepath}")
    except Exception as e:
        logger.error(f"Could not save debug file {filepath}. Error: {e}")


async def run_verification_workflow(nsv_file: UploadFile, sv_file: UploadFile) -> VerificationReport:
    """
    Orchestrates the new "Multi-Modal Auditor" verification workflow.
    """
    overall_status = "Success"
    # --- FIX 3: Use the correct type hint ---
    page_results: List[PageAuditResult] = []

    page_metas: List[Dict] =[]
    with TemporaryFileHandler(base_path=CONFIG['application']['temp_storage_path']) as handler:
        logger.info(f"Starting multi-modal audit for request ID: {handler.request_id}")
        
        # --- ADDITION: Create a dedicated folder for debug outputs ---
        debug_output_path = Path(handler.temp_dir) / "debug_outputs"
        debug_output_path.mkdir(exist_ok=True)
        logger.info(f"Debug outputs will be saved in: {debug_output_path}")

        nsv_path = await handler.save_upload_file(nsv_file)
        sv_path = await handler.save_upload_file(sv_file)
        
        # --- 1. Extract Multi-Modal Content from Both Documents ---
        logger.info("Extracting multi-modal content from NSV...")
        nsv_page_bundles = handler.extract_content_per_page(nsv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        logger.info("Extracting multi-modal content from SV...")
        sv_page_bundles = handler.extract_content_per_page(sv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        # --- DEBUG STEP 1: Save the extracted content bundles ---
        _save_debug_json(nsv_page_bundles, "step_1_nsv_page_bundles.json", debug_output_path)
        _save_debug_json(sv_page_bundles, "step_1_sv_page_bundles.json", debug_output_path)

        if len(nsv_page_bundles) != len(sv_page_bundles):
            raise PageCountMismatchError(f"NSV has {len(nsv_page_bundles)} pages, SV has {len(sv_page_bundles)} pages.")

        # --- 2. Initial Analysis of NSV to Determine "What to Look For" ---
        logger.info("Phase 1: Analyzing NSV text to build requirements map...")
        requirements_map: Dict[int, PageHolisticAnalysis] = {}
        for page_bundle in nsv_page_bundles:
            page_num = page_bundle['page_num']
            page_img = page_bundle["image_path"]
            prompt = get_ns_document_analysis_prompt_holistic(page_bundle['markdown_text'])
            page_req_result = LLM_CLIENT.invoke_vision_structured(
                prompt=prompt,image_path=page_img,response_model=PageHolisticAnalysis
            )
            requirements_map[page_num]=page_req_result
            yield page_num,page_req_result
        
        # --- DEBUG STEP 2: Save the generated requirements map ---
        _save_debug_json(requirements_map, "step_2_requirements_map.json", debug_output_path)

        # --- 3. Page-by-Page Multi-Modal Audit ---
        logger.info("Phase 2: Performing page-by-page multi-modal audit...")
        for page_num in range(1, len(nsv_page_bundles) + 1):
            page_meta={}
            nsv_bundle = nsv_page_bundles[page_num - 1]
            sv_bundle = sv_page_bundles[page_num - 1]
            page_requirements = requirements_map[page_num].model_dump()

            # --- 3a. Gather the Evidence Inputs ---
            sv_markdown = sv_bundle['markdown_text']
            nsv_markdown = nsv_bundle['markdown_text']
            nsv_image_path = sv_bundle['image_path']
            sv_image_path = sv_bundle['image_path']
                
            page_meta["page_num"]=page_num
            
            # if we do not have markdown
            if not sv_markdown or not sv_markdown.strip():
                page_meta["sv_type"]="scanned"
                logger.info(f"Page {page_num} of SV appears scanned. Using OCR...")
                try:
                    sv_content = extract_text_from_image(sv_image_path, api_url=SECRETS['ocr_url']).plain_text
                    nsv_content =extract_text_from_image(nsv_image_path, api_url=SECRETS['ocr_url']).plain_text
                except OcrAPIError:
                    logger.info("OCR API NOT WORKING")
            else:
                page_meta["sv_type"]="digital" 
                sv_content=sv_markdown
                nsv_content=nsv_markdown

            # ---------- handle digital documents -----------------
            if page_meta["sv_type"]=="digital":
                try:
                    nsv_img = cv2.imread(str(nsv_image_path))
                    sv_img = cv2.imread(str(sv_image_path))
                    page_meta=analyze_page_meta_from_image(nsv_img,sv_img,page_meta)
                    if not page_requirements['required_inputs'] and page_meta["difference"] and page_meta["content"]=="not_matching":
                        yield  nsv_img,sv_img,page_meta
                        raise ContentMismatchError("Content Mismatch Found")
                except Exception as e:
                    logger.error(f"Could Not Read and process images:{e}")
            else:
                page_meta["source"] = "not_matching"
                


            
            # --- 3b. Execute the Final Audit with the VLLM ---
            audit_prompt = get_multimodal_audit_prompt(
                nsv_markdown=nsv_markdown,
                sv_markdown=sv_markdown,
                sv_ocr_text=sv_ocr_text,
                required_inputs_analysis=page_requirements.model_dump(),
                page_number=page_num
            )
            
            # --- FIX 4: Corrected "Failsafe" block ---
            page_audit_result: PageAuditResult = LLM_CLIENT.invoke_vision_structured(
                prompt=audit_prompt,
                image_path=sv_image_path, 
                response_model=PageAuditResult
            )
            
            # --- DEBUG STEP 3b: Save the audit prompt and result for the current page ---
            audit_log = {
                "page_number": page_num,
                "audit_prompt_sent_to_llm": audit_prompt,
                "audit_result_from_llm": page_audit_result
            }
            _save_debug_json(audit_log, f"step_3b_page_{page_num:02d}_audit.json", debug_output_path)


            page_results.append(page_audit_result)
            
            if page_audit_result.page_status != "Verified":
                overall_status = "Failure"
                logger.warning(f"Page {page_num} failed verification with status: {page_audit_result.page_status}")
            else:
                logger.info(f"Page {page_num} successfully verified.")

        # --- 4. Construct the Final Report ---
        logger.info(f"Verification finished. Overall status: {overall_status}")
        report = VerificationReport(
            overall_status=overall_status,
            nsv_filename=nsv_file.filename,
            sv_filename=sv_file.filename,
            page_count=len(nsv_page_bundles),
            page_results=page_results
        )

        # --- DEBUG STEP 4: Save the final report ---
        _save_debug_json(report, "step_4_final_verification_report.json", debug_output_path)

        return report