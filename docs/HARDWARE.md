# Hardware support

Hardware and feature support for **Samsung Galaxy Tab A 10.1 with S Pen (SM-P580 / gtanotexlwifi)**. Results refer to Linux 7.3.4 under Mobian. Nura installation and boot are untested.

## Device

| Component | Hardware |
|---|---|
| SoC | Samsung Exynos7870, eight Arm Cortex-A53 cores |
| GPU | Arm Mali-T830 |
| Memory | 3 GiB RAM |
| Display | 10.1-inch, 1200×1920 MIPI DSI; BOE HX8279D, BOE-v2 and CPT/Chunghwa panel variants |
| Storage | eMMC and microSD slot |
| Wireless | Qualcomm QCA9377: SDIO Wi-Fi and UART Bluetooth |
| GNSS | Broadcom BCM4752 |
| Input | STM FTS touchscreen, capacitive Back/Menu keys, GPIO keys, Hall cover sensor, Wacom W9019 digitizer |
| Sensors | ST K2HH/LIS2HH12 accelerometer, Capella CM3323 light sensor, Semtech SX9306 grip sensor |
| Audio | Exynos I²S, Samsung S1402X digital mixer, Realtek RT5659 codec |
| Power | Samsung S2MPU05-family PMIC; Silicon Mitus SM5703 charger, fuel gauge, MUIC and flash controller |
| Cameras | Rear Samsung S5K4H5YC with DW9807 autofocus actuator and calibration EEPROM; front SK hynix SR259 |

## Status

| Status | Meaning |
|---|---|
| Working | The listed function works. Limitations are stated separately. |
| Partial | Some functions work; integration, quality or mode coverage is incomplete. |
| Broken | A failure has been observed. |
| Unsupported | Required driver, board support or userspace integration is missing. |
| Untested | No conclusive functional test is available. |

## Platform and memory

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Boot | S-BOOT → U-Boot → systemd-boot → EFI Linux | Partial | Linux 7.3.4 boots under Mobian; Nura boot chain and initramfs untested. |
| Board description | `exynos7870-gtanotexlwifi.dts` | Partial | P580 support is present; downstream revision 00/02 differences are not fully covered. |
| CPU / SMP | Arm64 / PSCI | Working | All eight cores online; short multicore stress test passed. |
| CPU frequency scaling | Samsung CMU, cpufreq-dt, OPP | Working | Both clusters scale across 13 OPPs. |
| Per-chip voltage calibration | U-Boot ECT/ASV fixups | Working | CPU/GPU voltages and shared BUCK2 floor are adjusted for the chip. Both CPU clusters share BUCK1; GPU and bus consumers share BUCK2. |
| CPU hotplug | PSCI | Untested | Core offline/online operation. |
| Memory | Arm64 memory management | Working | Two RAM banks; firmware and secure-world reservations reduce usable capacity. A short 256 MiB test passed. |
| Contiguous allocation | CMA | Partial | Configured for media DMA; fragmentation and sustained allocation remain untested. |
| Userspace DMA allocation | DMA heap | Working | Camera processing uses `/dev/dma_heap/system`. |
| Buffer sharing | DMA-BUF / fences | Partial | Complete camera → encoder → display sharing and synchronization remain untested. |
| Compressed swap | ZRAM | Working | Active in the running system. |
| System MMU | Exynos IOMMU | Partial | Display/media paths operate; domain fault recovery and long DMA stress remain untested. |
| Interrupts / timekeeping | GIC / Arm architectural timer | Working | Normal operation; suspend timekeeping remains untested. |
| Peripheral buses | Samsung I²C/HSI2C, UART, PL330 DMA | Partial | Used by working peripherals; digitizer, grip and GNSS integration remain incomplete. |
| Clock output | Samsung CLKOUT | Broken | Probe error `-22`; parent/board configuration unresolved. |
| Watchdog | `s3c2410_wdt` | Untested | Configured; timeout/reset operation untested. |
| Hardware RNG / crypto acceleration | SoC hardware blocks | Untested | Hardware-specific operation unvalidated; hardware RNG is disabled in the port configuration. |
| Persistent crash logs | Ramoops / pstore | Partial | Registered; panic/reboot log retention untested. |

