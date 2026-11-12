# Installation

## Requirements

- Samsung SM-P580 with TWRP installed.
- Debian arm64 computer and a USB cable.
- USB debugging enabled and the computer authorized in Android.
- Root ADB access (`adb root`) or working `su`. Without either, the device check requires SELinux `Permissive` and readable firmware files.

## Prepare and install

With Android running:

```sh
./port.sh deps
./port.sh prepare
./port.sh install --erase-android-data
adb reboot
```

Preparation reads the device identity and firmware, builds the images, reboots into TWRP and backs up BOOT, RECOVERY, EFS and USERDATA. It then requests a password for the `mobian` account and creates the rootfs.

**Installation erases Android apps, settings and files, including internal storage.** Keep `backup/` on another disk. Writes are verified by SHA256 readback; RECOVERY/TWRP, EFS and the partition table are preserved.

If TWRP cannot unmount Data, disable MTP and uncheck Data in its Mount menu. Run `./port.sh finish` to resume preparation, then repeat the install command. Do not reboot after a write or readback error.

## Install without a USERDATA backup

Follow the separate [build steps](BUILD.md), using these backup and install commands:

```sh
./port.sh backup --skip-userdata
./port.sh rootfs
./port.sh verify
./port.sh install --erase-android-data --skip-userdata
adb reboot
```

This still backs up BOOT, RECOVERY and EFS. Android apps, settings and files cannot be restored without the USERDATA backup.

## First boot

Sign in as `mobian` using the password chosen during preparation. Connect Wi-Fi from Settings.

For SSH over USB, run on the computer:

```sh
bash scripts/usb-host.sh
ssh mobian@10.77.0.2
```

The computer uses `10.77.0.1/24`; the tablet uses `10.77.0.2/24`.

## Restore Android

Open TWRP with Volume Up + Home + Power, connect USB and use the complete Android backup:

```sh
./port.sh restore --restore-android-data
adb reboot
```

This replaces Mobian with the backed-up Android BOOT and USERDATA. EFS and TWRP remain untouched.

For recovery after a failed boot, open TWRP and run `./port.sh logs`. Logs are saved under `out/device-logs/`.
