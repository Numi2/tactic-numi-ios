#!/usr/bin/env python3
"""Build the repo-owned iOS original asset pack.

This pack is the smallest checked-in asset surface that lets the iOS package
ship with deterministic, non-retail resources while the full replacement art
set is being produced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path


RUNTIME_ASSET_DIR = Path("Core/Libraries/Source/WWVegas/WW3D2/RequiredAssets")
MENU_FIXTURE = Path("GeneralsZH/Data/Window/Menus/ExtrasMenu.wnd")
IOS_CONFIG_DIR = Path("ios/config")

RUNTIME_ASSETS = (
    "AddProjectorGradient.tga",
    "Dazzle.INI",
    "MultProjectorGradient.tga",
    "ShatterAVel.tbl",
    "ShatterPlanes0.w3d",
    "ShatterVel.tbl",
    "w3d_missing_texture.tga",
)

DAZZLE_TEXTURES = (
    ("SunDazzle.tga", (255, 245, 198, 255), "dazzle radial sprite"),
    ("SunHalo.tga", (255, 232, 160, 220), "halo radial sprite"),
    ("SunLensFlare.tga", (255, 250, 220, 235), "lens flare atlas"),
)

MANDATORY_BOOT_INI_DIRS = (
    "Animation2D",
    "AudioSettings",
    "Campaign",
    "ChallengeMode",
    "CommandButton",
    "CommandMap",
    "CommandSet",
    "ControlBarResizer",
    "ControlBarScheme",
    "Credits",
    "DrawGroupInfo",
    "Eva",
    "GameLOD",
    "GameLODPresets",
    "InGameUI",
    "MiscAudio",
    "Mouse",
    "Music",
    "ParticleSystem",
    "Science",
    "Multiplayer",
    "Terrain",
    "Roads",
    "Video",
    "Water",
    "Weather",
    "Rank",
    "PlayerTemplate",
    "FXList",
    "Weapon",
    "ObjectCreationList",
    "Locomotor",
    "SpecialPower",
    "DamageFX",
    "Armor",
    "Object",
    "Upgrade",
    "AIData",
    "Crate",
    "ShellMenuScheme",
    "SoundEffects",
    "Speech",
    "Voice",
    "WindowTransitions",
)

DEFAULT_BOOT_INI_DIRS = (
    "CommandButton",
    "ControlBarScheme",
    "Science",
    "Multiplayer",
    "Terrain",
    "Roads",
    "Music",
    "SoundEffects",
    "Speech",
    "Video",
    "Voice",
    "Water",
    "Weather",
    "PlayerTemplate",
    "FXList",
    "ObjectCreationList",
    "SpecialPower",
    "Object",
    "Upgrade",
    "AIData",
    "Crate",
    "ShellMenuScheme",
)

IOS_BOOT_GAMEDATA = """GameData
  Windowed = No
  XResolution = 1024
  YResolution = 768
  UseTrees = Yes
  UseFPSLimit = Yes
  FramesPerSecondLimit = 60
  ShellMapOn = No
  PlayIntro = No
