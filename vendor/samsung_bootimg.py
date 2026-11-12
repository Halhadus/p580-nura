#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
"""Samsung boot image header v0."""
import hashlib
import struct

PAGE = 2048
# Samsung mkbootimg defaults
BASE = 0x10000000
KERNEL_OFFSET = 0x00008000
RAMDISK_OFFSET = 0x01000000
SECOND_OFFSET = 0x00f00000
TAGS_OFFSET = 0x00000100
SEANDROID = b"SEANDROIDENFORCE"

def pad(data, size=PAGE):
    return data + b"\0" * ((size - len(data) % size) % size)

def samsung_bootimg(kernel, dt):
    """A boot image as S-BOOT wants it: header v0 with dt_size, no ramdisk."""
    sha = hashlib.sha1()
    for blob in (kernel, b"", b"", dt):   # kernel, ramdisk, second, dt
        sha.update(blob)
        sha.update(struct.pack("<I", len(blob)))
    header = struct.pack(
        "<8s10I16s512s32s1024s",
        b"ANDROID!",
        len(kernel), BASE + KERNEL_OFFSET,
        0, BASE + RAMDISK_OFFSET,
        0, BASE + SECOND_OFFSET,
        BASE + TAGS_OFFSET, PAGE, len(dt), 0,
        b"", b"", sha.digest(), b"")
    return pad(header) + pad(kernel) + pad(dt) + SEANDROID
