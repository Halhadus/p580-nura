# Building

On a Debian arm64 computer, connect the tablet running Android with USB debugging enabled:

```sh
./port.sh deps
./port.sh prepare
```

The password for the `mobian` account is requested during rootfs creation. Build output:

| File | Purpose |
|---|---|
| `out/boot-p580.img` | U-Boot boot image |
| `out/rootfs-p580.img` | Mobian root filesystem |
| `out/p580.dtb` | Device tree |

To run each build step separately:

```sh
./port.sh info
./port.sh firmware
./port.sh sources
./port.sh kernel
./port.sh uboot
./port.sh backup
./port.sh rootfs
./port.sh verify
```

`JOBS` sets the number of parallel build jobs; the default is 4. `IMAGE_SIZE_GIB` sets the rootfs image size from 4 to 32 GiB; the default is 6 GiB. The image must fit the tablet's USERDATA partition.

Continue with [installation](INSTALL.md).
