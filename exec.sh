# Create the root project folder and navigate into it
mkdir docsign_platform && cd docsign_platform

# --- Create Backend Structure (FastAPI specific) ---
echo "Creating FastAPI backend structure..."
mkdir -p backend/app/api/v1
mkdir -p backend/app/core
mkdir -p backend/app/crud
mkdir -p backend/app/db
mkdir -p backend/app/models
mkdir -p backend/app/schemas
mkdir -p backend/app/services
mkdir -p backend/app/tasks
mkdir -p backend/app/utils
mkdir -p backend/storage/originals backend/storage/signatures backend/storage/signed

# Create gitkeep files for empty storage directories
touch backend/storage/originals/.gitkeep
touch backend/storage/signatures/.gitkeep
touch backend/storage/signed/.gitkeep

# Create backend Python package files
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/core/__init__.py
touch backend/app/crud/__init__.py
touch backend/app/db/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/tasks/__init__.py
touch backend/app/utils/__init__.py

# Create API router files
touch backend/app/api/v1/api.py
touch backend/app/api/v1/envelopes.py
touch backend/app/api/v1/signing.py
touch backend/app/api/v1/verification.py

# Create core configuration file
touch backend/app/core/config.py

# Create CRUD files
touch backend/app/crud/crud_envelope.py
touch backend/app/crud/crud_recipient.py
touch backend/app/crud/crud_field.py

# Create database session file
touch backend/app/db/session.py
touch backend/app/db/base.py

# Create model files
touch backend/app/models/envelope.py
touch backend/app/models/recipient.py
touch backend/app/models/field.py
touch backend/app/models/audit_trail.py

# Create Pydantic schema files
touch backend/app/schemas/envelope.py
touch backend/app/schemas/recipient.py
touch backend/app/schemas/field.py
touch backend/app/schemas/message.py # For simple API messages
touch backend/app/schemas/token.py   # For signing tokens

# Create service files for your external APIs
touch backend/app/services/signature_service.py
touch backend/app/services/ocr_service.py
touch backend/app/services/llm_service.py
touch backend/app/services/pdf_processor.py # Renamed for clarity

# Create Celery task files
touch backend/app/tasks/finalize_document.py
touch backend/app/tasks/send_email.py

# Create utility files
touch backend/app/utils/helpers.py

# Create root backend files
touch backend/main.py
touch backend/requirements.txt

# --- Create Frontend Structure (No Changes) ---
echo "Creating frontend structure..."
mkdir -p frontend/assets/css frontend/assets/js frontend/assets/libs

# Create HTML files
touch frontend/index.html
touch frontend/setup.html
touch frontend/sign.html
touch frontend/verify.html

# Create CSS file
touch frontend/assets/css/style.css

# Create JavaScript files
touch frontend/assets/js/apiClient.js
touch frontend/assets/js/setup.js
touch frontend/assets/js/sign.js
touch frontend/assets/js/verify.js

# Placeholder for 3rd party libs
touch frontend/assets/libs/.gitkeep

# --- Create Root Project Files ---
echo "Creating root project files..."
touch .env
touch .gitignore

# --- Populate .gitignore ---
echo "Populating .gitignore..."
cat << EOF > .gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
pip-log.txt
pip-delete-this-directory.txt

# Environment variables
.env

# Storage - DO NOT commit user data
backend/storage/

# IDE / Editor specific
.idea/
.vscode/
*.swp

# OS specific
.DS_Store
Thumbs.db
EOF

echo ""
echo "Project structure and blank files created successfully for a FastAPI application."
echo ""
echo "Next steps:"
echo "1. Create a Python virtual environment: python -m venv venv"
echo "2. Activate it: source venv/bin/activate (on Mac/Linux) or venv\\Scripts\\activate (on Windows)"
echo "3. I will provide the content for 'backend/requirements.txt' for you to install."