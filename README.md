# Nura for Samsung Galaxy Tab A 10.1 with S Pen (SM-P580)

**p580-nura** is a Nura Linux port for the **Samsung Galaxy Tab A 10.1 with S Pen (SM-P580 / gtanotexlwifi)**, built with pmbootstrap and pmaports.

**Experimental:** Nura installation and boot are untested. The hardware tables record tests with Linux 7.3.4 under Mobian.

## Build and install

Install pmbootstrap 3.11.0 or later, Python 3, Git and ADB on a Linux computer. The checked-out `pmaports` submodule contains the P580 package recipes and patches.

```sh
./port.sh build
```

On first use, pmbootstrap asks for the device, panel variant, UI, service manager and user settings. Choose `samsung-gtanotexlwifi`, the matching `boe`, `boe-v2` or `cpt` panel, Phosh and systemd.

Open TWRP, disable MTP and connect USB:

```sh
./port.sh backup
./port.sh install --erase-android-data
adb reboot
```

**Installation overwrites BOOT and USERDATA, including internal storage.**

See [building](docs/BUILD.md) and [installation](docs/INSTALL.md) for panel selection, storage layout and backup options.

## Hardware support

| Function | Status | Scope / limitation |
|---|---|---|
| Boot / Phosh desktop | Partial | Linux 7.3.4 boots under Mobian; Nura boot chain untested |
| CPU / RAM | Working | Eight Cortex-A53 cores, 3 GiB RAM with firmware reservations |
| CPUFreq / per-chip ASV | Working | Both CPU clusters scale; U-Boot applies chip-specific voltages and shared GPU/bus rail limits |
| GPU / GPU frequency scaling | Working | Mali-T830 / Panfrost; Phoc hardware rendering; observed 343–1001 MHz |
| Display | Working | Native DRM/KMS, 1200×1920; BOE panel tested; BOE-v2 and CPT variants untested |
| Manual brightness | Working | Manual adjustment confirmed; outdoor boost unsupported |
| Night Light / gamma | Unsupported | Gamma control unavailable |
| Touch / multitouch | Working | STM FTS; multiple contact slots observed; palm rejection untested |
| Back / Menu / Home | Working | Press/release events confirmed |
| Power / volume keys / cover | Untested | GPIO keys and primary Hall input defined; secondary cover input missing |
| S Pen | Unsupported | Wacom W9019 driver/board integration missing; pen input and insertion switch unavailable |
| Accelerometer / rotation | Working | K2HH/LIS2HH12 readings and screen rotation; absolute calibration untested |
| Ambient light sensor | Working | CM3323 RGB/clear readings and lux events |
| Automatic brightness | Partial | Light events update brightness settings; visible response and calibration untested |
| Grip / Wi-Fi SAR | Unsupported | SX9306 driver, board enablement and WLAN power-policy integration missing |
| eMMC / ext4 root | Working | HS400 Enhanced Strobe; short read/write tests passed; sustained/random I/O untested |
| microSD | Partial | Card detected and mounted; UHS voltage-switch warning remains |
| Wi-Fi | Working | QCA9377 SDIO association/DHCP; signed regulatory database loaded; 5 GHz/AP/P2P untested |
| Bluetooth / A2DP | Partial | Controller and headset connection work; A2DP sink enumerates, audible playback untested |
| Bluetooth HFP/HSP | Untested | RFCOMM works; SCO routing and duplex headset audio unvalidated |
| USB networking / SSH | Partial | USB Ethernet and SSH tested under Mobian; Nura configfs setup untested; device address `172.16.42.1` |
| USB host / OTG | Unsupported | Peripheral mode forced; role switching and VBUS sourcing incomplete |
| Speakers | Working | Exynos I²S → S1402X → RT5659; audible playback confirmed |
| Internal microphone | Partial | Capture graph active; recorded output and gain/noise quality unvalidated |
| Wired headphones / jack | Untested | GPIO detection and UCM route present |
| Wired headset mic / remote | Unsupported | Headset routing/selection and ADC button integration incomplete |
| USB charging | Working | SM5703 charger; other adapter modes and full-cycle behavior untested |
| Battery gauge / temperatures | Partial | Voltage, current, SOC and AP/cell temperatures available; gauge temperature uses cell NTC; cycle accuracy untested |
| Thermal management | Partial | TMU and AP/cell thermistors available; sustained cooling/throttling behavior unvalidated |
| Suspend / resume | Untested | Sleep targets masked; low-power entry, wake sources and standby drain unvalidated |
| RTC | Partial | Clock and awake alarm IRQ work; suspend wake and power-off retention untested |
| H.264 hardware decode | Working | MFC; 640×360, 150 frames tested |
| Hardware encode | Working | H.264 at 640×360/1920×1080; MPEG-4/VP8/HEVC at 640×360; H.263 at 352×288; NV21 input tested previously with FFmpeg 7.1.5; Nura FFmpeg untested |
| Rear / front cameras | Partial | S5K4H5YC/SR259 raw capture and qcam preview work; dark output and brief brightness flicker remain |
| Camera ISP | Partial | CPU Software ISP works through libcamera; Exynos FIMC-IS2 hardware ISP unsupported |
| Rear autofocus / EEPROM | Broken | DW9807 transfer timeouts and calibration EEPROM bind/read failure; autofocus and calibration consumption incomplete |
| Camera flash / torch | Untested | SM5703 driver and board definition present |
| Camera desktop streaming | Partial | PipeWire sources enumerate; application/portal streams and recording untested |
| GNSS | Unsupported | BCM4752 UART/power control defined; native protocol/location integration missing |

See [hardware support](docs/HARDWARE.md) for drivers, subsystem details and integration gaps.

## Repository layout

| Path | Purpose |
|---|---|
| `port.sh`, `scripts/` | Build, TWRP backup and verified installation |
| `pmaports/device/testing/device-samsung-gtanotexlwifi` | Deviceinfo, panel variants, initramfs modules and device configuration |
| `pmaports/device/testing/linux-samsung-gtanotexlwifi` | Kernel configuration and ordered patch sources |
| `pmaports/device/testing/firmware-samsung-gtanotexlwifi` | QCA9377 Wi-Fi/Bluetooth and MFC firmware |
| `pmaports/device/testing/u-boot-samsung-gtanotexlwifi` | U-Boot, runtime address fixups and Samsung BOOT packaging |
| `pmaports/temp/libcamera` | libcamera, CSIS pipeline support and sensor gain helpers |

[Source projects and revisions](docs/SOURCES.md) · [License](LICENSE)
