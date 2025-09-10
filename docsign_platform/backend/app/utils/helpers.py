import hashlib

def calculate_sha256(file_path: str) -> str:
    """
    Calculates the SHA-256 hash of a file.

    Args:
        file_path: The absolute path to the file.

    Returns:
        The hex digest of the file's hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read the file in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()