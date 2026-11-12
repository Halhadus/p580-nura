#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def prepare(root, name, fresh=False):
    base = root/'patches'/name; work = root/'work'/name
    names = [line.strip() for line in (base/'series').read_text().splitlines() if line.strip() and not line.startswith('#')]
    if len(names) != len(set(names)) or any(Path(p).name != p or not p.endswith('.patch') for p in names): raise SystemExit('Invalid patch series entry')
    current = [{'name': p, 'sha256': hashlib.sha256((base/p).read_bytes()).hexdigest()} for p in names]
    # Do not let git apply discover the recipe repository above the source tree.
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(work.parent))
    env.pop('GIT_DIR', None); env.pop('GIT_WORK_TREE', None)
    progress = work/'.p580-series.json'
    if progress.exists():
        done = json.loads(progress.read_text())
        if current[:len(done)] != done: raise SystemExit(f'{name}: the applied patch series has changed.')
    elif fresh: done = []
    else: raise SystemExit(f'{name}: source preparation is incomplete.')
    for entry in current[len(done):]:
        patch = base/entry['name']; print(name+': '+entry['name'], flush=True)
        subprocess.run(['git', '-C', str(work), 'apply', '--check', str(patch)], check=True, env=env)
        subprocess.run(['git', '-C', str(work), 'apply', str(patch)], check=True, env=env)
        done.append(entry)
        temp = progress.with_suffix('.part'); temp.write_text(json.dumps(done, indent=2)+'\n'); temp.replace(progress)
    if not progress.exists(): progress.write_text('[]\n')
    print(name+': source ready.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('name', choices=['linux', 'u-boot', 'libcamera']); parser.add_argument('--fresh', action='store_true'); args = parser.parse_args()
    prepare(Path(__file__).resolve().parents[1], args.name, args.fresh)
