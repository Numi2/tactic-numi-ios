#!/bin/bash
# Build, package, sign, and optionally install the iOS Zero Hour app.
#
# This is the repo-owned iPhone entrypoint. It keeps the existing lower-level
# package script focused on app assembly while making the end-to-end device flow
# reproducible from a clean checkout.
#
# Usage:
#   GX_TEAM_ID=<team> GX_BUNDLE_ID=com.you.generalszh \
#     ./scripts/build/ios/build-package-ios-zh.sh [--install] [--dev] [--clean-assets]
set -euo pipefail

DO_INSTALL=0
DEV_MODE=0
CLEAN_ASSETS=0

for arg in "$@"; do
    case "$arg" in
        --install) DO_INSTALL=1 ;;
        --dev) DEV_MODE=1 ;;
        --clean-assets) CLEAN_ASSETS=1 ;;
        *) echo "ERROR: unknown argument '$arg' (usage: $0 [--install] [--dev] [--clean-assets])"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
PRESET="${GX_IOS_PRESET:-ios-vulkan}"
TARGET="${GX_IOS_TARGET:-z_generals}"
ORIGINAL_ASSET_PACK="${GX_ORIGINAL_ASSET_PACK:-${PROJECT_ROOT}/ios-original-assets/generated/GameData}"
ORIGINAL_SLICE_WORKLIST="${GX_ORIGINAL_SLICE_WORKLIST:-${PROJECT_ROOT}/ios-original-assets/manifest/playable_slice_worklist.json}"

if ! command -v cmake >/dev/null 2>&1; then
    echo "ERROR: cmake is required for the iOS build."
    exit 1
fi
if ! command -v xcodegen >/dev/null 2>&1; then
    echo "ERROR: xcodegen is required. Install with: brew install xcodegen"
    exit 1
fi
if ! command -v xcodebuild >/dev/null 2>&1; then
    echo "ERROR: full Xcode is required; xcodebuild was not found."
    exit 1
fi
if [[ -z "${VULKAN_SDK:-}" || ! -f "${VULKAN_SDK}/lib/MoltenVK.xcframework/ios-arm64/libMoltenVK.a" ]]; then
    echo "ERROR: VULKAN_SDK must point at a Vulkan SDK macOS root with iOS MoltenVK."
    echo "  Example: export VULKAN_SDK=\$HOME/VulkanSDK/<version>/macOS"
    exit 1
fi

echo "==> Preparing iOS DXVK source"
git -C "${PROJECT_ROOT}" submodule update --init references/fbraz3-dxvk

echo "==> Preparing MoltenVK"
"${PROJECT_ROOT}/scripts/build/ios/fetch-moltenvk.sh"

if [[ "${DEV_MODE}" != "1" ]]; then
    echo "==> Building repo-owned original iOS asset pack"
    ASSET_ARGS=(--out-dir "${ORIGINAL_ASSET_PACK}")
    if [[ "${CLEAN_ASSETS}" == "1" || ! -d "${ORIGINAL_ASSET_PACK}" ]]; then
        ASSET_ARGS=(--clean "${ASSET_ARGS[@]}")
    fi
    "${PROJECT_ROOT}/scripts/tooling/assets/build_ios_original_asset_pack.py" "${ASSET_ARGS[@]}"
fi

echo "==> Configuring ${PRESET}"
cmake --preset "${PRESET}"

echo "==> Building ${TARGET}"
cmake --build "${PROJECT_ROOT}/build/${PRESET}" --target "${TARGET}"

echo "==> Packaging iOS app"
PACKAGE_ARGS=()
if [[ "${DEV_MODE}" == "1" ]]; then
    PACKAGE_ARGS+=(--dev)
fi
if [[ "${DO_INSTALL}" == "1" ]]; then
    PACKAGE_ARGS+=(--install)
fi

if [[ -f "${ORIGINAL_SLICE_WORKLIST}" ]]; then
    GX_ORIGINAL_ASSET_PACK="${ORIGINAL_ASSET_PACK}" \
    GX_ORIGINAL_SLICE_WORKLIST="${ORIGINAL_SLICE_WORKLIST}" \
        "${PROJECT_ROOT}/scripts/build/ios/package-ios-zh.sh" "${PACKAGE_ARGS[@]}"
else
    GX_ORIGINAL_ASSET_PACK="${ORIGINAL_ASSET_PACK}" \
        "${PROJECT_ROOT}/scripts/build/ios/package-ios-zh.sh" "${PACKAGE_ARGS[@]}"
fi
