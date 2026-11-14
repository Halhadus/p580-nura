#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
TOP=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export TOP
case ${1:-help} in
 build) shift; exec sh "$TOP/scripts/build.sh" "$@" ;;
 backup|install) command=$1; shift; exec python3 "$TOP/scripts/device.py" "$command" "$@" ;;
 help|-h|--help) printf '%s\n' './port.sh build [--lax] [--force]' './port.sh backup [--skip-userdata]' './port.sh install --erase-android-data [--skip-userdata]' ;;
 *) printf 'Unknown command: %s\n' "$1" >&2; exit 2 ;;
esac
