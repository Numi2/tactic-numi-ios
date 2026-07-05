#!/usr/bin/env python3
"""Inventory GeneralsX asset deploy trees for the iOS original asset pipeline.

The scanner is intentionally conservative: it inventories loose files today and
flags BIG archives as unresolved containers. Run it after extracting or staging
the legal game data tree to produce the first replacement backlog.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ASSET_CATEGORIES = {
    "archives": {".big"},
    "models": {".w3d"},
    "textures": {".dds", ".tga", ".png", ".bmp", ".jpg", ".jpeg"},
    "audio": {".wav", ".mp3", ".mpa", ".aud"},
    "video": {".bik", ".vp6", ".avi", ".mp4", ".mov"},
    "maps": {".map", ".scb", ".tga"},
    "ui": {".wnd", ".apt", ".const", ".dat"},
    "ini": {".ini"},
    "localization": {".csf", ".str", ".txt"},
    "fonts": {".ttf", ".otf", ".fnt"},
    "scripts": {".lua", ".py"},
}

TEXT_EXTENSIONS = {".ini", ".wnd", ".str", ".txt", ".const", ".dat"}
REFERENCE_RE = re.compile(
    r"(?i)([A-Za-z0-9_./\\ -]+\.(?:w3d|dds|tga|png|bmp|wav|mp3|bik|vp6|ini|wnd|csf|str|map|scb|ttf|otf))"
)


def normalize_rel(path):
    return path.replace(os.sep, "/")


def category_for(path):
    ext = path.suffix.lower()
    if "/window/" in normalize_rel(str(path)).lower() or ext == ".wnd":
        return "ui"
    if "/maps/" in normalize_rel(str(path)).lower() or ext in {".map", ".scb"}:
        return "maps"
    for category, extensions in ASSET_CATEGORIES.items():
        if ext in extensions:
            return category
    return "other"


def sha256_file(path, block_size=1024 * 1024):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_text_lossy(path):
    return path.read_text(encoding="utf-8", errors="replace")


def extract_references(path):
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return []
    try:
        content = read_text_lossy(path)
    except OSError:
        return []
    refs = []
    for match in REFERENCE_RE.finditer(content):
        ref = match.group(1).strip().strip('"').strip("'")
        ref = ref.replace("\\", "/")
        refs.append(ref)
    return sorted(set(refs), key=str.lower)


def collect(root, include_hashes=False):
    files = []
    references = defaultdict(list)
    categories = Counter()
    extensions = Counter()
    total_bytes = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = normalize_rel(str(path.relative_to(root)))
        ext = path.suffix.lower()
        size = path.stat().st_size
        category = category_for(Path(rel))
        entry = {
            "path": rel,
            "category": category,
            "extension": ext or "<none>",
            "bytes": size,
        }
        if include_hashes:
            entry["sha256"] = sha256_file(path)
        files.append(entry)
        categories[category] += 1
        extensions[ext or "<none>"] += 1
        total_bytes += size

        refs = extract_references(path)
        if refs:
            references[rel] = refs

    indexed_names = {Path(item["path"]).name.lower(): item["path"] for item in files}
    indexed_paths = {item["path"].lower(): item["path"] for item in files}
    missing_refs = []
    resolved_refs = []
    for source, refs in references.items():
        for ref in refs:
            ref_key = ref.lower()
            name_key = Path(ref).name.lower()
            target = indexed_paths.get(ref_key) or indexed_names.get(name_key)
            record = {"source": source, "reference": ref}
            if target:
                record["target"] = target
                resolved_refs.append(record)
            else:
                missing_refs.append(record)

    archives = [item for item in files if item["category"] == "archives"]
    return {
        "root": str(root),
        "summary": {
            "file_count": len(files),
            "total_bytes": total_bytes,
            "categories": dict(sorted(categories.items())),
            "extensions": dict(sorted(extensions.items())),
            "archive_count": len(archives),
            "reference_sources": len(references),
            "resolved_reference_count": len(resolved_refs),
            "missing_reference_count": len(missing_refs),
        },
        "files": files,
        "references": dict(sorted(references.items())),
        "resolved_references": resolved_refs,
        "missing_references": missing_refs,
        "archives": archives,
    }


def production_backlog(manifest):
    summary = manifest["summary"]
    categories = summary["categories"]
    backlog = []
    for category in [
        "models", "textures", "audio", "video", "ui", "maps", "ini",
        "localization", "fonts",
    ]:
        count = categories.get(category, 0)
        if count:
            backlog.append((category, count))
    return backlog


def write_markdown(manifest, path):
    summary = manifest["summary"]
    backlog = production_backlog(manifest)
    lines = [
        "# iOS Asset Inventory",
        "",
        f"Source root: `{manifest['root']}`",
        "",
        "## Summary",
        "",
        f"- Files: {summary['file_count']}",
        f"- Size: {summary['total_bytes'] / (1024 * 1024):.2f} MiB",
        f"- BIG archives requiring extraction: {summary['archive_count']}",
        f"- Text files with references: {summary['reference_sources']}",
        f"- Resolved loose references: {summary['resolved_reference_count']}",
        f"- Missing loose references: {summary['missing_reference_count']}",
        "",
        "## Categories",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for category, count in summary["categories"].items():
        lines.append(f"| {category} | {count} |")

    lines.extend([
        "",
        "## iOS Original Asset Backlog",
        "",
    ])
    if backlog:
        for category, count in backlog:
            lines.append(f"- Replace or regenerate `{count}` `{category}` assets.")
    else:
        lines.append("- No loose replacement candidates found. Extract BIG archives first.")

    lines.extend([
        "",
        "## Archive Containers",
        "",
    ])
    archives = manifest["archives"][:100]
    if archives:
        for archive in archives:
            mib = archive["bytes"] / (1024 * 1024)
            lines.append(f"- `{archive['path']}` ({mib:.2f} MiB)")
        if len(manifest["archives"]) > len(archives):
            lines.append(f"- ... {len(manifest['archives']) - len(archives)} more")
    else:
        lines.append("- None found.")

    lines.extend([
        "",
        "## Largest Files",
        "",
        "| File | Category | Size MiB |",
        "|---|---|---:|",
    ])
    largest = sorted(manifest["files"], key=lambda item: item["bytes"], reverse=True)[:50]
    for item in largest:
        lines.append(f"| `{item['path']}` | {item['category']} | {item['bytes'] / (1024 * 1024):.2f} |")

    if manifest["missing_references"]:
        lines.extend([
            "",
            "## Missing Loose References",
            "",
            "These may live inside BIG archives, use extensionless engine lookup, or need replacement.",
            "",
            "| Source | Reference |",
            "|---|---|",
        ])
        for item in manifest["missing_references"][:200]:
            lines.append(f"| `{item['source']}` | `{item['reference']}` |")
        if len(manifest["missing_references"]) > 200:
            lines.append(f"| ... | {len(manifest['missing_references']) - 200} more |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Scan GeneralsX iOS asset manifests")
    parser.add_argument("root", nargs="?", default=os.environ.get("GX_GAME_DATA", os.path.expanduser("~/GeneralsX/GeneralsZH")),
                        help="Deployed game data root (default: GX_GAME_DATA or ~/GeneralsX/GeneralsZH)")
    parser.add_argument("--json-out", default="build/asset-manifest/ios_asset_manifest.json",
                        help="JSON manifest output path")
    parser.add_argument("--md-out", default="build/asset-manifest/ios_asset_inventory.md",
                        help="Markdown report output path")
    parser.add_argument("--hash", action="store_true",
                        help="Include SHA-256 hashes for every file")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: asset root not found: {root}", file=sys.stderr)
        return 1

    manifest = collect(root, include_hashes=args.hash)

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(manifest, md_out)

    summary = manifest["summary"]
    print(f"Scanned {summary['file_count']} files from {root}")
    print(f"Wrote {json_out}")
    print(f"Wrote {md_out}")
    if summary["archive_count"]:
        print(f"NOTE: {summary['archive_count']} BIG archives require extraction for full dependency coverage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
