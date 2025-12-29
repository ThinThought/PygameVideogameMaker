#!/usr/bin/env sh

IP="$DEPLOY_CONSOLE_IP"

if [ -z $IP ]; then
  echo "❌ ERROR: Debes definir la variable de entorno DEPLOY_CONSOLE_IP con la IP de la consola."
  DEPLOY_CONSOLE_USER="${DEPLOY_CONSOLE_USER:-root}"
DEPLOY_GAME_NAME="${DEPLOY_CONSOLE_USER:-PygameVideogameMaker}"
DEPLOY_DEST_DIR="${DEPLOY_DEST_DIR:-/userdata/roms/pygame}"
DEST="$DEPLOY_CONSOLE_USER@$IP:$DEPLOY_DEST_DIR"
GAME_NAME="$DEPLOY_GAME_NAME"
fi

DEPLOY_CONSOLE_USER="${DEPLOY_CONSOLE_USER:-root}"
DEPLOY_GAME_NAME="${DEPLOY_CONSOLE_USER:-PygameVideogameMaker}"
DEPLOY_DEST_DIR="${DEPLOY_DEST_DIR:-/userdata/roms/pygame}"
DEST="$DEPLOY_CONSOLE_USER@$IP:$DEPLOY_DEST_DIR"
GAME_NAME="$DEPLOY_GAME_NAME"

PROJECT_DIR="."
PROJECT_DIR_DEST="$DEST/$GAME_NAME"

set -eu
rm -rf vendor
mkdir -p vendor

uv pip freeze \
  | grep -vE '^-e |^file:|^\.$' \
  | sed 's/@.*//' \
  | xargs -n1 uv pip install --target vendor --no-compile


echo "✅ vendor/ listo"
echo "📦 Root: $PROJECT_DIR"
echo "🎯 Dest: $PROJECT_DIR_DEST"

# 1) Sincroniza el proyecto
rsync -av --delete --no-owner --no-group \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  "$PROJECT_DIR" \
  "$PROJECT_DIR_DEST"

echo "✅ Synced."
