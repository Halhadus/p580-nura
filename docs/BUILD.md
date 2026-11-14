# Building

## Requirements

- Linux computer supported by pmbootstrap; native arm64 or cross-build from x86_64.
- pmbootstrap 3.11.0 or later, Git and Python 3.
- Internet access and sufficient space for Mesa, kernel, U-Boot and libcamera build trees.
- ADB for the later TWRP backup/install steps.

pmbootstrap creates its Alpine build environments and installs package build dependencies.

## Configuration

```sh
./port.sh build
```

The first invocation runs `pmbootstrap init` with a project-local `pmbootstrap.cfg`, this repository's `pmaports` checkout and `work/pmbootstrap`. Select `samsung-gtanotexlwifi`, the appropriate panel, Phosh and systemd.

To revisit those choices:

```sh
pmbootstrap -c "$PWD/pmbootstrap.cfg" -p "$PWD/pmaports" -w "$PWD/work/pmbootstrap" init
```

## Build modes

| Command | Behavior |
|---|---|
| `./port.sh build` | Strict package builds with fresh build chroots; up-to-date APKs and compiler/download caches are reused |
| `./port.sh build --lax` | Keeps build chroots and reuses up-to-date APKs and compiler/download caches |
| `./port.sh build --lax --force` | Rebuilds the six port packages while keeping build chroots and compiler/download caches |

In lax mode, image generation installs local APKs and binary dependencies without automatic package builds. Build missing dependencies explicitly before generating the image.

pmbootstrap compares package versions when deciding whether to build. Bump the relevant APKBUILD's `pkgrel` after changing a patch or configuration, or use `--force` to rebuild the port packages at the same version. Normal package builds recreate their source directories; `--lax` does not resume compilation from existing object files. The rootfs and BOOT images are regenerated after the package stage succeeds.

## Panel selection

| Variant | Panel compatible | Hardware validation |
|---|---|---|
| `boe` | `boe,hx8279d-gtanotexl` | Tested under Mobian / Linux 7.3.4 |
| `boe-v2` | `boe,hx8279d-gtanotexl-v2` | Untested |
| `cpt` | `chunghwa,hx8279d-gtanotexl` | Untested |

Identify the panel before choosing a variant. In Android or a recovery that exposes the panel driver:

```sh
adb shell cat /sys/class/lcd/panel/window_type
adb shell cat /proc/cmdline
```

The low byte of Samsung's `lcdtype` identifies the known variants: `0` for BOE, `3` for BOE-v2 and `1` for CPT/Chunghwa.

Each panel variant selects a DTB from the kernel package. See [hardware support](HARDWARE.md) for panel and board-revision coverage.

## Build outputs

| File | Contents |
|---|---|
| `out/rootfs-p580.img` | Raw Nura GPT image containing FAT32 `/boot` and ext4 `/` subpartitions |
| `out/boot-p580.img` | Samsung Android-header wrapper containing U-Boot and its stub DTBH |
| `out/images.json` | Device, size and SHA256 records for the two install artifacts |
| `out/export/` | pmbootstrap export links |

The combined Nura image is written inside the existing Android USERDATA partition. The initramfs discovers the boot and root subpartitions using loop devices. S-BOOT loads U-Boot from BOOT, U-Boot maps USERDATA as a block device and starts systemd-boot from its EFI system partition. systemd-boot then loads the packaged EFI kernel, initramfs and selected DTB.

## Camera preview

For a Wayland preview, install `qcam` and `qt6-qtwayland`, then run `qcam`. See [camera support](HARDWARE.md#cameras) for image-quality and capture limitations.
