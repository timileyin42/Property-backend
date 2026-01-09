from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
import time
from dateutil import tz

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Ensure UTC timezone is available
os.environ.setdefault("TZ", "UTC")
try:
    time.tzset()
except Exception:
    pass
tz.gettz("UTC")

from app.core.config import settings
from app.core.database import Base

# Import all models to ensure they're registered with Base
from app.models.user import User
from app.models.property import Property
from app.models.investment import Investment
from app.models.update import Update
from app.models.inquiry import PropertyInquiry
from app.models.occupancy import PropertyOccupancy
from app.models.revenue import PropertyRevenue
from app.models.distribution import EarningsDistribution
from app.models.investment_application import InvestmentApplication

# this is the Alembic Config object
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Custom type render function to handle DateTime(timezone=True)
def render_item(type_, obj, autogen_context):
    """Render types for autogenerate."""
    from sqlalchemy import DateTime
    if type_ == 'type' and isinstance(obj, DateTime):
        # Always render DateTime without timezone parameter to avoid Windows issues
        return "sa.DateTime()"
    return False

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


def process_revision_directives(context, revision, directives):
    """Process revision directives to fix timezone issues."""
    if config.cmd_opts and config.cmd_opts.autogenerate:
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            process_revision_directives=process_revision_directives,
            # Skip timezone rendering
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
