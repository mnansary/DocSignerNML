from fastapi import APIRouter
from . import envelopes, signing, verification # Uncomment 'verification'

api_router = APIRouter()

# Include the routers from the individual endpoint files
api_router.include_router(envelopes.router, prefix="/envelopes", tags=["Envelopes"])
api_router.include_router(signing.router, prefix="/sign", tags=["Signing"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])