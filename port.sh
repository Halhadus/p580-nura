#!/bin/bash
# SPDX-License-Identifier: MIT
set -euo pipefail
export PATH="/usr/sbin:/sbin:$PATH"
cd "$(dirname "$0")"
case ${1:-help} in
 deps|sources|kernel|uboot) exec bash "scripts/$1.sh" ;;
 info|firmware|backup|install|restore|logs) cmd=$1; shift; exec python3 scripts/device.py "$cmd" "$@" ;;
 libcamera-deps|libcamera-source|libcamera-build) exec bash scripts/libcamera.sh "${1#libcamera-}" ;;
 rootfs) exec bash scripts/rootfs.sh ;;
 verify) exec bash scripts/verify.sh ;;
 update-build) bash scripts/sources.sh; bash scripts/kernel.sh; bash scripts/uboot.sh; exec python3 scripts/update.py package ;;
 update-install|update-rollback) exec python3 scripts/update.py "${1#update-}" ;;
 finish) shift; python3 scripts/device.py backup "$@"; bash scripts/rootfs.sh; bash scripts/verify.sh ;;
 prepare) python3 scripts/device.py info; python3 scripts/device.py firmware; bash scripts/sources.sh; bash scripts/kernel.sh; bash scripts/uboot.sh; python3 scripts/device.py backup; bash scripts/rootfs.sh; bash scripts/verify.sh ;;
 help|-h|--help) printf '%s\n' './port.sh deps | sources | kernel | uboot | rootfs | verify' './port.sh info | firmware | backup [--skip-userdata] | prepare | finish [--skip-userdata]' './port.sh install --erase-android-data [--skip-userdata] | restore --restore-android-data' './port.sh update-build | update-install | update-rollback | logs' './port.sh libcamera-deps | libcamera-source | libcamera-build' ;;
 *) echo "Unknown command: $1" >&2; exit 2 ;;
esac
