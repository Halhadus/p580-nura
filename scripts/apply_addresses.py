#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read the tablet's own saved EFS without mounting or changing it."""
import gzip, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
root, dtb = Path(sys.argv[1]), Path(sys.argv[2])
debugfs = shutil.which('debugfs', path='/usr/sbin:/sbin:'+os.environ.get('PATH', os.defpath))
if not debugfs: sys.exit('debugfs is unavailable; install e2fsprogs on the build host.')
index = root / 'backup/index.json'
if not index.is_file():
    sys.exit('Missing backup/index.json. Run ./port.sh backup first.')
record = json.loads(index.read_text())
try:
    meta = record['files']['EFS']
    if meta['file'] != 'EFS.img.gz' or type(meta['size']) is not int or meta['size'] <= 0 or not re.fullmatch(r'[0-9a-f]{64}', meta['sha256_raw']): raise ValueError
except (KeyError, TypeError, ValueError): sys.exit('Invalid EFS backup metadata.')
with tempfile.TemporaryDirectory(prefix='p580-efs-', dir=root/'out') as tmp:
    image = Path(tmp)/'efs.img'
    digest, size = hashlib.sha256(), 0
    try:
        with gzip.open(root/'backup'/meta['file'], 'rb') as src, image.open('wb') as dst:
            for chunk in iter(lambda: src.read(4 * 1024 * 1024), b''):
                size += len(chunk)
                if size > meta['size']: sys.exit('EFS backup size mismatch.')
                digest.update(chunk); dst.write(chunk)
    except (OSError, EOFError) as error: sys.exit('Could not read EFS backup: '+str(error))
    if size != meta['size'] or digest.hexdigest() != meta['sha256_raw']: sys.exit('EFS backup size or SHA256 mismatch.')
    found = {}
    for kind, path in [('wifi','/wifi/.mac.info'), ('bluetooth','/bluetooth/bt_addr')]:
        value = subprocess.check_output([debugfs,'-R','cat '+path,str(image)], text=True).strip()
        if re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}',value): found[kind]=bytes.fromhex(value.replace(':',''))
        else: print('No valid address in EFS: '+kind, file=sys.stderr)
if not found: sys.exit('No valid Wi-Fi or Bluetooth addresses found in EFS.')
def find(parent, name):
    for child in subprocess.check_output(['fdtget','-l',str(dtb),parent],text=True).split():
        path = parent.rstrip('/')+'/'+child
        if child == name: return path
        match = find(path,name)
        if match: return match
for kind, value in found.items():
    node = find('/', 'wifi@1' if kind=='wifi' else 'bluetooth')
    if not node: sys.exit('Missing device-tree node for: '+kind)
    prop = 'local-mac-address' if kind=='wifi' else 'local-bd-address'
    if kind=='bluetooth': value=value[::-1]
    subprocess.run(['fdtput','-t','bx',str(dtb),node,prop,*[f'{x:02x}' for x in value]],check=True)
print('Applied EFS addresses:', ', '.join(found))
