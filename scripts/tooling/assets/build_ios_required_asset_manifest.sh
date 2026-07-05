#!/bin/bash
# Build the hard required-asset manifest for the iOS asset pipeline.
#
# This script intentionally rejects the small in-repository GeneralsZH fixture.
# The production manifest must be generated from a legally staged game data tree
# containing the real BIG archives.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

ASSET_ROOT="${1:-${GX_GAME_DATA:-${HOME}/GeneralsX/GeneralsZH}}"
OUT_DIR="${GX_ASSET_MANIFEST_DIR:-${PROJECT_ROOT}/build/asset-manifest}"
JSON_OUT="${GX_ASSET_MANIFEST_JSON:-${OUT_DIR}/ios_required_asset_manifest.json}"
MD_OUT="${GX_ASSET_MANIFEST_MD:-${OUT_DIR}/ios_required_asset_inventory.md}"

if [[ ! -d "${ASSET_ROOT}" ]]; then
    echo "ERROR: staged asset tree not found: ${ASSET_ROOT}" >&2
    echo "  Stage legal Zero Hour data first, for example:" >&2
    echo "    ./scripts/get-assets.sh <steam_username>" >&2
    echo "  or set GX_GAME_DATA=/path/to/GeneralsZH" >&2
    exit 1
fi

if ! compgen -G "${ASSET_ROOT}"'/*.big' >/dev/null; then
    echo "ERROR: ${ASSET_ROOT} does not contain root-level .big archives." >&2
    echo "  This looks like the repo fixture or an incomplete asset tree, not real staged game data." >&2
    echo "  Expected files include archives such as INI.big, Textures.big, W3D.big, Audio.big, or similar." >&2
    exit 1
fi

mkdir -p "${OUT_DIR}"

echo "==> Building iOS required asset manifest from ${ASSET_ROOT}"
"${PROJECT_ROOT}/scripts/tooling/assets/scan_ios_asset_manifest.py" \
    "${ASSET_ROOT}" \
    --json-out "${JSON_OUT}" \
    --md-out "${MD_OUT}" \
    --fail-on-missing

echo "==> Wrote ${JSON_OUT}"
echo "==> Wrote ${MD_OUT}"
