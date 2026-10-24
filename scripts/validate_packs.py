#!/usr/bin/env python3
"""Validate every resource pack in the repo.

    python3 scripts/validate_packs.py [root]

Checks, for loose files in the tree and for every entry inside every *.zip:
  - each .json / .mcmeta parses as JSON
  - each .png starts with the PNG signature
  - each zip has pack.mcmeta at its root
Then prints a size report. Exits 1 on any error, and also when it found no zip to check,
so a broken checkout can't pass by checking nothing.
"""
import json
import os
import sys
import zipfile

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

errors = []
warnings = []


def check_entry(where: str, name: str, data: bytes) -> None:
    lower = name.lower()
    if lower.endswith((".json", ".mcmeta")):
        if data.startswith(b"\xef\xbb\xbf"):
            warnings.append(f"{where}: {name}: starts with a UTF-8 BOM")
            data = data[3:]
        try:
            json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            errors.append(f"{where}: {name}: invalid JSON ({e})")
    elif lower.endswith(".png"):
        if not data.startswith(PNG_SIGNATURE):
            errors.append(f"{where}: {name}: not a PNG (bad signature)")


def check_zip(path: str) -> tuple[int, int, int]:
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as e:
        errors.append(f"{path}: not a zip ({e})")
        return 0, 0, 0
    with zf:
        bad = zf.testzip()
        if bad is not None:
            errors.append(f"{path}: CRC mismatch in {bad}")
        names = [i for i in zf.infolist() if not i.is_dir()]
        if "pack.mcmeta" not in {i.filename for i in names}:
            errors.append(f"{path}: no pack.mcmeta at the zip root")
        for info in names:
            check_entry(path, info.filename, zf.read(info))
        return len(names), sum(i.file_size for i in names), sum(i.compress_size for i in names)


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    zips = []
    loose = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            path = os.path.join(dirpath, fn)
            if fn.lower().endswith(".zip"):
                zips.append(path)
            elif fn.lower().endswith((".json", ".mcmeta", ".png")):
                loose += 1
                with open(path, "rb") as f:
                    check_entry("tree", os.path.relpath(path, root), f.read())

    if not zips:
        errors.append(f"no *.zip found under {root}")

    print(f"{'pack':<34} {'files':>6} {'zip bytes':>12} {'unpacked':>12}")
    for path in zips:
        count, unpacked, _ = check_zip(path)
        print(f"{os.path.relpath(path, root):<34} {count:>6} {os.path.getsize(path):>12,} {unpacked:>12,}")
    print(f"loose json/mcmeta/png files checked: {loose}")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(zips)} zip(s), {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
