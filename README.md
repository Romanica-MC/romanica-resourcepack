# Romanica Resource Pack

Custom textures and sounds for the Romanica server (Java, plus Bedrock through Geyser).

## What's here

| File | What it is |
| --- | --- |
| `resourcepack.zip` | The Java BASE pack, "Romanica Texture Pack v2.0.8" (`pack_format` 88). This is the pack the server sends. |
| `resourcepack-format{1,2,3,4,84}.zip` | Legacy per-format variants. They have a `pack.json` but no `pack.mcmeta`, so Minecraft won't load them as they are. `scripts/validate_packs.py` reports this. |
| `scripts/build_pack.py` | Rebuilds `resourcepack.zip` deterministically: sorted entries, fixed timestamps, no converter leftovers. |
| `scripts/validate_packs.py` | Checks that every JSON/mcmeta parses, that every PNG has a valid signature, and that every zip has a root `pack.mcmeta`. Prints a size report. CI runs it on every push and PR. |

The zips are committed to the tree, and the same builds are also attached to the `textures` release. The server pushes the pack from its release URL, and the plugin pins its SHA-1. **Changing a served zip therefore needs a matching change to the plugin config (URL + SHA-1).**

## Rebuild and check

```sh
python3 scripts/build_pack.py resourcepack.zip resourcepack.new.zip
mv resourcepack.new.zip resourcepack.zip
python3 scripts/validate_packs.py
sha1sum resourcepack.zip   # put this in the plugin config with the new URL
```

Running `build_pack.py` on its own output gives the same bytes, so the SHA-1 only changes when the content does.

The Bedrock packs (`ImperiumMC_Bedrock_v1/v2.zip`) and the EFFECTS pack exist only as release assets, not in this tree.
