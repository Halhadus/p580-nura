#!/bin/bash
# SPDX-License-Identifier: MIT
set -euo pipefail
[ "$(dpkg --print-architecture)" = arm64 ] || { echo 'Dependencies require a Debian arm64 host.' >&2; exit 1; }
sudo apt-get update
sudo apt-get install --no-install-recommends build-essential bsdextrautils kmod git curl ca-certificates xz-utils zstd zip unzip bc bison flex libssl-dev libelf-dev libgnutls28-dev uuid-dev device-tree-compiler u-boot-tools python3 python3-dev python3-setuptools python3-pyelftools python3-packaging swig libpython3-dev mmdebstrap debian-archive-keyring e2fsprogs dosfstools fdisk adb rsync openssh-client
