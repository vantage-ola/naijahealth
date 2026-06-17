#!/bin/sh
set -e

echo "Running database migrations..."
PYTHONPATH=/app alembic upgrade head

case "$1" in
    web)
        exec uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
        ;;
    *)
        exec "$@"
        ;;
esac
