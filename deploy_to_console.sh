#!/usr/bin/env sh

IP="192.168.1.90"
DEST="root@$IP:/userdata/roms/pygame"
GAME_NAME="PygameTemplate"

PROJECT_DIR="."
PROJECT_DIR_DEST="$DEST/$GAME_NAME"

set -eu
rm -rf vendor
mkdir -p vendor

uv pip install --target vendor \
  --no-compile \
  rich

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
