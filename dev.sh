#!/usr/bin/env bash
#
# dev.sh — enciende y apaga el entorno Docker de El Tapaso.
#
# Busca puertos libres automáticamente (base de datos, backend y frontend),
# los guarda en el .env y levanta los contenedores. Si el puerto que tenías
# ya lo está usando otro programa, toma el siguiente disponible y te avisa.
#
#   ./dev.sh up          levanta todo
#   ./dev.sh down        apaga
#   ./dev.sh help        ver todas las opciones
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

ENV_FILE="$PROJECT_DIR/.env"
ENV_EXAMPLE="$PROJECT_DIR/.env.example"

# Puertos deseados. Si están ocupados, el script busca el siguiente libre.
DEFAULT_DB_PORT=5432
DEFAULT_BACKEND_PORT=8000
DEFAULT_FRONTEND_PORT=5173
DEFAULT_MAILPIT_PORT=8025
MAX_INTENTOS=100

# ------------------------------- colores ----------------------------------- #
if [ -t 1 ]; then
  ROJO='\033[0;31m'; VERDE='\033[0;32m'; AMARILLO='\033[0;33m'
  AZUL='\033[0;36m'; NEGRITA='\033[1m'; FIN='\033[0m'
else
  ROJO=''; VERDE=''; AMARILLO=''; AZUL=''; NEGRITA=''; FIN=''
fi

info()  { printf "${AZUL}==>${FIN} %s\n" "$*"; }
ok()    { printf "${VERDE}  ✓${FIN} %s\n" "$*"; }
aviso() { printf "${AMARILLO}  !${FIN} %s\n" "$*"; }
error() { printf "${ROJO}==> ERROR:${FIN} %s\n" "$*" >&2; }
morir() { error "$*"; exit 1; }

# ----------------------------- comprobaciones ------------------------------ #
verificar_docker() {
  command -v docker >/dev/null 2>&1 || morir "Docker no está instalado. Ver docs/guias/guia-instalacion.md"
  docker compose version >/dev/null 2>&1 || morir "Falta el plugin 'docker compose' (v2)."
  docker info >/dev/null 2>&1 || morir "El demonio de Docker no responde. ¿Está Docker Desktop encendido? En Linux: sudo systemctl start docker"
}

crear_env_si_falta() {
  if [ ! -f "$ENV_FILE" ]; then
    [ -f "$ENV_EXAMPLE" ] || morir "No existe .env.example"
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    ok "Archivo .env creado a partir de .env.example"
  fi
  # Los .env creados antes de que existiera el modo Supabase no tienen esta
  # variable; sin ella Compose no levantaría la base de datos local.
  if ! grep -qE "^COMPOSE_PROFILES=" "$ENV_FILE"; then
    printf '\n# local-db = contenedor de PostgreSQL; vacío = base remota (Supabase)\nCOMPOSE_PROFILES=local-db\n' >> "$ENV_FILE"
    aviso "Se añadió COMPOSE_PROFILES=local-db a tu .env"
  fi

  # Los .env de cada app sirven para correr sin Docker; se crean por comodidad.
  for app in backend-django frontend-react; do
    if [ -f "apps/$app/.env.example" ] && [ ! -f "apps/$app/.env" ]; then
      cp "apps/$app/.env.example" "apps/$app/.env"
      ok "Archivo apps/$app/.env creado"
    fi
  done
}

# --------------------------- manejo del .env ------------------------------- #
leer_env() {          # leer_env CLAVE  ->  imprime el valor (sin comentarios)
  local clave="$1"
  [ -f "$ENV_FILE" ] || return 0
  sed -nE "s/^${clave}=([^#]*).*/\1/p" "$ENV_FILE" | head -1 | tr -d '[:space:]'
}

escribir_env() {      # escribir_env CLAVE VALOR  (conserva el comentario final)
  local clave="$1" valor="$2" comentario=''
  if grep -qE "^${clave}=" "$ENV_FILE"; then
    comentario="$(sed -nE "s/^${clave}=[^#]*(#.*)?$/\1/p" "$ENV_FILE" | head -1)"
    if [ -n "$comentario" ]; then
      sed -i.bak -E "s|^${clave}=.*|${clave}=${valor}        ${comentario}|" "$ENV_FILE"
    else
      sed -i.bak -E "s|^${clave}=.*|${clave}=${valor}|" "$ENV_FILE"
    fi
    rm -f "${ENV_FILE}.bak"
  else
    printf '%s=%s\n' "$clave" "$valor" >> "$ENV_FILE"
  fi
}

# --------------------------- ¿la BD es local? ------------------------------ #
usa_bd_local() {
  case ",$(leer_env COMPOSE_PROFILES)," in
    *,local-db,*) return 0 ;;
    *) return 1 ;;
  esac
}

