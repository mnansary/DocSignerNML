from sqlalchemy.orm import declarative_base

# Create a base class for all declarative models
# All your database model classes (Envelope, Recipient, etc.) will inherit from this.
Base = declarative_base()