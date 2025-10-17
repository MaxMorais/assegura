#!/usr/bin/env python3
"""Script to run database migrations for testing."""

import os
import sys
from pathlib import Path

# Set testing environment
os.environ["TESTING"] = "true"

# Add src to path
backend_root = Path(__file__).parent
src_path = backend_root / "src"
sys.path.insert(0, str(src_path))

# Import and run alembic
from alembic.config import Config
from alembic import command

def main():
    # Create alembic config
    alembic_cfg = Config("alembic.ini")

    # Run upgrade
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    main()