descripcion_bd() {
  if usa_bd_local; then
    printf "localhost:%s (contenedor)" "$(leer_env POSTGRES_PORT_HOST)"
  else
    printf "%s (remota)" "$(leer_env POSTGRES_HOST)"
  fi
}

# ------------------------------- puertos ----------------------------------- #
# Puertos que ya publican los contenedores DE ESTE proyecto: para nosotros
# cuentan como libres (si no, al reiniciar el script los cambiaría sin razón).
puertos_propios() {
  docker compose ps --format '{{.Ports}}' 2>/dev/null \
    | grep -oE ':[0-9]+->' | grep -oE '[0-9]+' | sort -u
}

# Con qué herramienta se comprueban los puertos. Se decide una sola vez.
#
# Ojo con Windows: si no hay Python instalado, el sistema deja igualmente un
# "python3" falso (el acceso directo a la Microsoft Store) que existe para
# `command -v` pero no ejecuta nada, imprime un aviso y devuelve error. Por eso
# no basta con que el comando exista: hay que probarlo antes de elegirlo.
HERRAMIENTA_PUERTOS=''

elegir_herramienta_puertos() {
  [ -z "$HERRAMIENTA_PUERTOS" ] || return 0
  if command -v ss >/dev/null 2>&1 && ss -ltn >/dev/null 2>&1; then
    HERRAMIENTA_PUERTOS=ss
  elif command -v lsof >/dev/null 2>&1 && lsof -v >/dev/null 2>&1; then
    HERRAMIENTA_PUERTOS=lsof
  elif command -v python3 >/dev/null 2>&1 && python3 -c '' >/dev/null 2>&1; then
    HERRAMIENTA_PUERTOS=python3
  elif command -v netstat >/dev/null 2>&1 && netstat -an >/dev/null 2>&1; then
    HERRAMIENTA_PUERTOS=netstat   # el caso de Git Bash en Windows
  else
    HERRAMIENTA_PUERTOS=ninguna
    aviso "No hay forma de comprobar los puertos aquí: los daré por libres."
  fi
}

puerto_ocupado() {    # puerto_ocupado 8000  ->  0 si está ocupado
  local puerto="$1"

  # ¿Lo tiene nuestro propio proyecto? Entonces no es un conflicto.
  if printf '%s\n' "$PUERTOS_PROPIOS" | grep -qx "$puerto"; then
    return 1
  fi

  elegir_herramienta_puertos
  case "$HERRAMIENTA_PUERTOS" in
    ss)
      ss -ltnH "sport = :$puerto" 2>/dev/null | grep -q . && return 0 || return 1
      ;;
    lsof)
      lsof -iTCP:"$puerto" -sTCP:LISTEN -t >/dev/null 2>&1 && return 0 || return 1
      ;;
    python3)
      python3 - "$puerto" 2>/dev/null <<'PY' && return 1 || return 0
import socket, sys
s = socket.socket()
try:
    s.bind(("0.0.0.0", int(sys.argv[1])))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
      ;;
    netstat)
      # El estado ("LISTENING") viene traducido en los Windows en español, así
      # que se mira solo la dirección local, que es igual en todos los idiomas.
      netstat -an 2>/dev/null \
        | awk -v p=":${puerto}$" 'tolower($1) ~ /^tcp/ && ($2 ~ p || $4 ~ p) { hallado = 1 }
                                  END { exit !hallado }' \
        && return 0 || return 1
      ;;
    *)
      return 1   # sin herramientas para comprobar: se asume libre
      ;;
  esac
}

buscar_puerto_libre() {   # buscar_puerto_libre 8000 -> primer puerto libre >= 8000
  local puerto="$1" intentos=0
  while puerto_ocupado "$puerto"; do
    puerto=$((puerto + 1))
    intentos=$((intentos + 1))
    [ "$intentos" -lt "$MAX_INTENTOS" ] || morir "No encontré un puerto libre cerca de $1"
  done
  printf '%s' "$puerto"
}

