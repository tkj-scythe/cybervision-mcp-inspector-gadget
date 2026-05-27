#!/usr/bin/env bash
# Fail if tracked files look like they contain Cyber Vision API tokens.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

patterns='ics-[a-f0-9]{20,}|CYBERVISION_API_TOKEN=[^[:space:]]+'
found=0

while IFS= read -r file; do
  [[ "$file" == ".env.example" ]] && continue
  if grep -qE "$patterns" "$file" 2>/dev/null; then
    echo "ERROR: possible secret in tracked file: $file" >&2
    found=1
  fi
done < <(git ls-files)

if [[ -f .env ]] && git check-ignore -q .env; then
  : # expected: local secrets stay ignored
elif [[ -f .env ]]; then
  echo "ERROR: .env exists but is not gitignored" >&2
  found=1
fi

if [[ "$found" -ne 0 ]]; then
  exit 1
fi

echo "OK: no secrets detected in tracked files."
