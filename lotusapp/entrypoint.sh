#!/bin/sh

echo "Aplicando migrações no banco de dados..."
python manage.py migrate
echo "Migrações aplicadas!"

exec "$@"