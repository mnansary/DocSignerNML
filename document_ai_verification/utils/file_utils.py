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
    Primarily used for storing generated page images.
    """
    def __init__(self, base_path: str = "temp_files"):
        self.request_id = str(uuid4())
        self.temp_dir = Path(base_path) / self.request_id
        
    def __enter__(self):
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created temporary directory for request: {self.temp_dir}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"Successfully cleaned up temporary directory: {self.temp_dir}")
        except OSError as e:
            logger.error(f"Failed to clean up temporary directory {self.temp_dir}: {e}")
            
    async def save_upload_file(self, upload_file: UploadFile) -> Path:
        """Saves a FastAPI UploadFile to the temporary directory."""
        file_path = self.temp_dir / upload_file.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            logger.info(f"Saved uploaded file '{upload_file.filename}' to '{file_path}'")
            return file_path
        finally:
            await upload_file.close()

    def extract_content_per_page(self, pdf_path: Path, dpi: int = 300) -> List[Dict[str, Any]]:
        """
        The master utility for multi-modal PDF processing. For each page, it extracts:
        1. A high-quality PNG image.
        2. Structured Markdown text (if the page is digital).

        This is done efficiently by converting images in a single batch and then
        processing the PDF for Markdown entirely in-memory.

        Args:
            pdf_path (Path): Path to the source PDF file.
            dpi (int): Dots Per Inch for the output images.

        Returns:
            A list of dictionaries, where each dictionary represents a page and
            contains: { "page_num": int, "markdown_text": str, "image_path": Path }
        """
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
                
                # Create an in-memory binary stream
                with io.BytesIO() as bytes_stream:
                    writer.write(bytes_stream)
                    bytes_stream.seek(0) # Rewind the stream to the beginning
                    
                    # MarkItDown can convert from a stream directly
                    result = md_converter.convert_stream(bytes_stream)
                    markdown_texts.append(result.text_content or "")
            
            logger.info(f"Successfully extracted Markdown from {len(markdown_texts)} pages.")
        except Exception as e:
            logger.error(f"Error during in-memory Markdown extraction: {e}")
            # Fill with empty strings to avoid crashing if markdown fails but images succeed
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
# Standalone Test Block (Updated for the new function)
# ===================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def create_dummy_pdf(path: Path):
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        # To make it a 'digital' PDF, we must add some resource, even if no text is drawn.
        # This is a limitation of making a truly empty but valid PDF.
        # For this test, a real digital PDF (like the project README saved as PDF) would be better.
        writer.add_page(page) # Add a second blank page
        with open(path, "wb") as f:
            writer.write(f)
        print(f"Created a dummy 2-page PDF at '{path}'")

    print("--- Running New File Utils Test ---")
    
    try:
        with TemporaryFileHandler(base_path="test_temp_output") as handler:
            print(f"Handler created with temp directory: {handler.temp_dir}")
            
            dummy_pdf_path = handler.temp_dir / "dummy_doc.pdf"
            create_dummy_pdf(dummy_pdf_path)
            
            print("\n--> Testing multi-modal content extraction...")
            page_data_bundles = handler.extract_content_per_page(dummy_pdf_path, dpi=96)
            
            # Verification
            assert len(page_data_bundles) == 2, f"Expected 2 pages, got {len(page_data_bundles)}"
            print(f"✅ Correct number of page bundles returned: {len(page_data_bundles)}")
            
            first_page = page_data_bundles[0]
            assert "page_num" in first_page and first_page['page_num'] == 1
            assert "markdown_text" in first_page
            assert "image_path" in first_page and first_page['image_path'].exists()
            print(f"✅ First page bundle structure is correct.")
            print(f"  - Page Num: {first_page['page_num']}")
            print(f"  - Image Path: {first_page['image_path'].name}")
            print(f"  - Markdown Preview: '{first_page['markdown_text'][:100]}...'")

        assert not handler.temp_dir.exists()
        print("\n--> Testing Cleanup...")
        print("Cleanup successful. Temporary directory was removed.")
        print("\n✅ All new file utility tests passed!")

    except Exception as e:
        print(f"\n❌ Test Failed: An error occurred: {e}")