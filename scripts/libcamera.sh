#!/bin/bash
# SPDX-License-Identifier: MIT
source "$(dirname "$0")/common.sh"
source "$TOP/config/libcamera.env"
ACTION=${1:-build}
K=$TOP/work/libcamera
check_target() {
 [ "$(dpkg --print-architecture)" = arm64 ] || die 'Build the camera packages on the arm64 tablet or an arm64 trixie build environment.'
 source /etc/os-release
 [[ "${ID:-}" = debian || "${ID:-}" = mobian ]] && [ "${VERSION_CODENAME:-}" = trixie ] || die 'Build these Debian 0.4.0 packages in trixie; do not build them against the sid host libraries.'
}
fetch() {
 local file=$1 hash=$2
 if [ ! -f "$TOP/cache/libcamera/$file" ]; then
  curl -fL --retry 3 "$LIBCAMERA_BASE_URL/$file" -o "$TOP/cache/libcamera/$file.part"
  mv "$TOP/cache/libcamera/$file.part" "$TOP/cache/libcamera/$file"
 fi
 printf '%s  %s\n' "$hash" "$TOP/cache/libcamera/$file" | sha256sum -c -
}
prepare() {
 mkdir -p "$TOP/cache/libcamera"
 fetch libcamera_0.4.0-7.dsc "$LIBCAMERA_DSC_SHA256"
 fetch libcamera_0.4.0.orig.tar.bz2 "$LIBCAMERA_ORIG_SHA256"
 fetch libcamera_0.4.0-7.debian.tar.xz "$LIBCAMERA_DEBIAN_SHA256"
 if [ ! -d "$K" ]; then
  dpkg-source -x "$TOP/cache/libcamera/libcamera_0.4.0-7.dsc" "$K"
  python3 "$TOP/scripts/patch_work.py" libcamera --fresh
 else
  python3 "$TOP/scripts/patch_work.py" libcamera
 fi
}
case "$ACTION" in
 deps)
  check_target
  sudo apt-get update
  sudo apt-get install --no-install-recommends build-essential dpkg-dev debhelper dh-sequence-python3 curl ca-certificates bzip2 xz-utils git pkgconf meson ninja-build openssl libdrm-dev libdw-dev libevent-dev libgnutls28-dev libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev libgtest-dev libjpeg-dev liblttng-ust-dev libpython3-dev libsdl2-dev libtiff-dev libudev-dev libyaml-dev libyuv-dev python3-jinja2 python3-ply python3-pybind11 python3-yaml qt6-base-dev
  ;;
 source) prepare ;;
 build)
  check_target
  prepare
  python3 - "$K" "$LIBCAMERA_VERSION" <<'PY'
import re, sys
from pathlib import Path
path = Path(sys.argv[1])/'debian/changelog'; version = sys.argv[2]; text = path.read_text()
if not text.startswith('libcamera ('+version+')'):
    if not re.match(r'libcamera \(0\.4\.0-7(?:\+p580[0-9]*)?\)', text): sys.exit('Unexpected libcamera source version; changelog preserved.')
    entry = 'libcamera ('+version+') trixie; urgency=medium\n\n  * Match P580 cameras, map analogue gain and fix the thread-affinity race.\n\n -- Halhadus <eneshakan45@proton.me>  Fri, 13 Nov 2026 12:00:00 +0300\n\n'
    path.write_text(entry+text)
PY
  (cd "$K" && rm -f debian/debhelper-build-stamp && dpkg-buildpackage -nc -B -uc -us -Pnodoc -j"$JOBS")
  mkdir -p "$TOP/out/libcamera"
  for package in libcamera0.4 libcamera-ipa libcamera-tools libcamera-v4l2; do
   file="$TOP/work/${package}_${LIBCAMERA_VERSION}_arm64.deb"
   [ -f "$file" ] || die "Missing camera package: $file"
   cp "$file" "$TOP/out/libcamera/"
  done
  (cd "$TOP/out/libcamera" && sha256sum *"_${LIBCAMERA_VERSION}_arm64.deb" > SHA256SUMS)
  echo 'Matched core/IPA/tools/V4L2 packages ready in out/libcamera; install them together.'
  ;;
 *) die 'Usage: libcamera.sh deps | source | build' ;;
esac