## Power management

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Main PMIC | SEC MFD / S2MPU05 regulators | Partial | Core supplies operate; not all regulator consumers and sleep states are represented. |
| SM5703 core / IRQ | SM5703 MFD | Partial | Charger and flash share the MFD register map; fuel gauge uses a separate I²C address. Not all child functions are integrated. |
| SM5703 regulator outputs | Regulator framework | Unsupported | Native LDO/buck child-driver and consumer integration incomplete. |
| USB charging | `sm5703-charger` | Working | Charging from USB confirmed. |
| Charger detection | `extcon-sm5502` / SM5703 MUIC | Partial | CDP detection observed; complete SDP/CDP/DCP and cable transition coverage remains untested. |
| Current / voltage limits | `sm5703-charger` / power_supply | Partial | Input/charge current, charge voltage and termination settings implemented; complete charge-cycle behavior untested. |
| Charge inhibition | power_supply `charge_behaviour` | Untested | `auto` and `inhibit-charge` implemented; desktop charge-limit policy not included. |
| Cell temperature protection | Battery thermal zone / charger | Untested | Software temperature checks and hysteresis implemented; physical inhibit/resume behavior unvalidated. |
| Battery voltage / current / SOC | `sm5703-fuelgauge` | Partial | Readouts available; current accuracy, SOC curve, learned capacity and aging unvalidated. |
| Dedicated adapter / termination | Charger / MUIC | Untested | Full DCP cycle, termination, recharge hysteresis and powered-off charging. |
| AP temperature | ADC0 / generic-adc-thermal | Working | P580 23-point NTC table; readout-only zone without cooling maps or shutdown trips. |
| Cell temperature | ADC1 / generic-adc-thermal | Working | Used by the battery thermal zone and fuel-gauge `TEMP` property. |
| SoC thermal management | Exynos TMU / thermal cooling | Partial | Temperature and cooling definitions present; sustained throttling behavior unvalidated. |
| CPU idle | PSCI cpuidle | Untested | CPU power-down state and WFI suspend-to-idle fallback exist in the local series; low-power entry/exit unvalidated. |
| System suspend / resume | Linux PM / systemd | Untested | Sleep targets are masked in the image. Device recovery, wake sources and standby drain unvalidated. |
| Bus / domain DVFS | MIF, INT, DISP, CAM | Unsupported | Native scaling and bandwidth coordination incomplete; firmware settings retained where native DVFS is absent. |
| Clock / supply power saving | Clock, regulator and PM-domain frameworks | Partial | `clk_ignore_unused regulator_ignore_unused` retained; several supplies remain always on. |
| RTC | S5M-family RTC | Partial | Clock and awake alarm IRQ work; suspend wake and power-off retention untested. |

## Display and graphics

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Display scanout | Exynos DECON / DRM KMS | Working | Native 1200×1920 mode, approximately 59.929 Hz. |
| DSI link | Samsung DSIM / MIPI PHY | Working | Local reset, PLL, timing and bootloader-handoff fixes. |
| BOE panel | `panel-himax-hx8279` | Working | BOE HX8279D variant physically tested. |
| BOE-v2 / CPT panel | `panel-himax-hx8279` | Untested | Select the matching `boe-v2` or `cpt` kernel variant. |
| Manual brightness | Backlight class | Working | Manual adjustment confirmed. |
| Automatic brightness | CM3323 / desktop policy | Partial | Lux events update brightness settings; visible response and calibration unvalidated. |
| Outdoor brightness boost | Panel backlight | Unsupported | Downstream boost range is not mapped into the current interface. |
| Night Light / gamma | DRM color management | Unsupported | Gamma control unavailable. |
| 3D acceleration | Panfrost / Mesa | Working | Phoc hardware rendering and OpenGL benchmark work. |
| GPU frequency scaling | Panfrost devfreq / OPP | Working | Observed range 343–1001 MHz. |
| GPU runtime power saving | Panfrost / PM domains | Untested | Actual idle power collapse unvalidated. |
| Panel power transitions | Panel / DSIM / DECON | Partial | Boot display works; repeated blank/unblank, cold/warm cycles and ESD recovery unvalidated. |
| Vulkan / OpenCL | Graphics / compute userspace | Untested | No validated native userspace implementation for this port. |

