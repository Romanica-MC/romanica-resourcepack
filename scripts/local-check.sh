#!/usr/bin/env bash
# Local replacement for .github/workflows/validate.yml (Actions permanently off, owner 2026-10-30).
# CI compared raw bytes; zlib deflate streams differ across python builds (same content,
# different compressed bytes), so the local check compares per-entry content + the file
# list — the same reproducibility guarantee, machine-portable.
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/validate_packs.py .
python scripts/build_pack.py resourcepack.zip rebuilt-local.zip
python - << 'PY'
import zipfile, sys
a = zipfile.ZipFile('resourcepack.zip'); b = zipfile.ZipFile('rebuilt-local.zip')
na = sorted(i.filename for i in a.infolist()); nb = sorted(i.filename for i in b.infolist())
assert na == nb, f"file list differs: {set(na) ^ set(nb)}"
diff = [n for n in na if a.read(n) != b.read(n)]
assert not diff, f"content differs: {diff[:5]}"
print(f"rebuild content-identical: {len(na)} entries, 0 differences")
PY
rm -f rebuilt-local.zip
echo "LOCAL CHECK: ALL GREEN"
