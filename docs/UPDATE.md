# Updates

Connect the tablet by USB. The updater needs `device-info/` identity records and a verified `backup/index.json` with EFS and RECOVERY backups. It does not read `cache/firmware/` or replace installed `/usr/lib/firmware` files; rebuilding the rootfs is unnecessary.

If host metadata was removed, save the currently installed `/dtb/exynos/exynos7870-gtanotexlwifi.dtb` and `/proc/config.gz` while Mobian is running. `P580_REFERENCE_DTB=/absolute/path/to/installed.dtb ./port.sh kernel` selects the exact known P580 panel compatible from that on-disk DTB instead of requiring the old Android panel ID. An unknown panel or another board is rejected. Use the running config as the initial incremental config. The kernel recipe sets `CONFIG_LOCALVERSION="-p580"` and disables `CONFIG_LOCALVERSION_AUTO`. Do not use the bootloader-modified live DTB as a generic source of static OPP voltages.

Recreate missing identity records from the exact SM-P580 in TWRP and take fresh BOOT/RECOVERY/EFS backups using `./port.sh backup --skip-userdata` before packaging. This saves the current Mobian BOOT; it does not recreate a deleted original Android backup. The guarded update installer also snapshots the current EFI/DTB/config before writing. Preserve any existing private backups.

Build the update:

```sh
./port.sh update-build
```

Open TWRP, disable MTP and unmount Data, then install:

```sh
./port.sh update-install
adb reboot
```

The update replaces U-Boot, kernel, modules, device tree and device configuration. Applications, accounts and user files are preserved. The previous boot files and affected configuration are backed up to `out/update-backup/`; keep that directory until the update is confirmed working.

If installation reports an error, stay in TWRP. To restore the saved version:

```sh
./port.sh update-rollback
adb reboot
```

## Camera userspace on an existing trixie installation

The local libcamera series enables `exynos7870-csis` in the simple pipeline with software ISP, adds the sensor analogue-gain helpers and backports the upstream thread-affinity startup fix. IPA modules are packaged separately; `libspa-0.2-libcamera` does not replace them. Fresh rootfs images use distribution libcamera packages; install the local packages below to enable the P580 cameras.

Build on the arm64 trixie tablet or an arm64 trixie build environment, with at least 3 GiB free and adequate power. Do not build against the sid host's newer libraries and copy those binaries to trixie. No kernel build or TWRP step is needed for this userspace change:

```sh
./port.sh libcamera-deps
JOBS=2 ./port.sh libcamera-build
sudo apt-get install qt6-wayland ./out/libcamera/libcamera0.4_0.4.0-7+p580_arm64.deb ./out/libcamera/libcamera-ipa_0.4.0-7+p580_arm64.deb ./out/libcamera/libcamera-tools_0.4.0-7+p580_arm64.deb ./out/libcamera/libcamera-v4l2_0.4.0-7+p580_arm64.deb
LIBCAMERA_LOG_LEVELS='*:DEBUG' cam -l
```

The recipe verifies pinned Debian `.dsc`, original tarball and Debian packaging hashes, applies only the libcamera patch series, and produces matched `+p580` packages in `out/libcamera`. It does not install them automatically. Keep the normal Debian core/IPA/tools/V4L2 versions together for rollback. Restart the user's PipeWire service if its camera enumeration is stale.

The recipe preserves compiled objects with `dpkg-buildpackage -nc` and reruns configuration, dependency checks and package tests. A failed test stops packaging. For a clean rebuild, run `debian/rules clean` in `work/libcamera` before invoking the recipe.

## Regulatory database signature selection

The port's kernel requires a signed regulatory database and trusts the upstream `wens` and `sforshee` keys. Select Debian's upstream database alternative and its registered slave signature together. Signature verification remains enabled; no country code or transmit-power limit is forced.

For an existing P580 installation, copy `scripts/configure_regdb.py` to the tablet and run it with sudo, then run `sudo iw reg reload` or reboot. The script verifies the paired alternatives and resulting symlinks. New rootfs builds perform the same selection automatically.

Reference: [Debian wireless-regdb README](https://salsa.debian.org/kernel-team/wireless-regdb/-/blob/debian/latest/debian/README.Debian).
