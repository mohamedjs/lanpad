#!/usr/bin/env bash
# Assemble the LANpad landing page into _site/ (for GitHub Pages deployment).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/_site"

rm -rf "$OUT"
mkdir -p "$OUT/assets"

cp "$ROOT/site/index.html" "$ROOT/site/site.css" "$ROOT/site/site.js" "$OUT/"
cp "$ROOT/packaging/icons/lanpad.svg" "$OUT/assets/"
cp "$ROOT/packaging/icons/lanpad.png" "$OUT/assets/" 2>/dev/null || true
cp "$ROOT/packaging/icons/lanpad.ico" "$OUT/assets/" 2>/dev/null || true

# Query latest release info if available
if command -v curl >/dev/null; then
  auth=()
  [ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
  curl -fsSL "${auth[@]}" "https://api.github.com/repos/mohamedjs/lanpad/releases/latest" -o "$OUT/release.json" 2>/dev/null \
    || echo "warning: no release.json; GitHub API will be queried by client"
fi

touch "$OUT/.nojekyll"
echo "Built $OUT ($(du -sh "$OUT" | cut -f1))"
