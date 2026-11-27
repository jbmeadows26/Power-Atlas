#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
runtime="$root/business-intelligence/document-runtime"
target="$root/site/private-workspace/document-assets"
npm ci --prefix "$runtime" --ignore-scripts --no-audit --no-fund --omit=optional
mkdir -p "$target"
cp "$runtime/node_modules/pdfjs-dist/build/pdf.mjs" "$runtime/node_modules/pdfjs-dist/build/pdf.worker.mjs" "$target/"
cp "$runtime/node_modules/fflate/esm/browser.js" "$target/fflate.mjs"
cp "$runtime/node_modules/pdfjs-dist/LICENSE" "$target/PDFJS-LICENSE.txt"
cp "$runtime/node_modules/fflate/LICENSE" "$target/FFLATE-LICENSE.txt"
