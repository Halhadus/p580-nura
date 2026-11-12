#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""SM-P580 host-side collection, backup and guarded BOOT/USERDATA writes."""
import argparse, gzip, hashlib, json, os, re, shlex, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
INFO, BACK = ROOT / 'device-info', ROOT / 'backup'
ADB = ['adb']
SHELL_PREFIX = ''
def run(*args, text=True, timeout=None): return subprocess.check_output(ADB + list(args), text=text, timeout=timeout)
def remote_command(command): return SHELL_PREFIX + shlex.quote(command) if SHELL_PREFIX else command
def shell(command, timeout=None): return run('shell', remote_command(command), timeout=timeout).strip()
def exists(path): return subprocess.run(ADB + ['shell', remote_command('test -r ' + shlex.quote(path))]).returncode == 0
def fail(message): sys.exit(message)
def connect():
    global ADB
    serial = os.environ.get('ADB_SERIAL')
    rows = subprocess.check_output(['adb', 'devices'], text=True).splitlines()[1:]
    good = [r.split()[0] for r in rows if len(r.split()) == 2 and r.split()[1] in ('device', 'recovery')]
    if serial and serial not in good: fail('ADB_SERIAL is not connected or authorized.')
    if not serial and len(good) != 1: fail('Connect one authorized ADB device, or select one with ADB_SERIAL.')
    ADB = ['adb', '-s', serial or good[0]]
    ensure_access()
def ensure_access():
    global SHELL_PREFIX
    SHELL_PREFIX = ''
    if shell('id -u', timeout=10) == '0': return
    for prefix in ['su -c ', 'su 0 sh -c ']:
        try:
            uid = run('shell', prefix + shlex.quote('id -u'), timeout=30).strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired): continue
        if uid == '0':
            SHELL_PREFIX = prefix
            return
    try: mode = shell('getenforce', timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired): fail('Root access is unavailable and the SELinux mode could not be read.')
    if mode != 'Permissive': fail('Root access is unavailable and SELinux is not Permissive; stopping.')

def info():
    model = shell('getprop ro.product.model')
    if model != 'SM-P580': fail('Only SM-P580 is supported.')
    serial = shell('getprop ro.serialno')
    if not serial: fail('Could not read the device serial number.')
    INFO.mkdir(exist_ok=True)
    (INFO/'model.txt').write_text(model+'\n')
    (INFO/'serial.txt').write_text(serial+'\n')
    panel = None
    try: cmdline = shell('cat /proc/cmdline')
    except subprocess.CalledProcessError: cmdline = ''
    match = re.search(r'\blcdtype=(\d+)\b', cmdline)
    if match: panel = {'lcdtype': int(match[1])}
    for path in ['/sys/class/lcd/panel/window_type', '/sys/class/lcd/panel/lcd_type']:
        if panel is not None: break
        try: value = shell('cat '+path)
        except subprocess.CalledProcessError: continue
        if re.fullmatch(r'[0-9a-fA-F]{1,2}(?:\s+[0-9a-fA-F]{1,2}){2}', value):
            panel = {'lcdtype': int(''.join(f'{int(x,16):02x}' for x in value.split()),16)}
        elif re.fullmatch(r'BOE_[0-9a-fA-F]{6}', value): panel = {'lcdtype': int(value[4:],16)}
    if panel is None:
        (INFO/'panel-info.json').unlink(missing_ok=True)
        fail('Could not read the panel ID.')
    (INFO/'panel-info.json').write_text(json.dumps(panel)+'\n')
    print('SM-P580 and panel identified.')
def identity():
    if not (INFO / 'model.txt').exists() or (INFO / 'model.txt').read_text().strip() != 'SM-P580': fail('Run ./port.sh info while Android is running.')
    saved = (INFO / 'serial.txt').read_text().strip()
    current = shell('getprop ro.serialno')
    if not saved or current != saved: fail('Android and recovery serial numbers do not match.')
def wait_for_twrp(timeout=180):
    deadline = time.monotonic() + timeout
    last_state, last_notice = None, 0
    while time.monotonic() < deadline:
        state = 'disconnected'
        try:
            for row in run('devices', timeout=5).splitlines()[1:]:
                fields = row.split()
                if len(fields) >= 2 and fields[0] == ADB[-1]: state = fields[1]
            now = time.monotonic()
            if state != last_state or now - last_notice >= 15:
                print('Waiting for TWRP; ADB state:', state, flush=True)
                last_state, last_notice = state, now
            if state in ('device', 'recovery') and shell('getprop ro.twrp.version', timeout=5): return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print('ADB probe failed; retrying.', flush=True)
        time.sleep(2)
    fail('Timed out waiting for TWRP. Open TWRP, connect USB and retry. No partitions were written.')

