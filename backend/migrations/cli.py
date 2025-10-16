"""Database migration management CLI commands.

Provides command-line interface for managing database migrations
with constitutional compliance and multi-tenant support.
"""

import logging

import click

from .utils import MigrationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """Database migration management CLI.

    ERPNext Test Automation Meta-Framework migration management with
    constitutional compliance and multi-tenant support.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option("--message", "-m", required=True, help="Migration message")
@click.option("--auto/--no-auto", default=True, help="Auto-generate migration")
@click.option("--sql", is_flag=True, help="Generate SQL-only migration")
def create(message: str, auto: bool, sql: bool) -> None:
    """Create a new migration.

    Generates a new migration file with the specified message.
    Use --auto to automatically detect model changes.
    """
    try:
        manager = MigrationManager()
        success = manager.create_migration(message, auto, sql)

        if success:
            click.echo(f"✅ Created migration: {message}")
        else:
            click.echo(f"❌ Failed to create migration: {message}", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Error creating migration: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("revision", default="head")
def upgrade(revision: str) -> None:
    """Upgrade database to specified revision.

    Applies all migrations up to the specified revision.
    Use 'head' to upgrade to the latest migration.
    """
    try:
        manager = MigrationManager()
        success = manager.upgrade_database(revision)

        if success:
            click.echo(f"✅ Upgraded database to revision: {revision}")
        else:
            click.echo(f"❌ Failed to upgrade database to: {revision}", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Error upgrading database: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("revision", default="-1")
def downgrade(revision: str) -> None:
    """Downgrade database to specified revision.

    Reverts migrations down to the specified revision.
    Use '-1' to downgrade by one revision.
    """
    try:
        manager = MigrationManager()
        success = manager.downgrade_database(revision)

        if success:
            click.echo(f"✅ Downgraded database to revision: {revision}")
        else:
            click.echo(f"❌ Failed to downgrade database to: {revision}", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Error downgrading database: {e}", err=True)
        raise click.Abort()


@cli.command()
def status() -> None:
    """Show current database migration status.

    Displays current revision, head revision, and migration status.
    """
    try:
        manager = MigrationManager()
        status_info = manager.check_database_status()

        click.echo("\n📊 Database Migration Status")
        click.echo("=" * 40)

        current = status_info.get("current_revision", "Unknown")
        head = status_info.get("head_revision", "Unknown")

        click.echo(f"Current Revision: {current}")
        click.echo(f"Head Revision:    {head}")

        if status_info.get("is_up_to_date"):
            click.echo("Status:           ✅ Up to date")
        elif status_info.get("needs_upgrade"):
            click.echo("Status:           ⚠️  Needs upgrade")
        else:
            click.echo("Status:           ❓ Unknown")

        if "error" in status_info:
            click.echo(f"Error:            ❌ {status_info['error']}")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error checking status: {e}", err=True)
        raise click.Abort()


@cli.command()
def history() -> None:
    """Show migration history.

    Displays the history of all applied migrations.
    """
    try:
        manager = MigrationManager()
        history = manager.get_migration_history()

        if not history:
            click.echo("No migration history found.")
            return

        click.echo("\n📜 Migration History")
        click.echo("=" * 40)

        for line in history:
            if line.strip():
                click.echo(line)

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error getting history: {e}", err=True)
        raise click.Abort()


@cli.command()
def validate() -> None:
    """Validate migration files and database state.

    Checks migration files for syntax errors and validates
    the current database state.
    """
    try:
        manager = MigrationManager()
        is_valid = manager.validate_migrations()

        if is_valid:
            click.echo("✅ All migrations are valid")
        else:
            click.echo("❌ Migration validation failed", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Error validating migrations: {e}", err=True)
        raise click.Abort()


@cli.command()
def init() -> None:
    """Initialize Alembic migration environment.

    Sets up the migration environment for a new database.
    This is typically only run once during initial setup.
    """
    try:
        manager = MigrationManager()
        success = manager.init_alembic()

        if success:
            click.echo("✅ Initialized Alembic migration environment")
        else:
            click.echo("❌ Failed to initialize Alembic", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"❌ Error initializing Alembic: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
