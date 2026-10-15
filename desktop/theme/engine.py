#!/usr/bin/env python3
"""Owned theme, background, font and branding writers. No inherited fallback.

Generated themes are published only after validation. Private journals preserve
original bytes and link identities before writers run, and restore on failure.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import uuid
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

HOME = Path.home()
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config')
STATE = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'tamlinux'
CACHE = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'tamlinux'
CURRENT = STATE / 'current'
ASSETS = Path(os.environ.get('TAMLINUX_ASSETS_DIR') or Path(__file__).resolve().parents[1] / 'assets')
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}

def run(command, *args, check=True, capture=False, env=None):
    return subprocess.run([command, *map(str, args)], check=check,
                          stdout=subprocess.PIPE if capture else None,
                          text=True, env=env, timeout=45)

def name(value):
    value = re.sub(r'<[^>]+>', '', value).lower().replace(' ', '-')
    if not re.fullmatch(r'[a-z0-9_][a-z0-9._+-]{0,127}', value):
        raise ValueError('invalid theme name')
    return value

def atomic(path, data=None, link=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / ('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        if link is not None:
            temporary.symlink_to(link)
        else:
            temporary.write_bytes(data.encode() if isinstance(data, str) else data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)

class Journal:
    def __init__(self, kind, paths):
        base = STATE / 'settings-recovery'
        base.mkdir(parents=True, exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix=kind + '.', dir=base))
        self.entries = []
        for index, path in enumerate(dict.fromkeys(map(Path, paths))):
            entry = {'path': str(path), 'present': path.exists() or path.is_symlink()}
            if entry['present']:
                saved = self.directory / str(index)
                if path.is_symlink():
                    entry['symlink'] = os.readlink(path)
                    # Preserve the original link and what its reader sees.
                if path.is_dir():
                    shutil.copytree(path, saved, symlinks=True)
                    entry['directory'] = True
                elif path.exists():
                    shutil.copy2(path, saved)
                entry['saved'] = str(index) if saved.exists() else None
            self.entries.append(entry)
        self.status('prepared')

    def status(self, status):
        atomic(self.directory / 'manifest.json', json.dumps(
            {'schema': 1, 'status': status, 'files': self.entries}, indent=2) + '\n')

    def restore(self):
        for entry in reversed(self.entries):
            path = Path(entry['path'])
            remove(path)
            if entry['present']:
                path.parent.mkdir(parents=True, exist_ok=True)
                if 'symlink' in entry:
                    atomic(path, link=entry['symlink'])
                elif entry.get('directory'):
                    shutil.copytree(self.directory / entry['saved'], path, symlinks=True)
                else:
                    shutil.copy2(self.directory / entry['saved'], path)
        self.status('restored-after-failure')

@contextlib.contextmanager
def transaction(kind, paths):
    journal = Journal(kind, paths)
    try:
        yield journal
    except BaseException:
        journal.restore()
        raise
    else:
        journal.status('completed')

def selected():
    path = CURRENT / 'theme.name'
    return name(path.read_text().strip()) if path.exists() else 'tokyo-night'

def themes():
    return sorted({p.name for base in (ASSETS / 'themes', CONFIG / 'tamlinux/themes')
                   if base.is_dir() for p in base.iterdir() if p.is_dir()
                   and re.fullmatch(r'[a-z0-9_][a-z0-9._+-]{0,127}', p.name)})

def images(*directories):
    return sorted({p.absolute() for base in directories if base.is_dir()
                   for p in base.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}, key=str)

def background_paths():
    return images(CURRENT / 'theme/backgrounds', CONFIG / 'tamlinux/backgrounds' / selected())

def retired_background(path, theme):
    """Only retire bundled selections, never a same-named personal image."""
    retired = json.loads((ASSETS / 'retired-backgrounds.json').read_text())['backgrounds']
    if theme + '/backgrounds/' + path.name not in retired:
        return False
    roots = [STATE / 'theme-generations', ASSETS / 'themes']
    # Prior immutable package outputs remain valid rollback inputs.
    parts = path.parts
    packaged = (len(parts) > 4 and parts[:3] == ('/', 'nix', 'store')
                and '/share/tamlinux/assets/themes/' in str(path))
    return packaged or any(path.is_relative_to(root) for root in roots)

def sync_shell():
    # A stopped shell is valid during staging/fresh provisioning.
    for service, method in (('theme', 'reload'), ('background', 'refresh')):
        try: run('tam-shell', '-q', service, method, check=False)
        except (OSError, subprocess.SubprocessError): pass

def stage_tree(source, destination, restricted=False):
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name.startswith('.'):
            continue
        if restricted and (item.is_symlink() or item.suffix == '.lua' or item.name in
                           {'alacritty.toml', 'foot.ini', 'ghostty.conf', 'kitty.conf', 'vscode.json'}):
            continue
        target = destination / item.name
        if item.is_dir():
            stage_tree(item, target, restricted)
        elif item.is_file():
            shutil.copyfile(item, target)

ADAPTERS = ['foot', 'tmux', 'gnome', 'browser', 'pi', 'claude', 't3code', 'vscode', 'obsidian', 'keyboard']

def application_paths():
    paths = [CONFIG / 'Code/User/settings.json', CONFIG / 'Code - Insiders/User/settings.json',
             CONFIG / 'VSCodium/User/settings.json', CONFIG / 'Cursor/User/settings.json',
             *[HOME / base / 'extensions' / leaf for base in ('.vscode', '.vscode-insiders', '.vscode-oss', '.cursor') for leaf in ('tam-theme', 'extensions.json', '.obsolete')],
             HOME / '.pi/agent/themes/tam-system.json', HOME / '.pi/agent/settings.json',
             Path(os.environ.get('CLAUDE_CONFIG_DIR') or HOME / '.claude') / 'themes/tamlinux.json',
             Path(os.environ.get('CLAUDE_CONFIG_DIR') or HOME / '.claude') / 'settings.json',
             Path(os.environ.get('T3CODE_HOME') or HOME / '.t3') / 'userdata/themes/tamlinux.json']
    obsidian = CONFIG / 'obsidian/obsidian.json'
    if obsidian.exists():
        vaults = json.loads(obsidian.read_text()).get('vaults', {}).values()
        paths += [Path(v['path']) / '.obsidian/themes/Tamlinux' for v in vaults]
    return paths

def set_theme(value, refresh=False, apply=True):
    theme = name(value)
    builtin, user = ASSETS / 'themes' / theme, CONFIG / 'tamlinux/themes' / theme
    if not builtin.is_dir() and not user.is_dir():
        raise ValueError(f'theme {theme!r} does not exist')
    generations = STATE / 'theme-generations'
    generations.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=theme + '.', dir=generations))
    try:
        if builtin.is_dir(): stage_tree(builtin, stage)
        if user.is_dir():
            restricted = (user / '.git').exists()
            stage_tree(user, stage, restricted)
            if restricted and not (stage / 'colors.toml').exists() and (user / 'alacritty.toml').is_file() and not (user / 'alacritty.toml').is_symlink():
                with tempfile.TemporaryDirectory() as scratch:
                    scratch = Path(scratch)
                    shutil.copyfile(user / 'alacritty.toml', scratch / 'alacritty.toml')
                    run('tam-theme-colors-from-alacritty', scratch)
                    if (scratch / 'colors.toml').exists(): shutil.copyfile(scratch / 'colors.toml', stage / 'colors.toml')
        run('tam-theme-colors-from-alacritty', stage)
        colors = tomllib.loads((stage / 'colors.toml').read_text())
        for key in ('background', 'foreground'):
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', colors.get(key, colors.get('color0' if key == 'background' else 'color7', ''))):
                raise ValueError('theme requires a valid foreground and background')
        run('tam-theme-set-templates', env=dict(os.environ, TAMLINUX_THEME_STAGE=str(stage)))
        for item in stage.glob('*'):
            if item.suffix in {'.toml', '.ini', '.json', '.conf', '.lua', '.theme', '.css'} and '{{' in item.read_text():
                raise ValueError(f'unresolved template in {item.name}')
        paths = [CURRENT / 'theme', CURRENT / 'theme.name', CURRENT / 'background'] + (application_paths() if apply else [])
        with transaction('theme', paths):
            # Old actual directories are saved before converting to the stable
            # generated-theme link; no inherited folder is read or deleted.
            if (CURRENT / 'theme').is_dir() and not (CURRENT / 'theme').is_symlink():
                remove(CURRENT / 'theme')
            atomic(CURRENT / 'theme', link=stage)
            atomic(CURRENT / 'theme.name', theme + '\n')
            old = (CURRENT / 'background').resolve()
            if not refresh or retired_background(old, theme):
                choices = background_paths()
                if choices:
                    old = (CURRENT / 'background').resolve()
                    index = next((i for i,p in enumerate(choices) if p.resolve() == old), -1)
                    atomic(CURRENT / 'background', link=choices[(index + 1) % len(choices)])
            if apply and not os.environ.get('TAMLINUX_THEME_OFFLINE'):
                for adapter in ADAPTERS: run('tam-theme-set-' + adapter, env=dict(os.environ, TAMLINUX_THEME_JOURNALED='1'))
                for app in ('terminal', 'hyprctl', 'btop', 'opencode', 'helix'):
                    run('tam-restart-' + app, check=False)
                run('tam-hook', 'theme-set', theme)
        if apply: sync_shell()
    except BaseException:
        # Preserve a published generation for forensic/recovery use. Unpublished
        # staging is disposable and cannot be the target of a saved selection.
        if (CURRENT / 'theme').resolve() != stage:
            remove(stage)
        if apply: sync_shell()
        raise

def set_background(value):
    path = Path(value).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError('background must be an image file')
    with transaction('background', [CURRENT / 'background']):
        atomic(CURRENT / 'background', link=path)
    run('tam-shell', '-q', 'background', 'set', path, check=False)

def install_theme(url):
    if not url:
        url = run('gum', 'input', '--placeholder=Git repo URL', capture=True).stdout.strip()
    if not url: return
    if not (re.fullmatch(r'https://[^\s]+', url) or re.fullmatch(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+:[^\s]+', url)) or 'omarchy.org' in url.lower():
        raise ValueError('expected an independent HTTPS or SSH git URL')
    theme = name(re.sub(r'^(?:tamlinux-|omarchy-)|-theme$', '', url.rsplit('/', 1)[-1].removesuffix('.git')))
    base = CONFIG / 'tamlinux/themes'; base.mkdir(parents=True, exist_ok=True)
    destination = base / theme
    if destination.exists() or destination.is_symlink():
        raise ValueError('theme already exists; preserve/remove it before replacement')
    with tempfile.TemporaryDirectory(prefix='.install-', dir=base) as scratch:
        clone = Path(scratch) / 'theme'
        run('git', '-c', 'protocol.ext.allow=never', '-c', 'protocol.file.allow=never', 'clone', '--', url, clone)
        shutil.move(clone, destination)
    try:
        set_theme(theme)
    except BaseException:
        # Keep the failed import for inspection; never replace a working install.
        raise

def font_set(family):
    if not family or any(c in family for c in '\r\n\0'):
        raise ValueError('invalid font family')
    families = run('fc-list', '-f', '%{family}\n', capture=True).stdout.replace(',', '\n').splitlines()
    if family.casefold() not in {f.strip().casefold() for f in families}:
        raise ValueError(f'font {family!r} is not installed')
    paths = [CONFIG / 'alacritty/alacritty.toml', CONFIG / 'kitty/kitty.conf', CONFIG / 'ghostty/config', CONFIG / 'foot/foot.ini', CONFIG / 'fontconfig/conf.d/99-tamlinux-monospace.conf', CONFIG / 'fontconfig/fonts.conf']
    quoted = json.dumps(family, ensure_ascii=False)
    with transaction('font', paths):
        for path in paths[:4]:
            if not path.exists(): continue
            text = path.read_text()
            if path.suffix == '.toml': text = re.sub(r'(?m)(\bfamily\s*=\s*)"(?:\\.|[^"\\\n])*"', lambda m:m[1]+quoted, text)
            elif path.name == 'kitty.conf':
                text, n = re.subn(r'(?m)^\s*font_family\s+.*$', lambda m:'font_family '+family, text)
                if not n: text += '\nfont_family '+family+'\n'
            elif path.name == 'config':
                text, n = re.subn(r'(?m)^\s*font-family\s*=.*$', lambda m:'font-family = '+quoted, text)
                if not n: text += '\nfont-family = '+quoted+'\n'
            else:
                foot_family = family.replace('\\', '\\\\').replace(':', '\\:')
                text = re.sub(r'(?m)^font=(?:\\.|[^:\n])*', lambda m:'font='+foot_family, text)
            atomic(path, text)
        atomic(paths[-2], '<?xml version="1.0"?>\n<fontconfig><match target="pattern"><test name="family" qual="any"><string>monospace</string></test><edit name="family" mode="prepend_first" binding="strong"><string>'+escape(family)+'</string></edit></match></fontconfig>\n')
        # Apply the owned rule after any existing user matches. Preserve the
        # unrelated fontconfig tree, and reject malformed configuration before
        # committing a selection rather than silently discarding preferences.
        if paths[-1].exists():
            parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
            tree = ET.fromstring(paths[-1].read_text(), parser=parser)
            if tree.tag != 'fontconfig': raise ValueError('expected fontconfig root')
        else:
            tree = ET.Element('fontconfig')
            default = ET.SubElement(tree, 'include', {'ignore_missing': 'yes'})
            default.text = 'conf.d'
        for node in list(tree):
            if node.tag == 'include' and node.text == 'conf.d/99-tamlinux-monospace.conf': tree.remove(node)
        node = ET.SubElement(tree, 'include', {'ignore_missing': 'yes'})
        node.text = 'conf.d/99-tamlinux-monospace.conf'
        atomic(paths[-1], '<?xml version="1.0"?>\n' + ET.tostring(tree, encoding='unicode') + '\n')
    run('tam-restart-terminal', check=False)
    run('tam-restart-shell', check=False)
    run('tam-hook', 'font-set', family)

def branding(target, operation, image=None):
    destination = CONFIG / 'tamlinux/branding' / (target + '.txt')
    with transaction('branding-' + target, [destination]):
        if operation == 'reset':
            atomic(destination, (ASSETS / 'branding' / (target + '.txt')).read_bytes())
        elif operation == 'text':
            if not destination.exists(): atomic(destination, (ASSETS / 'branding' / (target + '.txt')).read_bytes())
            run('tam-launch-editor', destination)
        elif operation == 'image':
            if image is None:
                image = run('tam-file-select', '--title', 'Pick PNG or SVG', '--extensions', 'png svg', capture=True).stdout.strip()
            if not image: return
            arguments = ['--width', '54', '--height', '26'] if target == 'about' else []
            run('tam-transcode-ascii', image, destination, *arguments)
        else: raise ValueError('expected text, image or reset')
    run('tam-launch-about' if target == 'about' else 'tam-launch-screensaver', *([] if target == 'about' else ['force']), check=False)

def main():
    action, *args = sys.argv[1:]
    os.umask(0o077)
    CURRENT.mkdir(parents=True, exist_ok=True)
    mutating = action in {'initialize', 'set', 'refresh', 'bg-set', 'bg-next', 'remove', 'install', 'font-set', 'branding-about', 'branding-screensaver'}
    with (open(CURRENT / '.theme.lock', 'a') if mutating else contextlib.nullcontext()) as lock:
        if mutating: fcntl.flock(lock, fcntl.LOCK_EX)
        if action == 'initialize' and not args:
            # Initialization owns only absent fresh state. Existing selections,
            # even dangling links, require explicit recovery/user action.
            if not any(path.exists() or path.is_symlink() for path in (CURRENT / 'theme', CURRENT / 'theme.name')):
                background = CURRENT / 'background'
                set_theme('tokyo-night', refresh=background.exists() or background.is_symlink(), apply=False)
        elif action == 'journal' and not args: print(Journal('theme-application', application_paths()).directory)
        elif action == 'set' and len(args) == 1: set_theme(args[0])
        elif action == 'refresh' and not args: set_theme(selected(), refresh=True)
        elif action == 'current' and not args: print(selected().replace('-', ' ').title())
        elif action == 'list' and not args: print('\n'.join(t.replace('-', ' ').title() for t in themes()))
        elif action == 'bg-set' and len(args) == 1: set_background(args[0])
        elif action == 'bg-next' and not args:
            choices = background_paths()
            if not choices: raise ValueError('no backgrounds for current theme')
            old = (CURRENT / 'background').resolve()
            index = next((i for i,p in enumerate(choices) if p.resolve() == old), -1)
            set_background(choices[(index + 1) % len(choices)])
        elif action == 'bg-install' and not args:
            path = CONFIG / 'tamlinux/backgrounds' / selected(); path.mkdir(parents=True, exist_ok=True)
            run('xdg-open', path)
        elif action == 'bg-switcher' and not args:
            run('tam-menu-images', '--selected', (CURRENT / 'background').resolve(), CURRENT / 'theme/backgrounds', CONFIG / 'tamlinux/backgrounds' / selected())
        elif action == 'switcher' and args in ([], ['--preload']):
            # Keep preview URLs alive after --preload returns. Picker readers
            # use immutable signature directories; concurrent queries cannot
            # replace or delete images another picker is still rendering.
            rows = []
            for theme in themes():
                for base in (CONFIG / 'tamlinux/themes', ASSETS / 'themes'):
                    source = base / theme
                    candidates = images(source) or images(source / 'backgrounds')
                    if candidates:
                        preview = next((p for p in candidates if p.stem == 'preview'), candidates[0])
                        stat = preview.stat()
                        rows.append((theme, preview, stat.st_size, stat.st_mtime_ns))
                        break
            signature = hashlib.sha256(repr(rows).encode()).hexdigest()
            previews = CACHE / 'theme-picker' / signature
            previews.mkdir(parents=True, exist_ok=True)
            for theme, preview, *_ in rows:
                link = previews / (theme + preview.suffix)
                if not link.is_symlink(): atomic(link, link=preview)
            run('tam-menu-images', '--print-name', '--show-labels', '--filterable', '--lazy-thumbnails', '--selected', next(iter(previews.glob(selected()+'.*')), ''), *args, previews)
        elif action == 'remove' and len(args) <= 1:
            if not args and not (CONFIG/'tamlinux/themes').is_dir(): raise ValueError('no extra themes installed')
            theme = name(args[0] if args else run('tam-menu-select', 'Remove extra theme', *[p.name for p in (CONFIG/'tamlinux/themes').iterdir() if p.is_dir()], capture=True).stdout.strip())
            path = CONFIG / 'tamlinux/themes' / theme
            if not path.exists(): raise ValueError('no user theme by that name')
            if theme == selected(): set_theme('tokyo-night' if theme != 'tokyo-night' else next(t for t in themes() if t != theme))
            Journal('theme-remove', [path]); remove(path)
        elif action == 'install' and len(args) <= 1: install_theme(args[0] if args else '')
        elif action == 'font-set' and len(args) == 1: font_set(args[0])
        elif action in ('branding-about', 'branding-screensaver') and len(args) in (1,2): branding(action.removeprefix('branding-'), args[0], args[1] if len(args) == 2 else None)
        else: raise ValueError('invalid arguments for tam-theme-'+action)

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, ET.ParseError, subprocess.SubprocessError, StopIteration) as error:
        sys.exit(f'tamlinux theme: {error}')
