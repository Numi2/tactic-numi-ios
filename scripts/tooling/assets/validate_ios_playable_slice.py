#!/usr/bin/env python3
"""Validate a generated iOS original playable slice against its worklist."""
import argparse
import json
import sys
from pathlib import Path


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")


def candidate_paths(game_data_root, asset_path):
    normalized = asset_path.replace("\\", "/").lstrip("/")
    candidates = [game_data_root / normalized]
    lower_name = Path(normalized).name.lower()
    for path in game_data_root.rglob("*"):
        if path.is_file() and path.name.lower() == lower_name:
            candidates.append(path)
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Validate generated original iOS slice assets")
    parser.add_argument("--worklist", default="ios-original-assets/manifest/playable_slice_worklist.json",
                        help="Playable-slice worklist JSON")
    parser.add_argument("--game-data", default="ios-original-assets/generated/GameData",
                        help="Generated GameData root")
    parser.add_argument("--report", default=None,
                        help="Optional JSON validation report path")
    args = parser.parse_args()

    worklist_path = Path(args.worklist)
    game_data_root = Path(args.game_data)
    if not game_data_root.is_dir():
        print(f"ERROR: generated GameData root not found: {game_data_root}", file=sys.stderr)
        return 1

    worklist = load_json(worklist_path)
    selected = worklist.get("selected_assets", [])
    missing = []
    present = []
    for asset in selected:
        asset_path = asset.get("path")
        if not asset_path:
            continue
        matches = [path for path in candidate_paths(game_data_root, asset_path) if path.is_file()]
        if matches:
            present.append({"path": asset_path, "matched": str(matches[0])})
        else:
            missing.append({"path": asset_path, "category": asset.get("category", "other")})

    report = {
        "worklist": str(worklist_path),
        "game_data": str(game_data_root),
        "selected_count": len(selected),
        "present_count": len(present),
        "missing_count": len(missing),
        "present": present,
        "missing": missing,
    }
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if missing:
        print(f"ERROR: generated slice is missing {len(missing)} selected assets", file=sys.stderr)
        for item in missing[:50]:
            print(f"  missing {item['category']}: {item['path']}", file=sys.stderr)
        if len(missing) > 50:
            print(f"  ... {len(missing) - 50} more", file=sys.stderr)
        return 2

    print(f"Generated slice OK: {len(present)} selected assets present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
