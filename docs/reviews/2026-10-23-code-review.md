# Code Review: romanica-resourcepack (2026-10-23)

> **Repo:** Romanica-MC/romanica-resourcepack · **Reviewed commit:** `0e5df6a` (main) · **Method:** static review + scripted validation of all committed zips (JSON parse, PNG signature checks, per-entry CRC diffing, sounds.json reference resolution, pack-format cross-check)
> Severities: **P0** = broken now · **P1** = likely breakage · **P2** = design debt · **P3** = nice-to-have

## Project Snapshot

Server resource pack for Romanica/ImperiumMC, a Rome-themed Minecraft prison server (Java + Bedrock via Geyser). There is no source tree at HEAD — the repo is 6 committed zip artifacts (~107 MB working tree, 124 MB `.git`) produced by the packsmc.com conversion service, plus README, .gitignore, and a stray `clouds.png`. The current base pack (`resourcepack.zip`, v2.0.8) contains 1,543 files: 1,104 PNGs, 60 JSONs, 358 `.mcmeta`, 19 oggs — all under a single `minecraft` namespace (pure vanilla overrides, no custom namespace). Activity is low: 4 commits (Jul 2 – Aug 8, 2026) but 43 release tags from v1.0.0 to v2.0.6, mostly authored July 9.

## Structure & Asset Assessment

- **Base pack** (`resourcepack.zip`, 48.9 MB zip / 56.3 MB unpacked, `pack.mcmeta` = format 88): textures block 841, item 255, entity 148, gui 123, painting 52, models 14, misc 12, environment 6 (incl. transparent `clouds.png`), colormap 2, font 2, map 2, particle 2. JSON: 45 `items/` (1.21.4+ item definitions), 6 `equipment/`, 4 `models/block/`, 3 `blockstates/`, 2 `atlases/`. Sounds: 19 oggs at vanilla paths (14 zombie, 4 blaze, `records/13`), no `sounds.json`.
- **"Format" zips** (`resourcepack-format{1,2,3,4,84}.zip`, 696 files each): per-entry CRC comparison proves all five are **byte-identical in content** — only zip entry timestamps differ. None contains a `pack.mcmeta`. They hold an older, smaller texture set plus a misplaced `assets/minecraft/sounds/sounds.json` (defines `custom_sound`, `gang_upgrade`, `shop_purchase`) referencing **zero ogg files**.
- **Verification performed:** every JSON and `.mcmeta` parsed (0 malformed in both zips), PNG signatures/dimensions checked, per-entry CRC diff of format zips, texture-reference resolution, duplicate-PNG hashing, `pack.mcmeta` formats cross-checked against the Minecraft wiki (26.2 = 88.0, 26.1 = 84.0 — both real; the historical mappings in the commit message are not).

## Strengths

- **Zero malformed files.** All 60 JSONs and 358 `.mcmeta`s across both pack generations parse cleanly; all PNGs have valid signatures.
- **Correct modern format usage** in `resourcepack.zip`: `atlases/items.json` uses `paletted_permutations` for trims; `items/chest.json` implements a Christmas chest via `minecraft:local_time` select cases ("12-24"…"12-26"); `equipment/*.json` use the 1.21.2+ layer format; `blockstates/smooth_stone_slab.json` + matching slab models are a clean custom-geometry override.
- **`pack_format: 88` is correct** for Minecraft 26.2, and the modern `min_format`/`max_format` int-array keys are the right mechanism.
- **Sound override strategy is sound:** 19 oggs placed at vanilla paths (`mob/zombie/*`, `mob/blaze/*`, `records/13.ogg`) override vanilla sound events without needing `sounds.json`.
- **`clouds.png` (16×16 RGBA, fully transparent) is the correct technique** to hide clouds server-side, and was correctly propagated into all 6 zip variants (commit `bb814a8`).
- Multi-version intent (ViaRewind/ViaBackwards per the commit message) shows the right compatibility instinct, even though the implementation fell short (see issues).

## Issues

