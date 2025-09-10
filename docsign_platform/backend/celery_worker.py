import os
import sys

# Add the current directory to the Python path.
# This ensures that 'app' can be imported.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- NEW AND CRUCIAL STEP ---
# Import the 'base' module from our db package.
# This action ensures that all SQLAlchemy models are imported and registered
# with the metadata before any task that uses them is called.
from app.db import base
# --- END OF NEW STEP ---

from app.celery_app import celery_app