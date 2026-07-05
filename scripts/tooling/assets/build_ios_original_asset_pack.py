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
IOS_SLICE_PLAYER_TEMPLATE = """PlayerTemplate FactionObserver
  Side = Observer
  BaseSide = Observer
  PlayableSide = No
  DisplayName = GUI:Observer
  IsObserver = Yes
End

PlayerTemplate FactionCivilian
  Side = Civilian
  BaseSide = Civilian
  PlayableSide = No
  DisplayName = INI:FactionCivilian
  PreferredColor = R:255 G:255 B:255
End

PlayerTemplate FactionIOS
  Side = IOS
  BaseSide = USA
  PlayableSide = Yes
  DisplayName = INI:FactionIOS
  StartMoney = 10000
  PreferredColor = R:32 G:168 B:255
  StartingBuilding = IOSCommandCenter
  StartingUnit0 = IOSRanger
  StartingUnit1 = IOSScoutVehicle
  PurchaseScienceCommandSetRank1 = IOSScienceCommandSet
  PurchaseScienceCommandSetRank3 = IOSScienceCommandSet
  PurchaseScienceCommandSetRank8 = IOSScienceCommandSet
  SpecialPowerShortcutCommandSet = IOSSpecialPowerCommandSet
End
"""

IOS_SLICE_COMMAND_BUTTON = """CommandButton Command_ConstructIOSPowerPlant
  Command = DOZER_CONSTRUCT
  Object = IOSPowerPlant
  TextLabel = INI:Command_ConstructIOSPowerPlant
  DescriptLabel = INI:Command_ConstructIOSPowerPlantDescription
  ButtonImage = IOSPowerPlantIcon
End

CommandButton Command_ConstructIOSBarracks
  Command = DOZER_CONSTRUCT
  Object = IOSBarracks
  TextLabel = INI:Command_ConstructIOSBarracks
  DescriptLabel = INI:Command_ConstructIOSBarracksDescription
  ButtonImage = IOSBarracksIcon
End

CommandButton Command_ConstructIOSScoutVehicle
  Command = UNIT_BUILD
  Object = IOSScoutVehicle
  TextLabel = INI:Command_ConstructIOSScoutVehicle
  DescriptLabel = INI:Command_ConstructIOSScoutVehicleDescription
  ButtonImage = IOSScoutVehicleIcon
End

CommandButton Command_ConstructIOSRanger
  Command = UNIT_BUILD
  Object = IOSRanger
  TextLabel = INI:Command_ConstructIOSRanger
  DescriptLabel = INI:Command_ConstructIOSRangerDescription
  ButtonImage = IOSRangerIcon
End

CommandButton Command_IOSStop
  Command = STOP
  TextLabel = INI:Command_Stop
  DescriptLabel = INI:Command_StopDescription
  ButtonImage = IOSStopIcon
End

CommandButton Command_IOSSelectAllOfType
  Command = SELECT_ALL_UNITS_OF_TYPE
  TextLabel = INI:Command_SelectAllOfType
  DescriptLabel = INI:Command_SelectAllOfTypeDescription
  ButtonImage = IOSSelectAllIcon
End
"""

IOS_SLICE_COMMAND_SET = """CommandSet IOSCommandCenterCommandSet
  1 = Command_ConstructIOSPowerPlant
  2 = Command_ConstructIOSBarracks
  13 = Command_IOSSelectAllOfType
  14 = Command_IOSStop
End

CommandSet IOSBarracksCommandSet
  1 = Command_ConstructIOSRanger
  13 = Command_IOSSelectAllOfType
  14 = Command_IOSStop
End

CommandSet IOSVehicleFactoryCommandSet
  1 = Command_ConstructIOSScoutVehicle
  13 = Command_IOSSelectAllOfType
  14 = Command_IOSStop
End

CommandSet IOSUnitCommandSet
  13 = Command_IOSSelectAllOfType
  14 = Command_IOSStop
End

CommandSet IOSScienceCommandSet
End

CommandSet IOSSpecialPowerCommandSet
End
"""

IOS_SLICE_WEAPON = """Weapon IOSRifleWeapon
  PrimaryDamage = 8.0
  PrimaryDamageRadius = 0.0
  AttackRange = 120.0
  DamageType = SMALL_ARMS
  DeathType = NORMAL
  WeaponSpeed = 999999.0
  ClipSize = 5
  ClipReloadTime = 1000
  DelayBetweenShots = 250
  AntiGround = Yes
End

Weapon IOSCannonWeapon
  PrimaryDamage = 35.0
  PrimaryDamageRadius = 8.0
  AttackRange = 160.0
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 250.0
  ClipSize = 1
  ClipReloadTime = 1500
  DelayBetweenShots = 1000
  AntiGround = Yes
End
"""

IOS_SLICE_LOCOMOTOR = """Locomotor IOSInfantryLocomotor
  Surfaces = GROUND
  Speed = 25
  SpeedDamaged = 18
  TurnRate = 360
  TurnRateDamaged = 240
  Acceleration = 80
  AccelerationDamaged = 60
  Braking = 80
  MinSpeed = 0
  ZAxisBehavior = NO_Z_MOTIVE_FORCE
  Appearance = TWO_LEGS
  StickToGround = Yes
End

Locomotor IOSVehicleLocomotor
  Surfaces = GROUND
  Speed = 40
  SpeedDamaged = 25
  TurnRate = 120
  TurnRateDamaged = 90
  Acceleration = 60
  AccelerationDamaged = 40
  Braking = 60
  MinSpeed = 0
  ZAxisBehavior = NO_Z_MOTIVE_FORCE
  Appearance = FOUR_WHEELS
  StickToGround = Yes
  CanMoveBackwards = Yes
End
"""

