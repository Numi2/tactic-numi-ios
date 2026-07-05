#!/usr/bin/env python3
"""Create the first iOS original playable-slice worklist from a hard manifest."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_LIMITS = {
    "ini": 40,
    "ui": 80,
    "maps": 12,
    "models": 120,
    "textures": 180,
    "audio": 100,
    "video": 12,
    "localization": 40,
    "fonts": 8,
}

SOURCE_SUBDIRS = [
    "source/blender",
    "source/imagen-prompts",
    "source/textures",
    "source/audio",
    "source/ui",
    "source/maps",
    "source/localization",
    "generated/GameData",
    "manifest",
    "validation",
]


def load_manifest(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"ERROR: manifest not readable: {path}: {exc}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: manifest is not valid JSON: {path}: {exc}")


def dependency_category(record):
    return record.get("category_hint") or record.get("target_category") or "other"


def collect_required_assets(manifest):
    indexed_by_path = {}
    for item in manifest.get("files", []):
        indexed_by_path[item.get("path", "").lower()] = item
    for item in manifest.get("archive_entries", []):
        indexed_by_path[item.get("archive_entry", "").lower()] = item

    required = {}
    for item in manifest.get("files", []):
        path = item.get("path")
        if not path:
            continue
        required[path] = {
            "path": path,
            "category": item.get("category") or "other",
            "bytes": item.get("bytes"),
            "source_references": [],
        }

    for record in manifest.get("resolved_references", []):
        target = record.get("target")
        if not target:
            continue
        key = target.lower()
        target_info = indexed_by_path.get(key, {})
        category = target_info.get("category") or record.get("category_hint") or "other"
        required.setdefault(target, {
            "path": target,
            "category": category,
            "bytes": target_info.get("bytes"),
            "source_references": [],
        })
        required[target]["source_references"].append({
            "source": record.get("source"),
            "reference": record.get("reference"),
            "kind": record.get("kind", "reference"),
            "origin": record.get("origin"),
        })
    return list(required.values())


def select_first_slice(required_assets, limits):
    grouped = defaultdict(list)
    for asset in required_assets:
        grouped[asset["category"]].append(asset)
    selected = []
    categories = sorted(set(grouped) | set(limits))
    for category in categories:
        candidates = sorted(
            grouped.get(category, []),
            key=lambda item: (-len(item["source_references"]), item["path"].lower()),
        )
        selected.extend(candidates)
    return selected


def write_markdown(path, manifest_path, selected, missing_count):
    by_category = defaultdict(list)
    for asset in selected:
        by_category[asset["category"]].append(asset)

    lines = [
        "# iOS Original Playable Slice Worklist",
        "",
        f"Source manifest: `{manifest_path}`",
        "",
        "## Gate Status",
        "",
        f"- Hard missing references in source manifest: {missing_count}",
        f"- Selected required assets: {len(selected)}",
        "",
        "## Source Layout",
        "",
    ]
    for subdir in SOURCE_SUBDIRS:
        lines.append(f"- `{subdir}/`")

    lines.extend([
        "",
        "## Asset Worklist",
        "",
    ])
    for category in sorted(by_category):
        lines.extend([
            f"### {category}",
            "",
            "| Asset | References |",
            "|---|---:|",
        ])
        for asset in by_category[category]:
            lines.append(f"| `{asset['path']}` | {len(asset['source_references'])} |")
        lines.append("")

    lines.extend([
        "## Completion Rules",
        "",
        "- Every selected asset must have an original source file under `source/`.",
        "- Every generated shipping asset must land under `generated/GameData/` with the manifest path preserved.",
        "- No generated package can ship while source manifest hard missing references remain.",
        "- Models need LOD and collision/proxy authoring before they count as complete.",
        "- Textures need offline mipmaps and iOS compression before they count as complete.",
        "- Audio must be split into streamed long-form and memory-ready short SFX before it counts as complete.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create an iOS playable-slice worklist from the hard asset manifest")
    parser.add_argument("--manifest", default="build/asset-manifest/ios_required_asset_manifest.json",
                        help="Hard manifest JSON produced by build_ios_required_asset_manifest.sh")
    parser.add_argument("--out-dir", default="ios-original-assets",
                        help="Playable-slice workspace root")
    parser.add_argument("--allow-missing", action="store_true",
                        help="Generate a worklist even when the manifest has hard missing references")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    missing_count = manifest.get("summary", {}).get("missing_reference_count", 0)
    if missing_count and not args.allow_missing:
        print(f"ERROR: source manifest has {missing_count} hard missing references; rerun with --allow-missing only for diagnostics.", file=sys.stderr)
        return 2

    required_assets = collect_required_assets(manifest)
    if not required_assets:
        print("ERROR: source manifest has no resolved required assets.", file=sys.stderr)
        return 1

    selected = select_first_slice(required_assets, DEFAULT_LIMITS)
    out_dir = Path(args.out_dir)
    for subdir in SOURCE_SUBDIRS:
        (out_dir / subdir).mkdir(parents=True, exist_ok=True)

    json_out = out_dir / "manifest" / "playable_slice_worklist.json"
    md_out = out_dir / "manifest" / "PLAYABLE_SLICE_WORKLIST.md"
    json_out.write_text(json.dumps({
        "source_manifest": str(manifest_path),
        "missing_reference_count": missing_count,
        "selected_assets": selected,
        "source_subdirs": SOURCE_SUBDIRS,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, manifest_path, selected, missing_count)

    print(f"Selected {len(selected)} assets from {len(required_assets)} resolved required assets")
    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
