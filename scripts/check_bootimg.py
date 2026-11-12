#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import hashlib, struct, sys
from pathlib import Path
b = Path(sys.argv[1]).read_bytes()
if len(b) < 2048: sys.exit('Truncated Android boot image')
if b[:8] != b'ANDROID!': sys.exit('Missing Android boot header')
v = struct.unpack_from('<10I', b, 8)
ks, _, rs, _, ss, _, _, page, ds, _ = v
if page != 2048 or rs or ss or ks == 0 or ds == 0: sys.exit('Unsupported Samsung boot image layout')
align = lambda n: (n + page - 1) // page * page
off = page + align(ks)
if off + ds > len(b): sys.exit('Truncated boot image payload')
if b[off:off+4] != b'DTBH': sys.exit('Missing Samsung DTBH table')
if len(b) > 32 * 1024 * 1024: sys.exit('BOOT image exceeds 32 MiB')
h = hashlib.sha1()
for blob in (b[page:page+ks], b'', b'', b[off:off+ds]):
    h.update(blob); h.update(struct.pack('<I', len(blob)))
if b[576:596] != h.digest(): sys.exit('Boot header SHA1 mismatch')
print(f'Samsung boot image verified: {len(b)} bytes')
