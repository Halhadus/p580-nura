#!/bin/bash
# SPDX-License-Identifier: MIT
source "$(dirname "$0")/common.sh"
K=$TOP/work/linux
O=$TOP/out/linux
[ -f "$K/Makefile" ] || die 'Run ./port.sh sources first.'
if [ ! -f "$O/.config" ]; then
 mkdir -p "$O"
 cp "$TOP/config/p580_defconfig" "$O/.config"
fi
# Apply the integration fixes to existing incremental configs as well.
"$K/scripts/config" --file "$O/.config" --set-str LOCALVERSION -p580 --disable LOCALVERSION_AUTO --module BT_RFCOMM --enable BT_RFCOMM_TTY --module BT_BNEP --module AUTOFS_FS --enable SECURITY_LANDLOCK
LSM=$("$K/scripts/config" --file "$O/.config" --state LSM)
case ,$LSM, in
 *,landlock,*|,undef,) ;;
 *) "$K/scripts/config" --file "$O/.config" --set-str LSM "landlock${LSM:+,$LSM}" ;;
esac
make -C "$K" O="$O" olddefconfig
make -C "$K" O="$O" -j"$JOBS" Image vmlinuz.efi exynos/exynos7870-gtanotexlwifi.dtb modules
make -C "$K" O="$O" INSTALL_MOD_PATH="$TOP/out/modules" DEPMOD="${DEPMOD:-/usr/sbin/depmod}" modules_install
cp "$O/.config" "$TOP/out/kernel.config"
python3 "$TOP/scripts/prepare_dtb.py" "$TOP"
