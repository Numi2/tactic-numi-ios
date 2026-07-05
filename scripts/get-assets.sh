#!/bin/bash
# Download C&C Generals Zero Hour game files from your own Steam account.
# Usage: ./get-assets.sh <your_steam_username> [--no-manifest]
# Steam Guard: you'll be prompted for the code on first login.
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <steam_username> [--no-manifest]"
    exit 1
fi

STEAM_USER="$1"
BUILD_MANIFEST=1
shift
for arg in "$@"; do
    case "$arg" in
        --no-manifest) BUILD_MANIFEST=0 ;;
        *) echo "ERROR: unknown argument '$arg' (usage: $0 <steam_username> [--no-manifest])"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST="$HOME/GeneralsX/GeneralsZH"
TMP_DIR="$HOME/GeneralsX/.steamcmd_zh"
MANIFEST_DIR="${GX_ASSET_MANIFEST_DIR:-${PROJECT_ROOT}/build/asset-manifest}"
MANIFEST_JSON="${GX_ASSET_MANIFEST_JSON:-${MANIFEST_DIR}/ios_required_asset_manifest.json}"
MANIFEST_MD="${GX_ASSET_MANIFEST_MD:-${MANIFEST_DIR}/ios_required_asset_inventory.md}"

mkdir -p "$TMP_DIR" "$DEST"

# App 2732960 = C&C Generals Zero Hour (Windows depot; assets are platform-independent)
steamcmd \
    +@sSteamCmdForcePlatformType windows \
    +force_install_dir "$TMP_DIR" \
    +login "$STEAM_USER" \
    +app_update 2732960 validate \
    +quit

echo "Moving game files into $DEST ..."
# Copy data files only; keep the deployed GeneralsX runtime (run.sh, dylibs) intact.
rsync -a --exclude="*.exe" --exclude="*.dll" "$TMP_DIR/" "$DEST/"

echo "Done. Assets in place:"
ls "$DEST"/*.big 2>/dev/null | head
echo
if [[ "$BUILD_MANIFEST" == "1" ]]; then
    echo "Building required iOS asset manifest from $DEST ..."
    mkdir -p "$MANIFEST_DIR"
    if "$PROJECT_ROOT/scripts/tooling/assets/scan_ios_asset_manifest.py" \
        "$DEST" \
        --json-out "$MANIFEST_JSON" \
        --md-out "$MANIFEST_MD" \
        --fail-on-missing; then
        echo "Required asset manifest:"
        echo "  $MANIFEST_JSON"
        echo "  $MANIFEST_MD"
    else
        status=$?
        echo "Asset manifest completed with unresolved references; reports were still written:"
        echo "  $MANIFEST_JSON"
        echo "  $MANIFEST_MD"
        exit "$status"
    fi
    echo
fi
echo "Launch with: cd ~/GeneralsX/GeneralsZH && ./run.sh -win"
