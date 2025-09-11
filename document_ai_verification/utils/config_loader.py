# document_ai_verification/utils/config_loader.py

import os
from pathlib import Path
from functools import lru_cache
import logging
import sys

from dotenv import load_dotenv

# --- Pre-requisite Check ---
try:
    import yaml
except ImportError:
    # This is a critical dependency, so we exit if it's not found.
    sys.exit("PyYAML is not installed. Please install it with: pip install pyyaml")

# --- Setup ---
logger = logging.getLogger(__name__)

# Dynamically determine the project's root directory.
# This script is in '.../utils/config_loader.py', so the root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

@lru_cache(maxsize=None)
def load_settings() -> dict:
    """
    Loads all settings from .env and config.yml files, caching the result.

    This function is designed to be called once. The lru_cache decorator ensures
    that the files are not read from the disk on subsequent calls.

    Returns:
        dict: A nested dictionary containing all application settings.

    Raises:
        FileNotFoundError: If the .env or config.yml file is missing.
    """
    # --- 1. Load Secrets from .env file ---
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        msg = f"CRITICAL: Environment file (.env) not found at {env_path}. The application cannot start."
        logger.error(msg)
        raise FileNotFoundError(msg)
    
    load_dotenv(dotenv_path=env_path)
    
    secrets = {
        "llm_api_url": os.getenv("LLM_API_URL"),
        "llm_api_key": os.getenv("LLM_API_KEY", ""), # Default to empty string if not set
        "llm_model_name": os.getenv("LLM_MODEL_NAME"),
        "ocr_url": os.getenv("OCR_URL"),
    }
    
    # Validate that essential secrets are present
    for key, value in secrets.items():
        if key != "llm_api_key" and not value: # API key is optional
            msg = f"CRITICAL: Required secret '{key.upper()}' not found in .env file."
            logger.error(msg)
            raise ValueError(msg)

    # --- 2. Load Parameters from config.yml file ---
    config_path = PROJECT_ROOT / "config.yml"
    if not config_path.exists():
        msg = f"CRITICAL: Configuration file (config.yml) not found at {config_path}. The application cannot start."
        logger.error(msg)
        raise FileNotFoundError(msg)

    with open(config_path, "r") as f:
        app_config = yaml.safe_load(f)

    # --- 3. Combine and Return ---
    settings = {
        "secrets": secrets,
        "config": app_config
    }
    
    logger.info("Application settings loaded successfully.")
    return settings

# ===================================================================
# Standalone Test Block
# ===================================================================
if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("--- Running Config Loader Test ---")
    try:
        # Call the function to load and cache the settings
        app_settings = load_settings()
        
        print("\n✅ Settings loaded successfully!")
        
        # Pretty-print the loaded settings for verification
        # Using json.dumps for clean, indented output
        print("\n--- Loaded Settings ---")
        print(json.dumps(app_settings, indent=2))
        print("-----------------------")
        
        # You can access nested settings like this:
        print(f"\nExample Access:")
        print(f"LLM Model: {app_settings['secrets']['llm_model_name']}")
        print(f"PDF DPI:   {app_settings['config']['application']['pdf_to_image_dpi']}")

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Test Failed: Could not load settings. Reason: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")