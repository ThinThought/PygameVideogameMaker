#!/usr/bin/env sh
set -eu
rm -rf vendor
mkdir -p vendor

uv pip install --target vendor \
  --no-compile \
  rich

echo "✅ vendor/ listo"
