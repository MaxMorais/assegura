"""Database migration utilities and management commands.

Provides utility functions for managing database migrations with
multi-tenant support and constitutional compliance.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manager for database migration operations."""

    def __init__(self, backend_root: Optional[Path] = None) -> None:
        """Initialize migration manager.

        Args:
            backend_root: Path to backend root directory
        """
        self.backend_root = backend_root or Path(__file__).parent.parent.parent
        self.alembic_ini = self.backend_root / "alembic.ini"
        self.migrations_dir = self.backend_root / "migrations"

        # Validate paths
        if not self.alembic_ini.exists():
            raise FileNotFoundError(f"Alembic config not found: {self.alembic_ini}")
        if not self.migrations_dir.exists():
            raise FileNotFoundError(
                f"Migrations directory not found: {self.migrations_dir}"
            )

    def run_alembic_command(self, command: list[str]) -> subprocess.CompletionProcess:
        """Run alembic command with proper configuration.

        Args:
            command: Alembic command arguments

        Returns:
            Subprocess result
        """
        # Build full command
        full_command = [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(self.alembic_ini),
            *command,
        ]

        logger.info(f"Running alembic command: {' '.join(command)}")

        # Run command from backend directory
        result = subprocess.run(
            full_command, cwd=self.backend_root, capture_output=True, text=True
        )

        # Log output
        if result.stdout:
            logger.info(f"Alembic stdout: {result.stdout}")
        if result.stderr:
            if result.returncode == 0:
                logger.info(f"Alembic stderr: {result.stderr}")
            else:
                logger.error(f"Alembic stderr: {result.stderr}")

        return result

    def init_alembic(self) -> bool:
        """Initialize Alembic migration environment.

        Returns:
            True if successful
        """
        try:
            result = self.run_alembic_command(["init", "migrations"])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to initialize Alembic: {e}")
            return False

    def create_migration(
        self, message: str, auto_generate: bool = True, sql: bool = False
    ) -> bool:
        """Create new migration.

        Args:
            message: Migration message/description
            auto_generate: Whether to auto-generate migration
            sql: Whether to generate SQL-only migration

        Returns:
            True if successful
        """
        try:
            command = ["revision"]

            if auto_generate:
                command.append("--autogenerate")

            if sql:
                command.append("--sql")

            command.extend(["-m", message])

            result = self.run_alembic_command(command)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False

    def upgrade_database(self, revision: str = "head") -> bool:
        """Upgrade database to specified revision.

        Args:
            revision: Target revision (default: head)

        Returns:
            True if successful
        """
        try:
            result = self.run_alembic_command(["upgrade", revision])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            return False

    def downgrade_database(self, revision: str = "-1") -> bool:
        """Downgrade database to specified revision.

        Args:
            revision: Target revision (default: previous)

        Returns:
            True if successful
        """
        try:
            result = self.run_alembic_command(["downgrade", revision])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            return False

    def get_current_revision(self) -> Optional[str]:
        """Get current database revision.

        Returns:
            Current revision ID or None if not available
        """
        try:
            result = self.run_alembic_command(["current"])
            if result.returncode == 0 and result.stdout:
                # Parse revision from output
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Rev:" in line:
                        return line.split("Rev:")[1].strip().split()[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None

    def get_migration_history(self) -> list[str]:
        """Get migration history.

        Returns:
            List of migration revisions
        """
        try:
            result = self.run_alembic_command(["history"])
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().split("\n")
            return []
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    def check_database_status(self) -> dict:
        """Check database migration status.

        Returns:
            Dictionary with status information
        """
        current_revision = self.get_current_revision()

        try:
            # Get head revision
            result = self.run_alembic_command(["heads"])
            head_revision = None
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Rev:" in line:
                        head_revision = line.split("Rev:")[1].strip().split()[0]
                        break

            return {
                "current_revision": current_revision,
                "head_revision": head_revision,
                "is_up_to_date": current_revision == head_revision,
                "needs_upgrade": current_revision != head_revision,
            }

        except Exception as e:
            logger.error(f"Failed to check database status: {e}")
            return {
                "current_revision": current_revision,
                "head_revision": None,
                "is_up_to_date": False,
                "needs_upgrade": False,
                "error": str(e),
            }

    def validate_migrations(self) -> bool:
        """Validate migration files and database state.

        Returns:
            True if migrations are valid
        """
        try:
            # Check for migration file syntax errors
            result = self.run_alembic_command(["check"])
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False


def create_migration_manager() -> MigrationManager:
    """Factory function to create migration manager.

    Returns:
        Configured MigrationManager instance
    """
    return MigrationManager()


# CLI-style functions for common operations
def create_migration(message: str, auto_generate: bool = True) -> bool:
    """Create new migration (convenience function).

    Args:
        message: Migration description
        auto_generate: Whether to auto-generate

    Returns:
        True if successful
    """
    manager = create_migration_manager()
    return manager.create_migration(message, auto_generate)


def upgrade_database(revision: str = "head") -> bool:
    """Upgrade database (convenience function).

    Args:
        revision: Target revision

    Returns:
        True if successful
    """
    manager = create_migration_manager()
    return manager.upgrade_database(revision)


def get_database_status() -> dict:
    """Get database status (convenience function).

    Returns:
        Status information dictionary
    """
    manager = create_migration_manager()
    return manager.check_database_status()
