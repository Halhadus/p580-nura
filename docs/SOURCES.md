# Sources

| Component | Source | Pinned version |
|---|---|---|
| Linux | [kernel.org](https://www.kernel.org/) | 7.3.4; URL and SHA256 in `config/sources.env` |
| U-Boot | [official U-Boot](https://github.com/u-boot/u-boot) | `7995bf8dea2d5b3eb7fcb836636f4773924ec35d`; archive hash in `config/sources.env` |
| libcamera | [Debian source](https://deb.debian.org/debian/pool/main/libc/libcamera/) | 0.4.0-7, local `+p580` packages; URL and SHA256 pins in `config/libcamera.env` |
| Rootfs | [Debian](https://deb.debian.org/debian/) / [Mobian](https://repo.mobian.org/) | trixie + trixie-security; package versions resolved at build time |

## References

| Project | Branch | Reference revision | Usage |
|---|---|---|---|
| [Ezmanw/Mobian-T580](https://github.com/Ezmanw/Mobian-T580) | `main` | `370d2ca1aeaef0e44145ff7a304579df50b7e799` | Exynos S-BOOT/U-Boot/EFI flow and Mobian recipe reference |
| [alessandro-fontana/gtaxlwifi-lineageos](https://github.com/alessandro-fontana/gtaxlwifi-lineageos) | `lineage-24.0` | `505aafb7f2bff808cb3b9f6b32f0250aa557d524` | T580 build and installation reference |
| [alessandro-fontana/linux-exynos7870](https://github.com/alessandro-fontana/linux-exynos7870) | `gtaxlwifi/7.3` | `d1979ff14a1d00807c7b05faef3330967fa60d3a` | Clock, power, display, touch, sensor, audio, wireless, storage and media support |
| [exynos7870-mainline/mainline-patches](https://gitlab.com/exynos7870-mainline/mainline-patches) | `main` | `5686e3b545bd34e80ec6e73604b8819d10e52a2c` | Exynos7870 patches |
| [alessandro-fontana/android_device_samsung_gtaxlwifi](https://github.com/alessandro-fontana/android_device_samsung_gtaxlwifi) | `lineage-24.0` | `f9a389d4fcdd0b7285400291fd3780925742b003` | Samsung boot image builder, audio routing and device configuration reference |
| [alessandro-fontana/android_external_gtaxl-loader](https://github.com/alessandro-fontana/android_external_gtaxl-loader) | `lineage-24.0` | `c3b1b60e3f4cba1cf9ebab758bd7361e745861d2` | ECT/ASV calibration and shared BUCK2 floor logic adapted to U-Boot; EFS address handling reference |
| [Valera1978/android_kernel_samsung_exynos7870](https://github.com/Valera1978/android_kernel_samsung_exynos7870) | `lineage-17.1` | `fd083ee596be966b36d0e6a027f18118fd3a5202` | P580 wiring, RAM/reservations, battery calibration, panel timing and initialization tables |
| [samsungexynos7870/android_kernel_samsung_exynos7870](https://github.com/samsungexynos7870/android_kernel_samsung_exynos7870) | `lineage-18.1-lts` | `e41078f882271fe43089a683a200bdab8803483b` | Additional P580 board wiring reference |
| [alessandro-fontana/android_external_libcamera](https://github.com/alessandro-fontana/android_external_libcamera) | `lineage-24.0` | `95f6b20d917be23759710c1f85a6f2deab106e0a` | T580 camera pipeline |

## Upstream changes

- [Kernel changes since this port's reference](https://github.com/alessandro-fontana/linux-exynos7870/compare/d1979ff14a1d00807c7b05faef3330967fa60d3a...gtaxlwifi/7.3)
- [LineageOS integration changes](https://github.com/alessandro-fontana/gtaxlwifi-lineageos/compare/505aafb7f2bff808cb3b9f6b32f0250aa557d524...lineage-24.0)
- [Mobian-T580 history](https://github.com/Ezmanw/Mobian-T580/commits/)
- [Exynos7870 patch history](https://gitlab.com/exynos7870-mainline/mainline-patches/-/commits/main)