def recovery():
    global SHELL_PREFIX
    print('Checking recovery connection...', flush=True)
    identity()
    if not shell('getprop ro.twrp.version', timeout=10):
        print('Rebooting into TWRP...', flush=True)
        subprocess.run(ADB + ['reboot', 'recovery'], check=True, timeout=10)
        SHELL_PREFIX = ''
        wait_for_twrp()
    SHELL_PREFIX = ''
    if shell('id -u', timeout=10) != '0': fail('TWRP requires root ADB access.')
    identity()
    print('TWRP root ADB connection ready.', flush=True)
def partitions():
    command = 'for p in /dev/block/by-name/* /dev/block/bootdevice/by-name/* /dev/block/platform/*/by-name/* /dev/block/platform/*/*/by-name/*; do if [ -L "$p" ]; then printf "%s %s\\n" "${p##*/}" "$(readlink -f "$p")"; fi; done'
    names = {}
    for row in shell(command).splitlines():
        name, path = row.split()
        if re.fullmatch(r'/dev/block/mmcblk0p[0-9]+', path): names[name.upper()] = path
    for required in ['BOOT', 'RECOVERY', 'USERDATA', 'EFS']:
        if required not in names: fail('Partition not found: ' + required + '; no partitions were written.')
    if len({names[n] for n in ['BOOT','RECOVERY','USERDATA','EFS']}) != 4: fail('Partition aliases resolve to the same device')
    uevent = shell('cat /sys/class/block/' + names['USERDATA'].rsplit('/',1)[-1] + '/uevent')
    if 'PARTNAME=USERDATA' not in uevent.splitlines(): fail('Invalid USERDATA partition label; no partitions were written.')
    return {name: {'path': path, 'size': int(shell('cat /sys/class/block/' + path.rsplit('/',1)[-1] + '/size')) * 512} for name, path in names.items()}
def cid():
    value = shell('cat /sys/class/block/mmcblk0/device/cid')
    if not re.fullmatch('[0-9a-fA-F]{32}', value): fail('Could not read the eMMC CID')
    return value

def unmount_data(part):
    # Longest mount path first also covers /data/media and bind mounts.
    mounts = []
    for row in shell('cat /proc/mounts').splitlines():
        dev, mount = row.split()[:2]
        if dev == part or mount == '/data' or mount.startswith('/data/') or mount in ['/sdcard','/storage/emulated','/storage/emulated/0']:
            mounts.append(mount)
    for mount in sorted(set(mounts), key=len, reverse=True):
        subprocess.run(ADB + ['shell', 'umount ' + shlex.quote(mount)], check=True)
    for row in shell('cat /proc/mounts').splitlines():
        dev, mount = row.split()[:2]
        if dev == part or mount == '/data' or mount.startswith('/data/'): fail('USERDATA is still mounted. Disable MTP and unmount Data in TWRP, then retry.')
def raw_read(path, target, size):
    proc = subprocess.Popen(ADB + ['exec-out', 'cat ' + shlex.quote(path)], stdout=subprocess.PIPE)
    digest, total = hashlib.sha256(), 0
    started = last_notice = time.monotonic()
    try:
        with gzip.open(str(target) + '.part', 'wb', compresslevel=1) as out:
            while True:
                chunk = proc.stdout.read(4 * 1024 * 1024)
                if not chunk: break
                digest.update(chunk); out.write(chunk); total += len(chunk)
                now = time.monotonic()
                if now - last_notice >= 5:
                    print(f'{target.name}: {total / 1024**3:.2f}/{size / 1024**3:.2f} GiB, {100 * total / max(size, 1):.1f}%, {total / 1024**2 / max(now - started, 0.001):.1f} MiB/s', flush=True)
                    last_notice = now
    except BaseException:
        proc.terminate(); proc.wait(); raise
    finally:
        proc.stdout.close()
    if proc.wait() != 0 or total != size: fail(f'Incomplete backup: {target.name}, {total}/{size} bytes.')
    Path(str(target) + '.part').replace(target)
    print(f'Backup complete: {target.name}, {total / 1024**3:.2f} GiB', flush=True)
    return {'file': target.name, 'size': total, 'sha256_raw': digest.hexdigest()}
