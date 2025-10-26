#!/bin/bash
set -e

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (noinput to avoid prompts)
python manage.py collectstatic --noinput

# Run create_groups to set up permissions
python manage.py create_groups

python manage.py loaddata fixtures/goods/cats.json
python manage.py loaddata fixtures/goods/prod.json

# # Ensure superuser from env (idempotent)
# if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
# python manage.py shell <<'PY'
# import os
# from django.contrib.auth import get_user_model
# User = get_user_model()
# username = os.environ["DJANGO_SUPERUSER_USERNAME", "root"]
# email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "gudiniboy@example.com")
# password = os.environ["DJANGO_SUPERUSER_PASSWORD", "root"]
# user = User.objects.filter(username=username).first()
# if not user:
#     User.objects.create_superuser(username=username, email=email, password=password)
# else:
#     changed = False
#     if not user.is_superuser:
#         user.is_superuser = True
#         changed = True
#     if not user.is_staff:
#         user.is_staff = True
#         changed = True
#     if password:
#         user.set_password(password)
#         changed = True
#     if user.email != email:
#         user.email = email
#         changed = True
#     if changed:
#         user.save()
# print(f"Superuser ensured: {username}")
# PY
# fi

# Run the command (passed from docker-compose)
exec "$@"