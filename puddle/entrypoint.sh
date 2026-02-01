#!/usr/bin/env bash
set -e

wait_for_migrations() {
  echo "⏳ Waiting for database migrations..."
  until python -c "import django; django.setup(); from django.db import connection; connection.cursor().execute('SELECT 1 FROM django_migrations LIMIT 1;')" 2>/dev/null; do
    echo "❓Database not ready yet..."
    sleep 5
  done
  echo "✅ Database ready!"
}

if [ "$SERVICE_ROLE" = "beat" ] || [ "$SERVICE_ROLE" = "worker" ]; then
  wait_for_migrations
fi



if [ "$SERVICE_ROLE" = "web" ]; then
  echo "🚀 Running web setup..."

  python manage.py makemigrations --noinput || true
  python manage.py migrate --noinput

  python manage.py collectstatic --noinput || true

  python manage.py create_groups || true

  python manage.py loaddata fixtures/goods/cats.json || true
  python manage.py loaddata fixtures/goods/prod.json || true
fi

echo "✅ Starting container as role: $SERVICE_ROLE"
exec "$@"
