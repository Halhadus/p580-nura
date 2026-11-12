#!/bin/bash
# SPDX-License-Identifier: MIT
source "$(dirname "$0")/common.sh"
fetch() {
 local url=$1 file=$2 hash=$3
 if [ ! -f "$file" ]; then curl -fL --retry 3 "$url" -o "$file.part"; mv "$file.part" "$file"; fi
 printf '%s  %s\n' "$hash" "$file" | sha256sum -c -
}
source "$TOP/config/sources.env"
fetch "$LINUX_URL" "$TOP/cache/linux.tar.xz" "$LINUX_SHA256"
fetch "$UBOOT_URL" "$TOP/cache/u-boot.tar.gz" "$UBOOT_SHA256"
prepare() {
 local name=$1 archive=$2
 if [ -d "$TOP/work/$name" ]; then python3 "$TOP/scripts/patch_work.py" "$name"; return; fi
 mkdir "$TOP/work/$name"
 tar -xf "$archive" --strip-components=1 -C "$TOP/work/$name"
 python3 "$TOP/scripts/patch_work.py" "$name" --fresh
}
prepare linux "$TOP/cache/linux.tar.xz"
prepare u-boot "$TOP/cache/u-boot.tar.gz"
echo 'Sources ready.'
