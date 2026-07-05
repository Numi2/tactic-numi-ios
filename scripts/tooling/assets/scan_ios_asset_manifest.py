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
import struct
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

TEXT_EXTENSIONS = {".ini", ".wnd", ".str", ".txt", ".const", ".dat", ".map"}
BINARY_DEP_EXTENSIONS = {".w3d", ".csf", ".map", ".scb", ".wnd"}
REFERENCE_RE = re.compile(
    r"(?i)([A-Za-z0-9_./\\ -]+\.(?:w3d|dds|tga|png|bmp|wav|mp3|bik|vp6|ini|wnd|csf|str|map|scb|ttf|otf))"
)
TOKEN_RE = re.compile(rb"[A-Za-z0-9_./\\:-]{3,260}")
TEXTURE_EXTENSIONS = {".dds", ".tga", ".png", ".bmp", ".jpg", ".jpeg"}
MODEL_EXTENSIONS = {".w3d"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".mpa", ".aud"}
VIDEO_EXTENSIONS = {".bik", ".vp6", ".avi", ".mp4", ".mov"}
UI_EXTENSIONS = {".wnd", ".apt", ".const"}
MAP_EXTENSIONS = {".map", ".scb"}
LOCALIZATION_EXTENSIONS = {".csf", ".str"}
FONT_EXTENSIONS = {".ttf", ".otf", ".fnt"}
KNOWN_EXTENSIONS = (
    TEXTURE_EXTENSIONS | MODEL_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS |
    UI_EXTENSIONS | MAP_EXTENSIONS | LOCALIZATION_EXTENSIONS | FONT_EXTENSIONS |
    {".ini"}
)
TEXTURE_NAME_CHUNK = 0x00000032
TEXTURE_REPLACER_CHUNK = 0x00000062
HLOD_SUB_OBJECT_CHUNK = 0x00000706
LOD_MODEL_COLLECTION_CHUNK = 0x00000741
W3D_CONTAINER_CHUNKS = {
    0x00000000, 0x00000030, 0x00000031, 0x00000038, 0x00000040,
    0x00000048, 0x00000200, 0x00000240, 0x00000300, 0x00000400,
    0x00000700, 0x00000702, 0x00000704, 0x00000705, 0x00000740,
    0x00000800, 0x00000900, 0x00000A00,
}
IMPLICIT_REFERENCE_KEYS = {
    "model",
    "animation",
    "idleanimation",
    "animationname",
    "texture",
    "image",
    "mappedimage",
    "buttonimage",
    "unitportrait",
    "portrait",
    "sound",
    "soundname",
    "filename",
    "file",
    "loadscreen",
    "window",
    "layout",
}
INI_KEY_CATEGORY_HINTS = {
    "model": "models",
    "modelname": "models",
    "animation": "models",
    "idleanimation": "models",
    "animationname": "models",
    "draw": "models",
    "texture": "textures",
    "image": "textures",
    "mappedimage": "textures",
    "buttonimage": "textures",
    "unitportrait": "textures",
    "portrait": "textures",
    "loadscreen": "textures",
    "sound": "audio",
    "soundname": "audio",
    "voice": "audio",
    "filename": "other",
    "file": "other",
    "window": "ui",
    "layout": "ui",
}
MAX_ARCHIVED_TEXT_BYTES = 8 * 1024 * 1024
MAX_ARCHIVED_BINARY_PARSE_BYTES = 64 * 1024 * 1024


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
    return extract_references_from_text(content)


def category_for_name(name):
    return category_for(Path(name.replace("\\", "/")))


def normalize_asset_key(path):
    return path.replace("\\", "/").lower().lstrip("./")


def basename_key(path):
    return Path(path.replace("\\", "/")).name.lower()


def decode_text_bytes(data):
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_archive_bytes(archive_path, offset, size):
    with archive_path.open("rb") as handle:
        handle.seek(offset)
        return handle.read(size)


