#!/usr/bin/env python3
"""Build a source archive that unpacks into Omarchy's plugin directory."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'manifest.json').read_text())
destination = ROOT / 'dist'
destination.mkdir(exist_ok=True)
archive = destination / f"omarchy-controller-idle-{manifest['version']}.tar.gz"
with tarfile.open(archive, 'w:gz') as bundle:
    for source in sorted(ROOT.rglob('*')):
        relative = source.relative_to(ROOT)
        if any(part in {'.git', '__pycache__', 'dist'} for part in relative.parts):
            continue
        if source.is_symlink():
            raise SystemExit(f'Refusing to package symlink: {relative}')
        if source.is_file():
            info = bundle.gettarinfo(str(source), f"{manifest['id']}/{relative}")
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with source.open('rb') as content:
                bundle.addfile(info, content)
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix(archive.suffix + '.sha256').write_text(f'{checksum}  {archive.name}\n')
print(archive)
