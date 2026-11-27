#!/usr/bin/env bash
set -euo pipefail
# All runtime assets served from the platform's own origin. No customer data
# or user-dependent URLs enter this build. Explicitly pinned model revision.
root="$(cd "$(dirname "$0")/.." && pwd)"
target="$root/site/private-workspace/adaptive-assets"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$target/vendor" "$target/models/Xenova/all-MiniLM-L6-v2/onnx" "$target/licenses"
npm install --prefix "$work" --ignore-scripts --no-audit --no-fund --omit=optional --save-exact @huggingface/transformers@3.8.0
pkg="$work/node_modules/@huggingface/transformers"
cp "$pkg/dist/transformers.min.js" "$target/vendor/"
cp "$pkg/dist/ort-wasm-simd-threaded.jsep.mjs" "$pkg/dist/ort-wasm-simd-threaded.jsep.wasm" "$target/vendor/"
cp "$pkg/LICENSE" "$target/licenses/transformers-Apache-2.0.txt"
ort="$work/node_modules/onnxruntime-web"
for f in "$ort"/LICENSE* "$ort"/ThirdPartyNotices*; do if [ -f "$f" ]; then cp "$f" "$target/licenses/onnxruntime-$(basename "$f")"; fi; done
model="$target/models/Xenova/all-MiniLM-L6-v2"
rev=cb3d680149bf9a3209564e1b27ab3bb355b65707
for file in config.json tokenizer.json tokenizer_config.json special_tokens_map.json vocab.txt README.md onnx/model_quantized.onnx; do
 curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' --retry 2 --connect-timeout 15 --max-time 150 "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/$rev/$file" -o "$model/$file"
 test -s "$model/$file"
done
echo "afdb6f1a0e45b715d0bb9b11772f032c399babd23bfc31fed1c170afc848bdb1  $model/onnx/model_quantized.onnx" | sha256sum -c -
cp "$pkg/LICENSE" "$target/licenses/model-Apache-2.0.txt"
cp "$model/README.md" "$target/licenses/model-card.md"
python3 - "$target" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1])
files=[{"path":str(f.relative_to(p)),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(p.rglob("*")) if f.is_file() and f.name!="manifest.json"]
manifest={"schemaVersion":1,"runtime":"Transformers.js 3.8.0","model":"Xenova/all-MiniLM-L6-v2","revision":"cb3d680149bf9a3209564e1b27ab3bb355b65707","license":"Apache-2.0","dtype":"q8","bytes":sum(f["bytes"] for f in files if not f["path"].startswith("licenses/")),"files":files}
(p/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("Adaptive local model bundle:",manifest["bytes"],"bytes")
PY
