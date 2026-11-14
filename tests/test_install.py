# SPDX-License-Identifier: MIT
import gzip, hashlib, importlib.util, json, struct, sys, tempfile, unittest, uuid, zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import device
import images

class ImageGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def image(self):
        path = self.root / 'rootfs.img'; sectors = 32768
        entries = bytearray(128 * 128)
        for index, (first, last, kind) in enumerate([(2048, 8191, 'c12a7328-f81f-11d2-ba4b-00a0c93ec93b'), (8192, sectors - 34, 'b921b045-1df0-41c3-af44-4c6f280d3fae')]):
            offset = index * 128
            entries[offset:offset + 16] = uuid.UUID(kind).bytes_le
            entries[offset + 16:offset + 32] = uuid.uuid4().bytes_le
            struct.pack_into('<QQ', entries, offset + 32, first, last)
        header = bytearray(512); header[:8] = b'EFI PART'
        struct.pack_into('<II', header, 8, 0x10000, 92)
        struct.pack_into('<QQQQ', header, 24, 1, sectors - 1, 34, sectors - 34)
        header[56:72] = uuid.uuid4().bytes_le
        struct.pack_into('<QIII', header, 72, 2, 128, 128, zlib.crc32(entries))
        struct.pack_into('<I', header, 16, zlib.crc32(header[:92]))
        mbr = bytearray(512); mbr[450] = 0xee; mbr[510:] = b'\x55\xaa'
        boot = bytearray(512); boot[82:90] = b'FAT32   '; boot[510:] = b'\x55\xaa'
        with path.open('wb') as out:
            out.truncate(sectors * 512); out.seek(0); out.write(mbr); out.write(header); out.write(entries)
            out.seek(2048 * 512); out.write(boot); out.seek(8192 * 512 + 1024 + 56); out.write(b'\x53\xef')
        return path

    def test_valid_gpt_and_corrupt_header(self):
        path = self.image(); self.assertEqual(images.check_rootfs(path), path.stat().st_size)
        with path.open('r+b') as out: out.seek(512 + 56); out.write(b'broken')
        with self.assertRaisesRegex(ValueError, 'checksum'): images.check_rootfs(path)

    def test_truncated_or_wrong_root_filesystem(self):
        path = self.image()
        with path.open('r+b') as out: out.seek(8192 * 512 + 1024 + 56); out.write(b'xx')
        with self.assertRaisesRegex(ValueError, 'ext4'): images.check_rootfs(path)
        with path.open('r+b') as out: out.truncate(1024 * 1024)
        with self.assertRaisesRegex(ValueError, 'Truncated'): images.check_rootfs(path)

    def test_sparse_or_plain_ext4_refused(self):
        path = self.root / 'wrong.img'; path.write_bytes(bytes(4096))
        with self.assertRaisesRegex(ValueError, 'GPT'): images.check_rootfs(path)

    def test_model_identity_mismatch(self):
        with patch.object(device, 'shell', return_value='SM-T580'):
            with self.assertRaisesRegex(SystemExit, 'Only SM-P580'): device.identity()

    def test_backup_from_other_tablet_refused(self):
        record = {'cid': 'different', 'serial': 'serial', 'partitions': {}}
        with patch.object(device, 'cid', return_value='current'):
            with self.assertRaisesRegex(SystemExit, 'different device'): device.check_backup_identity(record, {})

    def test_corrupt_backup_refused(self):
        path = self.root / 'BOOT.img.gz'
        with gzip.open(path, 'wb') as out: out.write(b'altered')
        record = {'files': {'BOOT': {'file': path.name, 'size': 7, 'sha256_raw': hashlib.sha256(b'original').hexdigest()}}}
        with patch.object(device, 'BACK', self.root):
            with self.assertRaisesRegex(SystemExit, 'Corrupt backup'): device.check_backup_file(record, {'BOOT': {'size': 7}}, 'BOOT')

    def test_bad_staged_chunk_does_not_write_partition(self):
        source = self.root / 'boot.img'; source.write_bytes(b'valid image'); (self.root / 'out').mkdir()
        calls = []
        def shell(command, timeout=None):
            calls.append(command)
            if command.startswith('sha256sum '): return '0' * 64 + '  staged.bin'
            return ''
        with patch.object(device, 'ROOT', self.root), patch.object(device, 'run', return_value=''), patch.object(device, 'shell', side_effect=shell):
            with self.assertRaisesRegex(SystemExit, 'staging SHA256 mismatch'):
                device.stream_write('/dev/block/mmcblk0p9', source, source.stat().st_size, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(any(command.startswith('dd ') for command in calls))

    def test_changed_manifest_stops_before_stream_write(self):
        for name in ['rootfs-p580.img', 'boot-p580.img']: (self.root / name).write_bytes(b'image')
        record = {'device': 'SM-P580', 'files': {name: {'file': file, 'size': 5, 'sha256': '0' * 64} for name, file in [('BOOT', 'boot-p580.img'), ('USERDATA', 'rootfs-p580.img')]}}
        (self.root / 'images.json').write_text(json.dumps(record))
        with patch.object(images.subprocess, 'run'), patch.object(images, 'check_rootfs'):
            with self.assertRaisesRegex(ValueError, 'checksum'): images.verify_images(self.root)

if __name__ == '__main__': unittest.main()
