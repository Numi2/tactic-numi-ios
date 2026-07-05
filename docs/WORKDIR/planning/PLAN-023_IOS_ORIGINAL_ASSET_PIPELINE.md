# PLAN-023: iOS Original Asset Pipeline

**Date**: 2026-07-05
**Status**: Proposed
**Scope**: GeneralsXZH first, shared asset tooling where applicable

## Goal

Replace the deploy-time retail asset dependency with an original,
iOS-optimized asset set that preserves gameplay readability while reducing
startup latency, memory pressure, and runtime decode work.

This plan is asset-pipeline work only. Gameplay determinism remains protected:
visual, audio, UI, and packaging changes must not alter simulation logic.

## Asset Classes Required

### Runtime Package

- Asset manifest and dependency graph.
- Replacement package layout for iOS bundle resources.
- Preload groups for shell, map, faction, and combat phases.
- Fallback model, fallback texture, fallback audio, and missing-icon assets.
- `Options.ini`, `DefaultOptions.ini`, and `dxvk.conf` variants for iOS.

### 3D Models

- Faction units: infantry, ground vehicles, aircraft, drones, deployables.
- Faction buildings: base structures, tech structures, defenses, superweapons.
- Civilian world props: buildings, vehicles, clutter, vegetation, bridges.
- Destruction states: damaged meshes, wrecks, rubble, debris chunks.
- Construction states and build pads.
- Collision/simple proxy meshes and LOD chains for every gameplay-visible model.

### Textures and Materials

- Albedo/diffuse maps.
- Team-color masks.
- Alpha-cutout maps for foliage, flags, fences, and wires.
- Damage, scorch, burn, and rubble overlays.
- Normal maps where they improve readability under the RTS camera.
- Packed material maps for roughness/metalness/specular where supported.
- Terrain tile sets, blend maps, cliff sets, road sets, and shore/water maps.
- Offline-generated mip chains and iOS texture-compression variants.

### Animation

- Infantry locomotion, idle, attack, garrison, death, and special-state clips.
- Vehicle wheel, track, turret, barrel, recoil, and deploy animations.
- Aircraft rotor, landing gear, banking, takeoff, and landing animations.
- Building construction, idle machinery, damage, and destruction animations.
- Animation naming compatibility with existing INI object definitions.

### VFX

- Particle atlases for smoke, dust, fire, sparks, muzzle flashes, shockwaves.
- Projectile trails, missile exhaust, laser/beam effects, toxin/radiation fields.
- Terrain decals for craters, scorch marks, tire tracks, and blast residue.
- Weather and ambient battlefield effects.
- iOS-tuned particle system definitions with strict max-count budgets.

### UI and Touch

- App icon and launch/splash art.
- Shell/menu backgrounds, frames, buttons, tabs, and state variants.
- Command bar icons, unit portraits, upgrade icons, and general power icons.
- Selection rings, rally markers, radius markers, minimap overlays.
- Touch-specific controls, pointer states, gesture affordances, and iPad scaling.
- Retina atlases with predictable dimensions and no runtime resizing.

### Maps

- Original skirmish test maps and vertical-slice validation maps.
- Heightfields, texture blend maps, water masks, object placement, waypoints.
- Minimap previews and map metadata.
- AI scripts/triggers where required by the map format.

### Audio

- Unit voice sets and faction response sets.
- EVA/system voice.
- Weapon, impact, explosion, vehicle, aircraft, building, and UI SFX.
- Ambient loops and music.
- Streamed long-form audio and memory-resident short SFX groups.

### Video and Localization

- Original intro/menu/campaign video replacements where supported.
- Localized strings and font coverage.
- iOS-bundled font aliases for names expected by the engine.

## Tooling Plan

### Phase 1: Inventory

Use `scripts/tooling/assets/scan_ios_asset_manifest.py` against the current
deploy tree:

```bash
scripts/tooling/assets/scan_ios_asset_manifest.py \
  "$HOME/GeneralsX/GeneralsZH" \
  --json-out build/asset-manifest/ios_asset_manifest.json \
  --md-out build/asset-manifest/ios_asset_inventory.md
```

The first scan inventories loose files, indexes `.big` archive directory
entries, parses small text entries inside archives, extracts common typed INI
dependencies, scans W3D chunk/string references, scans binary map/UI payloads
for embedded asset tokens, and indexes CSF labels. Full coverage still requires
deeper typed parsers for every W3D, map, DDS, and localization field.

### Phase 2: Dependency Graph

- Expand INI object definitions to model, animation, texture, particle, audio,
  icon, and localization dependencies.
- Deepen W3D, map, UI, and localization binary decoding where references are
  not visible through string scanning.
- Generate per-map and per-faction preload groups.
- Fail the pipeline when an original replacement pack has unresolved required
  dependencies.

### Phase 3: Generation

- Use Imagen for original concept sheets, loading art, icon drafts, decals, and
  texture references.
- Use Blender headless for mesh generation, cleanup, LOD creation, collision
  proxies, baking, and export validation.
- Use offline audio tools for loudness normalization, compression, and stream
  separation.
- Use atlas/compression tooling for ASTC-first iOS textures and current-engine
  fallback formats.

### Phase 4: Packaging

- Add a generated asset-pack source path to `scripts/build/ios/package-ios-zh.sh`.
- Bundle generated assets under `GameData` or a future iOS-native asset root.
- Keep `--dev` code-only packaging fast.
- Add package-time validation for missing files and oversized assets.

### Phase 5: Runtime Validation

- Launch the app with bundled generated assets.
- Load the shell and one skirmish validation map.
- Verify no missing asset fallbacks are hit.
- Track resident memory, startup time, map load time, and frame pacing.
- Confirm replay determinism is unaffected by replacement visual/audio assets.

## iOS Budget Targets

Initial targets, to be tuned with device captures:

- Texture compression: ASTC for iOS-native packs, DDS-compatible fallback while
  the current DXVK path requires legacy compatibility.
- Terrain textures: prefer 512-1024 px tiles with offline mip chains.
- Unit textures: 512 px common units, 1024 px hero/large units.
- Building textures: 1024 px common, 2048 px only for large first-screen assets.
- Audio: stream music and long ambience; keep short combat/UI SFX memory-ready.
- Models: require LODs and collision proxies before an asset can enter a map.
- Particles: cap emitter counts by effect class and map visibility.

## First Vertical Slice

The first original pack should be small and complete:

- One test terrain tile set.
- One simple skirmish validation map.
- One faction command center.
- One power building.
- One production building.
- One infantry unit.
- One ground vehicle.
- One projectile and explosion effect.
- One command bar icon/portrait set.
- One UI shell background and button atlas.
- One music loop, one UI click, and one weapon/explosion SFX set.

This slice gives the pipeline enough coverage to test model, texture, UI, audio,
map, particle, package, and runtime memory behavior without attempting the full
game at once.

## Acceptance Criteria

- The scanner produces JSON and Markdown reports for a staged asset tree.
- The manifest identifies loose files, archive containers, category counts,
  largest files, and unresolved references.
- The original asset pipeline has documented budgets and phase gates.
- The next engineering task is clear: add BIG archive indexing and dependency
  resolution.
