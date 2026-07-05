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

STOCK_TEMPLATE_MODEL_NAMES = (
    "GenericDebris",
    "GenericBridge",
    "WaterWaveBridge",
    "GarrisonGun",
    "WaveHit01",
    "WaveSplash01",
    "WaveSplashLeft01",
    "WaveSplashRight01",
    "WaveSpray01",
    "WaveSpray02",
    "WaveSpray03",
    "GLAScudStorm",
    "Boss_GLAScudStorm",
    "Chem_GLAScudStorm",
    "Demo_GLAScudStorm",
    "Slth_GLAScudStorm",
    "AmericaParticleCannonUplink",
    "AirF_AmericaParticleCannonUplink",
    "Lazr_AmericaParticleCannonUplink",
    "SupW_AmericaParticleCannonUplink",
    "Boss_ParticleCannonUplink",
    "ChinaNuclearMissileLauncher",
    "Boss_NuclearMissileLauncher",
    "Infa_ChinaNuclearMissileLauncher",
    "Nuke_ChinaNuclearMissileLauncher",
    "Tank_ChinaNuclearMissileLauncher",
)

STOCK_GENERATED_TEMPLATE_NAMES = (
    "GarrisonGun",
    "WaveHit01",
    "WaveSplash01",
    "WaveSplashLeft01",
    "WaveSplashRight01",
    "WaveSpray01",
    "WaveSpray02",
    "WaveSpray03",
    "GLAScudStorm",
    "Boss_GLAScudStorm",
    "Chem_GLAScudStorm",
    "Demo_GLAScudStorm",
    "Slth_GLAScudStorm",
    "AmericaParticleCannonUplink",
    "AirF_AmericaParticleCannonUplink",
    "Lazr_AmericaParticleCannonUplink",
    "SupW_AmericaParticleCannonUplink",
    "Boss_ParticleCannonUplink",
    "ChinaNuclearMissileLauncher",
    "Boss_NuclearMissileLauncher",
    "Infa_ChinaNuclearMissileLauncher",
    "Nuke_ChinaNuclearMissileLauncher",
    "Tank_ChinaNuclearMissileLauncher",
)

STOCK_MAPPED_IMAGE_ALIASES = (
    ("Apocalypse", "IOSGeneralPowersIcon.tga"),
    ("Campaign_China", "IOSStarGold.tga"),
    ("Campaign_GLA", "IOSStarGold.tga"),
    ("Campaign_USA", "IOSStarGold.tga"),
    ("Challenge_Bronz", "IOSStarBronze.tga"),
    ("Challenge_Gold", "IOSStarGold.tga"),
    ("Challenge_Silver", "IOSStarSilver.tga"),
    ("ChinaCampaign_B", "IOSStarBronze.tga"),
    ("ChinaCampaign_G", "IOSStarGold.tga"),
    ("ChinaCampaign_S", "IOSStarSilver.tga"),
    ("CustomMatch_deselected", "IOSOptionsIcon.tga"),
    ("CustomMatch_selected", "IOSFactionEnabled.tga"),
    ("Domination_100", "IOSStarBronze.tga"),
    ("Domination_1000", "IOSStarSilver.tga"),
    ("Domination_10000", "IOSStarGold.tga"),
    ("Domination_500", "IOSStarSilver.tga"),
    ("Endurance", "IOSGeneralPowersIcon.tga"),
    ("Endurance_B", "IOSStarBronze.tga"),
    ("Endurance_G", "IOSStarGold.tga"),
    ("Endurance_S", "IOSStarSilver.tga"),
    ("FairPlay", "IOSFactionEnabled.tga"),
    ("GLACampaign_B", "IOSStarBronze.tga"),
    ("GLACampaign_G", "IOSStarGold.tga"),
    ("GLACampaign_S", "IOSStarSilver.tga"),
    ("GlobalGen", "IOSGeneralPowersIcon.tga"),
    ("HonorAirWing", "IOSScoutVehicleIcon.tga"),
    ("HonorBattleTank", "IOSScoutVehicleIcon.tga"),
    ("HonorBlitz10", "IOSStarGold.tga"),
    ("HonorBlitz5", "IOSStarSilver.tga"),
    ("HonorChallenge1", "IOSStarBronze.tga"),
    ("HonorChallenge2", "IOSStarBronze.tga"),
    ("HonorChallenge3", "IOSStarSilver.tga"),
    ("HonorChallenge4", "IOSStarSilver.tga"),
    ("HonorChallenge5", "IOSStarGold.tga"),
    ("HonorChallenge6", "IOSStarGold.tga"),
    ("HonorChallenge7", "IOSGeneralPowersIcon.tga"),
    ("HonorStreak_100", "IOSStarBronze.tga"),
    ("HonorStreak_1000", "IOSStarGold.tga"),
    ("HonorStreak_500", "IOSStarSilver.tga"),
    ("HonorStreak_B", "IOSStarBronze.tga"),
    ("HonorStreak_G", "IOSStarGold.tga"),
    ("HonorStreak_S", "IOSStarSilver.tga"),
    ("Loyalty_China", "IOSFactionSideIcon.tga"),
    ("Loyalty_GLA", "IOSFactionSideIcon.tga"),
    ("Loyalty_USA", "IOSFactionSideIcon.tga"),
    ("USACampaign_B", "IOSStarBronze.tga"),
    ("USACampaign_G", "IOSStarGold.tga"),
    ("USACampaign_S", "IOSStarSilver.tga"),
    ("Ultimate", "IOSGeneralPowersIcon.tga"),
)

IOS_MODEL_ASSETS = (
    "IOSCommandCenter",
    "IOSPowerPlant",
    "IOSBarracks",
    "IOSDozer",
    "IOSRanger",
    "IOSScoutVehicle",
    "IOSBeacon",
    "IOSRallyPointMarker",
    "IOSGenericDebris",
    "IOSGenericBridge",
    "IOSWaterWaveBridge",
    *STOCK_TEMPLATE_MODEL_NAMES,
)

DAZZLE_TEXTURES = (
    ("SunDazzle.tga", (255, 245, 198, 255), "dazzle radial sprite"),
    ("SunHalo.tga", (255, 232, 160, 220), "halo radial sprite"),
    ("SunLensFlare.tga", (255, 250, 220, 235), "lens flare atlas"),
)

IOS_RUNTIME_TEXTURES = (
    ("EXLaser.tga", (90, 220, 255, 255), "waypoint laser texture"),
    ("EXScorch01.tga", (55, 45, 38, 255), "scorch decal texture"),
    ("EXSnowFlake.tga", (240, 248, 255, 230), "snow flake texture"),
    ("Noise0000.tga", (112, 128, 142, 255), "water noise texture"),
    ("TBBib.tga", (42, 48, 42, 180), "building bib texture"),
    ("TBRedBib.tga", (120, 42, 42, 190), "highlight bib texture"),
    ("TMGras23a.tga", (48, 112, 60, 255), "grass shadow texture"),
    ("TSCloudMed.tga", (178, 192, 205, 210), "cloud texture"),
    ("TSMoonLarg.tga", (224, 226, 215, 255), "sky body texture"),
    ("TSMorningE.tga", (92, 142, 170, 255), "skybox east texture"),
    ("TSMorningN.tga", (82, 132, 162, 255), "skybox north texture"),
    ("TSMorningS.tga", (106, 152, 176, 255), "skybox south texture"),
    ("TSMorningT.tga", (130, 170, 190, 255), "skybox top texture"),
    ("TSMorningW.tga", (96, 136, 165, 255), "skybox west texture"),
    ("TSNoiseUrb.tga", (88, 88, 88, 255), "terrain noise texture"),
    ("TWAlphaEdge.tga", (128, 180, 210, 160), "water alpha edge texture"),
    ("TWWater01.tga", (38, 104, 148, 210), "standing water texture"),
    ("TXAsph01a.tga", (80, 80, 76, 255), "asphalt shadow texture"),
    ("TXSnow04a.tga", (224, 230, 232, 255), "snow shadow texture"),
    ("WaterSurfaceBubbles.tga", (180, 220, 238, 190), "water sparkle texture"),
    ("alphaclip.tga", (255, 255, 255, 180), "water alpha clip texture"),
    ("exmask_g.tga", (128, 128, 128, 255), "fade mask texture"),
    ("missing.tga", (255, 0, 255, 255), "missing fallback texture"),
    ("shadow.tga", (0, 0, 0, 140), "projected shadow texture"),
    ("shroud1024.tga", (0, 0, 0, 220), "shroud texture"),
    ("wave1.tga", (70, 142, 180, 210), "water wave texture"),
    ("wave2.tga", (56, 126, 170, 210), "water wave texture"),
    ("wave256.tga", (64, 132, 178, 210), "water wave texture"),
)

