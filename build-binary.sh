#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/dist"
BUILD_ROOT="$ROOT/.build-vmmigration"
PYTHON="${PYTHON:-python3}"

echo "VM Migration Center - binary build"
echo "Design and Development by : antonios.mortos@oultook.com"
echo

command -v "$PYTHON" >/dev/null 2>&1 || { echo "python3 is required for build." >&2; exit 2; }

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT" "$OUT"

"$PYTHON" -m venv "$BUILD_ROOT/venv"
"$BUILD_ROOT/venv/bin/pip" install --upgrade pip wheel
"$BUILD_ROOT/venv/bin/pip" install "nuitka>=2.7,<3"

"$BUILD_ROOT/venv/bin/python" -m nuitka \
  --onefile \
  --assume-yes-for-downloads \
  --include-package=lbm_vdrc \
  --output-dir="$BUILD_ROOT/out" \
  --output-filename=vmmigration \
  "$ROOT/vmmigration.py"

install -m 0755 "$BUILD_ROOT/out/vmmigration" "$OUT/vmmigration"

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$OUT" && sha256sum vmmigration > vmmigration.sha256)
fi

echo
echo "Binary created:"
echo "  $OUT/vmmigration"
[[ -f "$OUT/vmmigration.sha256" ]] && echo "  $OUT/vmmigration.sha256"
