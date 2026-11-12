#!/bin/bash
# SPDX-License-Identifier: MIT
source "$(dirname "$0")/common.sh"
K=$TOP/work/linux
U=$TOP/work/u-boot
O=$TOP/out/u-boot
[ -f "$U/Makefile" ] || die 'Run ./port.sh sources first.'
make -C "$U" O="$O" p580_defconfig
make -C "$U" O="$O" DEVICE_TREE=exynos/exynos7870-gtanotexlwifi -j"$JOBS"
cc -O2 -I"$K/scripts/dtc/libfdt" "$TOP/vendor/dtbtool/dtbtool-exynos.c" "$K"/scripts/dtc/libfdt/fdt*.c -o "$TOP/out/dtbTool-exynos"
"$TOP/out/dtbTool-exynos" -o "$TOP/out/stub-dt.img" "$O/u-boot.dtb"
python3 "$TOP/scripts/pack_uboot.py" "$O/u-boot-nodtb.bin" "$TOP/out/stub-dt.img" "$TOP/out/boot-p580.img"
python3 "$TOP/scripts/check_bootimg.py" "$TOP/out/boot-p580.img"
