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

# Same-origin OCR assets; no third-party requests from the browser.
npm install --prefix "$TMP" --no-save --ignore-scripts --omit=optional --no-audit --no-fund tesseract.js@6.0.1 tesseract.js-core@6.0.0 @tesseract.js-data/eng@1.0.0
OCR="$DEST/ocr"
mkdir -p "$OCR/core" "$OCR/lang"
cp "$TMP/node_modules/tesseract.js/dist/tesseract.min.js" "$TMP/node_modules/tesseract.js/dist/worker.min.js" "$OCR/"
cp "$TMP/node_modules/tesseract.js-core"/tesseract-core*.wasm* "$OCR/core/"
cp "$TMP/node_modules/@tesseract.js-data/eng/4.0.0_best_int/eng.traineddata.gz" "$OCR/lang/"
for pkg in tesseract.js tesseract.js-core @tesseract.js-data/eng; do
  label="${pkg##*/}"
  license="$(find "$TMP/node_modules/$pkg" -maxdepth 1 -type f -iname 'license*' -print -quit)"
  if [ -n "$license" ]; then cp "$license" "$OCR/LICENSE-$label"; fi
done
test -s "$OCR/lang/eng.traineddata.gz"
test -s "$OCR/core/tesseract-core-lstm.wasm.js"
