# document_ai_verification/core/exceptions.py

class DocumentVerificationError(Exception):
    """
    Base exception for all custom errors related to the verification process.
    Catching this will catch any of our specific verification errors.
    """
    def __init__(self, message="An error occurred during document verification."):
        self.message = message
        super().__init__(self.message)

class PageCountMismatchError(DocumentVerificationError):
    """
    Raised when the non-signed and signed documents have a different number of pages.
    This is a critical, early-stage validation failure.
    """
    def __init__(self, message="Document page counts do not match."):
        super().__init__(message)

class ContentMismatchError(DocumentVerificationError):
    """
    Raised when the static, non-input content of a page appears to have been altered.
    This could indicate tampering.
    """
    def __init__(self, message="Static content on a page does not match the original document."):
        super().__init__(message)

class VerificationFailureError(DocumentVerificationError):
    """
    Raised when a specific, required input (like a signature or date) is found
    to be missing or unfulfilled on the signed document.
    This is the most common expected failure.
    """
    def __init__(self, message="A required input was not fulfilled."):
        super().__init__(message)