def check_backup_identity(record, parts):
    if record['cid'] != cid() or record['serial'] != shell('getprop ro.serialno'): fail('The backup belongs to a different device')
    for name in ['BOOT','RECOVERY','EFS','USERDATA']:
        if record['partitions'][name] != parts[name]: fail('Partition layout does not match the backup: ' + name)
def check_backup_file(record, parts, name):
    meta = record['files'].get(name)
    if not meta or meta['file'] != name + '.img.gz' or not (BACK / meta['file']).is_file(): fail('Missing backup: ' + name)
    print('Backup checksum:', name, flush=True)
    try: size, digest = hash_file(BACK / meta['file'], compressed=True)
    except (OSError, EOFError) as error: fail(f'Could not read backup: {name}: {error}')
    if size != parts[name]['size'] or size != meta['size'] or digest != meta['sha256_raw']: fail('Corrupt backup; no partitions were written: ' + name)
def backup(skip_userdata=False):
    print('Backup destination:', BACK, flush=True)
    recovery(); parts = partitions(); unmount_data(parts['USERDATA']['path'])
    BACK.mkdir(exist_ok=True)
    if (BACK / 'index.json').exists():
        validate_backup(parts, allow_skipped_userdata=skip_userdata)
        print('Existing backup verified.', flush=True)
        return
    record = {'cid':cid(), 'serial':shell('getprop ro.serialno'), 'partitions':parts, 'files':{}}
    incomplete = BACK / 'incomplete-index.json'
    if incomplete.exists():
        record = json.loads(incomplete.read_text()); check_backup_identity(record, parts)
    names = ['BOOT','RECOVERY','EFS'] if skip_userdata and 'USERDATA' not in record['files'] else ['BOOT','RECOVERY','EFS','USERDATA']
    for name in names:
        if name in record['files']: check_backup_file(record, parts, name)
    remaining = [name for name in names if name not in record['files']]
    if shutil.disk_usage(ROOT).free < sum(parts[name]['size'] for name in remaining) + 256 * 1024**2: fail('Insufficient disk space for the remaining raw backups plus 256 MiB.')
    record['skipped'] = ['USERDATA'] if skip_userdata and 'USERDATA' not in record['files'] else []
    if record['skipped']: print('USERDATA backup skipped; no USERDATA restore point was created. This backup command does not write partitions.', flush=True)
    (BACK / 'mounts.txt').write_text(shell('cat /proc/mounts') + '\n')
    (BACK / 'partition-map.txt').write_text(shell('cat /proc/partitions') + '\n' + json.dumps(parts, indent=2) + '\n')
    for name in remaining:
        print('Raw backup:', name, flush=True)
        record['files'][name] = raw_read(parts[name]['path'], BACK / (name + '.img.gz'), parts[name]['size'])
        incomplete.write_text(json.dumps(record, indent=2))
    (BACK / 'index.json').write_text(json.dumps(record, indent=2)); incomplete.unlink(missing_ok=True)
    print('Backup complete: ' + ', '.join(record['files']) + '. No partitions were written.')
def validate_backup(parts, allow_skipped_userdata=False):
    record = json.loads((BACK / 'index.json').read_text())
    check_backup_identity(record, parts)
    skipped = record.get('skipped', [])
    if skipped and (skipped != ['USERDATA'] or 'USERDATA' in record['files']): fail('Invalid skipped-partition record in the backup.')
    if skipped and not allow_skipped_userdata: fail('USERDATA was not backed up. Use --skip-userdata to install without Android user-data recovery.')
    for name in ['BOOT','RECOVERY','EFS','USERDATA']:
        if name not in skipped: check_backup_file(record, parts, name)
    return record

def remote_hash(path, size):
    if not isinstance(size, int) or size <= 0: fail('Invalid readback size.')
    block = min(size & -size, 1024 * 1024)
    print(f'Verifying SHA256 on device: {path}, {size} bytes.', flush=True)
    command = f'set -o pipefail && dd if={shlex.quote(path)} bs={block} count={size // block} | sha256sum && echo P580_READBACK_OK'
    try: output = shell(command)
    except subprocess.CalledProcessError as error:
        if error.output: print(error.output, file=sys.stderr)
        fail('Readback failed. Stay in TWRP; do not reboot.')
    digests, complete = [], False
    for line in output.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})[ \t]+\*?-', line.strip())
        if match: digests.append(match.group(1).lower())
        elif line.strip() == 'P580_READBACK_OK': complete = True
        else: print(line, file=sys.stderr)
    if not complete or len(digests) != 1: fail('Incomplete readback or invalid SHA256 output. Stay in TWRP; do not reboot.')
    return digests[0]
