from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router

# --- Application Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- Middleware Configuration ---

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- API Router Inclusion ---
app.include_router(api_router, prefix=settings.API_V1_STR)


# --- Static Files Mount (for serving the frontend) ---
# This serves the 'frontend' directory at the root URL.
# For example, a request to "/" will serve "frontend/index.html".
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")


# --- Health Check Endpoint ---
@app.get("/health")
def read_root():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}