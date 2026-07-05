# iOS Original Asset Manifest Plan

**Date**: 2026-07-05
**Status**: Active first-step plan
**Scope**: GeneralsXZH iOS original asset replacement

## Purpose

Build the first reliable inventory of assets required by the iOS build before
creating replacement art. The current iOS package path bundles
`$HOME/GeneralsX/GeneralsZH` into `GeneralsXZH.app/GameData`, plus staged fonts
and iOS config. The repository itself does not contain the full production asset
set, so the manifest must be generated from a staged deploy tree and, in the
next pass, indexed `.big` archive contents.

The full production roadmap lives in
`docs/WORKDIR/planning/PLAN-023_IOS_ORIGINAL_ASSET_PIPELINE.md`.

## Manifest Outputs

The manifest pass must produce:

- Machine-readable JSON for automation.
- Markdown summary for review.
- Category counts by asset type.
- Largest-file report for memory and package-size triage.
- Archive list for `.big` containers that still need extraction/indexing.
- Reference graph from text assets where references are visible.
- Missing-reference report for assets that are archived, extensionless, or not
  yet replaced.
- Package validation gate for generated original asset packs before signing.

## Current Scanner

Run:

```bash
scripts/tooling/assets/build_ios_required_asset_manifest.sh \
  "$HOME/GeneralsX/GeneralsZH"
```

For deterministic source validation, add `--hash` to include SHA-256 hashes for
every loose file when invoking `scan_ios_asset_manifest.py` directly.

The wrapper rejects the tiny repo fixture and requires a staged tree with
root-level `.big` archives, then writes:

- `build/asset-manifest/ios_required_asset_manifest.json`
- `build/asset-manifest/ios_required_asset_inventory.md`

The current scanner inventories loose files, indexes `.big` directory entries,
parses small text entries inside archives, extracts typed INI dependencies for
common model/UI/audio/texture fields, scans W3D chunk strings for texture/model
references, scans binary map/UI payloads for embedded asset tokens, and indexes
CSF labels. It does not yet fully decode every W3D struct, DDS metadata, or
every map/CSF binary field.

## Required Asset Buckets

### Runtime Package

- `.big` archives or replacement package format.
- INI gameplay/object/UI/audio/particle definitions.
- iOS `Options.ini`, `DefaultOptions.ini`, and `dxvk.conf`.
- File manifests, dependency graphs, preload groups, and fallback assets.

### 3D World

- Terrain textures and blend sets.
- Props: trees, rocks, bridges, civilian buildings, oil derricks, clutter.
- Water, shore, foam, reflection/noise textures.
- Shroud/fog-of-war masks.
- Selection rings, command radius markers, rally markers.

### Units and Buildings

- Original faction unit models for infantry, vehicles, aircraft, drones, and
  variants.
- Original faction building models for base, tech, defense, and superweapon
  roles.
- Damaged, construction, wrecked, rubble, debris, and collision/LOD assets.

### Animation

- Infantry locomotion, attack, idle, garrison, evacuation, and death clips.
- Vehicle wheels, tracks, turrets, barrels, recoil, deploy states.
- Aircraft rotors, landing gear, takeoff, landing, banking states.
- Building construction, idle machinery, damage, and destruction clips.

### Textures and Materials

- Albedo/diffuse textures.
- Team-color masks.
- Normal maps where useful at the RTS camera distance.
- Packed roughness/metalness/specular maps where supported.
- Emissive, damage, burn, alpha-cutout, and LOD texture variants.
- Offline mip chains and iOS texture-compression variants.

### VFX and Particles

- Explosions, smoke, dust, fire, sparks, shockwaves.
- Muzzle flashes, missiles, bullets, tracers, beams.
- Toxin, radiation, napalm, weather, tire trails, scorch decals.
- Particle atlases and particle INI definitions with iOS max-count budgets.

### UI and Touch

- Shell/menu backgrounds, loading screens, buttons, panels, tabs, frames.
- Command bar icons, unit/building portraits, upgrade icons, general powers.
- Minimap frame and overlays.
- Touch overlays, cursor/pointer states, controller glyphs if enabled.
- Retina/iPad-safe atlases and `.wnd` definitions or replacements.

### Maps

- Skirmish validation maps.
- Campaign maps if supported.
- Heightfields, texture blends, object placement, waypoints, scripts, triggers.
- Minimap previews and map metadata.

### Audio, Video, Fonts, Localization

- Unit voices, EVA/system voice, weapon SFX, impacts, ambience, UI SFX, music.
- iOS-friendly video transcodes for any supported cinematic/menu loops.
- Windows-name-compatible font aliases currently expected by packaging:
  `arial.ttf`, `arialbold.ttf`, `couriernew.ttf`, `timesnewroman.ttf`.
- Localized string tables and Unicode fallback coverage.

## First Replacement Batch

The first generated batch should be a complete vertical slice:

- App shell/UI frame and button atlas.
- One terrain tile set.
- One skirmish validation map.
- One command center, one power building, one production building.
- One infantry unit and one ground vehicle.
- One projectile, explosion effect, and scorch decal.
- One command icon/portrait set.
- One music loop, one UI click, one weapon SFX, and one explosion SFX.

After generating the hard manifest, create the first worklist with:

```bash
scripts/tooling/assets/create_ios_playable_slice_worklist.py \
  --manifest build/asset-manifest/ios_required_asset_manifest.json \
  --out-dir ios-original-assets
```

This creates the source/generated workspace and writes:

- `ios-original-assets/manifest/playable_slice_worklist.json`
- `ios-original-assets/manifest/PLAYABLE_SLICE_WORKLIST.md`

When the generated pack is ready, package it with:

```bash
GX_ORIGINAL_ASSET_PACK="$PWD/ios-original-assets/generated/GameData" \
  scripts/build/ios/package-ios-zh.sh
```

The package script copies that generated tree into the app bundle and validates
the bundled `GameData` manifest before signing.

## Next Engineering Tasks

1. Expand typed INI coverage for less common object, weapon, FX, science, and
   command-button fields.
2. Deepen W3D dependency decoding for animation hierarchy links, skeletons, LOD
   collections, and texture replacer structs beyond first-pass string scanning.
3. Decode map and UI binary formats where references are not visible as strings.
4. Generate per-map and per-faction preload groups.
5. Add budget checks for texture dimensions, model LOD presence, and oversized
   audio/video files.
6. Replace selected worklist entries with generated original source and shipping
   files under `ios-original-assets/`.
