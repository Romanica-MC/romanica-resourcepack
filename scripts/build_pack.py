#!/usr/bin/env python3
"""Rebuild a resource pack zip deterministically.

    python3 scripts/build_pack.py <input.zip> <output.zip>

Drops the junk entries listed below, sets the pack.mcmeta description, and writes every
entry in sorted order with a fixed timestamp, fixed permissions and the same compression,
so the same input always gives a byte-identical output (and the same SHA-1). The plugin
pins that SHA-1, so an accidental rebuild must not change it.
"""
import json
import re
import sys
import zipfile

DESCRIPTION = "Romanica Texture Pack v2.0.8"

# Conversion leftovers from the packsmc.com converter, and an unreferenced font backup.
DROP_EXACT = {"pack.credits.txt"}
DROP_PREFIXES = ("assets/minecraft/.packsmc/", "assets/minecraft/font/old font/")

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o100644
DESCRIPTION_RE = re.compile(r'("description"\s*:\s*)"(?:[^"\\]|\\.)*"')


def dropped(name: str) -> bool:
    return name in DROP_EXACT or name.startswith(DROP_PREFIXES)


def set_description(raw: bytes) -> bytes:
    # Edit the string in place rather than re-serialising, so the rest of the file keeps
    # its exact bytes.
    text = raw.decode("utf-8")
    new, count = DESCRIPTION_RE.subn(lambda m: m.group(1) + json.dumps(DESCRIPTION), text)
    if count != 1:
        raise SystemExit(f"pack.mcmeta: expected one description, found {count}")
    if json.loads(new)["pack"]["description"] != DESCRIPTION:
        raise SystemExit("pack.mcmeta: description edit did not take")
    return new.encode("utf-8")


def build(src: str, dst: str) -> None:
    with zipfile.ZipFile(src) as zin:
        names = sorted(n for n in zin.namelist() if not n.endswith("/") and not dropped(n))
        if "pack.mcmeta" not in names:
            raise SystemExit(f"{src}: no pack.mcmeta at the zip root")
        data = {n: zin.read(n) for n in names}
    data["pack.mcmeta"] = set_description(data["pack.mcmeta"])

    with zipfile.ZipFile(dst, "w") as zout:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = FILE_MODE << 16
            zout.writestr(info, data[name], compresslevel=9)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])