def stream_write(path, source, size, expected, compressed=False):
    import tempfile
    if size <= 0 or not re.fullmatch('[0-9a-f]{64}', expected): fail('Invalid write metadata.')
    digest, total = hashlib.sha256(), 0
    print(f'Source image: {size} bytes, SHA256={expected}', flush=True)
    opener = gzip.open if compressed else open
    with tempfile.TemporaryDirectory(prefix='p580-stage-', dir=ROOT/'out') as temporary, opener(source, 'rb') as inp:
        local = Path(temporary)/'chunk.bin'
        while True:
            chunk = inp.read(4 * 1024 * 1024)
            if not chunk: break
            if total + len(chunk) > size: fail('The source image exceeds its expected size; writing stopped.')
            chunk_sha = hashlib.sha256(chunk).hexdigest()
            if size <= 4 * 1024 * 1024 and (len(chunk) != size or chunk_sha != expected): fail('Source image size or SHA256 changed; no partition was written.')
            local.write_bytes(chunk)
            remote = f'/tmp/p580-write-{os.getpid()}-{chunk_sha[:16]}.bin'
            try:
                print(f'RAM staging: offset={total}, bytes={len(chunk)}', flush=True)
                output = run('push', str(local), remote)
                if output.strip(): print(output.strip(), flush=True)
                staged = shell('sha256sum ' + shlex.quote(remote))
                fields = staged.split()
                if not fields or fields[0].lower() != chunk_sha: fail('RAM staging SHA256 mismatch; this chunk was not written: ' + staged)
                print('Staged chunk verified; writing to device.', flush=True)
                command = f'dd if={shlex.quote(remote)} of={shlex.quote(path)} bs=4096 seek={total // 4096} && sync && echo P580_WRITE_OK'
                output = shell(command)
                for line in output.splitlines():
                    if line.strip() != 'P580_WRITE_OK': print(line, file=sys.stderr)
                if 'P580_WRITE_OK' not in output.splitlines(): fail('Device write did not complete. Stay in TWRP; do not reboot.')
            except subprocess.CalledProcessError as error:
                if error.output: print(error.output, file=sys.stderr)
                fail('ADB transfer or device write failed. Stay in TWRP; do not reboot.')
            finally:
                try: shell('rm -f ' + shlex.quote(remote), timeout=10)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error: print('Could not remove the staged RAM file: ' + str(error), file=sys.stderr)
            digest.update(chunk); total += len(chunk)
            print(f'Written: {total}/{size} bytes', flush=True)
    if total != size or digest.hexdigest() != expected: fail('Source size or SHA256 changed. Stay in TWRP; do not reboot.')
    actual = remote_hash(path, size)
    print(f'Expected SHA256: {expected}\nReadback SHA256: {actual}', flush=True)
    if actual != expected: fail('Device SHA256 mismatch. Stay in TWRP; do not reboot.')
    print('Write verified:', path)
def hash_file(path, compressed=False):
    h, size = hashlib.sha256(), 0
    with (gzip.open if compressed else open)(path, 'rb') as f:
        for chunk in iter(lambda:f.read(4 * 1024 * 1024), b''): h.update(chunk); size += len(chunk)
    return size, h.hexdigest()
def install(erase, skip_userdata=False):
    if not erase: fail('Installation erases USERDATA. Use ./port.sh install --erase-android-data to continue.')
    recovery(); parts = partitions(); record = validate_backup(parts, allow_skipped_userdata=skip_userdata)
    if record.get('skipped'): print('Installing without a USERDATA backup; Android user data cannot be restored.', flush=True)
    unmount_data(parts['USERDATA']['path'])
    images = {'USERDATA':ROOT/'out/rootfs-p580.img', 'BOOT':ROOT/'out/boot-p580.img'}
    if remote_hash(parts['RECOVERY']['path'], parts['RECOVERY']['size']) != record['files']['RECOVERY']['sha256_raw']: fail('RECOVERY has changed since the backup; installation stopped.')
    subprocess.run([sys.executable, str(ROOT/'scripts/check_bootimg.py'), str(images['BOOT'])], check=True)
    image_meta = {}
    for name, path in images.items():
        size, sha = hash_file(path)
        if size > parts[name]['size']: fail(name + ' image does not fit its partition')
        image_meta[name] = (size, sha)
    subprocess.run(['e2fsck', '-f', '-n', str(images['USERDATA'])], check=True)
    # BOOT is last: recovery remains available if rootfs transfer fails.
    for name in ['USERDATA','BOOT']:
        size, sha = image_meta[name]
        if remote_hash(parts[name]['path'], size) == sha:
            print(name + ' image already matches the device; skipping the write.', flush=True)
            continue
        print('Writing:',name,flush=True); stream_write(parts[name]['path'], images[name], size, sha)
    print('Installation verified. Run adb reboot to start Mobian.')