## Input

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Touchscreen | `stmfts` / evdev | Working | Touch coordinates and multiple contact slots observed. |
| Maximum contacts / palm rejection | STM FTS | Untested | Maximum simultaneous contacts and pen-aware filtering unvalidated. |
| Screen-off gestures / touch wake | STM FTS / wake IRQ | Untested | Gesture mode and suspend wake unvalidated. |
| Back / Menu keys | `stmfts` / evdev | Working | Press/release events confirmed. |
| Home key | `gpio-keys` | Working | Press/release events confirmed. |
| Power / volume keys | `gpio-keys` | Untested | Board definitions present; physical event tests outstanding. |
| Primary cover sensor | `gpio-keys` / `SW_LID` | Untested | GPA1-3 input described; image logind policy ignores lid events. |
| Secondary cover sensor | GPIO input | Unsupported | Downstream revision 02 specifies GPF4-0; current board description lacks this input. |
| S Pen digitizer | Wacom W9019, I²C `0x56` | Unsupported | 3.3 V supply described; `hsi2c4` disabled and digitizer not bound. Native protocol, power and IRQ integration required. |
| Pen pressure / hover / side button | Linux input / libinput | Unsupported | Depends on W9019 input support and correct report decoding. |
| Pen insertion / removal | GPIO switch | Unsupported | Downstream sense GPIO not exposed as a native switch input. |
| Pen rotation / palm rejection | Digitizer / touchscreen / compositor | Unsupported | Axis mapping, display rotation and touch arbitration incomplete. |

## Sensors

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Accelerometer | K2HH/LIS2HH12 / ST IIO accelerometer | Working | XYZ readings and screen rotation confirmed. |
| Accelerometer calibration | IIO mount matrix / scale | Partial | Mount matrix present; six-face calibration, offsets and persistence unvalidated. |
| Motion wake / self-test | Accelerometer IRQ / IIO | Untested | Rotation currently uses polling; motion IRQ and wake behavior unvalidated. |
| Ambient light / RGB channels | CM3323 / IIO | Working | Red, green, blue and clear readings; local triggered-buffer support. |
| Lux conversion | Light-sensor consumer | Partial | Lux events available; absolute calibration unvalidated. LDO33 remains always on without driver supply ownership. |
| Grip / capacitive proximity | SX9306, I²C `0x2b` | Unsupported | Downstream GPA2-3 IRQ and main channel 2 defined; native driver/binding and board integration missing. |
| Grip-based Wi-Fi SAR | IIO / WLAN transmit-power policy | Unsupported | Sensor thresholds, calibration and proximity-dependent WLAN power coordination missing. |
| Headset remote ADC | Exynos ADC channel 2 | Unsupported | Native button consumer and jack/mic-bias integration missing. |

## Storage

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Internal eMMC | `dw_mmc-exynos` / block layer | Working | Samsung AJTD4R, approximately 14.7 GiB; ext4 root on USERDATA. |
| HS400 Enhanced Strobe | Exynos MMC timing support | Working | 8-bit bus; observed clock 199875000 Hz. Local HS200/HS400, strobe and ULP-mode patches. |
| eMMC read / write | Block I/O / ext4 | Working | Short 128 MiB tests: direct read 176.434 MiB/s; write plus `fdatasync` 36.170 MiB/s end to end. |
| Sustained / random I/O | Block I/O / filesystem | Untested | Long writes, fsync latency, near-full and thermal-load performance. |
| microSD | `dw_mmc-exynos` | Partial | Detection and mount work; UHS voltage-switch warning remains. Write/hotplug and alternate-card coverage unvalidated. |
| RPMB / encryption acceleration | eMMC / crypto | Untested | Authenticated RPMB transactions and hardware encryption path unvalidated. |

## Wireless and GNSS

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Wi-Fi station | QCA9377 / `ath10k_sdio` | Working | Basic association, DHCP and DNS using device-specific calibration. |
| Regulatory database | cfg80211 / wireless-regdb | Working | Signed wireless-regdb; signature verification enabled. |
| 5 GHz / roaming / throughput | ath10k / NetworkManager | Untested | No performance or roaming coverage. |
| AP / P2P | ath10k / nl80211 | Untested | Hotspot and group formation unvalidated. |
| WoWLAN / scan offload | ath10k / SDIO wake | Untested | Local patches present; system-sleep behavior unvalidated. |
| Bluetooth controller | QCA9377 / `hci_qca` | Working | Firmware/NVM loading, discovery and headset connection. |
| A2DP | BlueZ / PipeWire | Partial | Headset and sink enumerate; audible playback unvalidated. |
| AVRCP | BlueZ | Partial | Connection observed; media-button and volume behavior untested. |
| RFCOMM | Bluetooth socket interface | Working | Socket test passed. |
| HFP/HSP / SCO audio | BlueZ / PipeWire / ASoC | Untested | Duplex audio and BT DAI routing unvalidated. |
| BLE / HID / PAN | Bluetooth profiles | Untested | GATT, input and network profile operation unvalidated. |
| GNSS | BCM4752 / UART / rfkill | Unsupported | UART and power-control definitions present; native initialization/protocol consumer and location fix missing. |

