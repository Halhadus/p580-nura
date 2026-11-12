#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import json, os, shutil, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1]); out = root/'out'
compatibles = {0: 'boe,hx8279d-gtanotexl', 1: 'chunghwa,hx8279d-gtanotexl', 3: 'boe,hx8279d-gtanotexl-v2'}
def find(tree, parent):
    for node in subprocess.check_output(['fdtget', '-l', str(tree), parent], text=True).split():
        path = parent.rstrip('/')+'/'+node
        if node == 'panel@0': return path
        found = find(tree, path)
        if found: return found
reference = os.environ.get('P580_REFERENCE_DTB')
if reference:
    reference = Path(reference)
    board = subprocess.check_output(['fdtget', '-t', 's', str(reference), '/', 'compatible'], text=True).split()
    if 'samsung,gtanotexlwifi' not in board: sys.exit('The reference DTB is not an SM-P580 device tree.')
    node = find(reference, '/')
    if not node: sys.exit('Panel node not found in the reference DTB.')
    panels = subprocess.check_output(['fdtget', '-t', 's', str(reference), node, 'compatible'], text=True).split()
    selected = [value for value in panels if value in compatibles.values()]
    if len(selected) != 1: sys.exit('Unknown or ambiguous panel in the reference DTB; existing selected DTB preserved.')
    compatible = selected[0]
else:
    panel = json.loads((root/'device-info/panel-info.json').read_text())
    lcdtype = panel.get('lcdtype')
    if type(lcdtype) is not int or not 0 <= lcdtype <= 0xffffff: sys.exit('Invalid panel ID.')
    kind = lcdtype & 255
    if kind not in compatibles: sys.exit(f'Unsupported panel ID: {lcdtype:#x}')
    compatible = compatibles[kind]
dest = out/'p580.dtb.part'
shutil.copy2(out/'linux/arch/arm64/boot/dts/exynos/exynos7870-gtanotexlwifi.dtb', dest)
node = find(dest, '/')
if not node: sys.exit('Panel node not found.')
subprocess.run(['fdtput', '-t', 's', str(dest), node, 'compatible', compatible, 'himax,hx8279'], check=True)
dest.replace(out/'p580.dtb')
