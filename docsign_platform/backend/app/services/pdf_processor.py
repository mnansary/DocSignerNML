# Add these imports to the top of the file
import base64
import os
import uuid
from app.core.config import settings

# Add this function to the file
def save_signature_image(base64_string: str) -> str:
    """
    Decodes a Base64 string and saves it as a PNG image.

    Args:
        base64_string: The Base64 encoded image string (e.g., "data:image/png;base64,iVBOR...").

    Returns:
        The file path where the image was saved.
    """
    try:
        # Split the metadata from the actual data
        header, encoded = base64_string.split(",", 1)
        
        # Decode the Base64 data
        data = base64.b64decode(encoded)
        
        # Define the save path
        signatures_dir = os.path.join(settings.STORAGE_BASE_PATH, "signatures")
        os.makedirs(signatures_dir, exist_ok=True)
        
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.png"
        file_path = os.path.join(signatures_dir, filename)
        
        # Write the image file
        with open(file_path, "wb") as f:
            f.write(data)
            
        return file_path

    except (ValueError, TypeError, base64.binascii.Error) as e:
        # Handle potential errors with malformed Base64 strings
        raise ValueError(f"Invalid Base64 string for signature image: {e}")