IOS_AUDIO_ASSETS = (
    ("ui_click.wav", "octave/ui_click.wav"),
    ("rally_set.wav", "octave/rally_set.wav"),
    ("place_building.wav", "octave/place_building.wav"),
    ("action_rejected.wav", "octave/action_rejected.wav"),
    ("load_ambient.wav", "octave/load_ambient.wav"),
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

IOS_AUDIO_SETTINGS = """AudioSettings
  AudioRoot = Data/Audio
  SoundsFolder = Sounds
  MusicFolder = Music
  StreamingFolder = Speech
  SoundsExtension = wav
  UseDigital = Yes
  UseMidi = No
  OutputRate = 44100
  OutputBits = 16
  OutputChannels = 2
  SampleCount2D = 8
  SampleCount3D = 8
  StreamCount = 1
  AudioFootprintInBytes = 2097152
  DefaultSoundVolume = 0%
  Default3DSoundVolume = 0%
  DefaultSpeechVolume = 0%
  DefaultMusicVolume = 0%
  Relative2DVolume = 100%
  MinSampleVolume = 0%
  Use3DSoundRangeVolumeFade = Yes
  GlobalMinRange = 0
  GlobalMaxRange = 600
  TimeBetweenDrawableSounds = 3000
  TimeToFadeAudio = 100
  ZoomSoundVolumePercentageAmount = 0%
End
"""

IOS_AI_DATA = """AIData
  StructureSeconds = 8.0
  TeamSeconds = 8.0
  Wealthy = 7000
  Poor = 1000
  ForceIdleMSEC = 250
  StructuresWealthyRate = 1.0
  TeamsWealthyRate = 1.0
  StructuresPoorRate = 1.0
  TeamsPoorRate = 1.0
  TeamResourcesToStart = 0.1
  GuardInnerModifierAI = 1.0
  GuardOuterModifierAI = 1.0
  GuardInnerModifierHuman = 1.0
  GuardOuterModifierHuman = 1.0
  GuardChaseUnitsDuration = 3000
  GuardEnemyScanRate = 1000
  GuardEnemyReturnScanRate = 3000
  SkirmishGroupFudgeDistance = 80.0
  RepulsedDistance = 60.0
  EnableRepulsors = Yes
  AlertRangeModifier = 1.0
  AggressiveRangeModifier = 1.0
  ForceSkirmishAI = Yes
  RotateSkirmishBases = No
  AttackUsesLineOfSight = Yes
  AttackIgnoreInsignificantBuildings = Yes
  AttackPriorityDistanceModifier = 1.0
  MaxRecruitRadius = 600.0
  SkirmishBaseDefenseExtraDistance = 120.0
  WallHeight = 15.0
  MinInfantryForGroup = 2
  MinVehiclesForGroup = 1
  MinDistanceForGroup = 120.0
  DistanceRequiresGroup = 240.0
  MinClumpDensity = 0.0
  InfantryPathfindDiameter = 1
  VehiclePathfindDiameter = 2
  RebuildDelayTimeSeconds = 8
  SupplyCenterSafeRadius = 180.0
  AIDozerBoredRadiusModifier = 1.0
  AICrushesInfantry = No
  MaxRetaliationDistance = 700.0
  RetaliationFriendsRadius = 240.0

  SkirmishBuildList FactionIOS
    Structure IOSPowerPlant
      Name = IOSAI_PowerPlant
      Location = X:420.0 Y:280.0
      Rebuilds = 1
      Angle = 0.0
      InitiallyBuilt = No
      RallyPointOffset = X:32.0 Y:0.0
      AutomaticallyBuild = Yes
    End
    Structure IOSBarracks
      Name = IOSAI_Barracks
      Location = X:420.0 Y:360.0
      Rebuilds = 1
      Angle = 0.0
      InitiallyBuilt = No
      RallyPointOffset = X:-48.0 Y:0.0
      AutomaticallyBuild = Yes
    End
  End
End
"""

IOS_SILENT_SOUND_EFFECTS = """AudioEvent DefaultSoundEffect
  Volume = 70%
  MinVolume = 0%
  Limit = 4
  Priority = LOWEST
  Type = UI EVERYONE
End

AudioEvent PlaceBuilding
  Sounds = place_building
  Volume = 70%
End

AudioEvent RallyPointSet
  Sounds = rally_set
  Volume = 55%
End

AudioEvent UnableToSetRallyPoint
  Sounds = action_rejected
  Volume = 65%
End

AudioEvent BeaconPlaced
  Sounds = ui_click
  Volume = 55%
End

AudioEvent BeaconPlacementFailed
  Sounds = action_rejected
  Volume = 65%
End

AudioEvent LoadScreenAmbient
  Sounds = load_ambient
  Volume = 35%
End

AudioEvent GUIClick
  Sounds = ui_click
  Volume = 45%
End
"""

IOS_SILENT_MUSIC = """MusicTrack DefaultMusicTrack
  Volume = 0%
  Ambient = Yes
End
"""

IOS_MISC_AUDIO = """MiscAudio
  GUIClickSound = GUIClick
  NoCanDoSound = UnableToSetRallyPoint
  AllCheerSound = NoSound
  BattleCrySound = NoSound
  MoneyDepositSound = NoSound
  MoneyWithdrawSound = NoSound
  RadarNotifyUnitUnderAttackSound = NoSound
  RadarNotifyHarvesterUnderAttackSound = NoSound
  RadarNotifyStructureUnderAttackSound = NoSound
  RadarNotifyUnderAttackSound = NoSound
  RadarNotifyOnlineSound = NoSound
  RadarNotifyOfflineSound = NoSound
  UnitPromoted = NoSound
  RepairSparks = NoSound
  CrateHeal = NoSound
  CrateMoney = NoSound
End
"""

IOS_BOOT_NOOP_INI = """; Generated iOS boot no-op.
; This file is intentionally parseable but definition-free because the engine
; requires at least one INI file in this directory during loadFileDirectory().
; Real playable-slice definitions are emitted in the category-specific
; ios_playable_slice.ini files or in the non-empty boot INIs above.
"""


def boot_ini_for(dirname: str) -> str:
    if dirname == "AIData":
        return IOS_AI_DATA
    if dirname == "AudioSettings":
        return IOS_AUDIO_SETTINGS
    if dirname == "SoundEffects":
        return IOS_SILENT_SOUND_EFFECTS
    if dirname == "Music":
        return IOS_SILENT_MUSIC
    if dirname == "MiscAudio":
        return IOS_MISC_AUDIO
    if dirname in ("Speech", "Voice"):
        return "DialogEvent DefaultDialog\n  Volume = 0%\nEnd\n"
    return IOS_BOOT_NOOP_INI

IOS_BOOT_LANGUAGE = "Language = English\nUnicodeFontName = Arial\n"
CSF_ID = (ord("C") << 24) | (ord("S") << 16) | (ord("F") << 8) | ord(" ")
CSF_LABEL = (ord("L") << 24) | (ord("B") << 16) | (ord("L") << 8) | ord(" ")
CSF_STRING = (ord("S") << 24) | (ord("T") << 16) | (ord("R") << 8) | ord(" ")
CSF_VERSION = 3
LANGUAGE_ID_US = 0
IOS_SLICE_MAP_NAME = "IOSPlayableSlice"
IOS_SLICE_MAP_PATH = f"Maps/{IOS_SLICE_MAP_NAME}/{IOS_SLICE_MAP_NAME}.map"
IOS_GAMEPLAY_WND_LAYOUTS = {
    "ControlBar.wnd": None,
    "ControlBarPopupDescription.wnd": None,
    "GeneralsExpPoints.wnd": None,
    "InGamePopupMessage.wnd": None,
    "InGameChat.wnd": None,
    "MOTD.wnd": None,
    "ReplayControl.wnd": None,
    "controlBarHidden.wnd": None,
    "Menus/CRCMismatch.wnd": "Connection Mismatch",
    "Menus/Defeat.wnd": "Defeat",
    "Menus/ChallengeLoadScreen.wnd": "Loading",
    "Menus/DisconnectScreen.wnd": "Disconnected",
    "Menus/GameSpyLoadScreen.wnd": "Loading",
    "Menus/LocalDefeat.wnd": "Defeat",
    "Menus/MapTransferScreen.wnd": "Loading",
    "Menus/MessageBox.wnd": None,
    "Menus/MultiplayerLoadScreen.wnd": "Loading",
    "Menus/ObserverQuit.wnd": "Observer Quit",
    "Menus/OptionsMenu.wnd": "Options",
    "Menus/PopupCommunicator.wnd": None,
    "Menus/PopupReplay.wnd": "Replay",
    "Menus/PopupSaveLoad.wnd": "Save",
    "Menus/QuitMenu.wnd": "Quit",
    "Menus/QuitMessageBox.wnd": "Quit",
    "Menus/QuitNoSave.wnd": "Quit",
    "Menus/ScoreScreen.wnd": "Score",
    "Menus/ShellGameLoadScreen.wnd": "Loading",
    "Menus/SinglePlayerLoadScreen.wnd": "Loading",
    "Menus/Victorious.wnd": "Victory",
}
IOS_CSF_LABELS = {
    "GUI:Observer": "Observer",
    "INI:FactionCivilian": "Civilian",
    "INI:FactionIOS": "iOS Task Force",
    "INI:IOSCommandCenter": "Command Center",
    "INI:IOSPowerPlant": "Power Plant",
    "INI:IOSBarracks": "Barracks",
    "INI:IOSDozer": "Builder",
    "INI:IOSRanger": "Ranger",
    "INI:IOSScoutVehicle": "Scout Vehicle",
    "INI:IOSBeacon": "Beacon",
    "INI:RallyPointMarker": "Rally Point",
    "INI:GenericDebris": "Debris",
    "INI:GenericBridge": "Bridge",
    "INI:WaterWaveBridge": "Water Bridge",
    "INI:Command_ConstructIOSDozer": "Build Builder",
    "INI:Command_ConstructIOSDozerDescription": "Produces a construction unit.",
    "INI:Command_ConstructIOSPowerPlant": "Build Power Plant",
    "INI:Command_ConstructIOSPowerPlantDescription": "Builds a compact generator for the iOS force.",
    "INI:Command_ConstructIOSBarracks": "Build Barracks",
    "INI:Command_ConstructIOSBarracksDescription": "Builds an infantry production structure.",
    "INI:Command_ConstructIOSScoutVehicle": "Build Scout Vehicle",
    "INI:Command_ConstructIOSScoutVehicleDescription": "Produces a fast armed scout vehicle.",
    "INI:Command_ConstructIOSRanger": "Train Ranger",
    "INI:Command_ConstructIOSRangerDescription": "Trains a basic infantry squad member.",
    "INI:Command_Stop": "Stop",
    "INI:Command_StopDescription": "Cancels the current order.",
    "INI:Command_SelectAllOfType": "Select Type",
    "INI:Command_SelectAllOfTypeDescription": "Selects matching units on screen.",
    "INI:Command_CancelUnitCreate": "Cancel Unit",
    "INI:Command_CancelUnitCreateDescription": "Cancels the selected production item.",
    "INI:Command_CancelUpgradeCreate": "Cancel Upgrade",
    "INI:Command_CancelUpgradeCreateDescription": "Cancels the selected upgrade item.",
    "INI:Command_CancelConstruction": "Cancel",
    "INI:Command_CancelConstructionDescription": "Cancels construction.",
    "INI:Command_Sell": "Sell",
    "INI:Command_SellDescription": "Sells the selected structure.",
    "INI:Command_SetRallyPoint": "Rally Point",
    "INI:Command_SetRallyPointDescription": "Sets the production rally point.",
    "INI:Command_Evacuate": "Evacuate",
    "INI:Command_EvacuateDescription": "Orders contained units to exit.",
    "INI:Command_StructureExit": "Exit",
    "INI:Command_StructureExitDescription": "Orders one contained unit to exit.",
    "INI:Command_TransportExit": "Unload",
    "INI:Command_TransportExitDescription": "Orders transport passengers to exit.",
    "GUI:Communicator": "Messages",
    "GUI:CommunicatorDescription": "Opens the communicator.",
    "GUI:Options": "Options",
    "GUI:OptionsDescription": "Opens the options menu.",
    "GUI:IdleWorker": "Idle Builder",
    "GUI:IdleWorkerDescription": "Selects the next idle builder.",
    "GUI:Beacon": "Beacon",
    "GUI:BeaconDescription": "Places a map beacon.",
    "GUI:GeneralPowerShortcut": "General Powers",
    "GUI:GeneralPowerShortcutDescription": "Opens available general powers.",
    "GUI:ToggleControlBar": "Control Bar",
    "GUI:ToggleControlBarDescription": "Toggles the expanded control bar.",
    "MAP:IOSPlayableSlice": "iOS Playable Slice",
}
IOS_CSF_LABELS.update({f"INI:{name}": name for name in STOCK_TEMPLATE_MODEL_NAMES})
IOS_SLICE_PLAYER_TEMPLATE = """PlayerTemplate FactionObserver
  Side = Observer
  BaseSide = Observer
  PlayableSide = No
  DisplayName = GUI:Observer
  SideIconImage = IOSObserverSideIcon
  GeneralImage = IOSObserverSideIcon
  IsObserver = Yes
End

PlayerTemplate FactionCivilian
  Side = Civilian
  BaseSide = Civilian
  PlayableSide = No
  DisplayName = INI:FactionCivilian
  PreferredColor = R:255 G:255 B:255
  SideIconImage = IOSCivilianSideIcon
  GeneralImage = IOSCivilianSideIcon
End

PlayerTemplate FactionIOS
  Side = IOS
  BaseSide = USA
  PlayableSide = Yes
  DisplayName = INI:FactionIOS
  LoadScreenImage = IOSLoadScreen
  ScoreScreenImage = IOSScoreScreen
  HeadWaterMark = IOSHeadWaterMark
  FlagWaterMark = IOSFlagWaterMark
  EnabledImage = IOSFactionEnabled
  SideIconImage = IOSFactionSideIcon
  GeneralImage = IOSFactionGeneral
  StartMoney = 10000
  PreferredColor = R:32 G:168 B:255
  StartingBuilding = IOSCommandCenter
  StartingUnit0 = IOSRanger
  StartingUnit1 = IOSScoutVehicle
  StartingUnit2 = IOSDozer
  BeaconName = IOSBeacon
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

CommandButton Command_ConstructIOSDozer
  Command = UNIT_BUILD
  Object = IOSDozer
  TextLabel = INI:Command_ConstructIOSDozer
  DescriptLabel = INI:Command_ConstructIOSDozerDescription
  ButtonImage = IOSDozerIcon
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

CommandButton Command_Stop
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

CommandButton Command_CancelUnitCreate
  Command = CANCEL_UNIT_BUILD
  TextLabel = INI:Command_CancelUnitCreate
  DescriptLabel = INI:Command_CancelUnitCreateDescription
  ButtonImage = IOSCancelIcon
  ButtonBorderType = SYSTEM
End

CommandButton Command_CancelUpgradeCreate
  Command = CANCEL_UPGRADE
  TextLabel = INI:Command_CancelUpgradeCreate
  DescriptLabel = INI:Command_CancelUpgradeCreateDescription
  ButtonImage = IOSCancelIcon
  ButtonBorderType = SYSTEM
End

CommandButton Command_CancelConstruction
  Command = DOZER_CONSTRUCT_CANCEL
  TextLabel = INI:Command_CancelConstruction
  DescriptLabel = INI:Command_CancelConstructionDescription
  ButtonImage = IOSCancelIcon
  ButtonBorderType = SYSTEM
End

CommandButton Command_Sell
  Command = SELL
  TextLabel = INI:Command_Sell
  DescriptLabel = INI:Command_SellDescription
  ButtonImage = IOSSellIcon
  ButtonBorderType = SYSTEM
End

CommandButton Command_SetRallyPoint
  Command = SET_RALLY_POINT
  TextLabel = INI:Command_SetRallyPoint
  DescriptLabel = INI:Command_SetRallyPointDescription
  ButtonImage = IOSRallyPointIcon
  ButtonBorderType = ACTION
End

CommandButton Command_Evacuate
  Command = EVACUATE
  TextLabel = INI:Command_Evacuate
  DescriptLabel = INI:Command_EvacuateDescription
  ButtonImage = IOSExitIcon
  ButtonBorderType = ACTION
End

CommandButton Command_StructureExit
  Command = EXIT_CONTAINER
  TextLabel = INI:Command_StructureExit
  DescriptLabel = INI:Command_StructureExitDescription
  ButtonImage = IOSExitIcon
  ButtonBorderType = ACTION
End

CommandButton Command_TransportExit
  Command = EXIT_CONTAINER
  TextLabel = INI:Command_TransportExit
  DescriptLabel = INI:Command_TransportExitDescription
  ButtonImage = IOSExitIcon
  ButtonBorderType = ACTION
End

CommandButton NonCommand_Communicator
  Command = NONE
  TextLabel = GUI:Communicator
  DescriptLabel = GUI:CommunicatorDescription
  ButtonImage = IOSCommunicatorIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_BriefingHistory
  Command = NONE
  TextLabel = GUI:Communicator
  DescriptLabel = GUI:CommunicatorDescription
  ButtonImage = IOSCommunicatorIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_Options
  Command = NONE
  TextLabel = GUI:Options
  DescriptLabel = GUI:OptionsDescription
  ButtonImage = IOSOptionsIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_IdleWorker
  Command = NONE
  TextLabel = GUI:IdleWorker
  DescriptLabel = GUI:IdleWorkerDescription
  ButtonImage = IOSIdleWorkerIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_Beacon
  Command = PLACE_BEACON
  TextLabel = GUI:Beacon
  DescriptLabel = GUI:BeaconDescription
  ButtonImage = IOSBeaconIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_GeneralsExperience
  Command = NONE
  TextLabel = GUI:GeneralPowerShortcut
  DescriptLabel = GUI:GeneralPowerShortcutDescription
  ButtonImage = IOSGeneralPowersIcon
  ButtonBorderType = SYSTEM
End

CommandButton NonCommand_UpDown
  Command = NONE
  TextLabel = GUI:ToggleControlBar
  DescriptLabel = GUI:ToggleControlBarDescription
  ButtonImage = IOSToggleControlBarIcon
  ButtonBorderType = SYSTEM
End
"""

IOS_SLICE_COMMAND_SET = """CommandSet IOSCommandCenterCommandSet
  1 = Command_ConstructIOSDozer
  13 = Command_IOSSelectAllOfType
  14 = Command_IOSStop
End

CommandSet IOSDozerCommandSet
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

IOS_SLICE_ARMOR = """Armor DEFAULT
  Armor = DEFAULT 100%
End

Armor IOSInfantryArmor
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
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSCommandCenter
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 1800.0
    InitialHealth = 1800.0
  End
  Behavior = ProductionUpdate ModuleTag_Production
    MaxQueueEntries = 4
  End
  Behavior = QueueProductionExitUpdate ModuleTag_ProductionExit
    UnitCreatePoint = X:0.0 Y:0.0 Z:0.0
    NaturalRallyPoint = X:72.0 Y:0.0 Z:0.0
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
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSPowerPlant
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 900.0
    InitialHealth = 900.0
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
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSBarracks
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 1100.0
    InitialHealth = 1100.0
  End
  Behavior = ProductionUpdate ModuleTag_Production
    MaxQueueEntries = 4
  End
  Behavior = QueueProductionExitUpdate ModuleTag_ProductionExit
    UnitCreatePoint = X:0.0 Y:0.0 Z:0.0
    NaturalRallyPoint = X:56.0 Y:0.0 Z:0.0
  End
  ButtonImage = IOSBarracksIcon
  SelectPortrait = IOSBarracksIcon
End

Object IOSDozer
  DisplayName = INI:IOSDozer
  Side = IOS
  EditorSorting = VEHICLE
  KindOf = PRELOAD SELECTABLE VEHICLE DOZER SCORE
  Buildable = Yes
  BuildCost = 1000
  BuildTime = 5.0
  CommandSet = IOSDozerCommandSet
  VisionRange = 150.0
  ShroudClearingRange = 180.0
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSDozer
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSVehicleArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 300.0
    InitialHealth = 300.0
  End
  Behavior = DozerAIUpdate ModuleTag_AI
    RepairHealthPercentPerSecond = 2%
    BoredTime = 5000
    BoredRange = 150
  End
  LocomotorSet = SET_NORMAL IOSVehicleLocomotor
  Behavior = PhysicsBehavior ModuleTag_Physics
    Mass = 40.0
  End
  ButtonImage = IOSDozerIcon
  SelectPortrait = IOSDozerIcon
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
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSRanger
    End
  End
  WeaponSet
    Conditions = None
    Weapon = PRIMARY IOSRifleWeapon
  End
  ArmorSet
    Conditions = None
    Armor = IOSInfantryArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 120.0
    InitialHealth = 120.0
  End
  Behavior = AIUpdateInterface ModuleTag_AI
    AutoAcquireEnemiesWhenIdle = Yes
  End
  LocomotorSet = SET_NORMAL IOSInfantryLocomotor
  Behavior = PhysicsBehavior ModuleTag_Physics
    Mass = 4.0
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
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSScoutVehicle
    End
  End
  WeaponSet
    Conditions = None
    Weapon = PRIMARY IOSCannonWeapon
  End
  ArmorSet
    Conditions = None
    Armor = IOSVehicleArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 360.0
    InitialHealth = 360.0
  End
  Behavior = AIUpdateInterface ModuleTag_AI
    AutoAcquireEnemiesWhenIdle = Yes
  End
  LocomotorSet = SET_NORMAL IOSVehicleLocomotor
  Behavior = PhysicsBehavior ModuleTag_Physics
    Mass = 40.0
  End
  ButtonImage = IOSScoutVehicleIcon
  SelectPortrait = IOSScoutVehicleIcon
End

Object IOSBeacon
  DisplayName = INI:IOSBeacon
  Side = IOS
  EditorSorting = MISC_MAN_MADE
  KindOf = IMMOBILE SELECTABLE INERT
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSBeacon
    End
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 1.0
    InitialHealth = 1.0
  End
End

Object RallyPointMarker
  DisplayName = INI:RallyPointMarker
  Side = IOS
  EditorSorting = MISC_MAN_MADE
  KindOf = IMMOBILE INERT
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSRallyPointMarker
    End
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 1.0
    InitialHealth = 1.0
  End
End

Object GenericDebris
  DisplayName = INI:GenericDebris
  Side = Civilian
  EditorSorting = MISC_MAN_MADE
  KindOf = INERT
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSGenericDebris
    End
  End
  Body = ActiveBody ModuleTag_Body
    MaxHealth = 1.0
    InitialHealth = 1.0
  End
  Behavior = PhysicsBehavior ModuleTag_Physics
    Mass = 1.0
  End
End

Object GenericBridge
  DisplayName = INI:GenericBridge
  Side = Civilian
  EditorSorting = MISC_MAN_MADE
  KindOf = STRUCTURE IMMOBILE BRIDGE
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSGenericBridge
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 2000.0
    InitialHealth = 2000.0
  End
End

Object WaterWaveBridge
  DisplayName = INI:WaterWaveBridge
  Side = Civilian
  EditorSorting = MISC_MAN_MADE
  KindOf = STRUCTURE IMMOBILE BRIDGE
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = IOSWaterWaveBridge
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 2000.0
    InitialHealth = 2000.0
  End
End
"""

IOS_STOCK_TEMPLATE_OBJECTS = "".join(
    f"""

Object {name}
  DisplayName = INI:{name}
  Side = Civilian
  EditorSorting = MISC_MAN_MADE
  KindOf = STRUCTURE IMMOBILE INERT
  Buildable = No
  Draw = W3DModelDraw ModuleTag_Draw
    DefaultConditionState
      Model = {name}
    End
  End
  ArmorSet
    Conditions = None
    Armor = IOSStructureArmor
    DamageFX = IOSDefaultDamageFX
  End
  Body = StructureBody ModuleTag_Body
    MaxHealth = 1000.0
    InitialHealth = 1000.0
  End
End
"""
    for name in STOCK_GENERATED_TEMPLATE_NAMES
)

IOS_SLICE_OBJECT = IOS_SLICE_OBJECT.rstrip() + IOS_STOCK_TEMPLATE_OBJECTS

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

def wnd_block(
    name: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    window_type: str = "USER",
    style: str = "USER",
    system_callback: str = "[None]",
    input_callback: str = "[None]",
    draw_callback: str = "[None]",
    text: str = "",
    font_size: int = 10,
    color: tuple[int, int, int, int] = (40, 44, 50, 210),
    indent: str = "  ",
    children: str = "",
) -> str:
    child_block = f"{children}" if children else ""
    return f"""{indent}WINDOW
{indent}  WINDOWTYPE = {window_type};
{indent}  SCREENRECT = UPPERLEFT: {x1} {y1}, BOTTOMRIGHT: {x2} {y2}, CREATIONRESOLUTION: 1024 768;
{indent}  NAME = "{name}";
{indent}  STATUS = ENABLED+IMAGE;
{indent}  STYLE = {style};
{indent}  SYSTEMCALLBACK = "{system_callback}";
{indent}  INPUTCALLBACK = "{input_callback}";
{indent}  TOOLTIPCALLBACK = "[None]";
{indent}  DRAWCALLBACK = "{draw_callback}";
{indent}  FONT = NAME: "Arial", SIZE: {font_size}, BOLD: 0;
{indent}  HEADERTEMPLATE = "[NONE]";
{indent}  TOOLTIPDELAY = -1;
{indent}  TEXT = "{text}";
{indent}  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
{indent}              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
{indent}              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
{indent}  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: {color[0]} {color[1]} {color[2]} {color[3]}, BORDERCOLOR: 180 190 205 180;
{indent}  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 25 28 32 180, BORDERCOLOR: 80 80 80 160;
{indent}  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 75 82 92 235, BORDERCOLOR: 255 235 170 220;{child_block}
{indent}END
"""


def child_wnd_block(
    name: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    window_type: str = "USER",
    style: str = "USER",
    system_callback: str = "[None]",
    input_callback: str = "[None]",
    draw_callback: str = "[None]",
    text: str = "",
    font_size: int = 10,
    color: tuple[int, int, int, int] = (40, 44, 50, 210),
) -> str:
    return "\n  CHILD\n" + wnd_block(
        name,
        x1,
        y1,
        x2,
        y2,
        window_type=window_type,
        style=style,
        system_callback=system_callback,
        input_callback=input_callback,
        draw_callback=draw_callback,
        text=text,
        font_size=font_size,
        color=color,
        indent="  ",
    )


def push_button(
    name: str,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    text: str = "",
) -> str:
    return child_wnd_block(
        name,
        x1,
        y1,
        x2,
        y2,
        window_type="PUSHBUTTON",
        style="PUSHBUTTON+USER",
        system_callback="PassSelectedButtonsToParentSystem",
        text=text,
        color=(58, 64, 72, 235),
    )


def control_bar_wnd() -> str:
    command_buttons = []
    for index in range(14):
        col = index % 7
        row = index // 7
        command_buttons.append(
            push_button(
                f"ControlBar.wnd:ButtonCommand{index + 1:02d}",
                372 + col * 52,
                606 + row * 52,
                418 + col * 52,
                652 + row * 52,
            )
        )
    queue_buttons = [
        push_button(f"ControlBar.wnd:ButtonQueue{index + 1:02d}", 765 + index * 42, 604, 802 + index * 42, 641)
        for index in range(9)
    ]
    upgrades = [
        push_button(f"ControlBar.wnd:UnitUpgrade{index + 1}", 824 + index * 38, 672, 858 + index * 38, 706)
        for index in range(8)
    ]
    children = "".join(
        [
            child_wnd_block("ControlBar.wnd:BackgroundMarker", 0, 582, 1024, 768, color=(16, 19, 24, 230)),
            child_wnd_block("ControlBar.wnd:ControlBarParent", 0, 582, 1024, 768, system_callback="ControlBarSystem", input_callback="ControlBarInput", color=(18, 22, 28, 235)),
            child_wnd_block("ControlBar.wnd:CommandWindow", 360, 596, 750, 714, color=(20, 24, 30, 190)),
            *command_buttons,
            child_wnd_block("ControlBar.wnd:ProductionQueueWindow", 756, 596, 1012, 646, color=(20, 24, 30, 190)),
            *queue_buttons,
            child_wnd_block("ControlBar.wnd:RightHUD", 780, 648, 1018, 756, color=(24, 29, 35, 210)),
            child_wnd_block("ControlBar.wnd:WinUnitSelected", 788, 656, 1010, 750, color=(24, 29, 35, 180)),
            child_wnd_block("ControlBar.wnd:CameoWindow", 792, 660, 858, 726, color=(48, 54, 62, 220)),
            *upgrades,
            child_wnd_block("ControlBar.wnd:MoneyDisplay", 18, 602, 154, 632, window_type="STATICTEXT", style="STATICTEXT+USER", text="$0", font_size=14, color=(24, 38, 30, 220)),
            child_wnd_block("ControlBar.wnd:PowerWindow", 18, 638, 154, 668, window_type="STATICTEXT", style="STATICTEXT+USER", text="POWER", font_size=12, color=(42, 34, 20, 220)),
            child_wnd_block("ControlBar.wnd:GeneralsExp", 18, 674, 154, 704, color=(36, 32, 48, 220)),
            child_wnd_block("ControlBar.wnd:ExpBarForeground", 22, 680, 150, 698, color=(120, 92, 32, 220)),
            child_wnd_block("ControlBar.wnd:WinUAttack", 166, 604, 344, 756, input_callback="LeftHUDInput", color=(28, 34, 40, 190)),
            push_button("ControlBar.wnd:PopupCommunicator", 900, 584, 944, 624),
            push_button("ControlBar.wnd:ButtonOptions", 952, 584, 1004, 624),
            push_button("ControlBar.wnd:ButtonIdleWorker", 166, 710, 212, 756),
            push_button("ControlBar.wnd:ButtonPlaceBeacon", 218, 710, 264, 756),
            push_button("ControlBar.wnd:ButtonGeneral", 270, 710, 316, 756),
            push_button("ControlBar.wnd:ButtonLarge", 322, 710, 352, 756),
            child_wnd_block("ControlBar.wnd:UnderConstructionWindow", 360, 596, 750, 714, color=(40, 28, 28, 190)),
            child_wnd_block("ControlBar.wnd:UnderConstructionDesc", 374, 610, 730, 640, window_type="STATICTEXT", style="STATICTEXT+USER", text="Constructing", color=(40, 28, 28, 190)),
            push_button("ControlBar.wnd:ButtonCancelConstruction", 660, 660, 730, 704, "Cancel"),
            child_wnd_block("ControlBar.wnd:OCLTimerWindow", 360, 596, 750, 714, color=(28, 32, 40, 190)),
            child_wnd_block("ControlBar.wnd:OCLTimerStaticText", 374, 610, 730, 640, window_type="STATICTEXT", style="STATICTEXT+USER", text="Timer", color=(28, 32, 40, 190)),
            child_wnd_block("ControlBar.wnd:OCLTimerProgressBar", 374, 652, 730, 674, color=(90, 120, 160, 220)),
            push_button("ControlBar.wnd:OCLTimerSellButton", 660, 680, 730, 724, "Sell"),
            child_wnd_block("ControlBar.wnd:BeaconWindow", 360, 596, 750, 714, color=(25, 35, 35, 190)),
            child_wnd_block("ControlBar.wnd:EditBeaconText", 374, 610, 700, 642, window_type="TEXTENTRY", style="TEXTENTRY+USER", color=(20, 25, 25, 220)),
            child_wnd_block("ControlBar.wnd:StaticTextBeaconLabel", 374, 650, 550, 678, window_type="STATICTEXT", style="STATICTEXT+USER", text="Beacon", color=(25, 35, 35, 190)),
            push_button("ControlBar.wnd:ButtonDeleteBeacon", 560, 650, 630, 694, "Delete"),
            push_button("ControlBar.wnd:ButtonClearBeaconText", 638, 650, 708, 694, "Clear"),
            child_wnd_block("ControlBar.wnd:ObserverPlayerListWindow", 166, 604, 352, 756, color=(24, 29, 35, 190)),
            child_wnd_block("ControlBar.wnd:ObserverPlayerInfoWindow", 780, 648, 1018, 756, color=(24, 29, 35, 190)),
            push_button("ControlBar.wnd:ButtonCancel", 704, 666, 748, 710),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 0 0, BOTTOMRIGHT: 1024 768, CREATIONRESOLUTION: 1024 768;
  NAME = "ControlBar.wnd";
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
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def control_bar_popup_description_wnd() -> str:
    children = "".join(
        [
            child_wnd_block(
                "ControlBarPopupDescription.wnd:StaticTextName",
                12,
                10,
                388,
                36,
                window_type="STATICTEXT",
                style="STATICTEXT+USER",
                text="Command",
                font_size=13,
                color=(22, 26, 30, 230),
            ),
            child_wnd_block(
                "ControlBarPopupDescription.wnd:StaticTextCost",
                12,
                38,
                388,
                62,
                window_type="STATICTEXT",
                style="STATICTEXT+USER",
                text="$0",
                font_size=12,
                color=(22, 34, 24, 220),
            ),
            child_wnd_block(
                "ControlBarPopupDescription.wnd:StaticTextDescription",
                12,
                66,
                388,
                154,
                window_type="STATICTEXT",
                style="STATICTEXT+USER",
                text="",
                font_size=11,
                color=(22, 26, 30, 230),
            ),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 420 438, BOTTOMRIGHT: 820 602, CREATIONRESOLUTION: 1024 768;
  NAME = "ControlBarPopupDescription.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 238, BORDERCOLOR: 180 190 205 180;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 160, BORDERCOLOR: 80 80 80 160;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 238, BORDERCOLOR: 255 235 170 220;{children}
END
"""


def generals_exp_points_wnd() -> str:
    rank1 = [
        push_button(f"GeneralsExpPoints.wnd:ButtonRank1Number{index}", 38 + index * 72, 112, 94 + index * 72, 168)
        for index in range(4)
    ]
    rank3 = [
        push_button(
            f"GeneralsExpPoints.wnd:ButtonRank3Number{index}",
            38 + (index % 5) * 72,
            204 + (index // 5) * 72,
            94 + (index % 5) * 72,
            260 + (index // 5) * 72,
        )
        for index in range(15)
    ]
    rank8 = [
        push_button(f"GeneralsExpPoints.wnd:ButtonRank8Number{index}", 38 + index * 72, 460, 94 + index * 72, 516)
        for index in range(4)
    ]
    children = "".join(
        [
            child_wnd_block("GeneralsExpPoints.wnd:GenExpParent", 0, 0, 430, 560, color=(18, 22, 28, 238)),
            child_wnd_block("GeneralsExpPoints.wnd:StaticTextTitle", 24, 18, 380, 48, window_type="STATICTEXT", style="STATICTEXT+USER", text="General Powers", font_size=16, color=(18, 22, 28, 180)),
            child_wnd_block("GeneralsExpPoints.wnd:StaticTextRankPointsAvailable", 24, 54, 380, 80, window_type="STATICTEXT", style="STATICTEXT+USER", text="Points Available: 0", font_size=12, color=(18, 22, 28, 180)),
            child_wnd_block("GeneralsExpPoints.wnd:StaticTextLevel", 24, 82, 220, 106, window_type="STATICTEXT", style="STATICTEXT+USER", text="Level 1", font_size=12, color=(18, 22, 28, 180)),
            child_wnd_block("GeneralsExpPoints.wnd:ProgressBarExperience", 224, 86, 386, 104, color=(120, 92, 32, 220)),
            *rank1,
            *rank3,
            *rank8,
            push_button("GeneralsExpPoints.wnd:ButtonExit", 320, 512, 394, 546, "Close"),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 292 96, BOTTOMRIGHT: 722 656, CREATIONRESOLUTION: 1024 768;
  NAME = "GeneralsExpPoints.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def ingame_chat_wnd() -> str:
    children = "".join(
        [
            child_wnd_block("InGameChat.wnd:StaticTextChatType", 12, 10, 214, 34, window_type="STATICTEXT", style="STATICTEXT+USER", text="Everyone", font_size=12, color=(18, 22, 28, 220)),
            child_wnd_block("InGameChat.wnd:TextEntryChat", 12, 38, 438, 72, window_type="TEXTENTRY", style="TEXTENTRY+USER", system_callback="InGameChatSystem", input_callback="InGameChatInput", color=(20, 25, 30, 235)),
            push_button("InGameChat.wnd:ButtonClear", 448, 38, 520, 72, "Clear"),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 240 650, BOTTOMRIGHT: 780 738, CREATIONRESOLUTION: 1024 768;
  NAME = "InGameChat.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "InGameChatSystem";
  INPUTCALLBACK = "InGameChatInput";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 238, BORDERCOLOR: 180 190 205 180;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 160, BORDERCOLOR: 80 80 80 160;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 10 13 17 238, BORDERCOLOR: 255 235 170 220;{children}
END
"""


def ingame_popup_message_wnd() -> str:
    children = "".join(
        [
            child_wnd_block("InGamePopupMessage.wnd:InGamePopupMessageParent", 0, 0, 420, 168, system_callback="InGamePopupMessageSystem", input_callback="InGamePopupMessageInput", color=(16, 20, 26, 242)),
            child_wnd_block("InGamePopupMessage.wnd:StaticTextMessage", 12, 12, 408, 112, window_type="STATICTEXT", style="STATICTEXT+USER", text="", font_size=12, color=(16, 20, 26, 210)),
            push_button("InGamePopupMessage.wnd:ButtonOk", 320, 124, 408, 156, "OK"),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = InGamePopupMessageInit;
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 302 260, BOTTOMRIGHT: 722 428, CREATIONRESOLUTION: 1024 768;
  NAME = "InGamePopupMessage.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def replay_control_wnd() -> str:
    children = "".join(
        [
            child_wnd_block("ReplayControl.wnd:ParentReplayControl", 0, 0, 320, 64, system_callback="ReplayControlSystem", input_callback="ReplayControlInput", color=(16, 20, 26, 220)),
            child_wnd_block("ReplayControl.wnd:StaticTextReplay", 12, 12, 308, 38, window_type="STATICTEXT", style="STATICTEXT+USER", text="Replay Controls", font_size=12, color=(16, 20, 26, 180)),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 352 12, BOTTOMRIGHT: 672 76, CREATIONRESOLUTION: 1024 768;
  NAME = "ReplayControl.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def motd_wnd() -> str:
    children = child_wnd_block("MOTD.wnd:MOTD", 0, 0, 420, 220, system_callback="MOTDSystem", color=(16, 20, 26, 230))
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 302 160, BOTTOMRIGHT: 722 380, CREATIONRESOLUTION: 1024 768;
  NAME = "MOTD.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def progress_bar(name: str, x1: int, y1: int, x2: int, y2: int) -> str:
    return child_wnd_block(
        name,
        x1,
        y1,
        x2,
        y2,
        window_type="PROGRESSBAR",
        style="PROGRESSBAR+USER",
        color=(74, 126, 184, 235),
    )


def single_player_load_screen_wnd() -> str:
    objective_lines = [
        child_wnd_block(
            f"SinglePlayerLoadScreen.wnd:StaticTextLine{index}",
            48,
            184 + index * 28,
            560,
            208 + index * 28,
            window_type="STATICTEXT",
            style="STATICTEXT+USER",
            font_size=12,
            color=(18, 22, 28, 180),
        )
        for index in range(5)
    ]
    cameo_text = [
        child_wnd_block(
            f"SinglePlayerLoadScreen.wnd:StaticTextCameoText{index}",
            650,
            206 + index * 42,
            960,
            236 + index * 42,
            window_type="STATICTEXT",
            style="STATICTEXT+USER",
            font_size=12,
            color=(18, 22, 28, 180),
        )
        for index in range(4)
    ]
    children = "".join(
        [
            child_wnd_block("SinglePlayerLoadScreen.wnd:ParentSinglePlayerLoadScreen", 0, 0, 1024, 768, color=(8, 10, 14, 245)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:ObjectivesWin", 40, 142, 590, 344, color=(16, 20, 26, 210)),
            *objective_lines,
            progress_bar("SinglePlayerLoadScreen.wnd:ProgressLoad", 210, 690, 814, 714),
            child_wnd_block("SinglePlayerLoadScreen.wnd:Percent", 824, 684, 928, 718, window_type="STATICTEXT", style="STATICTEXT+USER", text="0%", font_size=14, color=(8, 10, 14, 0)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:WindowCameo1", 610, 190, 642, 222, color=(40, 48, 58, 220)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:WindowCameo2", 610, 232, 642, 264, color=(40, 48, 58, 220)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:WindowCameo3", 610, 274, 642, 306, color=(40, 48, 58, 220)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:WindowHead", 740, 72, 910, 182, color=(30, 36, 44, 200)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:WindowHiliteCameo", 604, 184, 648, 228, color=(190, 160, 70, 120)),
            child_wnd_block("SinglePlayerLoadScreen.wnd:StaticTextCameoText", 650, 164, 960, 194, window_type="STATICTEXT", style="STATICTEXT+USER", font_size=12, color=(18, 22, 28, 180)),
            *cameo_text,
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 0 0, BOTTOMRIGHT: 1024 768, CREATIONRESOLUTION: 1024 768;
  NAME = "SinglePlayerLoadScreen.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 0 0 0 0, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def shell_game_load_screen_wnd() -> str:
    children = "".join(
        [
            child_wnd_block("ShellGameLoadScreen.wnd:StaticTextLegal", 120, 304, 904, 346, window_type="STATICTEXT", style="STATICTEXT+CENTER+USER", text="GeneralsX iOS", font_size=18, color=(8, 10, 14, 0)),
            progress_bar("ShellGameLoadScreen.wnd:ProgressLoad", 210, 690, 814, 714),
        ]
    )
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = [None];
  LAYOUTUPDATE = [None];
  LAYOUTSHUTDOWN = [None];
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 0 0, BOTTOMRIGHT: 1024 768, CREATIONRESOLUTION: 1024 768;
  NAME = "ShellGameLoadScreen.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;{children}
END
"""


def main_menu_wnd() -> str:
    buttons = [
        "ButtonSinglePlayer", "ButtonMultiplayer", "ButtonSkirmish", "ButtonOnline",
        "ButtonNetwork", "ButtonOptions", "ButtonExit", "ButtonMOTD",
        "ButtonWorldBuilder", "ButtonGetUpdate", "ButtonChallenge", "ButtonUSA",
        "ButtonGLA", "ButtonChina", "ButtonUSARecentSave", "ButtonUSALoadGame",
        "ButtonGLARecentSave", "ButtonGLALoadGame", "ButtonChinaRecentSave",
        "ButtonChinaLoadGame", "ButtonMultiBack", "ButtonSingleBack",
        "ButtonLoadReplayBack", "ButtonReplay", "ButtonLoadReplay", "ButtonLoadGame",
        "ButtonCredits", "ButtonEasy", "ButtonMedium", "ButtonHard", "ButtonDiffBack",
        "ButtonTRAINING",
    ]
    children: list[str] = [
        child_wnd_block("MainMenu.wnd:MainMenuParent", 0, 0, 1024, 768, system_callback="MainMenuSystem", input_callback="MainMenuInput", color=(8, 10, 14, 232)),
        child_wnd_block("MainMenu.wnd:MainMenuRuler", 0, 0, 1024, 768, color=(8, 10, 14, 0)),
        child_wnd_block("MainMenu.wnd:LabelVersion", 16, 724, 620, 752, window_type="STATICTEXT", style="STATICTEXT+USER", text="GeneralsX iOS", font_size=12, color=(8, 10, 14, 0)),
        child_wnd_block("MainMenu.wnd:StaticTextRandom1", 620, 96, 960, 122, window_type="STATICTEXT", style="STATICTEXT+USER", text="", color=(8, 10, 14, 0)),
        child_wnd_block("MainMenu.wnd:StaticTextRandom2", 620, 126, 960, 152, window_type="STATICTEXT", style="STATICTEXT+USER", text="", color=(8, 10, 14, 0)),
    ]
    for index in range(5):
        suffix = "" if index == 0 else str(index)
        children.append(child_wnd_block(f"MainMenu.wnd:MapBorder{suffix}", 604, 176 + index * 82, 964, 238 + index * 82, color=(22, 26, 32, 210)))
    faction_names = [
        "WinFactionGLA", "WinFactionChina", "WinFactionUS", "WinGrowMarker",
        "WinFactionTraining", "WinFactionTrainingSmall", "WinFactionTrainingMedium",
        "WinFactionSkirmish", "WinFactionSkirmishSmall", "WinFactionSkirmishMedium",
        "WinFactionUSSmall", "WinFactionUSMedium", "WinFactionGLASmall",
        "WinFactionGLAMedium", "WinFactionChinaSmall", "WinFactionChinaMedium",
    ]
    for index, name in enumerate(faction_names):
        children.append(child_wnd_block(f"MainMenu.wnd:{name}", 608 + (index % 4) * 86, 184 + (index // 4) * 42, 684 + (index % 4) * 86, 216 + (index // 4) * 42, color=(36, 42, 50, 160)))
    for index, name in enumerate(buttons):
        x1 = 72 + (index % 2) * 214
        y1 = 126 + (index // 2) * 34
        children.append(push_button(f"MainMenu.wnd:{name}", x1, y1, x1 + 190, y1 + 28, name.replace("Button", "")))
    return f"""FILE_VERSION = 2;
STARTLAYOUTBLOCK
  LAYOUTINIT = MainMenuInit;
  LAYOUTUPDATE = MainMenuUpdate;
  LAYOUTSHUTDOWN = MainMenuShutdown;
ENDLAYOUTBLOCK
WINDOW
  WINDOWTYPE = USER;
  SCREENRECT = UPPERLEFT: 0 0, BOTTOMRIGHT: 1024 768, CREATIONRESOLUTION: 1024 768;
  NAME = "MainMenu.wnd";
  STATUS = ENABLED+IMAGE;
  STYLE = USER;
  SYSTEMCALLBACK = "[None]";
  INPUTCALLBACK = "[None]";
  TOOLTIPCALLBACK = "[None]";
  DRAWCALLBACK = "[None]";
  FONT = NAME: "Arial", SIZE: 10, BOLD: 0;
  HEADERTEMPLATE = "[NONE]";
  TOOLTIPDELAY = -1;
  TEXTCOLOR = ENABLED: 255 255 255 255, ENABLEDBORDER: 0 0 0 255,
              DISABLED: 180 180 180 255, DISABLEDBORDER: 0 0 0 255,
              HILITE: 255 235 170 255, HILITEBORDER: 0 0 0 255;
  ENABLEDDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;
  DISABLEDDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;
  HILITEDRAWDATA = IMAGE: NoImage, COLOR: 8 10 14 245, BORDERCOLOR: 0 0 0 0;{''.join(children)}
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


def build_csf(labels: dict[str, str]) -> bytes:
    payload = bytearray()
    sorted_items = sorted(labels.items())
    payload.extend(struct.pack("<iiiiii", CSF_ID, CSF_VERSION, len(sorted_items), len(sorted_items), 0, LANGUAGE_ID_US))
    for label, text in sorted_items:
        label_bytes = label.encode("ascii")
        text_units = text.encode("utf-16le")
        obfuscated = bytearray()
        for index in range(0, len(text_units), 2):
            unit = text_units[index] | (text_units[index + 1] << 8)
            unit = (~unit) & 0xFFFF
            obfuscated.extend(struct.pack("<H", unit))
        payload.extend(struct.pack("<iii", CSF_LABEL, 1, len(label_bytes)))
        payload.extend(label_bytes)
        payload.extend(struct.pack("<ii", CSF_STRING, len(obfuscated) // 2))
        payload.extend(obfuscated)
    return bytes(payload)


def chunky_toc(symbols: dict[str, int]) -> bytes:
    payload = bytearray()
    payload.extend(b"CkMp")
    payload.extend(struct.pack("<i", len(symbols)))
    for name, symbol_id in symbols.items():
        name_bytes = name.encode("ascii")
        if len(name_bytes) > 255:
            raise ValueError(f"chunk symbol too long: {name}")
        payload.extend(struct.pack("<B", len(name_bytes)))
        payload.extend(name_bytes)
        payload.extend(struct.pack("<I", symbol_id))
    return bytes(payload)


def chunky_chunk(symbol_id: int, version: int, data: bytes) -> bytes:
    return struct.pack("<IHi", symbol_id, version, len(data)) + data


def chunky_ascii(text: str) -> bytes:
    encoded = text.encode("ascii")
    return struct.pack("<H", len(encoded)) + encoded


def chunky_dict(
    pairs: list[tuple[str, int, object]],
    symbol_ids: dict[str, int],
) -> bytes:
    payload = bytearray()
    payload.extend(struct.pack("<H", len(pairs)))
    for key, dtype, value in pairs:
        payload.extend(struct.pack("<i", (symbol_ids[key] << 8) | dtype))
        if dtype == 1:
            payload.extend(struct.pack("<i", int(value)))
        elif dtype == 3:
            payload.extend(chunky_ascii(str(value)))
        else:
            raise ValueError(f"unsupported generated dict type: {dtype}")
    return bytes(payload)


def build_ios_slice_map() -> bytes:
    symbol_ids = {
        "HeightMapData": 1,
        "WorldInfo": 2,
        "ObjectsList": 3,
        "Object": 4,
        "mapName": 5,
        "waypointID": 6,
        "waypointName": 7,
    }
    toc_symbols = {
        "waypointName": 7,
        "waypointID": 6,
        "mapName": 5,
        "Object": 4,
        "ObjectsList": 3,
        "WorldInfo": 2,
        "HeightMapData": 1,
    }

    width = 66
    height = 66
    border = 1
    active_width = width - (2 * border)
    active_height = height - (2 * border)
    flat_height = 24
    height_data = bytes([flat_height]) * (width * height)
    height_payload = bytearray()
    height_payload.extend(struct.pack("<iii", width, height, border))
    height_payload.extend(struct.pack("<i", 1))
    height_payload.extend(struct.pack("<ii", active_width, active_height))
    height_payload.extend(struct.pack("<i", len(height_data)))
    height_payload.extend(height_data)

    world_dict = chunky_dict(
        [("mapName", 3, "MAP:IOSPlayableSlice")],
        symbol_ids,
    )

    def waypoint_chunk(waypoint_id: int, name: str, x: float, y: float) -> bytes:
        payload = bytearray()
        payload.extend(struct.pack("<fff", x, y, 0.0))
        payload.extend(struct.pack("<f", 0.0))
        payload.extend(struct.pack("<i", 0))
        payload.extend(chunky_ascii(""))
        payload.extend(
            chunky_dict(
                [
                    ("waypointID", 1, waypoint_id),
                    ("waypointName", 3, name),
                ],
                symbol_ids,
            )
        )
        return chunky_chunk(symbol_ids["Object"], 3, bytes(payload))

    objects_payload = bytearray()
    objects_payload.extend(waypoint_chunk(1, "InitialCameraPosition", 320.0, 320.0))
    objects_payload.extend(waypoint_chunk(2, "Player_1_Start", 180.0, 320.0))
    objects_payload.extend(waypoint_chunk(3, "Player_1_Rally", 240.0, 320.0))
    objects_payload.extend(waypoint_chunk(4, "Player_2_Start", 460.0, 320.0))
    objects_payload.extend(waypoint_chunk(5, "Player_2_Rally", 400.0, 320.0))

    payload = bytearray()
    payload.extend(chunky_toc(toc_symbols))
    payload.extend(chunky_chunk(symbol_ids["HeightMapData"], 4, bytes(height_payload)))
    payload.extend(chunky_chunk(symbol_ids["WorldInfo"], 1, world_dict))
    payload.extend(chunky_chunk(symbol_ids["ObjectsList"], 1, bytes(objects_payload)))
    return bytes(payload)


def build_ios_map_cache(map_bytes: bytes) -> str:
    crc = 0
    for byte in map_bytes:
        crc = ((crc >> 8) | (crc << 24)) & 0xFFFFFFFF
        crc = (crc + byte) & 0xFFFFFFFF
    return f"""MapCache {IOS_SLICE_MAP_PATH}
  isOfficial = Yes
  isMultiplayer = Yes
  extentMin = X:0.0 Y:0.0 Z:0.0
  extentMax = X:640.0 Y:640.0 Z:0.0
  numPlayers = 2
  fileSize = {len(map_bytes)}
  fileCRC = {crc}
  timestampLo = 0
  timestampHi = 0
  displayName = "iOS Playable Slice"
  nameLookupTag = MAP:IOSPlayableSlice
  Player_1_Start = X:180.0 Y:320.0 Z:0.0
  Player_2_Start = X:460.0 Y:320.0 Z:0.0
  InitialCameraPosition = X:320.0 Y:320.0 Z:0.0
End
"""


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
        ("IOSDozerIcon.tga", (190, 170, 90, 255)),
        ("IOSRangerIcon.tga", (210, 230, 245, 255)),
        ("IOSScoutVehicleIcon.tga", (120, 150, 165, 255)),
        ("IOSStopIcon.tga", (220, 62, 54, 255)),
        ("IOSSelectAllIcon.tga", (150, 96, 210, 255)),
        ("IOSCancelIcon.tga", (220, 54, 48, 255)),
        ("IOSSellIcon.tga", (220, 164, 42, 255)),
        ("IOSRallyPointIcon.tga", (76, 198, 126, 255)),
        ("IOSExitIcon.tga", (96, 188, 232, 255)),
        ("IOSCommunicatorIcon.tga", (64, 180, 220, 255)),
        ("IOSOptionsIcon.tga", (178, 188, 198, 255)),
        ("IOSIdleWorkerIcon.tga", (214, 174, 82, 255)),
        ("IOSBeaconIcon.tga", (236, 84, 76, 255)),
        ("IOSGeneralPowersIcon.tga", (110, 104, 224, 255)),
        ("IOSToggleControlBarIcon.tga", (82, 210, 164, 255)),
        ("IOSVeterancy1Icon.tga", (104, 208, 132, 255)),
        ("IOSVeterancy2Icon.tga", (84, 178, 232, 255)),
        ("IOSVeterancy3Icon.tga", (236, 202, 78, 255)),
        ("IOSAmmoFullIcon.tga", (232, 118, 68, 255)),
        ("IOSAmmoEmptyIcon.tga", (92, 102, 112, 255)),
        ("IOSContainerFullIcon.tga", (126, 216, 184, 255)),
        ("IOSContainerEmptyIcon.tga", (76, 88, 96, 255)),
        ("IOSObserverSideIcon.tga", (126, 138, 150, 255)),
        ("IOSCivilianSideIcon.tga", (184, 184, 168, 255)),
        ("IOSFactionSideIcon.tga", (38, 156, 238, 255)),
        ("IOSFactionGeneral.tga", (62, 132, 216, 255)),
        ("IOSFactionEnabled.tga", (48, 170, 238, 255)),
        ("IOSHeadWaterMark.tga", (38, 104, 176, 180)),
        ("IOSFlagWaterMark.tga", (42, 190, 224, 210)),
        ("IOSLoadScreen.tga", (34, 98, 154, 255)),
        ("IOSScoreScreen.tga", (40, 126, 98, 255)),
        ("IOSMapPreview.tga", (58, 150, 118, 255)),
        ("IOSStarBronze.tga", (188, 116, 58, 255)),
        ("IOSStarSilver.tga", (178, 190, 198, 255)),
        ("IOSStarGold.tga", (238, 202, 78, 255)),
        ("IOSStarRedYellow.tga", (238, 72, 62, 255)),
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

    mapped_images = []
    for filename, _color in icon_colors:
        name = filename.removesuffix(".tga")
        mapped_images.append((name, filename, 64, 64))
    mapped_images.extend((name, texture, 64, 64) for name, texture in STOCK_MAPPED_IMAGE_ALIASES)
    mapped_images.extend(
        (
            ("BarButtonGenStarON", "IOSGeneralPowersIcon.tga", 64, 64),
            ("BarButtonGenStarOFF", "IOSGeneralPowersIcon.tga", 64, 64),
            ("SSChevron1L", "IOSRangerIcon.tga", 64, 64),
            ("SSChevron2L", "IOSScoutVehicleIcon.tga", 64, 64),
            ("SSChevron3L", "IOSCommandCenterIcon.tga", 64, 64),
            ("SCVeter1", "IOSVeterancy1Icon.tga", 64, 64),
            ("SCVeter2", "IOSVeterancy2Icon.tga", 64, 64),
            ("SCVeter3", "IOSVeterancy3Icon.tga", 64, 64),
            ("SCPAmmoFull", "IOSAmmoFullIcon.tga", 64, 64),
            ("SCPAmmoEmpty", "IOSAmmoEmptyIcon.tga", 64, 64),
            ("SCPPipFull", "IOSContainerFullIcon.tga", 64, 64),
            ("SCPPipEmpty", "IOSContainerEmptyIcon.tga", 64, 64),
            ("Star-Bronze", "IOSStarBronze.tga", 64, 64),
            ("Star-Silver", "IOSStarSilver.tga", 64, 64),
            ("Star-Gold", "IOSStarGold.tga", 64, 64),
            ("RedYell_Star", "IOSStarRedYellow.tga", 64, 64),
            ("MapPreview", "IOSMapPreview.tga", 64, 64),
            ("Maps_IOSPlayableSlice_IOSPlayableSlice", "IOSMapPreview.tga", 64, 64),
            ("maps_iosplayableslice_iosplayableslice", "IOSMapPreview.tga", 64, 64),
            ("MissionLoad_USA", "IOSLoadScreen.tga", 64, 64),
            ("MissionLoad_GLA", "IOSLoadScreen.tga", 64, 64),
            ("MissionLoad_China", "IOSLoadScreen.tga", 64, 64),
            ("TitleScreen", "IOSLoadScreen.tga", 64, 64),
            ("SAFactionLogoLg_US", "IOSFactionGeneral.tga", 64, 64),
            ("SUFactionLogoLg_GLA", "IOSFactionGeneral.tga", 64, 64),
            ("SNFactionLogoLg_China", "IOSFactionGeneral.tga", 64, 64),
            ("SAFactionLogo144_US", "IOSFactionSideIcon.tga", 64, 64),
            ("SUFactionLogo144_GLA", "IOSFactionSideIcon.tga", 64, 64),
            ("SNFactionLogo144_China", "IOSFactionSideIcon.tga", 64, 64),
            ("LoadingBar_Progress", "IOSFactionEnabled.tga", 64, 64),
            ("LoadingBar_ProgressCenter1", "IOSFactionEnabled.tga", 64, 64),
            ("LoadingBar_ProgressCenter2", "IOSFactionEnabled.tga", 64, 64),
            ("LoadingBar_ProgressCenter3", "IOSFactionEnabled.tga", 64, 64),
            ("GeneralsChallengeWinLoss", "IOSScoreScreen.tga", 64, 64),
            ("MutiPlayer_ScoreScreen", "IOSScoreScreen.tga", 64, 64),
            ("TecBuilding", "IOSPowerPlantIcon.tga", 64, 64),
            ("Cash", "IOSSellIcon.tga", 64, 64),
            ("UnknownMap", "IOSMapPreview.tga", 64, 64),
            ("Gradient", "IOSLoadScreen.tga", 64, 64),
            ("GameinfoRANDOM", "IOSFactionSideIcon.tga", 64, 64),
            ("GameinfoOBSRVR", "IOSObserverSideIcon.tga", 64, 64),
            ("Observer", "IOSObserverSideIcon.tga", 64, 64),
            ("Ping01", "IOSStarGold.tga", 64, 64),
            ("Ping02", "IOSStarSilver.tga", 64, 64),
            ("Ping03", "IOSStarBronze.tga", 64, 64),
            ("Password", "IOSOptionsIcon.tga", 64, 64),
            ("GoodStatsIcon", "IOSGeneralPowersIcon.tga", 64, 64),
            ("NewPlayer", "IOSFactionSideIcon.tga", 64, 64),
            ("OfficersClubsmall", "IOSGeneralPowersIcon.tga", 64, 64),
            ("OfficersClub", "IOSGeneralPowersIcon.tga", 64, 64),
        )
    )
    mapped_image_text = "".join(
        f"""MappedImage {name}
  Texture = {texture}
  TextureWidth = {width}
  TextureHeight = {height}
  Coords = Left:0 Top:0 Right:{width} Bottom:{height}
  Status = NONE
End

"""
        for name, texture, width, height in mapped_images
    )
    write_text(
        out_dir / "Data" / "INI" / "MappedImages" / "TextureSize_512" / "ios_playable_slice.ini",
        mapped_image_text,
        records,
        "ios_playable_slice_mapped_images",
        project_root,
    )

    map_bytes = build_ios_slice_map()
    write_binary(
        out_dir / IOS_SLICE_MAP_PATH,
        map_bytes,
        records,
        "ios_playable_slice_map",
        project_root,
    )
    write_text(
        out_dir / "Maps" / IOS_SLICE_MAP_NAME / "map.ini",
        "; Generated iOS playable slice map overrides.\n",
        records,
        "ios_playable_slice_map_ini",
        project_root,
    )
    write_text(
        out_dir / "Maps" / IOS_SLICE_MAP_NAME / "map.str",
        "MAP:IOSPlayableSlice\n\"iOS Playable Slice\"\nEND\n",
        records,
        "ios_playable_slice_map_strings",
        project_root,
    )
    write_text(
        out_dir / "Maps" / "MapCache.ini",
        build_ios_map_cache(map_bytes),
        records,
        "ios_playable_slice_map_cache",
        project_root,
    )
    write_radial_tga(
        out_dir / "Maps" / IOS_SLICE_MAP_NAME / f"{IOS_SLICE_MAP_NAME}.tga",
        (58, 150, 118, 255),
        records,
        "ios_playable_slice_map_preview",
        project_root,
        size=128,
    )


def build_pack(project_root: Path, out_dir: Path, clean: bool) -> dict[str, object]:
    out_dir = out_dir.resolve()
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []

    for dest_name, source_name in IOS_AUDIO_ASSETS:
        copy_file(
            project_root / "ios-original-assets" / "source" / "audio" / source_name,
            out_dir / "Data" / "Audio" / "Sounds" / dest_name,
            records,
            "ios_octave_audio_sound",
            project_root,
        )

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

    base_model = project_root / RUNTIME_ASSET_DIR / "ShatterPlanes0.w3d"
    for model_name in IOS_MODEL_ASSETS:
        filename = f"{model_name}.w3d"
        copy_file(
            base_model,
            out_dir / "Data" / "Runtime" / "RequiredAssets" / filename,
            records,
            "ios_generated_model_asset",
            project_root,
        )
        copy_file(
            base_model,
            out_dir / filename,
            records,
            "ios_generated_model_root_lookup",
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

    for filename, color, role in IOS_RUNTIME_TEXTURES:
        write_radial_tga(
            out_dir / "Data" / "Art" / "Textures" / filename,
            color,
            records,
            f"ios_runtime_{role}",
            project_root,
            size=64,
        )
        write_radial_tga(
            out_dir / filename,
            color,
            records,
            f"ios_runtime_root_{role}",
            project_root,
            size=64,
        )

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
        main_menu_wnd(),
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
    for layout_path, title in sorted(IOS_GAMEPLAY_WND_LAYOUTS.items()):
        layout_name = Path(layout_path).name
        if layout_name == "ControlBar.wnd":
            layout_text = control_bar_wnd()
        elif layout_name == "ControlBarPopupDescription.wnd":
            layout_text = control_bar_popup_description_wnd()
        elif layout_name == "GeneralsExpPoints.wnd":
            layout_text = generals_exp_points_wnd()
        elif layout_name == "InGameChat.wnd":
            layout_text = ingame_chat_wnd()
        elif layout_name == "InGamePopupMessage.wnd":
            layout_text = ingame_popup_message_wnd()
        elif layout_name == "MOTD.wnd":
            layout_text = motd_wnd()
        elif layout_name == "ReplayControl.wnd":
            layout_text = replay_control_wnd()
        elif layout_name == "SinglePlayerLoadScreen.wnd":
            layout_text = single_player_load_screen_wnd()
        elif layout_name == "ShellGameLoadScreen.wnd":
            layout_text = shell_game_load_screen_wnd()
        else:
            layout_text = minimal_wnd(layout_name, title)
        write_text(
            out_dir / "Data" / "Window" / layout_path,
            layout_text,
            records,
            "ios_gameplay_window_layout",
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
        IOS_BOOT_NOOP_INI,
        records,
        "localization_header_template_noop_ini",
        project_root,
    )
    write_binary(
        out_dir / "Data" / "English" / "generals.csf",
        build_csf(IOS_CSF_LABELS),
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
            boot_ini_for(dirname),
            records,
            "ios_boot_default_ini",
            project_root,
        )
    for dirname in MANDATORY_BOOT_INI_DIRS:
        write_text(
            out_dir / "Data" / "INI" / dirname / "ios_boot.ini",
            boot_ini_for(dirname),
            records,
            "ios_boot_ini",
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