asignar_puertos() {
  PUERTOS_PROPIOS="$(puertos_propios || true)"

  local db_deseado backend_deseado frontend_deseado mailpit_deseado
  db_deseado="$(leer_env POSTGRES_PORT_HOST)";  db_deseado="${db_deseado:-$DEFAULT_DB_PORT}"
  backend_deseado="$(leer_env BACKEND_PORT)";   backend_deseado="${backend_deseado:-$DEFAULT_BACKEND_PORT}"
  frontend_deseado="$(leer_env FRONTEND_PORT)"; frontend_deseado="${frontend_deseado:-$DEFAULT_FRONTEND_PORT}"
  mailpit_deseado="$(leer_env MAILPIT_PORT)";   mailpit_deseado="${mailpit_deseado:-$DEFAULT_MAILPIT_PORT}"

  if usa_bd_local; then
    DB_PORT="$(buscar_puerto_libre "$db_deseado")"
  else
    DB_PORT="$db_deseado"   # base remota: no se publica ningún puerto local
  fi
  BACKEND_PORT="$(buscar_puerto_libre "$backend_deseado")"
  # El frontend no puede quedar en el mismo puerto que el backend.
  FRONTEND_PORT="$(buscar_puerto_libre "$frontend_deseado")"
  while [ "$FRONTEND_PORT" = "$BACKEND_PORT" ]; do
    FRONTEND_PORT="$(buscar_puerto_libre $((FRONTEND_PORT + 1)))"
  done
  # Y el buzón de pruebas no puede chocar con ninguno de los dos.
  MAILPIT_PORT="$(buscar_puerto_libre "$mailpit_deseado")"
  while [ "$MAILPIT_PORT" = "$BACKEND_PORT" ] || [ "$MAILPIT_PORT" = "$FRONTEND_PORT" ]; do
    MAILPIT_PORT="$(buscar_puerto_libre $((MAILPIT_PORT + 1)))"
  done

  [ "$DB_PORT" = "$db_deseado" ]             || aviso "Puerto $db_deseado ocupado -> base de datos en $DB_PORT"
  [ "$BACKEND_PORT" = "$backend_deseado" ]   || aviso "Puerto $backend_deseado ocupado -> backend en $BACKEND_PORT"
  [ "$FRONTEND_PORT" = "$frontend_deseado" ] || aviso "Puerto $frontend_deseado ocupado -> frontend en $FRONTEND_PORT"
  [ "$MAILPIT_PORT" = "$mailpit_deseado" ]   || aviso "Puerto $mailpit_deseado ocupado -> buzón de correo en $MAILPIT_PORT"

  usa_bd_local && escribir_env POSTGRES_PORT_HOST "$DB_PORT"
  escribir_env BACKEND_PORT       "$BACKEND_PORT"
  escribir_env FRONTEND_PORT      "$FRONTEND_PORT"
  escribir_env MAILPIT_PORT       "$MAILPIT_PORT"
  # El navegador llama a la API por el puerto publicado: deben ir sincronizados.
  escribir_env VITE_API_URL       "http://localhost:${BACKEND_PORT}/api/v1"
  # Y los enlaces de los correos (invitación, recuperación, verificación) los
  # abre el frontend: si el puerto cambió, tienen que apuntar al nuevo.
  escribir_env URL_FRONTEND       "http://localhost:${FRONTEND_PORT}"

  if usa_bd_local; then
    ok "Puertos: base de datos $DB_PORT · backend $BACKEND_PORT · frontend $FRONTEND_PORT"
  else
    ok "Puertos: backend $BACKEND_PORT · frontend $FRONTEND_PORT · BD remota: $(leer_env POSTGRES_HOST)"
  fi
}

# ------------------------------- ayudantes --------------------------------- #
esperar_servicio() {   # esperar_servicio URL SEGUNDOS
  local url="$1" limite="${2:-60}" t=0
  command -v curl >/dev/null 2>&1 || return 0
  while [ "$t" -lt "$limite" ]; do
    curl -fsS -o /dev/null "$url" 2>/dev/null && return 0
    sleep 2; t=$((t + 2))
  done
  return 1
}

mostrar_urls() {
  local db backend frontend mailpit
  db="$(leer_env POSTGRES_PORT_HOST)"
  backend="$(leer_env BACKEND_PORT)"
  frontend="$(leer_env FRONTEND_PORT)"
  mailpit="$(leer_env MAILPIT_PORT)"; mailpit="${mailpit:-$DEFAULT_MAILPIT_PORT}"
  printf "\n${NEGRITA}El Tapaso está arriba:${FIN}\n\n"
  printf "  Frontend .............. http://localhost:%s\n" "$frontend"
  printf "  API ................... http://localhost:%s/api/v1/\n" "$backend"
  printf "  Documentación API ..... http://localhost:%s/api/docs/\n" "$backend"
  printf "  Admin de Django ....... http://localhost:%s/admin/\n" "$backend"
  printf "  Correos de prueba ..... http://localhost:%s\n" "$mailpit"
  printf "  Base de datos ......... %s\n\n" "$(descripcion_bd)"
  printf "  Logs:   ./dev.sh logs        Apagar:  ./dev.sh down\n\n"
}

