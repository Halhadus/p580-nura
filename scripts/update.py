#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Update the installed Mobian through TWRP; never rewrite USERDATA."""
import json, re, shlex, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path
import device as d

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'out'
MOUNT = '/tmp/p580-mobian-root'
BACK = OUT/'update-backup'
FILES = ['EFI/BOOT/BOOTAA64.EFI', 'dtb/exynos/exynos7870-gtanotexlwifi.dtb', 'etc/wireplumber/wireplumber.conf.d/51-p580-alsa-format.conf']

def sha(path): return d.hash_file(path)[1]
def adb(*args): return subprocess.run(d.ADB+list(args), check=True)
def shell(command): return d.shell(command)
def q(value): return shlex.quote(str(value))
def atomic_json(path, value):
    temp = path.with_suffix('.part'); temp.write_text(json.dumps(value, indent=2)+'\n'); temp.replace(path)

def package():
    subprocess.run([sys.executable, str(ROOT/'scripts/check_bootimg.py'), str(OUT/'boot-p580.img')], check=True)
    config = (OUT/'kernel.config').read_text()
    for symbol in ['CPU_FREQ', 'CPUFREQ_DT', 'CPU_THERMAL', 'DRM_PANFROST']:
        if f'CONFIG_{symbol}=y' not in config: sys.exit('Required kernel feature is disabled: '+symbol)
    release = (OUT/'linux/include/config/kernel.release').read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9._+-]+-p580', release): sys.exit('A P580 kernel release is required.')
    record = json.loads((ROOT/'backup/index.json').read_text())
    source = OUT/'modules/lib/modules'/release
    if not source.is_dir(): sys.exit('Kernel modules are missing.')
    subprocess.run([sys.executable, str(ROOT/'scripts/apply_addresses.py'), str(ROOT), str(OUT/'p580.dtb')], check=True)
    with tempfile.TemporaryDirectory(prefix='update-package-', dir=OUT) as temporary:
        stage = Path(temporary)
        files = {'boot-p580.img': OUT/'boot-p580.img', FILES[0]: OUT/'linux/arch/arm64/boot/vmlinuz.efi', FILES[1]: OUT/'p580.dtb', FILES[2]: ROOT/'config/overlay'/FILES[2]}
        files.update({str(Path('usr/lib/modules')/release/p.relative_to(source)): p for p in source.rglob('*') if p.is_file() and not p.is_symlink()})
        for name, src in files.items():
            dest = stage/name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dest)
        metadata = {'release': release, 'cid': record['cid'], 'partitions': record['partitions'], 'recovery_sha256': record['files']['RECOVERY']['sha256_raw'], 'files': {name: sha(stage/name) for name in sorted(files)}}
        atomic_json(stage/'manifest.json', metadata)
        target = OUT/'p580-update.tar.gz'
        with tarfile.open(str(target)+'.part', 'w:gz', compresslevel=1) as archive:
            for p in sorted(stage.rglob('*')):
                if p.is_file(): archive.add(p, arcname=str(p.relative_to(stage)), recursive=False)
        Path(str(target)+'.part').replace(target)
        (OUT/'p580-update.sha256').write_text(sha(target)+'\n')
    print('Update package ready: out/p580-update.tar.gz')