## USB

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| USB peripheral / PHY | Exynos USB / DWC3 | Working | Peripheral controller and USB Ethernet operate. |
| USB networking / SSH | Nura configfs gadget | Untested | USB Ethernet; device address normally `172.16.42.1`. |
| Role switching / OTG | DWC3 / MUIC | Unsupported | Board forces peripheral mode; role detection and VBUS-source integration incomplete. |
| Host VBUS supply | SM5703 boost / regulator | Unsupported | Native boost control and supply ownership incomplete. |
| Other gadget functions | USB configfs / function drivers | Untested | Several functions configured in the kernel; default image provides ECM only. |

## Audio

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| AP audio link | Exynos I²S → S1402X → RT5659 / ASoC | Working | Local machine/mixer drivers; ALSA UCM and PipeWire/WirePlumber integration. |
| Speakers | RT5659 / UCM | Working | Audible playback confirmed; stereo mapping unvalidated. |
| Internal microphone | RT5659 ADC / UCM | Partial | Capture graph active; recorded output and gain/noise quality unvalidated. |
| Headphone playback / jack | RT5659 / GPIO jack / UCM | Untested | GPA0-5 detection and headphone route present. |
| Headset microphone | RT5659 IN1 / UCM | Unsupported | Board route exists; complete headset selection, detection and mic-bias policy missing. |
| Headset remote | ADC2 / GPIO key detect | Unsupported | Button thresholds and native jack/input reporting missing. |
| Sample format / clocking | ALSA / WirePlumber | Partial | Current AP path constrained to S16LE at 48 kHz; the image rule applies to ALSA nodes generally. Other formats/rates unvalidated. |
| Duplex / latency / runtime PM | ASoC / DMA / DAPM | Untested | Simultaneous playback/capture, long streams and power-transition behavior. |

## Cameras

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Rear sensor | S5K4H5YC, I²C `0x37` / V4L2 | Working | Four CSI-2 lanes to CSIS0; 26 MHz input clock. Raw SGRBG10/BA10 capture at 1640×1228 verified. |
| Front sensor | SR259, I²C `0x30` / V4L2 | Working | One CSI-2 lane to CSIS1; 26 MHz input clock. Raw SBGGR10/BG10 capture at 1632×1228 verified. |
| Receiver / raw DMA | `exynos7870-csis` / media controller | Working | Raw frame delivery from both sensors; local PHY/SysMMU support. |
| Sensor power sequencing | V4L2 sensor drivers / regulators | Partial | Ordered supply enable and reverse unwind implemented; repeated power-cycle and autosuspend coverage unvalidated. |
| Processed capture | libcamera simple pipeline / CPU Software ISP | Working | Bayer input processed into RGB by Software ISP/Soft IPA. |
| VGA stream | libcamera / ABGR8888 | Working | 90 contiguous frames without file writes: rear approximately 30 fps, front approximately 28.6 fps at 640×480. |
| qcam preview | Qt / Wayland / libcamera | Working | Preview from both cameras; `qt6-qtwayland` required. |
| Image quality / exposure | Sensor controls / Soft IPA | Partial | Dark output and brief brightness flicker, especially at the front. Exposure timing, black level and sensor-specific tuning incomplete. |
| Gain conversion | libcamera sensor helpers | Working | Rear control 32 = 1×, front control 16 = 1×. Exposure controls use sensor lines. |
| Sensor properties / control delays | libcamera sensor registry | Unsupported | Static properties and measured exposure/gain delays missing. |
| Full-resolution processed stream | Sensor modes / Software ISP | Partial | Large-buffer captures succeed; sustainable preview rate and power budget unvalidated. |
| Rear autofocus actuator | DW9807, I²C `0x0c` / V4L2 | Broken | Driver bound but transfers time out with `-110`; physical focusing unvalidated. |
| Autofocus algorithm | libcamera / focus controls | Unsupported | Focus statistics/search and calibrated lens range not integrated. |
| Rear calibration EEPROM | at24, I²C `0x58` / NVMEM | Broken | Driver configured/loaded; EEPROM bind/read fails. Current consumer requests IO 1.8 V; downstream read sequence also enables AF 2.8 V. |
| Factory calibration | EEPROM parser / libcamera tuning | Unsupported | No verified dump/CRC chain or native AWB, shading and AF calibration consumption. |
| Hardware ISP | Exynos FIMC-IS2 | Unsupported | Sensor front-end/BNS, 3AA statistics, ISP, MCSC and VRA integration missing, including firmware/setfile and clock/power/SysMMU handling. |
| Flash / torch | SM5703 LED flash class | Untested | Driver and board limits present; I²C control used. Physical output and exposure-synchronized flash unvalidated. |
| PipeWire camera sources | SPA libcamera plugin | Partial | Both sources enumerate; application/portal streaming untested. |
| Recording / audio sync | libcamera → encoder → muxer | Untested | End-to-end recording, format conversion and audio synchronization. |
| Concurrent capture / reopen | Shared rails / CSIS / libcamera | Untested | Simultaneous front/rear use and repeated reopen/autosuspend. |

