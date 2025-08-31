from fastapi import FastAPI

from app.api.routers import users, login, templates, documents, signing

app = FastAPI(title="Document Signing Platform", version="0.1.0")


@app.get("/")
def read_root():
    """A simple endpoint to confirm the API is running."""
    return {"message": "Welcome to the Document Signing Platform API"}


app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(login.router, prefix="/api/v1/login", tags=["login"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(signing.router, prefix="/api/v1/signing", tags=["signing"])