def parse_big_archive(path, extract_text=False):
    entries = []
    text_entries = {}
    errors = []
    try:
        with path.open("rb") as handle:
            if handle.read(4) != b"BIGF":
                errors.append("not a BIGF archive")
                return entries, text_entries, errors
            archive_size_raw = handle.read(4)
            file_count_raw = handle.read(4)
            handle.read(4)
            if len(archive_size_raw) != 4 or len(file_count_raw) != 4:
                errors.append("truncated BIG header")
                return entries, text_entries, errors
            archive_size = struct.unpack("<I", archive_size_raw)[0]
            file_count = struct.unpack(">I", file_count_raw)[0]
            for index in range(file_count):
                header = handle.read(8)
                if len(header) != 8:
                    errors.append(f"truncated directory entry {index}")
                    break
                offset, size = struct.unpack(">II", header)
                name_bytes = bytearray()
                while True:
                    char = handle.read(1)
                    if not char:
                        errors.append(f"unterminated path for directory entry {index}")
                        break
                    if char == b"\0":
                        break
                    name_bytes.extend(char)
                name = name_bytes.decode("utf-8", errors="replace").replace("\\", "/")
                entry = {
                    "path": normalize_rel(str(path)),
                    "archive_entry": name,
                    "category": category_for_name(name),
                    "extension": Path(name).suffix.lower() or "<none>",
                    "bytes": size,
                    "offset": offset,
                    "archive_size": archive_size,
                }
                entries.append(entry)
                if extract_text and Path(name).suffix.lower() in TEXT_EXTENSIONS and size <= MAX_ARCHIVED_TEXT_BYTES:
                    pos = handle.tell()
                    try:
                        handle.seek(offset)
                        text_entries[name] = decode_text_bytes(handle.read(size))
                    finally:
                        handle.seek(pos)
    except OSError as exc:
        errors.append(str(exc))
    return entries, text_entries, errors


def extract_references_from_text(content):
    refs = []
    for match in REFERENCE_RE.finditer(content):
        ref = match.group(1).strip().strip('"').strip("'")
        refs.append(ref.replace("\\", "/"))
    implicit = extract_implicit_references(content)
    refs.extend(implicit)
    return sorted(set(refs), key=str.lower)


def infer_reference_category(ref, hint=None):
    ext = Path(ref.replace("\\", "/")).suffix.lower()
    if ext in MODEL_EXTENSIONS:
        return "models"
    if ext in TEXTURE_EXTENSIONS:
        return "textures"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in UI_EXTENSIONS:
        return "ui"
    if ext in MAP_EXTENSIONS:
        return "maps"
    if ext in LOCALIZATION_EXTENSIONS:
        return "localization"
    if ext in FONT_EXTENSIONS:
        return "fonts"
    if ext == ".ini":
        return "ini"
    return hint or "other"


def make_dependency(source, ref, kind, hint=None, origin=None):
    ref = ref.strip().strip('"').strip("'").replace("\\", "/")
    return {
        "source": source,
        "reference": ref,
        "kind": kind,
        "category_hint": infer_reference_category(ref, hint),
        "origin": origin or kind,
    }


def extract_implicit_references(content):
    refs = []
    assignment_re = re.compile(r"(?i)^\s*([A-Za-z0-9_]+)\s*=\s*([A-Za-z0-9_./\\:-]+)", re.MULTILINE)
    for key, value in assignment_re.findall(content):
        key_lower = key.lower()
        if key_lower not in IMPLICIT_REFERENCE_KEYS:
            continue
        if "." in Path(value).name:
            refs.append(value.replace("\\", "/"))
    return refs


def extract_typed_text_dependencies(source, content):
    deps = []
    seen = set()
    for match in REFERENCE_RE.finditer(content):
        ref = match.group(1).strip().strip('"').strip("'").replace("\\", "/")
        dep = make_dependency(source, ref, "text_explicit", origin="regex")
        key = (dep["source"], dep["reference"], dep["kind"], dep["origin"])
        if key not in seen:
            deps.append(dep)
            seen.add(key)

    assignment_re = re.compile(r"(?i)^\s*([A-Za-z0-9_]+)\s*=\s*([A-Za-z0-9_./\\:-]+)", re.MULTILINE)
    for key_name, value in assignment_re.findall(content):
        key_lower = key_name.lower()
        if key_lower not in IMPLICIT_REFERENCE_KEYS:
            continue
        hint = INI_KEY_CATEGORY_HINTS.get(key_lower)
        if "." not in Path(value).name:
            if hint == "models":
                value = f"{value}.w3d"
            elif hint == "ui":
                value = f"{value}.wnd"
            else:
                continue
        dep = make_dependency(source, value, "ini_field", hint=hint, origin=key_name)
        key = (dep["source"], dep["reference"], dep["kind"], dep["origin"])
        if key not in seen:
            deps.append(dep)
            seen.add(key)
    return deps