### Camera pipeline

| Stage | Current implementation |
|---|---|
| Capture | Sensor → MIPI CSI-2 → CSIS raw DMA |
| Image processing | libcamera simple pipeline → CPU Software ISP / Soft IPA → RGB |
| Preview | qcam Qt/Wayland |
| Hardware ISP | FIMC-IS2 is not used by the current capture path. |
| Calibration | Rear EEPROM access and downstream-format conversion are missing. The board declares no front calibration EEPROM, OIS or companion chip. |

## Video acceleration

| Function | Driver / interface | Status | Notes |
|---|---|---|---|
| Video codec | Exynos MFC / `s5p-mfc` | Working | Native V4L2 stateful encoder/decoder with MFC firmware. Separate from the camera ISP. |
| H.264 decode | MFC / V4L2 | Working | 150-frame test at 640×360. |
| Other decode formats | MFC / V4L2 | Untested | Hardware decode of other formats unvalidated. |
| H.264 encode | MFC / FFmpeg | Working | 640×360 and 1920×1080, 150 frames per mode. |
| MPEG-4 / VP8 / HEVC encode | MFC / FFmpeg | Working | 640×360, 150 frames per codec. |
| H.263 encode | MFC / FFmpeg | Working | 352×288, 150 frames. |
| Encoder input | FFmpeg 7.1.5 / NV21 | Working | Tested modes require NV21; encoded outputs verified by CPU decode. |
| Codec controls / concurrent sessions | V4L2 codec API | Untested | Profile/level, GOP/bitrate changes, flush/reconfiguration, long streams and concurrency. |
| Zero-copy decode → display | DMA-BUF / DRM | Untested | End-to-end import/export and synchronization. |
| Hardware JPEG / scaler | Exynos JPEG / GSC | Untested | Native acceleration unvalidated. |
| 2D acceleration | Exynos G2D | Unsupported | Native integration incomplete. Desktop rendering uses Panfrost. |
| Protected media | Secure buffers / trusted media path | Unsupported | Native protected-buffer and playback integration missing. |

## Integration gaps

| Subsystem | Missing kernel / board support | Missing userspace support |
|---|---|---|
| Power management | Remaining supply/clock/domain consumers; SM5703 regulator children; MIF/INT/DISP/CAM DVFS and bandwidth coordination | Desktop power/charging policy beyond the current image defaults |
| Display | Gamma/color-control path and outdoor-backlight mapping | Calibrated automatic-brightness policy |
| S Pen | W9019 protocol, power/IRQ support, digitizer node and silo switch | Rotation/calibration and pen-aware touch handling |
| Sensors / SAR | SX9306 binding, IIO driver and board enablement; CM3323 supply ownership | Grip-dependent WLAN transmit-power policy |
| USB | MUIC role reporting, DWC3 role switching and host VBUS control | Additional gadget profiles |
| Audio | Headset-type/button integration and ADC2 consumer | Headset-microphone UCM selection and routing |
| Camera | DW9807/EEPROM access faults; hardware ISP resources and native driver integration | Sensor properties/control delays, calibration parsing/tuning and autofocus |
| GNSS | Receiver initialization/protocol and power integration | Native protocol consumer and location-service integration |

## Sources

- [Build inputs and project references](SOURCES.md).
- [P580 kernel package and patches](../pmaports/device/testing/linux-samsung-gtanotexlwifi/APKBUILD).
- [Deviceinfo and runtime configuration](../pmaports/device/testing/device-samsung-gtanotexlwifi/APKBUILD).
- [U-Boot and address fixups](../pmaports/device/testing/u-boot-samsung-gtanotexlwifi/APKBUILD).
- [Firmware package](../pmaports/device/testing/firmware-samsung-gtanotexlwifi/APKBUILD) and [libcamera package](../pmaports/temp/libcamera/APKBUILD).
