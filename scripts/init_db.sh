#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U postgres > /dev/null 2>&1; do
  sleep 1
done

echo "Running migrations..."
cd /app
alembic upgrade head

echo "Database initialized."