def printable_token_references(data):
    refs = []
    for match in TOKEN_RE.finditer(data):
        token = match.group(0).decode("ascii", errors="ignore").strip("\x00")
        token = token.replace("\\", "/")
        ext = Path(token).suffix.lower()
        if ext in KNOWN_EXTENSIONS:
            refs.append(token)
    return refs


def parse_w3d_dependencies(source, data):
    deps = []
    diagnostics = []
    seen = set()

    def add(ref, kind, origin):
        dep = make_dependency(source, ref, kind, origin=origin)
        key = (dep["source"], dep["reference"], dep["kind"], dep["origin"])
        if key not in seen:
            deps.append(dep)
            seen.add(key)

    def walk(start, end, depth=0):
        pos = start
        while pos + 8 <= end:
            chunk_id, raw_size = struct.unpack_from("<II", data, pos)
            size = raw_size & 0x7FFFFFFF
            has_children = bool(raw_size & 0x80000000) or chunk_id in W3D_CONTAINER_CHUNKS
            payload_start = pos + 8
            payload_end = payload_start + size
            if size < 0 or payload_end > end or payload_end < payload_start:
                break
            payload = data[payload_start:payload_end]
            if chunk_id == TEXTURE_NAME_CHUNK:
                name = payload.split(b"\0", 1)[0].decode("ascii", errors="ignore")
                if name:
                    add(name, "w3d_texture", "W3D_CHUNK_TEXTURE_NAME")
            elif chunk_id in {TEXTURE_REPLACER_CHUNK, HLOD_SUB_OBJECT_CHUNK, LOD_MODEL_COLLECTION_CHUNK}:
                for ref in printable_token_references(payload):
                    add(ref, "w3d_struct_string", f"chunk_0x{chunk_id:08x}")
            if has_children and depth < 64:
                walk(payload_start, payload_end, depth + 1)
            else:
                for ref in printable_token_references(payload):
                    add(ref, "w3d_binary_string", f"chunk_0x{chunk_id:08x}")
            pos = payload_end
        if pos != end and depth == 0:
            diagnostics.append({"source": source, "warning": f"stopped W3D parse at byte {pos} of {end}"})

    walk(0, len(data))
    return deps, diagnostics


def parse_csf_dependencies(source, data):
    labels = []
    diagnostics = []
    try:
        if len(data) < 24 or data[:4] != b" FSC":
            return [], [{"source": source, "warning": "not a recognized CSF file"}]
        label_count = struct.unpack_from("<I", data, 8)[0]
        pos = 24
        for _ in range(label_count):
            if pos + 12 > len(data):
                break
            marker = data[pos:pos + 4]
            pos += 4
            if marker not in {b" LBL", b"LBL "}:
                break
            string_count = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            name_len = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            name = data[pos:pos + name_len].decode("ascii", errors="replace")
            pos += name_len
            labels.append({"source": source, "label": name, "string_count": string_count})
            for _ in range(string_count):
                if pos + 8 > len(data):
                    break
                string_marker = data[pos:pos + 4]
                pos += 4
                length = struct.unpack_from("<I", data, pos)[0]
                pos += 4
                pos += length * 2
                if string_marker == b"WRTS" and pos + 4 <= len(data):
                    extra_len = struct.unpack_from("<I", data, pos)[0]
                    pos += 4 + extra_len
    except (struct.error, UnicodeDecodeError) as exc:
        diagnostics.append({"source": source, "warning": f"CSF parse failed: {exc}"})
    return [], diagnostics + labels


