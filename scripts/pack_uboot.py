#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package U-Boot in a Samsung boot image."""
import importlib.util, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('samsung_bootimg', root / 'vendor/samsung_bootimg.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
kernel, dtb, output = map(Path, sys.argv[1:])
output.write_bytes(module.samsung_bootimg(kernel.read_bytes(), dtb.read_bytes()))
