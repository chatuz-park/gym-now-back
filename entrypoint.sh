#!/usr/bin/env bash
set -e

# Optional envs
: "${DJANGO_MIGRATE:=true}"
: "${DJANGO_COLLECTSTATIC:=false}"

host="${DB_HOST:-localhost}"
port="${DB_PORT:-5432}"

echo "Waiting for database at ${host}:${port}..."
for i in {1..60}; do
  if nc -z "$host" "$port"; then
    echo "Database is up!"
    break
  fi
  echo "DB not ready yet... ($i)"
  sleep 1
done

if [ "$DJANGO_MIGRATE" = "true" ]; then
  echo "Applying migrations..."
  python manage.py migrate --noinput
fi

if [ "$DJANGO_COLLECTSTATIC" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

exec "$@"


