#!/usr/bin/env sh

IP="$DEPLOY_CONSOLE_IP"

if [ -z $IP ]; then
  echo "❌ ERROR: Set the DEPLOY_CONSOLE_IP environment variable to the console IP."
  DEPLOY_CONSOLE_USER="${DEPLOY_CONSOLE_USER:-root}"
  DEPLOY_GAME_NAME="${DEPLOY_CONSOLE_USER:-PygameVideogameMaker}"
  DEPLOY_DEST_DIR="${DEPLOY_DEST_DIR:-/userdata/roms/pygame}"
  DEST="$DEPLOY_CONSOLE_USER@$IP:$DEPLOY_DEST_DIR"
  GAME_NAME="$DEPLOY_GAME_NAME"
fi

PROJECT_DIR="."
PROJECT_DIR_DEST="$DEST/$GAME_NAME"

set -eu
rm -rf vendor
mkdir -p vendor

uv pip freeze \
  | grep -vE '^-e |^file:|^\.$' \
  | sed 's/@.*//' \
  | xargs -n1 uv pip install --target vendor --no-compile


echo "✅ vendor/ ready"
echo "📦 Root: $PROJECT_DIR"
echo "🎯 Dest: $PROJECT_DIR_DEST"

# 1) Sync the project
rsync -av --delete --no-owner --no-group \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  "$PROJECT_DIR" \
  "$PROJECT_DIR_DEST"

echo "✅ Synced."
