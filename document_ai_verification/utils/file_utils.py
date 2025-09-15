# document_ai_verification/utils/file_utils.py

import logging
import shutil
import io
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

# --- Pre-requisite Check & Imports ---
try:
    from pdf2image import convert_from_path
    from pypdf import PdfReader, PdfWriter
    from markitdown import MarkItDown
    from fastapi import UploadFile
except ImportError:
    import sys
    sys.exit("Required libraries not found. Run: pip install -r requirements.txt")

# --- Setup ---
logger = logging.getLogger(__name__)

# CRITICAL REMINDER: pdf2image requires the 'poppler' utility to be installed on the system.
# Ubuntu/Debian: sudo apt-get install poppler-utils
# Mac (Homebrew): brew install poppler

class TemporaryFileHandler:
    """
    Manages the lifecycle of temporary files for a single verification request.
    Can be used as a context manager (`with`) or controlled manually (`setup`/`cleanup`).
    """
    def __init__(self, base_path: str = "temp_files"):
        self.request_id = str(uuid4())
        self.temp_dir = Path(base_path) / self.request_id

    def setup(self):
        """Creates the temporary directory."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created temporary directory for request: {self.temp_dir}")

    def cleanup(self):
        """Removes the temporary directory and all its contents."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Successfully cleaned up temporary directory: {self.temp_dir}")
        except OSError as e:
            logger.error(f"Failed to clean up temporary directory {self.temp_dir}: {e}")
        
    def __enter__(self):
        """Context manager entry point. Calls setup."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point. Calls cleanup."""
        self.cleanup()
            
    # --- NEW: Method to save raw bytes to a file ---
    def save_bytes_as_file(self, file_bytes: bytes, filename: str) -> Path:
        """Saves a byte string to a file in the temporary directory."""
        file_path = self.temp_dir / filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)
        logger.info(f"Saved bytes to file '{filename}' at '{file_path}'")
        return file_path
    
    # This method can now be deprecated or removed if you only use the byte-based approach
    async def save_upload_file(self, upload_file: UploadFile) -> Path:
        """Saves a FastAPI UploadFile to the temporary directory."""
        await upload_file.seek(0)
        file_path = self.temp_dir / upload_file.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            logger.info(f"Saved uploaded file '{upload_file.filename}' to '{file_path}'")
            return file_path
        finally:
            pass

    def extract_content_per_page(self, pdf_path: Path, dpi: int = 300) -> List[Dict[str, Any]]:
        """
        The master utility for multi-modal PDF processing. For each page, it extracts:
        1. A high-quality PNG image.
        2. Structured Markdown text (if the page is digital).
        """
        # ... (The rest of this function remains exactly the same) ...
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        # --- Step 1: Convert all pages to images in a single, efficient batch ---
        image_output_dir = self.temp_dir / f"{pdf_path.stem}_images"
        image_output_dir.mkdir(exist_ok=True)
        logger.info(f"Batch converting '{pdf_path.name}' to images...")
        try:
            convert_from_path(
                pdf_path=pdf_path, dpi=dpi, output_folder=image_output_dir,
                fmt="png", thread_count=4, output_file=f"{pdf_path.stem}_page_"
            )
            image_paths = sorted(list(image_output_dir.glob("*.png")))
            logger.info(f"Successfully converted PDF to {len(image_paths)} images.")
        except Exception as e:
            logger.error(f"Critical error during image conversion. Check Poppler installation. Error: {e}")
            raise

        # --- Step 2: Extract Markdown per page using an efficient in-memory process ---
        logger.info(f"Extracting Markdown from '{pdf_path.name}' page by page (in-memory)...")
        markdown_texts = []
        md_converter = MarkItDown()
        try:
            reader = PdfReader(pdf_path)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                
                with io.BytesIO() as bytes_stream:
                    writer.write(bytes_stream)
                    bytes_stream.seek(0)
                    
                    result = md_converter.convert_stream(bytes_stream)
                    markdown_texts.append(result.text_content or "")
            
            logger.info(f"Successfully extracted Markdown from {len(markdown_texts)} pages.")
        except Exception as e:
            logger.error(f"Error during in-memory Markdown extraction: {e}")
            markdown_texts = [""] * len(image_paths)

        # --- Step 3: Combine results into the final structured list ---
        if len(image_paths) != len(markdown_texts):
            raise ValueError("Mismatch between number of images and extracted markdown pages.")

        page_bundles = []
        for i in range(len(image_paths)):
            page_bundles.append({
                "page_num": i + 1,
                "markdown_text": markdown_texts[i],
                "image_path": image_paths[i]
            })
            
        return page_bundles


# ===================================================================
# Standalone Test Block (No changes needed)
# ===================================================================
if __name__ == "__main__":
    # ... (your test block will continue to work as is) ...
    pass