def load_payload():
    payload = OUT/'p580-update.tar.gz'
    if sha(payload) != (OUT/'p580-update.sha256').read_text().strip(): sys.exit('Update archive checksum mismatch.')
    temporary = tempfile.TemporaryDirectory(prefix='update-unpack-', dir=OUT)
    stage = Path(temporary.name)
    with tarfile.open(payload) as archive:
        for member in archive.getmembers():
            if not member.isfile() or member.name.startswith('/') or '..' in Path(member.name).parts: sys.exit('Invalid path or file type in the update archive.')
        archive.extractall(stage, filter='data')
    meta = json.loads((stage/'manifest.json').read_text())
    release = meta['release']
    if not re.fullmatch(r'[A-Za-z0-9._+-]+-p580', release): sys.exit('Invalid kernel release in the update package.')
    required = {'boot-p580.img', *FILES}
    if not required.issubset(meta['files']): sys.exit('The update manifest is missing required files.')
    for name, digest in meta['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts: sys.exit('Invalid update path: '+name)
        if name not in ['boot-p580.img', FILES[0], FILES[1], FILES[2]] and not name.startswith('usr/lib/modules/'+release+'/'): sys.exit('Unexpected update path: '+name)
        if sha(stage/name) != digest: sys.exit('Update file checksum mismatch: '+name)
    return temporary, stage, meta

def check_device(meta, parts):
    if d.cid() != meta['cid']: sys.exit('The update package belongs to a different eMMC.')
    for name in ['BOOT', 'RECOVERY', 'USERDATA', 'EFS']:
        if parts[name] != meta['partitions'][name]: sys.exit('Partition changed: '+name)
    if d.remote_hash(parts['RECOVERY']['path'], parts['RECOVERY']['size']) != meta['recovery_sha256']: sys.exit('RECOVERY has changed; update stopped.')

def mount_root(parts):
    d.unmount_data(parts['USERDATA']['path'])
    shell('mkdir -p '+q(MOUNT)+' && mount -t ext4 '+q(parts['USERDATA']['path'])+' '+q(MOUNT))
    try:
        if not d.exists(MOUNT+'/etc/mobian_version') and not d.exists(MOUNT+'/etc/os-release'): sys.exit('Mobian rootfs not found.')
        for path in FILES[:2]:
            if not d.exists(MOUNT+'/'+path): sys.exit('Installed Mobian boot file is missing: '+path)
    except BaseException:
        shell('umount '+q(MOUNT)); raise

def backup_current(meta, parts):
    if (BACK/'index.json').is_file():
        saved = json.loads((BACK/'index.json').read_text())
        if saved['cid'] != meta['cid'] or saved['partitions'] != parts or saved['release'] != meta['release']: sys.exit('The existing update backup does not match this device, layout or release.')
        verify_backup(saved)
        print('Existing update backup verified:', BACK, flush=True)
        return
    if BACK.exists(): sys.exit('Incomplete update backup: out/update-backup. No partitions were written.')
    BACK.mkdir()
    saved = {'cid': meta['cid'], 'partitions': parts, 'release': meta['release'], 'files': {}, 'absent': [], 'modules_sha256': None}
    saved['boot'] = d.raw_read(parts['BOOT']['path'], BACK/'BOOT.img.gz', parts['BOOT']['size'])
    for name in FILES:
        if not d.exists(MOUNT+'/'+name): saved['absent'].append(name); continue
        dest = BACK/name; dest.parent.mkdir(parents=True, exist_ok=True)
        adb('pull', MOUNT+'/'+name, str(dest)); saved['files'][name] = sha(dest)
    module_path = 'usr/lib/modules/'+meta['release']
    if d.exists(MOUNT+'/'+module_path):
        archive = BACK/'modules.tar.gz'
        archive.write_bytes(d.run('exec-out', 'tar -czf - -C '+q(MOUNT)+' '+q(module_path), text=False))
        saved['modules_sha256'] = sha(archive)
    atomic_json(BACK/'index.json', saved)
    verify_backup(saved)
    print('Update backup complete:', BACK, flush=True)

def verify_backup(saved):
    if not re.fullmatch(r'[0-9][A-Za-z0-9._+-]*', saved['release']): sys.exit('Invalid kernel release in the backup.')
    if saved['modules_sha256'] is not None:
        archive = BACK/'modules.tar.gz'
        if sha(archive) != saved['modules_sha256']: sys.exit('Module backup checksum mismatch.')
        prefix = 'usr/lib/modules/'+saved['release']
        with tarfile.open(archive) as source:
            for member in source.getmembers():
                if member.name != prefix and not member.name.startswith(prefix+'/'): sys.exit('Invalid path in the module backup.')
                if member.name.startswith('/') or '..' in Path(member.name).parts: sys.exit('Invalid path in the module backup.')
    size, digest = d.hash_file(BACK/'BOOT.img.gz', compressed=True)
    if size != saved['boot']['size'] or digest != saved['boot']['sha256_raw']: sys.exit('Corrupt BOOT update backup.')
    if any(name not in FILES for name in list(saved['files'])+saved['absent']): sys.exit('Invalid backup path.')
    for name, digest in saved['files'].items():
        if sha(BACK/name) != digest: sys.exit('Update backup checksum mismatch: '+name)

def verify_remote(base, files):
    names = list(files)
    for offset in range(0, len(names), 40):
        group = names[offset:offset+40]
        output = shell('cd '+q(base)+' && sha256sum '+' '.join(q(name) for name in group))
        found = {}
        for row in output.splitlines():
            digest, name = row.split(None, 1); found[name.lstrip('*')] = digest
        if found != {name: files[name] for name in group}: sys.exit('Device file verification failed; stay in TWRP.')

def install():
    temporary, stage, meta = load_payload()
    mounted = False
    try:
        d.connect(); d.recovery(); parts = d.partitions(); check_device(meta, parts)
        mount_root(parts); mounted = True
        backup_current(meta, parts)
        remote = MOUNT+'/var/lib/p580-update/stage'
        shell('mkdir -p '+q(remote))
        adb('push', str(OUT/'p580-update.tar.gz'), remote+'/payload.tar.gz')
        if shell('sha256sum '+q(remote+'/payload.tar.gz')).split()[0] != sha(OUT/'p580-update.tar.gz'): sys.exit('Update transfer checksum mismatch; BOOT was not written.')
        shell('cd '+q(remote)+' && tar -xzf payload.tar.gz')
        verify_remote(remote, meta['files'])
        image = stage/'boot-p580.img'; size, digest = d.hash_file(image)
        if size > parts['BOOT']['size']: sys.exit('The boot image exceeds the BOOT partition size.')
        # Calibrating U-Boot goes first: a power loss must not pair the old loader with enabled static OPPs.
        if d.remote_hash(parts['BOOT']['path'], size) != digest: d.stream_write(parts['BOOT']['path'], image, size, digest)
        names = [name for name in meta['files'] if name.startswith('usr/lib/modules/')]+[FILES[1], FILES[0], FILES[2]]
        commands = ['set -e']
        for name in names:
            dest = MOUNT+'/'+name
            mode = '644'
            commands += ['mkdir -p '+q(str(Path(dest).parent)), 'cp '+q(remote+'/'+name)+' '+q(dest+'.p580-new'), 'chmod '+mode+' '+q(dest+'.p580-new'), 'mv -f '+q(dest+'.p580-new')+' '+q(dest)]
        commands += ['sync']
        script = stage/'install.sh'; script.write_text('\n'.join(commands)+'\n')
        adb('push', str(script), remote+'/install.sh'); shell('sh '+q(remote+'/install.sh'))
        verify_remote(MOUNT, {name: meta['files'][name] for name in names})
        shell('sync && rm -rf '+q(remote))
        print('Update verified. Run adb reboot to start Mobian.')
    finally:
        if mounted: shell('sync && umount '+q(MOUNT))
        temporary.cleanup()

def rollback():
    saved = json.loads((BACK/'index.json').read_text()); verify_backup(saved)
    d.connect(); d.recovery(); parts = d.partitions()
    if d.cid() != saved['cid'] or parts != saved['partitions']: sys.exit('Rollback device or partition layout mismatch.')
    mounted = False
    try:
        mount_root(parts); mounted = True
        module_path = MOUNT+'/usr/lib/modules/'+saved['release']
        if saved['modules_sha256'] is not None:
            remote = '/tmp/p580-rollback-modules.tar.gz'
            adb('push', str(BACK/'modules.tar.gz'), remote)
            if shell('sha256sum '+q(remote)).split()[0] != saved['modules_sha256']: sys.exit('Module rollback transfer checksum mismatch.')
            shell('rm -rf '+q(module_path)+' && tar -xzf '+q(remote)+' -C '+q(MOUNT)+' && sync && rm -f '+q(remote))
        else: shell('rm -rf '+q(module_path))
        for name in saved['files']:
            dest = MOUNT+'/'+name
            shell('mkdir -p '+q(str(Path(dest).parent)))
            adb('push', str(BACK/name), dest+'.p580-rollback')
            mode = '644'
            shell('chmod '+mode+' '+q(dest+'.p580-rollback')+' && mv -f '+q(dest+'.p580-rollback')+' '+q(dest))
        for name in saved['absent']: shell('rm -f '+q(MOUNT+'/'+name))
        verify_remote(MOUNT, saved['files'])
        meta = saved['boot']; d.stream_write(parts['BOOT']['path'], BACK/'BOOT.img.gz', meta['size'], meta['sha256_raw'], compressed=True)
        print('Rollback complete. Run adb reboot to start Mobian.')
    finally:
        if mounted: shell('sync && umount '+q(MOUNT))

if __name__ == '__main__':
    {'package': package, 'install': install, 'rollback': rollback}[sys.argv[1]]()