def restore(erase):
    if not erase: fail('Restoring Android erases Mobian data. Use ./port.sh restore --restore-android-data to continue.')
    recovery(); parts=partitions(); record=validate_backup(parts); unmount_data(parts['USERDATA']['path'])
    for name in ['USERDATA','BOOT']:
        meta=record['files'][name]; stream_write(parts[name]['path'], BACK/meta['file'], meta['size'], meta['sha256_raw'], compressed=True)
    print('Android USERDATA and BOOT restored. Run adb reboot to start Android.')
def firmware():
    identity(); dest=ROOT/'cache/firmware'; dest.mkdir(parents=True, exist_ok=True)
    mappings={
      'ath10k/QCA9377/hw1.0/board.bin':['ath10k/QCA9377/hw1.0/board.bin','qca6174/bdwlan30.bin','bdwlan30.bin','wlan/qca_cld/qca6174/bdwlan30.bin'],
      'qca/nvm_00230302.bin':['qca/nvm_00230302.bin','nvm_tlv_tf_1.1.bin','qca6174/nvm_tlv_tf_1.1.bin'],
      'qca/rampatch_00230302.bin':['qca/rampatch_00230302.bin','rampatch_tlv_tf_1.1.tlv','rampatch_tlv_tf_1.1.bin'],
      's5p-mfc-v10.fw':['mfc_fw.bin','s5p-mfc-v10.fw']}
    prefixes=['/vendor/firmware/','/system/vendor/firmware/','/system/etc/firmware/','/vendor/etc/firmware/','/vendor/firmware_mnt/image/']
    manifest={}
    for output,candidates in mappings.items():
        found=next((prefix+candidate for prefix in prefixes for candidate in candidates if exists(prefix+candidate)),None)
        if not found:
            manifest[output]={'status':'not found'}; continue
        target=dest/output; target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_suffix(target.suffix+'.part')
        with temporary.open('wb') as stream:
            subprocess.run(ADB+['exec-out',remote_command('cat '+shlex.quote(found))], stdout=stream, check=True)
        temporary.replace(target)
        size,sha=hash_file(target)
        manifest[output]={'source':found,'size':size,'sha256':sha}
    (ROOT/'cache/firmware-manifest.json').write_text(json.dumps(manifest,indent=2))
    if not (dest/'ath10k/QCA9377/hw1.0/board.bin').is_file(): fail('P580 board.bin not found. Mount System/Vendor in TWRP and retry ./port.sh firmware.')
    print('Firmware ready: cache/firmware/')
def logs():
    # Call from TWRP after a failed kernel boot. Do not power-cycle before collecting pstore.
    recovery(); dest=ROOT/'out/device-logs'; dest.mkdir(parents=True,exist_ok=True)
    for name,cmd in {'dmesg.txt':'dmesg','cmdline.txt':'cat /proc/cmdline','partitions.txt':'cat /proc/partitions'}.items(): (dest/name).write_text(shell(cmd)+'\n')
    if exists('/sys/fs/pstore'): subprocess.run(ADB+['pull','/sys/fs/pstore',str(dest/'pstore')],check=True)
    print('Recovery logs:',dest)
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['info','firmware','backup','install','restore','logs']); parser.add_argument('--erase-android-data',action='store_true'); parser.add_argument('--restore-android-data',action='store_true'); parser.add_argument('--skip-userdata',action='store_true',help='skip the USERDATA backup; Android user data cannot be restored'); args=parser.parse_args()
    if args.skip_userdata and args.command not in ['backup','install']: parser.error('--skip-userdata is only valid for backup or install')
    connect()
    {'info':info,'firmware':firmware,'backup':lambda:backup(args.skip_userdata),'install':lambda:install(args.erase_android_data,args.skip_userdata),'restore':lambda:restore(args.restore_android_data),'logs':logs}[args.command]()
if __name__=='__main__': main()
