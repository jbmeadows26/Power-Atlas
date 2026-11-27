#!/usr/bin/env bash
set -euo pipefail
# Build-time download only. Documents are never part of this operation.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
npm install --prefix "$TMP" --no-save --ignore-scripts --omit=optional --no-audit --no-fund pdfjs-dist@5.4.624
PKG="$TMP/node_modules/pdfjs-dist"
DEST="$ROOT/site/personal-intelligence/vendor"
mkdir -p "$DEST"
cp "$PKG/legacy/build/pdf.mjs" "$PKG/legacy/build/pdf.worker.mjs" "$PKG/LICENSE" "$DEST/"
test -s "$DEST/pdf.mjs"
test -s "$DEST/pdf.worker.mjs"
