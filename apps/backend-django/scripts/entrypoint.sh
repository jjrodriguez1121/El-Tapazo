#!/bin/sh
# Se ejecuta antes del comando principal del contenedor de backend.
set -e

HOST="${POSTGRES_HOST:-db}"
PORT="${POSTGRES_PORT:-5432}"

echo "==> Esperando a la base de datos en ${HOST}:${PORT} ..."
intentos=0
until python -c "
import os, socket, sys

sock = socket.socket()
sock.settimeout(3)
try:
    sock.connect((os.environ.get('POSTGRES_HOST', 'db'), int(os.environ.get('POSTGRES_PORT', 5432))))
except OSError:
    sys.exit(1)
finally:
    sock.close()
" 2>/dev/null; do
    intentos=$((intentos + 1))
    if [ "$intentos" -ge 30 ]; then
        echo "ERROR: la base de datos no respondió tras 60 segundos."
        echo "       Revisa POSTGRES_HOST y POSTGRES_PORT en el .env."
        exit 1
    fi
    sleep 2
done
echo "==> Base de datos disponible."

echo "==> Aplicando migraciones..."
python manage.py migrate --noinput

echo "==> Creando datos iniciales (si faltan)..."
python manage.py crear_datos_iniciales

exec "$@"
