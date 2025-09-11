# document_ai_verification/core/verification_service.py

import logging
from pathlib import Path
import json
from typing import Dict, Any, List

from fastapi import UploadFile

# Import all our custom modules
from ..utils.config_loader import load_settings
from ..utils.file_utils import TemporaryFileHandler
from ..ai.llm.client import LLMService
from ..ai.llm.prompts import (
    get_ns_document_analysis_prompt,
    get_vllm_ocr_prompt,
    get_multimodal_audit_prompt,
)
# --- FIX 1: Import the correct schemas ---
from ..ai.llm.schemas import (
    PageInputAnalysis,
    VllmOcrResult,
    PageAuditResult  # <-- Import the correct class
)
from ..ai.ocr.client import extract_text_from_image, OcrAPIError
from .exceptions import PageCountMismatchError
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

async def run_verification_workflow(nsv_file: UploadFile, sv_file: UploadFile) -> VerificationReport:
    """
    Orchestrates the new "Multi-Modal Auditor" verification workflow.
    """
    overall_status = "Success"
    # --- FIX 3: Use the correct type hint ---
    page_results: List[PageAuditResult] = []

    with TemporaryFileHandler(base_path=CONFIG['application']['temp_storage_path']) as handler:
        logger.info(f"Starting multi-modal audit for request ID: {handler.request_id}")
        
        nsv_path = await handler.save_upload_file(nsv_file)
        sv_path = await handler.save_upload_file(sv_file)
        
        # --- 1. Extract Multi-Modal Content from Both Documents ---
        logger.info("Extracting multi-modal content from NSV...")
        nsv_page_bundles = handler.extract_content_per_page(nsv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        logger.info("Extracting multi-modal content from SV...")
        sv_page_bundles = handler.extract_content_per_page(sv_path, dpi=CONFIG['application']['pdf_to_image_dpi'])
        
        if len(nsv_page_bundles) != len(sv_page_bundles):
            raise PageCountMismatchError(f"NSV has {len(nsv_page_bundles)} pages, SV has {len(sv_page_bundles)} pages.")

        # --- 2. Initial Analysis of NSV to Determine "What to Look For" ---
        logger.info("Phase 1: Analyzing NSV text to build requirements map...")
        requirements_map: Dict[int, PageInputAnalysis] = {}
        for page_bundle in nsv_page_bundles:
            page_num = page_bundle['page_num']
            prompt = get_ns_document_analysis_prompt(page_bundle['markdown_text'])
            requirements_map[page_num] = LLM_CLIENT.invoke_structured(
                prompt=prompt, response_model=PageInputAnalysis
            )

        # --- 3. Page-by-Page Multi-Modal Audit ---
        logger.info("Phase 2: Performing page-by-page multi-modal audit...")
        for page_num in range(1, len(nsv_page_bundles) + 1):
            nsv_bundle = nsv_page_bundles[page_num - 1]
            sv_bundle = sv_page_bundles[page_num - 1]
            page_requirements = requirements_map[page_num]

            # --- 3a. Gather the Evidence Inputs ---
            nsv_markdown = nsv_bundle['markdown_text']
            sv_markdown = sv_bundle['markdown_text']
            sv_image_path = sv_bundle['image_path']
            
            if not sv_markdown or not sv_markdown.strip():
                logger.info(f"Page {page_num} of SV appears scanned. Using VLLM for OCR...")
                try:
                    ocr_prompt = get_vllm_ocr_prompt()
                    vllm_ocr_result = LLM_CLIENT.invoke_vision_structured(
                        prompt=ocr_prompt,
                        image_path=sv_image_path,
                        response_model=VllmOcrResult
                    )
                    sv_markdown = vllm_ocr_result.markdown_content
                    logger.info(f"Successfully generated Markdown for scanned page {page_num}.")
                except Exception as e:
                    logger.error(f"VLLM-based OCR failed for page {page_num}: {e}")
                    sv_markdown = "<!-- VLLM OCR failed for this page -->"

            try:
                sv_ocr_text = extract_text_from_image(sv_image_path, api_url=SECRETS['ocr_url']).plain_text
            except OcrAPIError as e:
                logger.warning(f"Standard OCR failed for page {page_num}: {e}. Proceeding without it.")
                sv_ocr_text = "Standard OCR failed to process this page."
            
            # --- 3b. Execute the Final Audit with the VLLM ---
            logger.info(f"Submitting evidence package for page {page_num} to VLLM for final audit...")
            audit_prompt = get_multimodal_audit_prompt(
                nsv_markdown=nsv_markdown,
                sv_markdown=sv_markdown,
                sv_ocr_text=sv_ocr_text,
                required_inputs_analysis=page_requirements.model_dump(),
                page_number=page_num
            )
            
            # --- FIX 4: Corrected "Failsafe" block ---
            # Directly get the structured Pydantic object. The LLM has already determined the status.
            page_audit_result: PageAuditResult = LLM_CLIENT.invoke_vision_structured(
                prompt=audit_prompt,
                image_path=sv_image_path, 
                response_model=PageAuditResult
            )

            # There's no need to manually rebuild the object or recalculate the status.
            # We trust the LLM's structured output which adheres to the PageAuditResult schema.
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
        return report