# ------------------------------- comandos ---------------------------------- #
# Al pasar de base local a remota, el contenedor de PostgreSQL se queda
# corriendo aunque ya no haga falta (Compose no lo considera huérfano porque
# el servicio sigue definido, solo que fuera del perfil activo).
apagar_bd_local_sobrante() {
  usa_bd_local && return 0
  docker ps --format '{{.Names}}' | grep -qx tapaso_db || return 0
  aviso "La base de datos es remota: apagando el contenedor local sobrante"
  COMPOSE_PROFILES=local-db docker compose stop db >/dev/null 2>&1 || true
  COMPOSE_PROFILES=local-db docker compose rm -f db >/dev/null 2>&1 || true
}

cmd_up() {
  local construir=0 servicios=()
  for arg in "$@"; do
    case "$arg" in
      --build|-b) construir=1 ;;
      *) servicios+=("$arg") ;;
    esac
  done

  verificar_docker
  crear_env_si_falta
  info "Buscando puertos libres..."
  asignar_puertos

  info "Levantando contenedores..."
  if [ "$construir" -eq 1 ]; then
    docker compose up -d --build --remove-orphans ${servicios[@]+"${servicios[@]}"}
  else
    docker compose up -d --remove-orphans ${servicios[@]+"${servicios[@]}"}
  fi

  apagar_bd_local_sobrante

  info "Esperando a que respondan los servicios..."
  if esperar_servicio "http://localhost:$(leer_env BACKEND_PORT)/api/docs/" 90; then
    ok "Backend respondiendo"
  else
    aviso "El backend aún no responde. Revisa: ./dev.sh logs backend"
  fi
  if esperar_servicio "http://localhost:$(leer_env FRONTEND_PORT)" 60; then
    ok "Frontend respondiendo"
  else
    aviso "El frontend aún no responde (la primera vez instala npm y demora). Revisa: ./dev.sh logs frontend"
  fi

  mostrar_urls
}

cmd_down() {
  verificar_docker
  info "Apagando contenedores..."
  docker compose down "$@"
  ok "Listo. Los datos de la base de datos se conservan."
}

cmd_restart() {
  cmd_down
  cmd_up "$@"
}

cmd_status() {
  verificar_docker
  docker compose ps
  printf "\n"
  mostrar_urls
}

cmd_logs() {
  verificar_docker
  docker compose logs -f "$@"
}

cmd_clean() {
  verificar_docker
  printf "${AMARILLO}Esto borra los contenedores Y la base de datos de este proyecto.${FIN}\n"
  printf "Escribe 'si' para continuar: "
  read -r respuesta
  case "$respuesta" in
    si|SI|Si|s|y|yes) docker compose down -v; ok "Entorno borrado." ;;
    *) info "Cancelado." ;;
  esac
}

# ------------------------- comandos del día a día -------------------------- #
requiere_arriba() {   # requiere_arriba backend
  local servicio="$1"
  docker compose ps --status running --services 2>/dev/null | grep -qx "$servicio" \
    || morir "El servicio '$servicio' no está corriendo. Levántalo con: ./dev.sh up"
}

cmd_manage() {        # cualquier comando de manage.py
  verificar_docker; requiere_arriba backend
  [ "$#" -gt 0 ] || morir "Uso: ./dev.sh manage <comando de manage.py>"
  docker compose exec backend python manage.py "$@"
}

cmd_migrate()        { cmd_manage migrate "$@"; }
cmd_makemigrations() { cmd_manage makemigrations "$@"; }
cmd_superuser()      { cmd_manage createsuperuser "$@"; }
cmd_shell()          { cmd_manage shell; }

cmd_startapp() {
  [ "$#" -eq 1 ] || morir "Uso: ./dev.sh startapp <nombre>"
  cmd_manage startapp "$1"
  aviso "Falta: crear las subcarpetas, registrarla en LOCAL_APPS y engancharla en config/urls.py"
  aviso "Pasos en docs/backend/crear-nueva-app.md"
}

cmd_sh() {            # terminal dentro de un contenedor
  local servicio="${1:-backend}"
  verificar_docker; requiere_arriba "$servicio"
  case "$servicio" in
    backend) docker compose exec backend bash ;;
    *)       docker compose exec "$servicio" sh ;;
  esac
}

cmd_psql() {
  verificar_docker; requiere_arriba db
  docker compose exec db psql -U "$(leer_env POSTGRES_USER)" -d "$(leer_env POSTGRES_DB)"
}

