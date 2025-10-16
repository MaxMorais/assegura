#!/bin/bash
set -e

# Create multiple databases for PostgreSQL container
# This script is executed during container initialization

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE erpnext_test_automation_test;
    GRANT ALL PRIVILEGES ON DATABASE erpnext_test_automation_test TO $POSTGRES_USER;
EOSQL

echo "Additional databases created successfully"