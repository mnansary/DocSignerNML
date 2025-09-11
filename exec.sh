#!/bin/bash

# --- Script to create the project structure for document_ai_verification ---

# Define the root directory name for the project
PROJECT_NAME="document_ai_verification"

echo "--- Starting Project Initialization ---"

# Create the main project directory
mkdir -p "$PROJECT_NAME"
echo "✅ Created root directory: $PROJECT_NAME"

# Use a subshell to create the structure inside the project directory
(
  # Change into the project directory
  cd "$PROJECT_NAME" || exit

  # Create all nested directories in a single command
  echo "--> Creating subdirectories..."
  mkdir -p \
    ai/llm \
    ai/ocr \
    ai/sign \
    core \
    api \
    utils
  echo "✅ Subdirectories created."

  # Create all the blank files in a single command
  echo "--> Creating blank project files..."
  touch \
    .env \
    config.yml \
    requirements.txt \
    README.md \
    gradio_app.py \
    ai/__init__.py \
    ai/llm/__init__.py \
    ai/llm/client.py \
    ai/llm/prompts.py \
    ai/llm/schemas.py \
    ai/ocr/__init__.py \
    ai/ocr/client.py \
    ai/ocr/schemas.py \
    ai/sign/__init__.py \
    ai/sign/client.py \
    ai/sign/schemas.py \
    core/__init__.py \
    core/verification_service.py \
    core/schemas.py \
    core/exceptions.py \
    api/__init__.py \
    api/main.py \
    utils/__init__.py \
    utils/config_loader.py \
    utils/file_utils.py
  echo "✅ Blank files created."
)

echo "" # Newline for readability
echo "--- Project structure for '$PROJECT_NAME' created successfully! ---"
echo "You can now start populating the configuration files and source code."