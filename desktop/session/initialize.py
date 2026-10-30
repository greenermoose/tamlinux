#!/usr/bin/env python3
"""Publish absent application/session defaults. Existing files and links win."""
import json
import os
from pathlib import Path
import tempfile


def initialize(assets, environ):
    home = Path(environ['HOME'])
    config = Path(environ.get('XDG_CONFIG_HOME') or home / '.config')
    state = Path(environ.get('XDG_STATE_HOME') or home / '.local/state')
    if any(not p.is_absolute() for p in (home, config, state)):
        raise ValueError('Home and XDG paths must be absolute')
    current = str(state / 'tamlinux/current/theme')
    entries = {}
    for relative, default in [('alacritty/alacritty.toml','alacritty.toml'),
        ('kitty/kitty.conf','kitty.conf'),('foot/foot.ini','foot.ini'),
        ('ghostty/config','ghostty.conf'),
        ('fontconfig/conf.d/99-tamlinux-monospace.conf','fonts.conf')]:
        text = (assets / 'defaults' / default).read_text().replace('~/.local/state/tamlinux/current/theme', current)
        entries[config / relative] = text
    entries[config / 'micro/bindings.json'] = (assets / 'defaults/micro-bindings.json').read_text()
    micro_scheme = config / 'micro/colorschemes/tamlinux.micro'
    # An existing scheme or settings file belongs to the user. Only select the
    # generated scheme automatically when both destinations are absent.
    if not micro_scheme.exists() and not micro_scheme.is_symlink():
        entries[micro_scheme] = None
        entries[config / 'micro/settings.json'] = '{"colorscheme": "tamlinux"}\n'
    # Personal configurations later in imv's search path must not be hidden
    # by a new XDG default. An explicit selection is left to its owner even
    # when it is currently missing. System fallback is deliberately overridden
    # for fresh users so the Tamlinux Escape default is available.
    personal_imv = (home / '.config/imv/config', home / '.imv_config', home / '.imv/config')
    if not environ.get('imv_config') and not any(p.exists() or p.is_symlink() for p in personal_imv):
        entries[config / 'imv/config'] = (assets / 'defaults/imv.conf').read_text()
    entries[config / 'helix/config.toml'] = 'theme = "tamlinux"\n'
    entries[config / 'helix/themes/tamlinux.toml'] = None
    entries[config / 'xdg-terminals.list'] = 'Alacritty.desktop\nfoot.desktop\nkitty.desktop\ncom.mitchellh.ghostty.desktop\n'
    # A user selection wins. These defaults avoid a dependency on any other
    # desktop's system MIME list; every handler belongs to the host contract.
    entries[config / 'mimeapps.list'] = ('[Default Applications]\n'
        'inode/directory=org.gnome.Nautilus.desktop\n'
        'application/pdf=org.gnome.Evince.desktop\n'
        'x-scheme-handler/http=chromium.desktop\n'
        'x-scheme-handler/https=chromium.desktop\n'
        'text/plain=Helix.desktop\n'
        + ''.join(kind + '=imv.desktop\n' for kind in
                  ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp', 'image/tiff'])
        + ''.join(kind + '=mpv.desktop\n' for kind in
                  ['video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/mpeg', 'video/ogg', 'application/ogg']))
    entries[state / 'tamlinux/defaults/editor'] = 'helix\n'
    entries[config / 'tamlinux/hypr/monitors.lua'] = '-- BEGIN fred.monitor managed displays\n-- END fred.monitor managed displays\n'
    written = []
    for target, data in entries.items():
        if target.exists() or target.is_symlink():
            continue
        # Refuse redirected parents; a pre-existing user's file/link remains
        # theirs, but absent defaults never get published through a symlink.
        if any(parent.is_symlink() for parent in target.parents):
            raise ValueError('Symlink parent at default destination')
        target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.tamlinux-default-', dir=target.parent)
        temporary = Path(name)
        try:
            if data is None:
                os.close(fd); fd = -1
                temporary.unlink()
                leaf = 'micro.micro' if target == micro_scheme else 'helix.toml'
                temporary.symlink_to(state / 'tamlinux/current/theme' / leaf)
            else:
                os.write(fd, data.encode()); os.fsync(fd); os.close(fd); fd = -1
            try:
                os.link(temporary, target, follow_symlinks=False)
                written.append(str(target))
            except FileExistsError:
                pass
        finally:
            if fd >= 0: os.close(fd)
            temporary.unlink(missing_ok=True)
    return written


if __name__ == '__main__':
    import sys
    try:
        print(json.dumps({'created': initialize(Path(sys.argv[1]), os.environ)}))
    except (OSError, ValueError, KeyError) as error:
        sys.exit('tam-session-init: '+str(error))
