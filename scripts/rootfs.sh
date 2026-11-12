#!/bin/bash
# SPDX-License-Identifier: MIT
[ "$(id -u)" = 0 ] || exec sudo --preserve-env=MOBIAN_PASSWORD,IMAGE_SIZE_GIB bash "$0"
source "$(dirname "$0")/common.sh"
[ "$(dpkg --print-architecture)" = arm64 ] || die 'Rootfs creation requires a Debian arm64 host.'
[ -f "$TOP/out/p580.dtb" ] || die 'Build the kernel first: ./port.sh kernel'
[ -f "$TOP/cache/firmware/ath10k/QCA9377/hw1.0/board.bin" ] || die 'Run ./port.sh firmware while Android is running.'
[ ! -e "$TOP/out/rootfs" ] || die 'Rootfs destination already exists: out/rootfs.'
ROOT=$TOP/out/rootfs
SIZE=${IMAGE_SIZE_GIB:-6}
[[ "$SIZE" =~ ^[0-9]+$ ]] || die 'IMAGE_SIZE_GIB must be an integer from 4 to 32.'
(( SIZE >= 4 && SIZE <= 32 )) || die 'IMAGE_SIZE_GIB must be an integer from 4 to 32.'
[ -f "$TOP/backup/index.json" ] || die 'Run ./port.sh backup first; a completed backup is required.'
if [ -z "${MOBIAN_PASSWORD:-}" ]; then
 [ -t 0 ] || die 'Run this command in a terminal to enter the password.'
 read -rs -p 'Mobian password: ' MOBIAN_PASSWORD; printf '\n'
 read -rs -p 'Confirm password: ' password_confirmation; printf '\n'
 [ "$MOBIAN_PASSWORD" = "$password_confirmation" ] || die 'Passwords do not match.'
 unset password_confirmation
fi
[ -n "$MOBIAN_PASSWORD" ] || die 'The password must not be empty.'
[[ "$MOBIAN_PASSWORD" != *$'\n'* && "$MOBIAN_PASSWORD" != *:* ]] || die 'The password must not contain a newline or colon.'
trap 'unset MOBIAN_PASSWORD password_confirmation' EXIT
RELEASE=$(cat "$TOP/out/linux/include/config/kernel.release")
[[ "$RELEASE" =~ ^[A-Za-z0-9._+-]+-p580$ ]] || die 'Invalid P580 kernel release.'
[ -d "$TOP/out/modules/lib/modules/$RELEASE" ] || die "Kernel modules are missing: $RELEASE"
python3 "$TOP/scripts/apply_addresses.py" "$TOP" "$TOP/out/p580.dtb"
PKGS=systemd-sysv,python3,udev,dbus,sudo,passwd,libcap2-bin,network-manager,wpasupplicant,iproute2,openssh-server,ca-certificates,mobian-phosh-base,gnome-terminal,nautilus,gnome-control-center,pipewire-audio,wireplumber,alsa-utils,alsa-ucm-conf,iio-sensor-proxy,usbutils,kmod,firmware-atheros,wireless-regdb,e2fsprogs,locales,bluez,rsync,less,libgl1-mesa-dri,libegl-mesa0,squeekboard,xwayland,libspa-0.2-libcamera,libcamera-ipa
KEYRING=$TOP/vendor/mobian.gpg
# shellcheck disable=SC2016 # mmdebstrap expands $1 inside the hook.
mmdebstrap --mode=root --architectures=arm64 --variant=minbase --components='main non-free-firmware' --include="$PKGS" --keyring=/usr/share/keyrings/debian-archive-keyring.gpg --keyring="$KEYRING" --setup-hook='mkdir -p "$1/usr/share/keyrings"' --setup-hook="copy-in $KEYRING /usr/share/keyrings/" trixie "$ROOT" 'deb https://deb.debian.org/debian trixie main non-free-firmware' 'deb https://deb.debian.org/debian-security trixie-security main non-free-firmware' 'deb https://repo.mobian.org/ trixie main non-free-firmware'
cat > "$ROOT/etc/apt/sources.list" <<'EOF'
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main non-free-firmware
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian-security trixie-security main non-free-firmware
deb [signed-by=/usr/share/keyrings/mobian.gpg] https://repo.mobian.org/ trixie main non-free-firmware
EOF
printf 'p580\n' > "$ROOT/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 p580\n' > "$ROOT/etc/hosts"
printf 'PARTLABEL=USERDATA / ext4 defaults,noatime 0 1\n' > "$ROOT/etc/fstab"
chroot "$ROOT" useradd -u 1000 -m -s /bin/bash -G sudo,audio,video,input,netdev,bluetooth mobian
printf 'mobian:%s\n' "$MOBIAN_PASSWORD" | chroot "$ROOT" chpasswd
chroot "$ROOT" passwd -l root
mkdir -p "$ROOT/EFI/BOOT" "$ROOT/dtb/exynos" "$ROOT/usr/lib/modules" "$ROOT/etc/NetworkManager/system-connections" "$ROOT/etc/phosh" "$ROOT/etc/systemd/logind.conf.d" "$ROOT/etc/ssh/sshd_config.d" "$ROOT/etc/modules-load.d"
cp "$TOP/out/linux/arch/arm64/boot/vmlinuz.efi" "$ROOT/EFI/BOOT/BOOTAA64.EFI"
cp "$TOP/out/p580.dtb" "$ROOT/dtb/exynos/exynos7870-gtanotexlwifi.dtb"
cp -a "$TOP/out/modules/lib/modules/$RELEASE" "$ROOT/usr/lib/modules/"
find "$ROOT/usr/lib/modules" -type l \( -name build -o -name source \) -delete
# Keep the tablet's own calibration across firmware package upgrades.
for relative in ath10k/QCA9377/hw1.0/board.bin qca/nvm_00230302.bin qca/rampatch_00230302.bin s5p-mfc-v10.fw; do
 [ -f "$TOP/cache/firmware/$relative" ] || continue
 for suffix in '' .zst .xz; do
  file="/usr/lib/firmware/$relative$suffix"
  if [ -e "$ROOT$file" ]; then chroot "$ROOT" dpkg-divert --local --rename --add "$file"; fi
 done