cmd_test() {
  verificar_docker
  local objetivo="${1:-todo}"
  if [ "$objetivo" = "todo" ] || [ "$objetivo" = "back" ]; then
    requiere_arriba backend; info "Pruebas del backend"
    # pytest devuelve 5 cuando todavía no hay pruebas escritas: no es un fallo.
    docker compose exec backend pytest || [ "$?" -eq 5 ]
  fi
  if [ "$objetivo" = "todo" ] || [ "$objetivo" = "front" ]; then
    requiere_arriba frontend; info "Pruebas del frontend"; docker compose exec frontend npm run test
  fi
}

cmd_lint() {
  verificar_docker
  requiere_arriba backend;  info "Revisando backend";  docker compose exec backend ruff check .
  requiere_arriba frontend; info "Revisando frontend"; docker compose exec frontend npm run lint
}

cmd_format() {
  verificar_docker
  requiere_arriba backend;  info "Formateando backend";  docker compose exec backend ruff format .
  requiere_arriba frontend; info "Formateando frontend"; docker compose exec frontend npm run format
}

cmd_help() {
  cat <<'AYUDA'
dev.sh — entorno Docker de El Tapaso (elige puertos libres automáticamente)

  ./dev.sh up                 Levanta base de datos, backend y frontend
  ./dev.sh up --build         Igual, pero reconstruyendo las imágenes
  ./dev.sh up backend         Levanta solo un servicio (db | backend | frontend)
  ./dev.sh down               Apaga los contenedores (conserva los datos)
  ./dev.sh restart            Apaga y vuelve a levantar
  ./dev.sh status             Estado de los servicios y sus URLs
  ./dev.sh logs [servicio]    Logs en vivo (Ctrl+C para salir)
  ./dev.sh ports              Muestra los puertos asignados
  ./dev.sh correos            Abre la bandeja donde llegan los correos de prueba
  ./dev.sh clean              Borra contenedores Y base de datos (pide confirmación)

Django:
  ./dev.sh migrate            Aplica las migraciones
  ./dev.sh makemigrations     Crea migraciones (opcional: nombre de la app)
  ./dev.sh superuser          Crea un usuario administrador
  ./dev.sh startapp <nombre>  Crea una app nueva de Django
  ./dev.sh shell              Shell de Django
  ./dev.sh manage <comando>   Cualquier otro comando de manage.py
  ./dev.sh psql               Consola de PostgreSQL

Calidad:
  ./dev.sh test [back|front]  Corre las pruebas
  ./dev.sh lint               Revisa el estilo del código
  ./dev.sh format             Formatea el código

Otros:
  ./dev.sh sh [servicio]      Terminal dentro de un contenedor (por defecto backend)
  ./dev.sh help               Esta ayuda

Los puertos elegidos quedan guardados en el .env, así que se mantienen entre
arranques. Si otro programa te quita un puerto, el script toma el siguiente
libre y actualiza el .env solo.
AYUDA
}

cmd_ports() {
  crear_env_si_falta
  printf "  Base de datos ... %s\n" "$(leer_env POSTGRES_PORT_HOST)"
  printf "  Backend ......... %s\n" "$(leer_env BACKEND_PORT)"
  printf "  Frontend ........ %s\n" "$(leer_env FRONTEND_PORT)"
  printf "  API para el front %s\n" "$(leer_env VITE_API_URL)"
}

PUERTOS_PROPIOS=""
comando="${1:-help}"
shift || true
case "$comando" in
  up|start|encender)    cmd_up "$@" ;;
  down|stop|apagar)     cmd_down "$@" ;;
  restart|reiniciar)    cmd_restart "$@" ;;
  status|ps|estado)     cmd_status ;;
  logs)                 cmd_logs "$@" ;;
  correos|correo)       cmd_correos ;;
  clean|limpiar)        cmd_clean ;;
  ports|puertos)        cmd_ports ;;
  migrate)              cmd_migrate "$@" ;;
  makemigrations)       cmd_makemigrations "$@" ;;
  superuser)            cmd_superuser "$@" ;;
  startapp)             cmd_startapp "$@" ;;
  shell)                cmd_shell ;;
  manage)               cmd_manage "$@" ;;
  psql)                 cmd_psql ;;
  test|pruebas)         cmd_test "$@" ;;
  lint)                 cmd_lint ;;
  format|formato)       cmd_format ;;
  sh|bash)              cmd_sh "$@" ;;
  help|-h|--help|ayuda) cmd_help ;;
  *) error "Comando desconocido: $comando"; printf "\n"; cmd_help; exit 1 ;;
esac
