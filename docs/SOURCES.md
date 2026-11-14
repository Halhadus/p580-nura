# Sources

| Component | Source / revision |
|---|---|
| Nura pmaports | Git submodule, based on `43082c8c84b3a085b496fd6c969bd104d68afb2a`; branch `p580-nura` |
| pmbootstrap | 3.11.0 or later |
| Linux | kernel.org Linux 7.3.4; source and SHA512 in the P580 kernel APKBUILD |
| U-Boot | Official revision `7995bf8dea2d5b3eb7fcb836636f4773924ec35d` (2026.04-rc3), with P580 and runtime address patches |
| Mesa | 26.2.6; Alpine recipe `82a2f41f324afea53a5225f80242404f259f72a7`, with P580 Midgard spill fallback and upstream MR !46050 bundle-ID fix |
| libcamera | 0.8.0; CSIS match and P580 gain helpers |
| P580 firmware | [P580 stock dump](https://github.com/Exynos7870-labs/samsung_gtanotexlwifikx_dump/tree/5eb24d166df949fe77ae122b882b200527af7e12), pinned revision `5eb24d166df949fe77ae122b882b200527af7e12` |
| Native QCA9377 SDIO firmware | linux-firmware revision `d7904d5b07a9e2c4cdd9f8b2c5a5faa9c6e665cf`; distribution notice installed by the firmware package |
| Downstream wiring | Valera1978 Samsung Exynos7870 kernel, revision `fd083ee596be966b36d0e6a027f18118fd3a5202` |

## Kernel patch provenance

[`origins.json`](../pmaports/device/testing/linux-samsung-gtanotexlwifi/origins.json) records the source repository, reference revision, upstream commit and local changes for imported kernel patches. Patch files and their application order are listed in the [kernel APKBUILD](../pmaports/device/testing/linux-samsung-gtanotexlwifi/APKBUILD).

The upstream reference is [`alessandro-fontana/linux-exynos7870`](https://github.com/alessandro-fontana/linux-exynos7870/tree/d1979ff14a1d00807c7b05faef3330967fa60d3a), branch `gtaxlwifi/7.3`, revision `d1979ff14a1d00807c7b05faef3330967fa60d3a`. [Compare subsequent upstream changes](https://github.com/alessandro-fontana/linux-exynos7870/compare/d1979ff14a1d00807c7b05faef3330967fa60d3a...gtaxlwifi/7.3) when updating the patch series.

The `1001`–`1005` patches contain local P580 board, panel, thermistor, camera-supply and panel-variant support.

## Packaging references

- [Nura deviceinfo reference](https://docs.nura.eco/pmaports/main/packaging/device-packages/deviceinfo-reference.html).
- [Firmware packaging](https://docs.nura.eco/pmaports/main/packaging/firmware-packages.html) and [kernel command lines](https://docs.nura.eco/pmaports/main/packaging/kernel-packages/kernel-cmdline.html).
- Existing pmaports `device-samsung-exynos7` and `device-samsung-n1awifi` packages for U-Boot/EFI and nested USERDATA installation; `device-motorola-dubai` for panel variants.
- [Nura source repositories](https://nura.eco/source-code/).
