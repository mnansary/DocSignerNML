import os
import sys
from logging.config import fileConfig

# Import create_engine directly
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# --- Start of Custom Modifications ---

# Add the 'app' directory to the system path to find our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your models' Base object and the application settings
from app.db.base import Base
from app.core.config import settings

# Import all your models here so that Base's metadata is populated
from app.models.envelope import Envelope
from app.models.recipient import Recipient
from app.models.field import Field
from app.models.audit_trail import AuditTrail

# This is the target metadata that Alembic will use to generate migrations
target_metadata = Base.metadata

# --- End of Custom Modifications ---

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use the URL directly from our application's settings
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Bypassing the faulty config parsing by creating the engine directly
    # from our reliable application settings.
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()