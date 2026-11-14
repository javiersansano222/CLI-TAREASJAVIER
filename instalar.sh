#!/usr/bin/env bash
# instalar.sh — instala la CLI «tareas» desde GitHub en macOS y Linux.
#
# Uso en una sola línea:
#   curl -fsSL https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main/instalar.sh | bash
#
# O desde una copia del repo:
#   bash instalar.sh
#
# Lo que toca: uv en ~/.local/bin, el PATH de tu shell, y solo si faltan
# .env y acciones.json en tu carpeta de inicio. Nunca pisa un .env que ya
# exista ni tu código.
set -euo pipefail

REPO="https://github.com/javiersansano222/CLI-TAREASJAVIER"
CRUDO="https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main"
BIN="$HOME/.local/bin"

paso() { printf '\n[%s] %s\n' "$1" "$2"; }

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: hace falta curl para bajar los ficheros." >&2
    echo "       Instálalo con «apt install curl» (Linux) o «brew install curl» (macOS)." >&2
    exit 1
fi

paso "1/6" "Comprobando uv (el gestor de paquetes)..."
if ! command -v uv >/dev/null 2>&1; then
    echo "      uv no está: lo instalo desde astral.sh"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$BIN:$PATH"
fi
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv sigue sin verse en el PATH. Abre una terminal nueva y repite el comando." >&2
    exit 1
fi

paso "2/6" "Preparando Python 3.12..."
uv python install 3.12

paso "3/6" "Instalando la CLI tareas desde GitHub..."
uv tool install "$REPO/archive/refs/heads/main.tar.gz" --force

paso "4/6" "Poniendo tareas en el PATH..."
uv tool update-shell || echo "      Aviso: no he podido; añade $BIN a tu PATH a mano."
export PATH="$BIN:$PATH"

paso "5/6" "Ficheros de configuración en $HOME..."
if [ -f "$HOME/.env" ]; then
    echo "      .env ya existía: no lo toco."
else
    curl -fsSL "$CRUDO/.env.example" -o "$HOME/.env"
    echo "      He creado .env con la plantilla: rellénalo con tu clave."
fi
if [ -f "$HOME/acciones.json" ]; then
    echo "      acciones.json ya existía: no lo toco."
else
    case "$(uname -s)" in
        Darwin) curl -fsSL "$CRUDO/acciones-mac.json" -o "$HOME/acciones.json" ;;
        *)      curl -fsSL "$CRUDO/acciones.json"      -o "$HOME/acciones.json" ;;
    esac
    echo "      He creado acciones.json con las rutas de tu sistema."
fi

paso "6/6" "Creando la carpeta de pruebas de la IA..."
mkdir -p "$HOME/pruebas-tareas/Apuntes" \
         "$HOME/pruebas-tareas/Resúmenes" \
         "$HOME/pruebas-tareas/Clasificados"
echo "      $HOME/pruebas-tareas"

# Comprobación con la ruta completa: el PATH de esta sesión puede estar viejo
if [ ! -x "$BIN/tareas" ]; then
    echo "ERROR: no encuentro el ejecutable en $BIN/tareas" >&2
    exit 1
fi
"$BIN/tareas" version
"$BIN/tareas" --config "$HOME/acciones.json" validar || \
    echo "      Aviso: el acciones.json de tu home no valida; mira el mensaje de arriba."

printf '\nListo. Abre una terminal NUEVA y escribe:\n'
printf '    tareas --help\n'
printf '    hola\n'
printf '    tareas validar\n\n'
printf 'Si no has rellenado .env, las órdenes de IA salen con código 4.\n'