End
"""

IOS_BOOT_LANGUAGE = "Language = English\nUnicodeFontName = Arial\n"
CSF_ID = (ord("C") << 24) | (ord("S") << 16) | (ord("F") << 8) | ord(" ")
CSF_VERSION = 3
LANGUAGE_ID_US = 0

def minimal_wnd(layout_name: str, title: str | None = None) -> str:
    text_block = ""
    if title:
        text_block = f"""
  CHILD
  WINDOW
    WINDOWTYPE = STATICTEXT;
    SCREENRECT = UPPERLEFT: 0 260, BOTTOMRIGHT: 1024 320, CREATIONRESOLUTION: 1024 768;
    NAME = "{layout_name}:Title";
    STATUS = ENABLED+NOFOCUS;
    STYLE = STATICTEXT+CENTER+VCENTER+USER;
    SYSTEMCALLBACK = "[None]";
    INPUTCALLBACK = "[None]";
    TOOLTIPCALLBACK = "[None]";
    DRAWCALLBACK = "[None]";
    FONT = NAME: "Arial", SIZE: 22, BOLD: 1;
    HEADERTEMPLATE = "[NONE]";
    TOOLTIPDELAY = -1;
    TEXT = "{title}";
    TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
                DISABLED: 255 255 255 255, DISABLEDBORDER: 0 0 0 255,
                HILITE: 255 255 255 255, HILITEBORDER: 0 0 0 255;
    STATICTEXTDATA = TEXTCOLOR: 255 255 255 255, BORDERCOLOR: 0 0 0 255;
    ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 255 255 255 0, BORDERCOLOR: 255 255 255 0;
    DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 255 255 255 0, BORDERCOLOR: 255 255 255 0;
    HILITEDRAWDATA = IMAGE: NoImage, COLOR: 255 255 255 0, BORDERCOLOR: 255 255 255 0;
  END"""
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 0 0, BOTTOMRIGHT: 1024 768, CREATIONRESOLUTION: 1024 768;
  NAME = "{layout_name}:Root";
  STATUS = ENABLED+IMAGE+NOFOCUS;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 255 255 255 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 255 255 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 255, BORDERCOLOR: 0 0 0 255;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 255, BORDERCOLOR: 0 0 0 255;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 255, BORDERCOLOR: 0 0 0 255;{text_block}
END
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def copy_file(
    src: Path,
    dest: Path,
    records: list[dict[str, object]],
    role: str,
    project_root: Path,
) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"required source asset missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    records.append(
        {
            "role": role,
            "path": manifest_path(dest, project_root),
            "source": manifest_path(src, project_root),
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        }
    )


def write_text(
    dest: Path,
    text: str,
    records: list[dict[str, object]],
    role: str,
    project_root: Path,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="\n")
    records.append(
        {
            "role": role,
            "path": manifest_path(dest, project_root),
            "source": "generated",
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        }
    )


def write_binary(
    dest: Path,
    payload: bytes,
    records: list[dict[str, object]],
    role: str,
    project_root: Path,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    records.append(
        {
            "role": role,
            "path": manifest_path(dest, project_root),
            "source": "generated",
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        }
    )


def write_radial_tga(
    dest: Path,
    color: tuple[int, int, int, int],
    records: list[dict[str, object]],
    role: str,
    project_root: Path,
    size: int = 64,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    header = bytearray(18)
    header[2] = 2
    header[12] = size & 0xFF
    header[13] = (size >> 8) & 0xFF
    header[14] = size & 0xFF
    header[15] = (size >> 8) & 0xFF
    header[16] = 32
    header[17] = 8
    pixels = bytearray()
    center = (size - 1) / 2.0
    radius = max(center, 1.0)
    red, green, blue, alpha = color
    for y in range(size):
        for x in range(size):
            dx = (x - center) / radius
            dy = (y - center) / radius
            falloff = max(0.0, 1.0 - (dx * dx + dy * dy) ** 0.5)
            intensity = falloff * falloff
            pixels.extend(
                (
                    int(blue * intensity),
                    int(green * intensity),
                    int(red * intensity),
                    int(alpha * intensity),
                )
            )
    dest.write_bytes(bytes(header) + bytes(pixels))
    records.append(
        {
            "role": role,
            "path": manifest_path(dest, project_root),
            "source": "generated",
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
        }
    )


def build_pack(project_root: Path, out_dir: Path, clean: bool) -> dict[str, object]:
    out_dir = out_dir.resolve()
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []

    for filename in RUNTIME_ASSETS:
        copy_file(
            project_root / RUNTIME_ASSET_DIR / filename,
            out_dir / "Data" / "Runtime" / "RequiredAssets" / filename,
            records,
            "ww3d_runtime_required_asset",
            project_root,
        )
        copy_file(
            project_root / RUNTIME_ASSET_DIR / filename,
            out_dir / filename,
            records,
            "ww3d_root_lookup_asset",
            project_root,
        )

    for filename, color, role in DAZZLE_TEXTURES:
        write_radial_tga(
            out_dir / "Data" / "Runtime" / "RequiredAssets" / filename,
            color,
            records,
            role,
            project_root,
        )
        write_radial_tga(out_dir / filename, color, records, role, project_root)

    copy_file(
        project_root / MENU_FIXTURE,
        out_dir / "Data" / "Window" / "Menus" / "ExtrasMenu.wnd",
        records,
        "ios_boot_menu",
        project_root,
    )

    write_text(
        out_dir / "Data" / "Window" / "Menus" / "BlankWindow.wnd",
        minimal_wnd("BlankWindow.wnd"),
        records,
        "ios_boot_window_layout",
        project_root,
    )
    write_text(
        out_dir / "Data" / "Window" / "Menus" / "MainMenu.wnd",
        minimal_wnd("MainMenu.wnd", "GENERALS X"),
        records,
        "ios_boot_window_layout",
        project_root,
    )
    write_text(
        out_dir / "Data" / "Window" / "Menus" / "LegalPage.wnd",
        minimal_wnd("LegalPage.wnd", "GENERALS X"),
        records,
        "ios_boot_window_layout",
        project_root,
    )

    copy_file(
        project_root / IOS_CONFIG_DIR / "Options.ini",
        out_dir / "DefaultOptions.ini",
        records,
        "ios_runtime_config",
        project_root,
    )
    copy_file(
        project_root / IOS_CONFIG_DIR / "dxvk.conf",
        out_dir / "dxvk.conf",
        records,
        "ios_runtime_config",
        project_root,
    )

    write_text(
        out_dir / "Data" / "English" / "Language.ini",
        IOS_BOOT_LANGUAGE,
        records,
        "localization_boot_config",
        project_root,
    )
    write_text(
        out_dir / "Data" / "English" / "HeaderTemplate" / "ios_boot.ini",
        "; Generated iOS boot placeholder.\n",
        records,
        "localization_header_template_placeholder",
        project_root,
    )
    write_binary(
        out_dir / "Data" / "English" / "generals.csf",
        struct.pack("<iiiiii", CSF_ID, CSF_VERSION, 0, 0, 0, LANGUAGE_ID_US),
        records,
        "localization_boot_csf",
        project_root,
    )

    write_text(
        out_dir / "Data" / "INI" / "Default" / "GameData.ini",
        IOS_BOOT_GAMEDATA,
        records,
        "ios_boot_game_data_ini",
        project_root,
    )
    for dirname in DEFAULT_BOOT_INI_DIRS:
        write_text(
            out_dir / "Data" / "INI" / "Default" / dirname / "ios_boot.ini",
            "; Generated iOS boot placeholder.\n",
            records,
            "ios_boot_default_ini_placeholder",
            project_root,
        )
    for dirname in MANDATORY_BOOT_INI_DIRS:
        write_text(
            out_dir / "Data" / "INI" / dirname / "ios_boot.ini",
            "; Generated iOS boot placeholder.\n",
            records,
            "ios_boot_ini_placeholder",
            project_root,
        )

    try:
        game_data_path = out_dir.relative_to(project_root).as_posix()
    except ValueError:
        game_data_path = out_dir.as_posix()

    manifest = {
        "schema": "generalsx-ios-original-asset-pack-v1",
        "game_data": game_data_path,
        "asset_count": len(records),
        "assets": records,
    }
    manifest_path = out_dir / "ios_original_asset_pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = manifest_path.as_posix()
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="GeneralsX repository root",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("ios-original-assets/generated/GameData"),
        help="output GameData directory",
    )
    parser.add_argument("--clean", action="store_true", help="remove the output directory first")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir
    manifest = build_pack(project_root, out_dir, args.clean)
    print(f"built {manifest['asset_count']} assets at {manifest['game_data']}")
    print(f"manifest: {manifest['manifest_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
