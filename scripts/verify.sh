#!/bin/bash
# SPDX-License-Identifier: MIT
source "$(dirname "$0")/common.sh"
python3 "$TOP/scripts/check_bootimg.py" "$TOP/out/boot-p580.img"
e2fsck -f -n "$TOP/out/rootfs-p580.img"
sha256sum -c "$TOP/out/IMAGE-SHA256SUMS"
echo 'Images verified.'
