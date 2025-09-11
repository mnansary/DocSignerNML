# document_ai_verification/ai/sign/client.py

import logging
from pathlib import Path
import os
import sys

import requests
from pydantic import ValidationError
from dotenv import load_dotenv

# ===================================================================
# HOW TO RUN THIS FILE FOR TESTING:
#
# 1. Open your terminal.
# 2. Navigate to the ROOT of your project (the directory that CONTAINS 'document_ai_verification').
# 3. Run the following command:
#    python -m document_ai_verification.ai.sign.client
#
# DO NOT run `python document_ai_verification/ai/sign/client.py`. It will fail with an ImportError.
# ===================================================================

# This relative import is CORRECT for the application structure.
from .schemas import SignatureDetectionResponse

# Set up a logger for this module.
logger = logging.getLogger(__name__)

class SignatureAPIError(Exception):
    """Custom exception for signature detection API errors."""
    pass

def detect_signatures(
    image_path: Path,
    api_url: str
) -> SignatureDetectionResponse:
    """
    Calls the signature detection API to find signatures in an image.
    The API will use its default confidence and IoU thresholds.

    Args:
        image_path (Path): The local path to the image file to process.
        api_url (str): The full URL of the signature detection endpoint.

    Returns:
        SignatureDetectionResponse: A Pydantic object containing the parsed API response.

    Raises:
        SignatureAPIError: If the API call fails or the response is invalid.
    """
    if not image_path.is_file():
        msg = f"Image file not found at path: {image_path}"
        logger.error(msg)
        raise SignatureAPIError(msg)

    logger.info(f"Sending request to signature detection API ({api_url}) for {image_path.name}")

    try:
        with open(image_path, "rb") as image_file:
            files = {"file": (image_path.name, image_file, "image/png")}
            # The request no longer sends confidence or iou parameters.
            response = requests.post(api_url, files=files, timeout=60)
            response.raise_for_status()
            response_json = response.json()
            return SignatureDetectionResponse.model_validate(response_json)

    except requests.exceptions.Timeout:
        msg = f"Signature Detection API request timed out after 60 seconds."
        logger.error(msg)
        raise SignatureAPIError(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Network error calling Signature Detection API: {e}"
        logger.error(msg)
        raise SignatureAPIError(msg) from e
    except (ValidationError, KeyError, TypeError) as e:
        msg = f"Failed to validate or parse signature detection API response. Raw response: {response.text[:200]}... Error: {e}"
        logger.error(msg)
        raise SignatureAPIError(msg) from e
    except Exception as e:
        msg = f"An unexpected error occurred in detect_signatures: {e}"
        logger.error(msg)
        raise SignatureAPIError(msg) from e

# ===================================================================
# Standalone Test Block
# ===================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Step 1: Load Environment File ---
    project_root = Path(__file__).resolve().parent.parent.parent
    dotenv_path = project_root / ".env"

    if not dotenv_path.exists():
        print(f"❌ Critical Error: .env file not found at {dotenv_path}")
        sys.exit(1)

    load_dotenv(dotenv_path=dotenv_path)
    print(f"✅ Loaded environment variables from: {dotenv_path}")

    # --- Step 2: Configure Paths and Parameters ---
    sample_image_path = project_root / "sample_document.png"
    api_url = os.getenv("SIGNATURE_DETECTION_URL")

    # --- Step 3: Run the Test ---
    if not api_url:
        print("\n❌ Test Skipped: SIGNATURE_DETECTION_URL is not defined in your .env file.")
    elif not sample_image_path.exists():
        print(f"\n❌ Test Skipped: Sample image 'sample_document.png' not found in project root: {project_root}")
    else:
        print("\n--- Running Signature Detection Client Test ---")
        print(f"API Endpoint: {api_url}")
        print(f"Image Path:   {sample_image_path}")
        print("Note: Using API's default confidence and IoU thresholds.")
        
        try:
            # Call the simplified function
            response = detect_signatures(
                image_path=sample_image_path,
                api_url=api_url
            )
            
            print("\n✅ API Call Successful! Response format is valid.")
            print("-" * 20)
            print(f"Request ID: {response.request_id}")
            print(f"Signatures Found: {response.detection_count}")
            
            if response.detections:
                print("Detections:")
                for i, det in enumerate(response.detections):
                    print(f"  - Detection {i+1}: Box={det.box}, Confidence={det.confidence:.4f}")
            
        except SignatureAPIError as e:
            print(f"\n❌ API Call Failed: {e}")