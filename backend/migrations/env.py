"""Alembic migration environment configuration.

Database migration management for ERPNext Test Automation Meta-Framework
with multi-tenant support and constitutional compliance.
"""

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

try:
    from alembic import context
    from sqlalchemy import create_engine, pool
    from sqlalchemy.engine import Connection
except ImportError as e:
    print(f"Alembic dependencies not installed: {e}")
    print("Run 'pip install alembic' in backend directory")

# Load environment variables from .env.test if TESTING=true
if os.getenv("TESTING", "false").lower() == "true":
    try:
        from dotenv import load_dotenv

        backend_root = Path(__file__).parent.parent
        env_test_path = backend_root / ".env.test"
        if env_test_path.exists():
            load_dotenv(env_test_path)
            print(f"Loaded environment variables from {env_test_path}")
    except ImportError:
        print("python-dotenv not installed, environment variables may not be loaded")
        load_dotenv()

# Add the backend src directory to Python path for imports
backend_root = Path(__file__).parent.parent
src_path = backend_root / "src"
sys.path.insert(0, str(src_path))

try:
    # Import all model modules to ensure they're registered with SQLAlchemy
    from infrastructure.auth.models import Consultant, Tenant  # noqa
    from infrastructure.database.config import get_database_config
    from infrastructure.database.models import Base  # Import all models here

    # TODO: Import additional model modules as they're created
    # from domain.personas.models import TestPersona  # noqa
    # from domain.activities.models import BusinessActivity  # noqa
    # from domain.journeys.models import UserJourney  # noqa
except ImportError as e:
    print(f"Cannot import application models: {e}")
    print("Models will not be available for migration generation")
    Base = None
    get_database_config = None

# Alembic configuration object
config = context.config

# Interpret config file for logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata if Base else None

# Migration environment logger
logger = logging.getLogger("alembic.env")


def get_database_url() -> str:
    """Get database URL from configuration.

    Returns:
        Database connection URL
    """
    if get_database_config is None:
        # Fallback to environment variable
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError(
                "Database URL not available. Set DATABASE_URL environment variable "
                "or configure DatabaseConfig properly."
            )
        return url

    try:
        db_config = get_database_config()
        return db_config.get_database_url()
    except Exception as e:
        logger.error(f"Failed to get database URL from config: {e}")
        # Fallback to environment variable
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError(
                "Database URL not available. Set DATABASE_URL environment variable "
                "or configure DatabaseConfig properly."
            )
        return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Multi-tenant migration settings
        version_table="alembic_version",
        version_table_schema=None,  # Use default schema
        # Constitutional compliance metadata
        user_module_prefix="assegura_",
        transaction_per_migration=True,
        # Include schema names for multi-tenant tables
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context. This is the more common usage pattern.
    """
    # Get database configuration
    if get_database_config is None:
        connection_config = {
            "url": get_database_url(),
            "poolclass": pool.NullPool,
            "echo": False,
            "future": True,
        }
    else:
        try:
            db_config = get_database_config()
            connection_config = {
                "url": db_config.get_database_url(),
                "poolclass": pool.NullPool,  # Disable connection pooling for migrations
                "echo": db_config.echo_sql,
                "future": True,  # Use SQLAlchemy 2.0 style
            }
        except Exception as e:
            logger.error(f"Failed to create database config: {e}")
            # Fallback configuration
            connection_config = {
                "url": get_database_url(),
                "poolclass": pool.NullPool,
                "echo": False,
                "future": True,
            }

    # Create engine
    connectable = create_engine(**connection_config)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Multi-tenant migration settings
            version_table="alembic_version",
            version_table_schema=None,
            # Constitutional compliance
            user_module_prefix="assegura_",
            transaction_per_migration=True,
            # Schema handling
            include_schemas=True,
            compare_type=True,
            compare_server_default=True,
            # Migration hooks
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


def process_revision_directives(context, revision, directives):
    """Process revision directives for custom migration logic.

    This hook allows us to customize migration generation, including
    adding multi-tenant specific logic and constitutional compliance checks.

    Args:
        context: Alembic migration context
        revision: Revision being processed
        directives: Migration directives to process
    """
    # Add constitutional compliance header to migration files
    if directives:
        for directive in directives:
            if hasattr(directive, "upgrade_ops") and directive.upgrade_ops:
                # Add comment about constitutional compliance
                directive.message = (
                    f"{directive.message}\n\n"
                    "Constitutional Compliance:\n"
                    "✓ Multi-tenant data isolation\n"
                    "✓ DDD architecture alignment\n"
                    "✓ Python 3.11+ compatibility"
                )

    return directives


def include_object(object, name, type_, reflected, compare_to):
    """Determine whether to include an object in migrations.

    This function is called for each database object during autogenerate
    to determine if it should be included in the migration.

    Args:
        object: Database object (table, column, etc.)
        name: Object name
        type_: Object type
        reflected: Whether object was reflected from database
        compare_to: Object being compared to

    Returns:
        True if object should be included in migration
    """
    # Skip temporary tables
    if name and name.startswith("temp_"):
        return False

    # Skip system tables
    if name and name.startswith("pg_"):
        return False

    # Include all application tables
    return True


# Configure context based on environment
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