def collect(root, include_hashes=False, index_archives=True, parse_archived_text=True):
    files = []
    archive_entries = []
    archive_errors = []
    references = defaultdict(list)
    typed_dependencies = []
    parser_diagnostics = []
    categories = Counter()
    extensions = Counter()
    total_bytes = 0
    text_blobs = {}

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
        if ext in TEXT_EXTENSIONS:
            try:
                typed_dependencies.extend(extract_typed_text_dependencies(rel, read_text_lossy(path)))
            except OSError as exc:
                parser_diagnostics.append({"source": rel, "warning": str(exc)})
        if ext in BINARY_DEP_EXTENSIONS and ext not in TEXT_EXTENSIONS:
            try:
                data = path.read_bytes()
                if ext == ".w3d":
                    deps, diagnostics = parse_w3d_dependencies(rel, data)
                    typed_dependencies.extend(deps)
                    parser_diagnostics.extend(diagnostics)
                elif ext == ".csf":
                    deps, diagnostics = parse_csf_dependencies(rel, data)
                    typed_dependencies.extend(deps)
                    parser_diagnostics.extend(diagnostics)
                else:
                    for ref in printable_token_references(data):
                        typed_dependencies.append(make_dependency(rel, ref, "binary_string", origin=ext))
            except OSError as exc:
                parser_diagnostics.append({"source": rel, "warning": str(exc)})
        if index_archives and ext == ".big":
            entries, archived_text, errors = parse_big_archive(
                path, extract_text=parse_archived_text
            )
            archive_entries.extend(entries)
            text_blobs.update({
                f"{rel}:{name}": content for name, content in archived_text.items()
            })
            for error in errors:
                archive_errors.append({"archive": rel, "error": error})

    for source, content in text_blobs.items():
        refs = extract_references_from_text(content)
        if refs:
            references[source] = refs
        typed_dependencies.extend(extract_typed_text_dependencies(source, content))
        for item in archive_entries:
            if source.endswith(":" + item["archive_entry"]):
                break

    if index_archives:
        for item in archive_entries:
            ext = item["extension"]
            if ext not in BINARY_DEP_EXTENSIONS or ext in TEXT_EXTENSIONS:
                continue
            if item["bytes"] > MAX_ARCHIVED_BINARY_PARSE_BYTES:
                parser_diagnostics.append({
                    "source": f"{item['path']}:{item['archive_entry']}",
                    "warning": f"skipped binary parse above {MAX_ARCHIVED_BINARY_PARSE_BYTES} bytes",
                })
                continue
            source = f"{item['path']}:{item['archive_entry']}"
            try:
                data = read_archive_bytes(root / item["path"], item["offset"], item["bytes"])
                if ext == ".w3d":
                    deps, diagnostics = parse_w3d_dependencies(source, data)
                    typed_dependencies.extend(deps)
                    parser_diagnostics.extend(diagnostics)
                elif ext == ".csf":
                    deps, diagnostics = parse_csf_dependencies(source, data)
                    typed_dependencies.extend(deps)
                    parser_diagnostics.extend(diagnostics)
                else:
                    for ref in printable_token_references(data):
                        typed_dependencies.append(make_dependency(source, ref, "binary_string", origin=ext))
            except OSError as exc:
                parser_diagnostics.append({"source": source, "warning": str(exc)})

    virtual_files = []
    virtual_files.extend(files)
    for item in archive_entries:
        archive_ref = f"{item['path']}:{item['archive_entry']}"
        virtual_files.append({
            "path": item["archive_entry"],
            "archive_ref": archive_ref,
            "category": item["category"],
            "extension": item["extension"],
            "bytes": item["bytes"],
        })

    indexed_names = {basename_key(item["path"]): item for item in virtual_files}
    indexed_paths = {normalize_asset_key(item["path"]): item for item in virtual_files}
    missing_refs = []
    resolved_refs = []
    all_reference_records = []
    for source, refs in references.items():
        for ref in refs:
            all_reference_records.append({"source": source, "reference": ref})
    all_reference_records.extend(typed_dependencies)

    deduped_reference_records = []
    seen_reference_records = set()
    for record in all_reference_records:
        key = (
            record.get("source"),
            normalize_asset_key(record.get("reference", "")),
        )
        if key in seen_reference_records:
            continue
        seen_reference_records.add(key)
        deduped_reference_records.append(record)

    for record in deduped_reference_records:
        ref = record["reference"]
        ref_key = normalize_asset_key(ref)
        name_key = basename_key(ref)
        target = indexed_paths.get(ref_key) or indexed_names.get(name_key)
        resolved_record = dict(record)
        if target:
            resolved_record["target"] = target["path"]
            if "archive_ref" in target:
                resolved_record["archive_ref"] = target["archive_ref"]
            resolved_refs.append(resolved_record)
        else:
            missing_refs.append(dict(record))

    archives = [item for item in files if item["category"] == "archives"]
    required_by_category = Counter()
    for record in resolved_refs:
        target = indexed_paths.get(normalize_asset_key(record["target"])) or indexed_names.get(basename_key(record["target"]))
        if target:
            required_by_category[target.get("category", "other")] += 1
    return {
        "root": str(root),
        "summary": {
            "file_count": len(files),
            "archive_entry_count": len(archive_entries),
            "total_bytes": total_bytes,
            "categories": dict(sorted(categories.items())),
            "archive_entry_categories": dict(sorted(Counter(item["category"] for item in archive_entries).items())),
            "extensions": dict(sorted(extensions.items())),
            "archive_count": len(archives),
            "archive_error_count": len(archive_errors),
            "reference_sources": len(references),
            "typed_dependency_count": len(typed_dependencies),
            "parser_diagnostic_count": len(parser_diagnostics),
            "resolved_reference_count": len(resolved_refs),
            "missing_reference_count": len(missing_refs),
            "required_by_category": dict(sorted(required_by_category.items())),
        },
        "files": files,
        "archive_entries": archive_entries,
        "archive_errors": archive_errors,
        "references": dict(sorted(references.items())),
        "typed_dependencies": typed_dependencies,
        "parser_diagnostics": parser_diagnostics,
        "resolved_references": resolved_refs,
        "missing_references": missing_refs,
        "archives": archives,
    }


