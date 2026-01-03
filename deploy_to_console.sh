#!/usr/bin/env sh
set -eu

IP="${DEPLOY_CONSOLE_IP:-}"
[ -z "$IP" ] && echo "❌ Set DEPLOY_CONSOLE_IP" && exit 1

DEPLOY_CONSOLE_USER="${DEPLOY_CONSOLE_USER:-root}"
DEPLOY_GAME_NAME="${DEPLOY_GAME_NAME:-PygameVideogameMaker}"
DEPLOY_DEST_DIR="/userdata/roms/pygame"

DEST_HOST="${DEPLOY_CONSOLE_USER}@${IP}"
REMOTE_BASE="${DEPLOY_DEST_DIR}/${DEPLOY_GAME_NAME}"

echo "📦 Root: ."
echo "🎯 Dest: ${DEST_HOST}:${REMOTE_BASE}"


uv pip freeze \
  | grep -vE '^-e |^file:|^\.$' \
  | sed 's/@.*//' \
  | xargs -n1 uv pip install --target vendor --no-compile

# 2) proyecto
rsync -av --delete --no-owner --no-group \
  --exclude ".venv/" \
  --exclude "__pycache__/" \
  ./ \
  "${DEST_HOST}:${REMOTE_BASE}/"


echo "✅ Synced."
