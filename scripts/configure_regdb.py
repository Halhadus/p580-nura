#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Select Debian's upstream-signed regdb pair for the upstream-key kernel."""
import argparse, os, subprocess
from pathlib import Path

def select_upstream(root):
    root = root.resolve()
    prefix = [] if root == Path('/') else ['chroot', str(root)]
    query = subprocess.check_output(prefix+['update-alternatives', '--query', 'regulatory.db'], text=True)
    options = {}; current = None; slaves = False
    for line in query.splitlines():
        if line.startswith('Alternative: '):
            current = line.split(': ',1)[1]; options[current] = {}; slaves = False
        elif current and line == 'Slaves:': slaves = True
        elif current and slaves and line.startswith(' '):
            key, value = line.strip().split(None,1); options[current][key] = value
        elif line and not line.startswith(' '): slaves = False
    matches = [name for name, group in options.items() if Path(name).name == 'regulatory.db-upstream' and Path(group.get('regulatory.db.p7s','')).name == 'regulatory.db.p7s-upstream']
    if len(matches) != 1: raise SystemExit('No unambiguous upstream database/signature alternative pair; existing selection preserved.')
    target = matches[0]; signature = options[target]['regulatory.db.p7s']
    for name in [target, signature]:
        path = root/name.lstrip('/')
        if not path.is_file() or path.stat().st_size == 0: raise SystemExit('Missing upstream regdb file: '+name)
    subprocess.run(prefix+['update-alternatives', '--set', 'regulatory.db', target], check=True)
    for link, expected in [('regulatory.db', target), ('regulatory.db.p7s', signature)]:
        actual = subprocess.check_output(prefix+['readlink', '-f', '/lib/firmware/'+link], text=True).strip()
        desired = subprocess.check_output(prefix+['readlink', '-f', expected], text=True).strip()
        if actual != desired: raise SystemExit('regdb alternative readback mismatch: '+link)
    print('Selected upstream-signed regulatory.db and paired signature. Kernel signature verification remains enabled.')
    if not prefix: print('Reload with sudo iw reg reload, or reboot; no country code was changed.')

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, default=Path('/')); args = parser.parse_args()
    if os.geteuid() != 0: parser.error('Run with sudo, or from the rootfs builder.')
    if args.root.resolve() == Path('/'):
        path = Path('/sys/firmware/devicetree/base/compatible')
        if not path.exists() or b'samsung,gtanotexlwifi\0' not in path.read_bytes(): parser.error('Live configuration is restricted to the SM-P580.')
    elif not (args.root/'etc/os-release').is_file(): parser.error('Target rootfs has no /etc/os-release.')
    select_upstream(args.root)

if __name__ == '__main__': main()