def production_backlog(manifest):
    summary = manifest["summary"]
    categories = Counter(summary["categories"])
    categories.update(summary.get("archive_entry_categories", {}))
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
        f"- Indexed BIG entries: {summary.get('archive_entry_count', 0)}",
        f"- Size: {summary['total_bytes'] / (1024 * 1024):.2f} MiB",
        f"- BIG archives requiring extraction: {summary['archive_count']}",
        f"- BIG archive parse errors: {summary.get('archive_error_count', 0)}",
        f"- Text files with references: {summary['reference_sources']}",
        f"- Typed dependencies: {summary.get('typed_dependency_count', 0)}",
        f"- Parser diagnostics: {summary.get('parser_diagnostic_count', 0)}",
        f"- Resolved references: {summary['resolved_reference_count']}",
        f"- Hard missing references: {summary['missing_reference_count']}",
        "",
        "## Categories",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for category, count in summary["categories"].items():
        lines.append(f"| {category} | {count} |")
    if summary.get("archive_entry_categories"):
        lines.extend([
            "",
            "## Indexed BIG Entry Categories",
            "",
            "| Category | Count |",
            "|---|---:|",
        ])
        for category, count in summary["archive_entry_categories"].items():
            lines.append(f"| {category} | {count} |")
    if summary.get("required_by_category"):
        lines.extend([
            "",
            "## Required Assets by Category",
            "",
            "| Category | Resolved References |",
            "|---|---:|",
        ])
        for category, count in summary["required_by_category"].items():
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
            "## Hard Missing References",
            "",
            "These references were not found as loose files or indexed BIG entries.",
            "",
            "| Source | Reference |",
            "|---|---|",
        ])
        for item in manifest["missing_references"][:200]:
            lines.append(f"| `{item['source']}` | `{item['reference']}` |")
        if len(manifest["missing_references"]) > 200:
            lines.append(f"| ... | {len(manifest['missing_references']) - 200} more |")

    if manifest.get("archive_errors"):
        lines.extend([
            "",
            "## BIG Parse Errors",
            "",
            "| Archive | Error |",
            "|---|---|",
        ])
        for item in manifest["archive_errors"][:100]:
            lines.append(f"| `{item['archive']}` | `{item['error']}` |")
    if manifest.get("parser_diagnostics"):
        lines.extend([
            "",
            "## Parser Diagnostics",
            "",
            "| Source | Detail |",
            "|---|---|",
        ])
        for item in manifest["parser_diagnostics"][:100]:
            source = item.get("source", "")
            detail = item.get("warning") or item.get("label") or str(item)
            lines.append(f"| `{source}` | `{detail}` |")

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
    parser.add_argument("--no-big-index", action="store_true",
                        help="Do not index BIG archive directory entries")
    parser.add_argument("--no-archived-text", action="store_true",
                        help="Do not parse text entries inside BIG archives")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: asset root not found: {root}", file=sys.stderr)
        return 1

    manifest = collect(
        root,
        include_hashes=args.hash,
        index_archives=not args.no_big_index,
        parse_archived_text=not args.no_archived_text,
    )

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
        print(f"Indexed {summary.get('archive_entry_count', 0)} entries from {summary['archive_count']} BIG archives.")
    if summary["missing_reference_count"]:
        print(f"WARNING: {summary['missing_reference_count']} hard missing references remain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
