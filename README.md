# Mobian for Samsung Galaxy Tab A 10.1 with S Pen (SM-P580)

Mainline Linux, U-Boot and Mobian/Phosh integration for **SM-P580 / gtanotexlwifi** (Exynos7870, Mali-T830, 3 GiB RAM).

The tablet boots through S-BOOT → U-Boot → EFI Linux into a native Phosh session. The build uses pinned official Linux and U-Boot archives with local patch series. No Android build tree or SD card is needed. Other models, including SM-T580 and SM-P585, are not installation targets.

## Hardware support

| Function | Status | Scope / limitation |
|---|---|---|
| Boot / Phosh desktop | Works | Linux 7.3.4, Mobian/Debian trixie |
| CPU / RAM | Works | Eight Cortex-A53 cores, 3 GiB RAM |
| CPUFreq / per-chip ASV | Works | Two CPU clusters |
| GPU / GPU frequency scaling | Works | Mali-T830 / Panfrost; Phoc uses hardware rendering |
| Display | Works | Native DRM, 1200×1920; BOE panel tested |
| Manual brightness | Works | Adjustable manually; outdoor boost is not implemented |
| Night Light / gamma | Not working | Gamma control unavailable |
| Touch / multitouch | Works | Multitouch supported |
| Back / Menu / Home | Works | Input press/release events confirmed |
| Power / volume keys / magnetic cover | Not validated | Not tested |
| Accelerometer / rotation / tilt | Works | Sensor events and observed screen rotation |
| Ambient light sensor | Works | RGB/clear readings and lux events |
| Automatic brightness | Policy verified | Ambient-light events update the brightness setting; visible panel response and calibration remain unvalidated |
| eMMC / ext4 root | Works | HS400 Enhanced Strobe; read/write works; sustained and random I/O performance unvalidated |
| microSD | Partial | Card detected and mounted; UHS voltage-switch warning remains |
| Wi-Fi | Basic connection works | QCA9377 SDIO association/DHCP; 5 GHz throughput/AP/P2P not validated |
| Bluetooth connection / A2DP | Connection works / A2DP partial | Headset and A2DP sink enumerated; audible A2DP playback unvalidated |
| Bluetooth HFP/HSP | Protocol available | RFCOMM available; HFP/SCO audio unvalidated |
| USB networking / SSH | Works | ECM gadget, tablet 10.77.0.2 |
| USB host / OTG | Not implemented | Current profile is peripheral only |
| Speaker / internal microphone | Partial validation | Speaker heard; capture graph active; mic recording quality and stereo routing need testing |
| Wired headphones / jack | Not validated | Codec and UCM routes present |
| Wired headset microphone / remote | Not implemented | Additional routing and ADC integration required |
| USB charging | Works | USB charging |
| Battery gauge / temperatures | Partial | Voltage, current, SOC and AP/cell temperatures available; gauge temperature uses the cell NTC; charge-cycle accuracy unvalidated |
| Dedicated charger / charge termination | Not validated | USB charging does not establish all adapter modes |
| Suspend / resume / idle drain | Not validated | Sleep targets masked; deep idle disabled in the board description |
| RTC | Awake alarm verified | Clock and alarm IRQ work while awake; suspend wake and power-off retention unvalidated |
| H.264 hardware decoding | Works | MFC decoder |
| Hardware encoding | Works in tested modes | H.264 up to 1920×1080; MPEG-4/VP8/HEVC at 640×360; H.263 at 352×288; NV21 input required with Debian FFmpeg 7.1.5 |
| Rear / front cameras | Capture works / quality partial | Raw capture and libcamera/qcam preview work with local libcamera packages; dark image and brightness flicker remain, especially at the front; autofocus, EEPROM and PipeWire application streaming unvalidated |
| S Pen (W9019) / GPS / grip sensor (SX9306) | Not implemented | Unavailable |

## Installation

A Debian arm64 computer, USB cable, Android ADB root access and TWRP are required. Allow 40 GiB of free disk space plus backup storage.

See [installation](docs/INSTALL.md), [building](docs/BUILD.md) and [updates](docs/UPDATE.md).

**Initial installation erases Android USERDATA.** A full backup is required by default. RECOVERY/TWRP, EFS and the partition table are preserved.

## References

[Source projects and revisions](docs/SOURCES.md) · [License](LICENSE)
