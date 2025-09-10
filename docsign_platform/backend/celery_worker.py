import os
import sys

# Add the current directory to the Python path.
# This ensures that 'app' can be imported.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.celery_app import celery_app