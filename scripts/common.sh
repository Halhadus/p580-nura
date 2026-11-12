#!/bin/bash
# SPDX-License-Identifier: MIT
set -euo pipefail
export PATH="/usr/sbin:/sbin:$PATH"
TOP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export ARCH=arm64
if [ "$(uname -m)" = aarch64 ]; then export CROSS_COMPILE=; else export CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}; fi
JOBS=${JOBS:-4}
mkdir -p "$TOP/out" "$TOP/cache" "$TOP/work"
die() { echo "$*" >&2; exit 1; }
