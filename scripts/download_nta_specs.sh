#!/usr/bin/env bash
# Download and extract NTA e-Tax specification files (CAB archives).
# Requires: curl, cabextract
# Usage: bash scripts/download_nta_specs.sh

set -euo pipefail

SPECS_DIR="$(cd "$(dirname "$0")/.." && pwd)/specs"
mkdir -p "$SPECS_DIR"

URLS=(
  "https://www.e-tax.nta.go.jp/shiyo/download/e-tax01.CAB"  # データ形式仕様書
  "https://www.e-tax.nta.go.jp/shiyo/download/e-tax09.CAB"  # XML構造設計書【所得税関係】
  "https://www.e-tax.nta.go.jp/shiyo/download/e-tax19.CAB"  # XMLスキーマ
)

for url in "${URLS[@]}"; do
  filename=$(basename "$url")
  dirname="${filename%.CAB}"

  echo "==> Downloading $filename ..."
  curl -L -o "$SPECS_DIR/$filename" "$url"

  echo "==> Extracting $filename -> $SPECS_DIR/$dirname/"
  mkdir -p "$SPECS_DIR/$dirname"
  cabextract -d "$SPECS_DIR/$dirname" "$SPECS_DIR/$filename"

  echo ""
done

echo "Done. Specs extracted to: $SPECS_DIR"