done
# ath10k tries board-2 before board.bin; force its normal board.bin fallback.
for suffix in '' .zst .xz; do
 file="/usr/lib/firmware/ath10k/QCA9377/hw1.0/board-2.bin$suffix"
 if [ -e "$ROOT$file" ]; then chroot "$ROOT" dpkg-divert --local --rename --add "$file"; fi
done
cp -a "$TOP/cache/firmware/." "$ROOT/usr/lib/firmware/"
cp -a "$TOP/config/overlay/." "$ROOT/"
python3 "$TOP/scripts/configure_regdb.py" --root "$ROOT"
# USB Ethernet gadget.
printf 'g_ether\nath10k_sdio\nhci_uart\niio_trig_sysfs\nst_accel_i2c\n' > "$ROOT/etc/modules-load.d/p580.conf"
cat > "$ROOT/etc/NetworkManager/system-connections/p580-usb.nmconnection" <<'EOF'
[connection]
id=p580-usb
type=ethernet
interface-name=usb0
autoconnect=true
[ipv4]
method=manual
address1=10.77.0.2/24
never-default=true
[ipv6]
method=disabled
EOF
chmod 600 "$ROOT/etc/NetworkManager/system-connections/p580-usb.nmconnection"
printf '[output:DSI-1]\nscale=2\n' > "$ROOT/etc/phosh/phoc.ini"
printf '[Login]\nHandleLidSwitch=ignore\nHandleLidSwitchExternalPower=ignore\nHandlePowerKey=poweroff\nIdleAction=ignore\n' > "$ROOT/etc/systemd/logind.conf.d/10-p580.conf"
printf 'PermitRootLogin no\n' > "$ROOT/etc/ssh/sshd_config.d/10-p580.conf"
chroot "$ROOT" systemctl set-default graphical.target
chroot "$ROOT" systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
chroot "$ROOT" systemctl enable NetworkManager ssh phosh p580-growfs.service p580-ssh-keygen.service
# Generate unique SSH host keys on the tablet, not in the distributed image.
rm -f "$ROOT"/etc/ssh/ssh_host_* "$ROOT/etc/machine-id"
printf '' > "$ROOT/etc/machine-id"
chroot "$ROOT" depmod -a "$RELEASE"
python3 -c 'import os,sys; p=sys.argv[1]; open(p,"wb").write(os.urandom(512)); os.chmod(p,0o600)' "$ROOT/var/lib/systemd/random-seed"
chroot "$ROOT" apt-get clean
chroot "$ROOT" dpkg-query -W > "$TOP/out/rootfs-packages.txt"
truncate -s "${SIZE}G" "$TOP/out/rootfs-p580.img"
mkfs.ext4 -F -L p580-rootfs -O ^metadata_csum_seed,^orphan_file -d "$ROOT" "$TOP/out/rootfs-p580.img"
sha256sum "$TOP/out/rootfs-p580.img" "$TOP/out/boot-p580.img" > "$TOP/out/IMAGE-SHA256SUMS"
echo 'Rootfs image ready: out/rootfs-p580.img'
