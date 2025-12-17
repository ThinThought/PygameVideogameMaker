#!/usr/bin/env sh
set -eu

IP="${IP:-192.168.1.90}"
DEST="root@$IP:/userdata/roms/pygame"

PROJECT_DIR="/home/daiego/Thin-Thought/Repositories/trimuiSandbox/"
PROJECT_DIR_DEST="$DEST/trimuiSandbox"

LAUNCHER="/home/daiego/Thin-Thought/Repositories/trimuiSandbox.pygame"
LAUNCHER_DEST="$DEST/trimuiSandbox.pygame"

echo "📦 Root: $PROJECT_DIR"
echo "🎯 Dest: $PROJECT_DIR_DEST"

# 1) Sincroniza el proyecto (excluye basura local)
rsync -av --delete --no-owner --no-group \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  "$PROJECT_DIR" \
  "$PROJECT_DIR_DEST"

echo "✅ Synced."
