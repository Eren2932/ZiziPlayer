"""Extract only the desktop source selected by desktop/current.json. No upstream execution."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import zipfile


def prepare(repo: Path, destination: Path):
    manifest = json.loads((repo / 'desktop/current.json').read_text(encoding='utf-8'))
    relative = PurePosixPath(manifest['source_zip'])
    if relative.is_absolute() or '..' in relative.parts or '\\' in str(relative) or relative.parts[:2] != ('desktop', 'releases'):
        raise ValueError('Source ZIP must be under desktop/releases')
    version = manifest['version']
    if not re.fullmatch(r'[0-9][A-Za-z0-9._+-]*', version):
        raise ValueError('Invalid desktop version')
    expected = manifest['sha256']
    if not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise ValueError('Invalid SHA-256')
    folder = manifest['project_directory']
    if not re.fullmatch(r'ZiziDesktop-[A-Za-z0-9._+-]+', folder):
        raise ValueError('Invalid project directory')
    source = repo.joinpath(*relative.parts)
    if source.stat().st_size > 100 * 1024 * 1024:
        raise ValueError('Source ZIP too large')
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Desktop source SHA-256 mismatch')
    if destination.exists():
        raise ValueError('Extraction destination already exists; refusing overwrite')
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) > 10000 or sum(i.file_size for i in infos) > 100 * 1024 * 1024:
            raise ValueError('Archive extraction limits exceeded')
        seen = set()
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if (path.is_absolute() or PureWindowsPath(name).drive or '\\' in name or ':' in name
                    or '..' in path.parts or not path.parts or path.parts[0] != folder
                    or any(ord(c) < 32 for c in name) or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError('Unsafe archive entry')
            for part in path.parts:
                stem = part.split('.')[0].upper()
                if part.endswith((' ', '.')) or stem in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}:
                    raise ValueError('Unsafe Windows file name')
            key = '/'.join(path.parts).casefold()
            if key in seen:
                raise ValueError('Duplicate archive entry')
            seen.add(key)
        for required in ('settings.gradle.kts', 'build.gradle.kts', 'Build-Desktop.ps1', 'upstream.json'):
            if folder + '/' + required not in archive.namelist():
                raise ValueError('Incomplete desktop source')
        destination.mkdir(parents=True)
        archive.extractall(destination)
    return destination / folder, version


if __name__ == '__main__':
    root, version = prepare(Path.cwd(), Path.cwd() / '_desktop-src')
    if os.getenv('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as out:
            out.write(f'DESKTOP_PROJECT={root.as_posix()}\nDESKTOP_VERSION={version}\n')
    print('Desktop source verified:', root, version)
