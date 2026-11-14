#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate and record the two install artifacts without mounting them."""
import argparse, hashlib, json, struct, subprocess, sys, uuid, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def check_rootfs(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        mbr = stream.read(512)
        if len(mbr) != 512 or mbr[510:] != b'\x55\xaa' or mbr[450] != 0xee: raise ValueError('Expected a GPT Nura image, not a sparse image or plain ext4 filesystem.')
        header = bytearray(stream.read(512))
        if len(header) != 512 or header[:8] != b'EFI PART': raise ValueError('Missing GPT header.')
        hsize, hcrc = struct.unpack_from('<II', header, 12)
        if not 92 <= hsize <= 512: raise ValueError('Invalid GPT header size.')
        struct.pack_into('<I', header, 16, 0)
        if zlib.crc32(header[:hsize]) != hcrc: raise ValueError('GPT header checksum mismatch.')
        backup_lba = struct.unpack_from('<Q', header, 32)[0]
        entries_lba, count, entry_size, crc = struct.unpack_from('<QIII', header, 72)
        if not 1 <= count <= 4096 or not 128 <= entry_size <= 1024 or count * entry_size > 4 * 1024 * 1024: raise ValueError('Invalid GPT entries.')
        if backup_lba * 512 >= size: raise ValueError('Truncated GPT image.')
        stream.seek(entries_lba * 512); entries = stream.read(count * entry_size)
        if len(entries) != count * entry_size or zlib.crc32(entries) != crc: raise ValueError('GPT partition-array checksum mismatch.')
        parts = []
        for offset in range(0, len(entries), entry_size):
            row = entries[offset:offset + entry_size]
            if row[:16] == bytes(16): continue
            first, last = struct.unpack_from('<QQ', row, 32)
            if first < 34 or first > last or (last + 1) * 512 > size: raise ValueError('Invalid partition bounds.')
            parts.append((first, last, uuid.UUID(bytes_le=row[:16])))
        parts.sort()
        esp = uuid.UUID('c12a7328-f81f-11d2-ba4b-00a0c93ec93b')
        if len(parts) != 2 or parts[0][2] != esp or parts[0][1] >= parts[1][0]: raise ValueError('Expected exactly one ESP and one non-overlapping root partition.')
        stream.seek(parts[0][0] * 512); boot = stream.read(512)
        if boot[82:90] != b'FAT32   ' or boot[510:] != b'\x55\xaa': raise ValueError('Boot partition is not FAT32.')
        stream.seek(parts[1][0] * 512 + 1024 + 56)
        if stream.read(2) != b'\x53\xef': raise ValueError('Root partition is not ext4.')
    return size

def verify_images(out, record=False):
    paths = {'USERDATA': out / 'rootfs-p580.img', 'BOOT': out / 'boot-p580.img'}
    validator = ROOT / 'pmaports/device/testing/u-boot-samsung-gtanotexlwifi/check_bootimg.py'
    subprocess.run([sys.executable, str(validator), str(paths['BOOT'])], check=True)
    check_rootfs(paths['USERDATA'])
    metadata = {name: {'file': path.name, 'size': path.stat().st_size, 'sha256': digest(path)} for name, path in paths.items()}
    if record:
        (out / 'images.json').write_text(json.dumps({'device': 'SM-P580', 'files': metadata}, indent=2) + '\n')
    else:
        saved = json.loads((out / 'images.json').read_text())
        if saved != {'device': 'SM-P580', 'files': metadata}: raise ValueError('Image size/checksum differs from the build manifest.')
    return metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--record', action='store_true'); args = parser.parse_args()
    verify_images(ROOT / 'out', args.record)