IOS_SLICE_ARMOR = """Armor IOSInfantryArmor
  Armor = DEFAULT 100%
End

Armor IOSVehicleArmor
  Armor = DEFAULT 100%
End

Armor IOSStructureArmor
  Armor = DEFAULT 100%
End
"""

IOS_SLICE_DAMAGE_FX = """DamageFX IOSDefaultDamageFX
End
"""

IOS_SLICE_OBJECT = """Object IOSCommandCenter
  DisplayName = INI:IOSCommandCenter
  Side = IOS
  EditorSorting = STRUCTURE
  KindOf = STRUCTURE SELECTABLE IMMOBILE COMMANDCENTER
  Buildable = Yes
  BuildCost = 2000
  BuildTime = 10.0
  EnergyProduction = 0
  CommandSet = IOSCommandCenterCommandSet
  VisionRange = 200.0
  ShroudClearingRange = 220.0
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  ButtonImage = IOSCommandCenterIcon
  SelectPortrait = IOSCommandCenterIcon
End

Object IOSPowerPlant
  DisplayName = INI:IOSPowerPlant
  Side = IOS
  EditorSorting = STRUCTURE
  KindOf = STRUCTURE SELECTABLE IMMOBILE FS_POWER
  Buildable = Yes
  BuildCost = 800
  BuildTime = 8.0
  EnergyProduction = 5
  VisionRange = 120.0
  ShroudClearingRange = 140.0
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  ButtonImage = IOSPowerPlantIcon
  SelectPortrait = IOSPowerPlantIcon
End

Object IOSBarracks
  DisplayName = INI:IOSBarracks
  Side = IOS
  EditorSorting = STRUCTURE
  KindOf = STRUCTURE SELECTABLE IMMOBILE FS_FACTORY
  Buildable = Yes
  BuildCost = 600
  BuildTime = 8.0
  EnergyProduction = -1
  CommandSet = IOSBarracksCommandSet
  VisionRange = 140.0
  ShroudClearingRange = 160.0
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  ButtonImage = IOSBarracksIcon
  SelectPortrait = IOSBarracksIcon
End

Object IOSRanger
  DisplayName = INI:IOSRanger
  Side = IOS
  EditorSorting = INFANTRY
  KindOf = PRELOAD SELECTABLE CAN_ATTACK INFANTRY SCORE
  Buildable = Yes
  BuildCost = 150
  BuildTime = 3.0
  CommandSet = IOSUnitCommandSet
  VisionRange = 160.0
  ShroudClearingRange = 180.0
  WeaponSet
    Conditions = None
    Weapon = PRIMARY IOSRifleWeapon
  End
  ArmorSet
    Conditions = None
    Armor = IOSInfantryArmor
    DamageFX = IOSDefaultDamageFX
  End
  ButtonImage = IOSRangerIcon
  SelectPortrait = IOSRangerIcon
End

Object IOSScoutVehicle
  DisplayName = INI:IOSScoutVehicle
  Side = IOS
  EditorSorting = VEHICLE
  KindOf = PRELOAD SELECTABLE CAN_ATTACK VEHICLE SCORE
  Buildable = Yes
  BuildCost = 600
  BuildTime = 6.0
  CommandSet = IOSUnitCommandSet
  VisionRange = 180.0
  ShroudClearingRange = 200.0
  WeaponSet
    Conditions = None
    Weapon = PRIMARY IOSCannonWeapon
  End
  ArmorSet
    Conditions = None
    Armor = IOSVehicleArmor
    DamageFX = IOSDefaultDamageFX
  End
  ButtonImage = IOSScoutVehicleIcon
  SelectPortrait = IOSScoutVehicleIcon
End
"""

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


def write_playable_slice_assets(
    out_dir: Path,
    records: list[dict[str, object]],
    project_root: Path,
) -> None:
    slice_files = (
        ("PlayerTemplate", IOS_SLICE_PLAYER_TEMPLATE),
        ("CommandButton", IOS_SLICE_COMMAND_BUTTON),
        ("CommandSet", IOS_SLICE_COMMAND_SET),
        ("Weapon", IOS_SLICE_WEAPON),
        ("Locomotor", IOS_SLICE_LOCOMOTOR),
        ("Armor", IOS_SLICE_ARMOR),
        ("DamageFX", IOS_SLICE_DAMAGE_FX),
        ("Object", IOS_SLICE_OBJECT),
    )
    for dirname, text in slice_files:
        write_text(
            out_dir / "Data" / "INI" / dirname / "ios_playable_slice.ini",
            text,
            records,
            "ios_playable_slice_ini",
            project_root,
        )

    icon_colors = (
        ("IOSCommandCenterIcon.tga", (44, 120, 220, 255)),
        ("IOSPowerPlantIcon.tga", (236, 190, 52, 255)),
        ("IOSBarracksIcon.tga", (80, 180, 120, 255)),
        ("IOSRangerIcon.tga", (210, 230, 245, 255)),
        ("IOSScoutVehicleIcon.tga", (120, 150, 165, 255)),
        ("IOSStopIcon.tga", (220, 62, 54, 255)),
        ("IOSSelectAllIcon.tga", (150, 96, 210, 255)),
    )
    for filename, color in icon_colors:
        write_radial_tga(
            out_dir / "Data" / "Art" / "Textures" / filename,
            color,
            records,
            "ios_playable_slice_icon",
            project_root,
            size=64,
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
    write_playable_slice_assets(out_dir, records, project_root)

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
