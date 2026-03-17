from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
import os
from pathlib import Path
import importlib.util

# Add project source to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Load db_models directly to avoid triggering __init__.py
spec = importlib.util.spec_from_file_location("db_models", src_path / "models" / "db_models.py")
db_models = importlib.util.module_from_spec(spec)
sys.modules["db_models"] = db_models
spec.loader.exec_module(db_models)

Base = db_models.Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override database URL from environment variable if set
# This allows different database paths for different environments (dev, staging, prod)
# Default: data/shrimp_market.db (relative to backend directory)
database_url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PATH")
if database_url:
    # Support both full URL and path-only formats
    if not database_url.startswith("sqlite"):
        database_url = f"sqlite:///{database_url}"
    config.set_main_option("sqlalchemy.url", database_url)
else:
    # Use default path: data/shrimp_market.db (same as in database.py)
    default_path = Path(__file__).parent.parent / "data" / "shrimp_market.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{default_path}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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
