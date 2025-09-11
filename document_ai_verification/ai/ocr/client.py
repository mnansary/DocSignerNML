# document_ai_verification/ai/ocr/client.py

import logging
from pathlib import Path
import os

import requests
from pydantic import ValidationError
from dotenv import load_dotenv

from .schemas import OCRResponse

# Set up a logger for this module. It will be configured in the main block for standalone testing.
logger = logging.getLogger(__name__)

class OcrAPIError(Exception):
    """Custom exception for OCR API errors."""
    pass

def extract_text_from_image(
    image_path: Path,
    api_url: str
) -> OCRResponse:
    """
    Calls the English OCR API to extract text from an image.

    Args:
        image_path (Path): The local path to the image file to process.
        api_url (str): The full URL of the OCR endpoint.

    Returns:
        OCRResponse: A Pydantic object containing the parsed API response.

    Raises:
        OcrAPIError: If the API call fails, the response is invalid,
                     or a non-200 status code is returned.
    """
    if not image_path.is_file():
        msg = f"Image file not found at path: {image_path}"
        logger.error(msg)
        raise OcrAPIError(msg)

    logger.info(f"Sending request to OCR API at {api_url} for image {image_path.name}")

    try:
        with open(image_path, "rb") as image_file:
            # The 'files' dictionary specifies the form field name ('file') and the file object
            files = {"file": (image_path.name, image_file, "image/png")}
            
            # Set a reasonable timeout as OCR can be a long-running task
            response = requests.post(api_url, files=files, timeout=90)
            
            # Raise an HTTPError for bad responses (4xx or 5xx)
            response.raise_for_status()
            
            response_json = response.json()
            
            # Validate and parse the response using the Pydantic model
            return OCRResponse.model_validate(response_json)

    except requests.exceptions.Timeout:
        msg = f"OCR API request timed out after 90 seconds."
        logger.error(msg)
        raise OcrAPIError(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Network error calling OCR API: {e}"
        logger.error(msg)
        raise OcrAPIError(msg) from e
    except (ValidationError, KeyError, TypeError) as e:
        msg = f"Failed to validate or parse OCR API response. Raw response might be: {response.text[:200]}... Error: {e}"
        logger.error(msg)
        raise OcrAPIError(msg) from e
    except Exception as e:
        msg = f"An unexpected error occurred in extract_text_from_image: {e}"
        logger.error(msg)
        raise OcrAPIError(msg) from e

# ===================================================================
# Standalone Test Block
# ===================================================================
if __name__ == "__main__":
    # Configure basic logging to see output in the console
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Step 1: Setup your environment ---
    # Ensure you have a .env file in the project root with your OCR_URL
    # Example .env content:
    # OCR_URL="http://myapi.com/enocr"
    
    # We navigate up two directories to find the project root where .env is located
    project_root = Path(__file__).resolve().parent.parent.parent
    dotenv_path = project_root / ".env"
    
    if not dotenv_path.exists():
        print(f"❌ Critical Error: .env file not found at {dotenv_path}")
        print("Please create it with the necessary OCR_URL variable.")
    else:
        load_dotenv(dotenv_path=dotenv_path)
        print(f"✅ Loaded environment variables from: {dotenv_path}")

    # --- Step 2: Configure your test image ---
    # Create a test image or update the path below to an existing image file.
    # For this example, we'll look for 'sample_document.png' in the project root.
    sample_image_path = project_root / "sample_document.png"

    # --- Step 3: Run the test ---
    ocr_api_url = os.getenv("OCR_URL")

    if not ocr_api_url:
        print("\n❌ Test Skipped: OCR_URL is not defined in your .env file.")
    elif not sample_image_path.exists():
        print(f"\n❌ Test Skipped: Sample image not found.")
        print(f"Please place a test image named 'sample_document.png' in the project root: {project_root}")
    else:
        print("\n--- Running OCR Client Test ---")
        print(f"API Endpoint: {ocr_api_url}")
        print(f"Image Path:   {sample_image_path}")
        
        try:
            # Call the main function to test the API
            ocr_response = extract_text_from_image(
                image_path=sample_image_path,
                api_url=ocr_api_url
            )
            
            print("\n✅ API Call Successful! Response format is valid.")
            print("-" * 20)
            print(f"Status: {ocr_response.status}")
            print(f"Plain Text Preview: '{ocr_response.plain_text[:100].replace(chr(10), ' ')}...'")
            print(f"Detailed Data Items Found: {len(ocr_response.detailed_data)}")
            
            # To see the full parsed structure, you can uncomment the next line:
            # print("\nFull Parsed Response:")
            # print(ocr_response.model_dump_json(indent=2))

        except OcrAPIError as e:
            print(f"\n❌ API Call Failed: {e}")