#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
: "${TOP:?Run ./port.sh build}"
lax=false
for option; do
	case $option in
	 --lax) lax=true ;;
	 --force) ;;
	 *) echo 'Usage: ./port.sh build [--lax] [--force]' >&2; exit 2 ;;
	esac
done
PMB=${PMBOOTSTRAP:-pmbootstrap}
command -v "$PMB" >/dev/null || { echo 'Install pmbootstrap >= 3.11.0 first.' >&2; exit 1; }
[ -f "$TOP/pmaports/pmaports.cfg" ] || { echo 'Initialize the pmaports submodule first.' >&2; exit 1; }
git -C "$TOP/pmaports" config --local remote.pmos.url https://gitlab.postmarketos.org/postmarketOS/pmaports.git
git -C "$TOP/pmaports" config --local remote.pmos.fetch '+refs/heads/*:refs/remotes/pmos/*'
if ! git -C "$TOP/pmaports" show-ref --verify --quiet refs/remotes/pmos/main; then
	git -C "$TOP/pmaports" fetch --no-tags pmos refs/heads/main:refs/remotes/pmos/main
fi
mkdir -p "$TOP/work" "$TOP/out/export"
PMB_CONFIG="$TOP/pmbootstrap.cfg"
pmb() { "$PMB" -c "$PMB_CONFIG" -p "$TOP/pmaports" -w "$TOP/work/pmbootstrap" "$@"; }
if [ ! -f "$TOP/pmbootstrap.cfg" ]; then pmb init; fi
python3 - "$TOP/pmbootstrap.cfg" <<'CONFIG'
import configparser, sys
config = configparser.ConfigParser(); config.read(sys.argv[1])
values = [config.get(section, 'device') for section in config.sections() if config.has_option(section, 'device')]
if values != ['samsung-gtanotexlwifi']: sys.exit('Select samsung-gtanotexlwifi with pmbootstrap init using this project config.')
CONFIG
if "$lax"; then
	PMB_CONFIG="$TOP/work/pmbootstrap-lax.cfg"
	python3 - "$TOP/pmbootstrap.cfg" "$PMB_CONFIG" <<'CONFIG'
import configparser, sys
config = configparser.ConfigParser(); config.read(sys.argv[1])
config.set('pmbootstrap', 'build_pkgs_on_install', 'False')
with open(sys.argv[2], 'w') as stream: config.write(stream)
CONFIG
fi
pmb build "$@" mesa libcamera linux-samsung-gtanotexlwifi u-boot-samsung-gtanotexlwifi firmware-samsung-gtanotexlwifi device-samsung-gtanotexlwifi
pmb install --no-sparse
pmb export --no-install "$TOP/out/export"
cp -L "$TOP/out/export/samsung-gtanotexlwifi.img" "$TOP/out/rootfs-p580.img.part"
cp -L "$TOP/out/export/boot.img" "$TOP/out/boot-p580.img.part"
mv "$TOP/out/rootfs-p580.img.part" "$TOP/out/rootfs-p580.img"
mv "$TOP/out/boot-p580.img.part" "$TOP/out/boot-p580.img"
python3 "$TOP/scripts/images.py" --record
printf '%s\n' 'Ready: out/rootfs-p580.img and out/boot-p580.img'
