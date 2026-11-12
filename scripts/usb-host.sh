#!/bin/bash
# SPDX-License-Identifier: MIT
set -euo pipefail
# Exact USB gadget host-side MAC configured in kernel cmdline.
for path in /sys/class/net/*; do
 [ -f "$path/address" ] || continue
 if [ "$(cat "$path/address")" = 02:58:00:00:00:01 ]; then
  iface=${path##*/}
  sudo ip address replace 10.77.0.1/24 dev "$iface"
  sudo ip link set "$iface" up
  echo "SSH: ssh mobian@10.77.0.2 ($iface)"
  exit 0
 fi
done
echo 'P580 USB network interface not found.' >&2
exit 1
