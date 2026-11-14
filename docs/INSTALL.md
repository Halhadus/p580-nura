# Installation

## Requirements

- Samsung SM-P580 with a working P580 TWRP recovery.
- Linux build computer, ADB and a USB cable.
- Completed `./port.sh build` and enough free storage for backups.

**Installation overwrites BOOT and USERDATA, including apps, settings and internal storage.** Keep external copies of the backups.

## Backup

Open TWRP, disable MTP and unmount Data. Then run:

```sh
./port.sh backup
```

The backup contains BOOT, RECOVERY, EFS and USERDATA with raw-data sizes and SHA256 digests. It also records model, serial, eMMC CID and partition layout. An interrupted backup can be resumed by rerunning the command.

To omit Android user data:

```sh
./port.sh backup --skip-userdata
```

BOOT, RECOVERY and EFS are still backed up. A skipped USERDATA backup provides no restore point for Android apps, settings or internal storage.

## Install

```sh
./port.sh install --erase-android-data
adb reboot
```

If USERDATA was omitted from the backup, explicitly use the same choice:

```sh
./port.sh install --erase-android-data --skip-userdata
adb reboot
```

The installer checks the backup against the connected tablet and validates the images before writing USERDATA and BOOT. Images are staged in RAM in chunks of up to 64 MiB; each chunk is checked by SHA256 before writing. Both images are verified by SHA256 readback.

If a transfer or readback fails, remain in TWRP. After fixing the connection, rerun the same install command; an image whose readback already matches is skipped. Never issue a reboot after a failed verification.

## First boot

Use the account and password chosen by pmbootstrap. The tablet normally uses `172.16.42.1` over USB networking, with the computer receiving another address in that subnet. Use the selected username for SSH.

Automatic suspend is disabled. The power button shuts down the tablet; cover events are ignored.

## Recovery

Open TWRP with Volume Up + Home + Power. BOOT and USERDATA backups can be restored manually from recovery after checking their recorded sizes/digests and confirming the target partitions. Keep `backup/index.json` with the image files.
