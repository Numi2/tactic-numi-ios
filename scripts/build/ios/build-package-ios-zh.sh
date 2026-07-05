#!/bin/bash
# Build, package, sign, and optionally install the iOS Zero Hour app.
#
# This is the repo-owned iPhone entrypoint. It keeps the existing lower-level
# package script focused on app assembly while making the end-to-end device flow
# reproducible from a clean checkout.
#
# Usage:
#   GX_TEAM_ID=<team> GX_BUNDLE_ID=com.you.generalszh \
#     ./scripts/build/ios/build-package-ios-zh.sh [--install] [--dev] [--clean-assets] [--sim]
set -euo pipefail

DO_INSTALL=0
DEV_MODE=0
CLEAN_ASSETS=0
SIMULATOR_MODE=0

for arg in "$@"; do
    case "$arg" in
        --install) DO_INSTALL=1 ;;
        --dev) DEV_MODE=1 ;;
        --clean-assets) CLEAN_ASSETS=1 ;;
        --sim|--simulator) SIMULATOR_MODE=1 ;;
        *) echo "ERROR: unknown argument '$arg' (usage: $0 [--install] [--dev] [--clean-assets] [--sim])"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
if [[ "${SIMULATOR_MODE}" == "1" ]]; then
    PRESET="${GX_IOS_PRESET:-ios-simulator-vulkan}"
    MOLTENVK_ARCH_DIR="ios-arm64_x86_64-simulator"
else
    PRESET="${GX_IOS_PRESET:-ios-vulkan}"
    MOLTENVK_ARCH_DIR="ios-arm64"
fi
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
if [[ -z "${VULKAN_SDK:-}" || ! -f "${VULKAN_SDK}/lib/MoltenVK.xcframework/${MOLTENVK_ARCH_DIR}/libMoltenVK.a" ]]; then
    echo "ERROR: VULKAN_SDK must point at a Vulkan SDK macOS root with iOS MoltenVK."
    echo "  Missing: \${VULKAN_SDK}/lib/MoltenVK.xcframework/${MOLTENVK_ARCH_DIR}/libMoltenVK.a"
    echo "  Example: export VULKAN_SDK=\$HOME/VulkanSDK/<version>/macOS"
    exit 1
fi
export PATH="${VULKAN_SDK}/bin:${PATH}"

echo "==> Preparing iOS DXVK source"
DXVK_REF_DIR="${PROJECT_ROOT}/references/fbraz3-dxvk"
if [[ -d "${DXVK_REF_DIR}/.git" ]]; then
    git -C "${DXVK_REF_DIR}" fetch --quiet origin generalsx-macos-v2.6
    git -C "${DXVK_REF_DIR}" checkout --quiet generalsx-macos-v2.6
else
    rm -rf "${DXVK_REF_DIR}"
    git clone --quiet --branch generalsx-macos-v2.6 \
        https://github.com/fbraz3/dxvk.git "${DXVK_REF_DIR}"
fi
git -C "${DXVK_REF_DIR}" submodule update --init --recursive --quiet

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
if [[ "${SIMULATOR_MODE}" == "1" ]]; then
    PACKAGE_ARGS+=(--sim)
fi

if [[ -f "${ORIGINAL_SLICE_WORKLIST}" ]]; then
    GX_IOS_PRESET="${PRESET}" \
    GX_ORIGINAL_ASSET_PACK="${ORIGINAL_ASSET_PACK}" \
    GX_ORIGINAL_SLICE_WORKLIST="${ORIGINAL_SLICE_WORKLIST}" \
        "${PROJECT_ROOT}/scripts/build/ios/package-ios-zh.sh" "${PACKAGE_ARGS[@]}"
else
    GX_IOS_PRESET="${PRESET}" \
    GX_ORIGINAL_ASSET_PACK="${ORIGINAL_ASSET_PACK}" \
        "${PROJECT_ROOT}/scripts/build/ios/package-ios-zh.sh" "${PACKAGE_ARGS[@]}"
fi
