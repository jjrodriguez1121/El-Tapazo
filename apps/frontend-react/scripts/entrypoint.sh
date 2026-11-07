#!/bin/sh
# Se ejecuta antes del servidor de Vite en el contenedor de desarrollo.
#
# node_modules vive en un volumen anónimo, y ese volumen sobrevive a
# `docker compose up` aunque la imagen se reconstruya. Sin este paso, cuando
# alguien agrega una dependencia al resto del equipo le llega el package.json
# nuevo, pero se queda con los paquetes viejos y la aplicación no arranca.
#
# Se compara la huella del package-lock.json con la de la última instalación y
# solo se instala si cambió: el arranque normal no espera a npm.
set -e

HUELLA_GUARDADA="node_modules/.huella-package-lock"
huella_actual="$(sha256sum package-lock.json | cut -d ' ' -f 1)"

if [ "$(cat "$HUELLA_GUARDADA" 2>/dev/null)" != "$huella_actual" ]; then
    echo "==> Cambió el package-lock.json: instalando dependencias..."
    npm ci --no-audit --no-fund
    echo "$huella_actual" > "$HUELLA_GUARDADA"
    echo "==> Dependencias al día."
fi

exec "$@"