- **[P0] All five `resourcepack-format*.zip` ship without `pack.mcmeta`** — verified by extraction; the file exists only in `resourcepack.zip`. Per the commit message these are "auto-detected by version, forced download on join", so every legacy-version client receiving one will reject the pack outright (a client cannot load a pack with no pack.mcmeta). The entire formats-1-88 scheme is currently non-functional as committed artifacts; it only works if the packsmc.com serving layer injects one at download time, which nothing in the repo documents.
- **[P1] The per-format variants are identical content** — CRC-verified identical across format1/2/3/4/84, so "Format 1: 1.7-1.9" etc. is fictional. Even with an injected pack.mcmeta, 1.7–1.12 clients get a pack built from 1.13+ texture paths (`textures/block/`, not `textures/blocks/`) and cannot resolve it; the legacy variants contain none of the actual per-format conversion work the filenames advertise. ~47 MB of redundant tracked binaries.
- **[P1] `min_format: [3, 0]` in `resourcepack.zip:pack.mcmeta` claims compatibility back to pack format 3 (1.11)** while the pack uses 1.21.2+ `equipment/`, 1.21.4+ `items/` definitions, and 1.19.3+ atlases. Any client in the 1.11–1.21.1 window served this pack will hard-fail on unknown asset types. The true floor is ~[46, 0] (1.21.4). `max_format: [999, 0]` is likewise an over-promise against future format bumps.
- **[P1] Custom sounds regression in the base pack.** The legacy zips define `custom_sound`, `gang_upgrade`, `shop_purchase` (in a misplaced `assets/minecraft/sounds/sounds.json`, and with no oggs shipped — doubly broken), and the v2.0.8 base pack (`resourcepack.zip`) ships **neither** `sounds.json` nor those three oggs. Any server plugin calling `/playsound minecraft:custom_sound` (or the gang/shop events) is silent under the current base pack.
- **[P2] Zips are committed to the repo, directly contradicting `README.md`** ("Packs are distributed as versioned GitHub Releases, not committed to this repo's tree"). v2.0.7 and v2.0.8 exist only as tree-committed zips with no tags/releases (latest release is v2.0.6), while each update rewrites ~12–49 MB into git history (`.git` already 124 MB). `resourcepack.zip` at 48.9 MB is also within 1.1 MB of GitHub's 50 MB warning threshold, so this cannot continue for long.
- **[P2] Commit `679b9a6`'s version→format map is wrong and will mislead future work.** Real values: 1.20.4 = 22 (not 84), 1.20.5 = 32 (not 88), format 3 = 1.11–1.12.2 (not "1.13-1.20.2"), format 4 = 1.13–1.14.4 (not "1.20.3"). Only 84→26.1 and 88→26.2 are right, and "Paper 26.x" conflates server software with client pack formats.
- **[P2] No build or validation tooling exists.** No scripts, no `.github/` CI, no way to regenerate the six zips deterministically — the last commit was a hand-rolled "ImperiumMC Bot" commit shipping a 48.9 MB binary. Every quality check in this review (JSON parse, sounds refs, format mapping) is unscripted and therefore unrepeatable.
- **[P3] Asset junk shipped inside the packs:** `assets/minecraft/.packsmc/conversion_id` and `pack.credits.txt` (service markers), `assets/minecraft/font/old font/default.png` (space in dir name, no font JSON references it), pre-1.13 path leftovers (`textures/entity/endercrystal/*` — modern path is `end_crystal/`), legacy single painting textures (`painting/graham.png` etc. alongside the modern sheets), and 56 duplicate PNG groups (~1.1 MB).
- **[P3] Download weight from HD re-exports:** 1024×1024 GUI textures (`gui/container/horse.png` and `hopper.png` at 4.1 MB each), six ~1.5 MB panorama frames, 2.6 MB painting sheet — roughly 14 MB of the 48.9 MB. Also 51 `_n` normal maps + 16 other PBR-suffix maps that vanilla Java does not consume unless Vibrant-Visuals-style PBR is active — verify they're actually used before paying for 109 HD textures.
- **[P3] Stale metadata:** `pack.mcmeta` description says "ImperiumMC Texture Pack **v2.0.7**" inside the v2.0.8 zip. A stray `clouds.png` is tracked at the repo root (build scratch that escaped the new `.gitignore`).

## Tooling & CI

There is no CI, no build script, and no validation step. Releases (v1.0.0–v2.0.6) were previously tagged on GitHub with assets (v2.0.6 on Jul 9 with 3 assets; release notes reference a 99.3 MB full pack and a 48.6 MB "MINARECRAFTORVM … LITE" variant), but that pipeline stopped at v2.0.6 — the last two versions are raw commits. Nothing in the repo can rebuild the zips, bump `pack.mcmeta`, or check that sounds/fonts/atlases resolve.

## Top Recommendations

1. **Fix or delete the format variants (P0).** Either generate genuinely converted per-format packs (correct texture paths, per-format `pack.mcmeta` with the right `pack_format`: 1/2/3/4/22/32…/84/88) or drop the five zips and serve the single base pack to everyone above its true minimum.
2. **Restore custom sounds:** move `sounds.json` to `assets/minecraft/sounds.json` (namespace root) in whatever pack is served and re-add `custom_sound.ogg`, `gang_upgrade.ogg`, `shop_purchase.ogg` — then verify with `/playsound` in-game on both a 26.2 client and a ViaBackwards client.
3. **Honest `pack.mcmeta`:** set `min_format` to the real feature floor (~[46, 0] given `items/` + `equipment/`), bound `max_format` to something real, and bump the description to v2.0.8.
4. **Stop committing zips; resume tagging.** Make releases the distribution channel again (the README already promises it), tag v2.0.7/v2.0.8 retroactively or supersede them with v2.0.9, and keep binaries out of the tree — at 48.9 MB you're one update from GitHub's 50 MB warning.
5. **Add a CI validator** (a single Python script run on push): parse all JSON/`.mcmeta`, verify PNG signatures and dimensions, check `sounds.json` → ogg resolution, texture refs, duplicate hashes, and print the format→version table. Everything flagged above is mechanically checkable.
6. **Asset diet:** drop `.packsmc/`, `pack.credits.txt`, `old font/`, `entity/endercrystal/`, legacy painting singles, and the 56 duplicate PNGs; re-encode the 1024² GUI/panorama textures (or justify them) — this alone likely cuts ~20% of download size, which matters for forced-download-on-join.
