"""Exercise the packaged theme adapter with synthetic TOML and isolated user state.

Tests preserve the existing parser, merge, numeric and input-limit behavior.
They require neither a desktop nor an installed theme distribution.
"""
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get('TAM_THEME_PAYLOAD_TEST_SCRIPT', ROOT / 'tam-theme-payload'))

# The limit the contract names, pinned here rather than read from the adapter so
# that raising it in the adapter fails this suite.
LIMIT = 64 * 1024

# The colors.toml every case that needs a palette uses.
COLORS = """\
foreground = "#d8dee9"
background = "#2e3440"
accent = "#81a1c1"
light_foreground = "#adb5c4"
red = "#bf616a"
muted = "#4c566a"
"""

PALETTE = {'foreground': '#d8dee9', 'background': '#2e3440', 'accent': '#81a1c1',
           'accentText': '#adb5c4', 'urgent': '#bf616a', 'muted': '#4c566a'}

# With no colors.toml at all the four roles with a key of their own take their
# own documented default, and the two that name no key of their own (accentText,
# muted) fall back to the resolved foreground instead of to their own default,
# which is why #f4f7f8 never appears in a payload.
DEFAULTS = {'foreground': '#d7dde2', 'background': '#14181c', 'accent': '#8eb6c9',
            'accentText': '#d7dde2', 'urgent': '#c46b6b', 'muted': '#d7dde2'}


def palette_of(foreground, background=None):
    """The palette a colors.toml naming only a foreground (and maybe a
    background) produces: the three roles with no key of their own keep their
    documented defaults, and accentText and muted follow the foreground."""
    return {'foreground': foreground, 'background': background or '#14181c',
            'accent': '#8eb6c9', 'accentText': foreground, 'urgent': '#c46b6b',
            'muted': foreground}


# One supplied key, so the four documented defaults that are not the foreground
# are all visible at once.
ONLY_FOREGROUND = palette_of('#112233')

# The shell.toml that carries every recognized role at once, in the form the
# upstream template writes it: inline comments, quoted strings, aliases, an
# unrelated section, an unknown key, and three wrong types.
SHELL = """\
# A comment the adapter has no reason to keep.
[bar]
background = "#112233"   # an inline comment, likewise
text       = 'rgb(445566)'
nonsense   = "#000000"   # a key no role reads

[hyprland]
active-border = "#aabbcc"

[chain]
one = "chain.two"
two = "#0a0b0c"

[popups]
background   = "transparent"
border       = "rgba(778899aa)"
border-alpha = 0.5

[tooltip]
background = 12            # a number is not a color
text       = ["#ffffff"]   # a list is not a color either
border     = "#fff"        # three digits are not six

[notifications]
countdown = "accent"

[menu]
background          = "#010203"
text                = "text"
border              = "hyprland.active-border"
scrim               = "transparent"
selected-background = "#040506"
selected-text       = "muted"

[polkit]
background   = "#111111"
text         = "foreground"
text-error   = "urgent"
border       = "menu.border"
border-error = "rgba(778899aa)"
accent       = "accent"
scrim        = "transparent"
border-alpha = 0.5

[image-picker]
scrim             = "background"
text              = "foreground"
selected-border   = "accent"
unselected-border = "urgent"

[controls]
normal-color = "#999999"

[lock]
border = "#777777"

[font]
base-size = 14
caption    = 10

[spacing]
scale = 0.8
"""


class ThemePayload(unittest.TestCase):
    def setUp(self):
        scratch = os.environ.get('TAM_TEST_SCRATCH')
        if scratch:
            Path(scratch).mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='tam-theme-payload-', dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / 'home'
        # The XDG path carries a space on purpose: a path with a space in it is
        # the ordinary case for a theme and must not need quoting to work.
        self.config = self.base / 'xdg config'
        self.state = self.base / 'xdg state'
        self.home.mkdir()
        self.config.mkdir()
        self.state.mkdir()
        # The adapter reads the environment for nothing else, and the shebang
        # needs a python3 to find.
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                        XDG_STATE_HOME=str(self.state), PATH='/usr/bin:/bin', TERM='dumb')
        self.assertTrue(os.access(SCRIPT, os.X_OK), SCRIPT)

    # Fixtures

    def write(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body)

    def theme(self, *parts):
        """The default theme directory, under the throwaway XDG state root."""
        return self.state / 'tamlinux' / 'current' / 'theme' / Path(*parts)

    def override(self):
        """The default override file, under the throwaway XDG_CONFIG_HOME."""
        return self.config / 'tamlinux' / 'shell.toml'

    def write_theme(self, colors=None, shell=None, directory=None):
        base = Path(directory) if directory else self.theme()
        for name, body in (('colors.toml', colors), ('shell.toml', shell)):
            if body is not None:
                self.write(base / name, body)

    def write_override(self, body):
        self.write(self.override(), body)

    def state_file(self):
        """The default Text Size state file, under the throwaway XDG_STATE_HOME."""
        return self.state / 'tamlinux' / 'shell.toml'

    def run_cli(self, *argv, **kwargs):
        result = subprocess.run([str(SCRIPT), *argv], env=self.env, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=20, **kwargs)
        return result

    def payload(self, *argv):
        """The parsed payload, with every way to fail checked on the way."""
        result = self.run_cli(*argv)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.count('\n'), 1, result.stdout)
        self.assertTrue(result.stdout.endswith('\n'), result.stdout)
        # Compact means compact: nothing in the object is padded with a space.
        self.assertNotIn(' ', result.stdout)
        return json.loads(result.stdout)

    def assertPayload(self, expected, *argv):
        """One whole object, compared key by key."""
        self.assertEqual(self.payload(*argv), expected)

    # 1. Defaults, and what the adapter knows with no theme at all.

    def test_missing_files_give_the_documented_defaults(self):
        self.assertPayload({'palette': DEFAULTS, 'surfaces': {}, 'style': {}})
        # Pinned as text too, so the separators, the key order, and the single
        # trailing newline are part of the contract and not an accident.
        self.assertEqual(
            self.run_cli().stdout,
            '{"palette":{"foreground":"#d7dde2","background":"#14181c","accent":"#8eb6c9",'
            '"accentText":"#d7dde2","urgent":"#c46b6b","muted":"#d7dde2"},'
            '"surfaces":{},"style":{}}\n')
        # One supplied key leaves the other five at their own defaults, and
        # accentText and muted at the resolved foreground.
        self.write_theme(colors='foreground = "#112233"\n')
        self.assertPayload({'palette': ONLY_FOREGROUND, 'surfaces': {}, 'style': {}})

    # 2. Modern palette keys beat the legacy colorN names for the same role.

    def test_explicit_palette_keys_win_over_conflicting_colorN_keys(self):
        self.write_theme(colors="""\
foreground = "#111111"
background = "#222222"
accent = "#333333"
light_foreground = "#444444"
red = "#555555"
muted = "#666666"
color0 = "#aaaaaa"
color1 = "#bbbbbb"
color4 = "#cccccc"
color7 = "#dddddd"
color8 = "#eeeeee"
""")
        self.assertPayload({'palette': {'foreground': '#111111', 'background': '#222222',
                                        'accent': '#333333', 'accentText': '#444444',
                                        'urgent': '#555555', 'muted': '#666666'},
                            'surfaces': {}, 'style': {}})

    # 3. The legacy names alone still produce the same six roles.

    def test_legacy_colorN_names_populate_the_roles(self):
        self.write_theme(colors="""\
color7 = "#D8DEE9"
color0 = "#2E3440"
color4 = "#81A1C1"
color1 = "#BF616A"
color8 = "#4C566A"
""")
        # Uppercase hex goes out lowercase, accentText falls back to the
        # resolved foreground because light_foreground is absent, and there is
        # no role for a legacy color to be the accent text of.
        self.assertPayload({'palette': {'foreground': '#d8dee9', 'background': '#2e3440',
                                        'accent': '#81a1c1', 'accentText': '#d8dee9',
                                        'urgent': '#bf616a', 'muted': '#4c566a'},
                            'surfaces': {}, 'style': {}})

    # 4. Nothing but a six-digit hex string is a palette color.

    def test_invalid_palette_values_are_ignored_rather_than_guessed(self):
        # One key per role, so the file is valid TOML and every role falls back
        # on its own account rather than because the file would not parse. A
        # repeated key would make it unparseable, and then this would pass for
        # the wrong reason.
        self.write_theme(colors="""\
foreground = ["#112233"]
background = 14
accent = true
light_foreground = "#fff"
red = "#12345678"
muted = "#1234567"
""")
        self.write_theme(shell="""\
[menu]
background = "; touch $HOME/pwned; #"

[bar]
text = 1979-05-27T07:32:00Z
""")
        self.assertPayload({'palette': DEFAULTS, 'surfaces': {}, 'style': {}})
        self.assertEqual(list(self.home.rglob('pwned')), [])

    # 5. Two invocations share nothing.

    def test_a_second_invocation_keeps_nothing_from_the_first(self):
        first = self.base / 'first theme'
        second = self.base / 'second theme'
        self.write_theme(colors=COLORS, directory=first)
        self.write_theme(colors='foreground = "#010101"\nbackground = "#020202"\n', directory=second)
        self.assertPayload({'palette': PALETTE, 'surfaces': {}, 'style': {}},
                           '--theme-dir', str(first), '--override', str(self.base / 'none'))
        # The second palette supplies no accent, urgent, or muted, and none of
        # the first palette survives into it.
        self.assertPayload({'palette': {'foreground': '#010101', 'background': '#020202',
                                        'accent': '#8eb6c9', 'accentText': '#010101',
                                        'urgent': '#c46b6b', 'muted': '#010101'},
                            'surfaces': {}, 'style': {}},
                           '--theme-dir', str(second), '--override', str(self.base / 'none'))
        # The same question asked of the functions themselves, so a cache in the
        # module would show up here too.
        adapter = self.load_adapter()
        self.assertEqual(adapter.build_palette({'accent': '#81a1c1'})['accent'], '#81a1c1')
        self.assertEqual(adapter.build_palette({})['accent'], '#8eb6c9')

    def load_adapter(self):
        """The adapter as an import, which a stateful module could not survive."""
        import importlib.util
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader('tam_theme_payload', str(SCRIPT))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        # No .pyc beside the adapter: a test must not leave anything in bin/.
        written = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = written
        return module

    # 6. shell.toml surfaces, in the shape the upstream template writes them.

    def test_shell_surfaces_resolve_and_nothing_else_leaks(self):
        self.write_theme(colors=COLORS, shell=SHELL)
        self.assertPayload({
            'palette': PALETTE,
            'surfaces': {
                'bar.background': '#112233',
                'bar.text': '#445566',
                'popups.background': '#00000000',
                # rgba(778899aa) is CSS order and becomes Qt order, then the
                # 0.5 companion multiplies alpha aa (170) into 85.
                'popups.border': '#55778899',
                'notifications.countdown': PALETTE['accent'],
                'menu.background': '#010203',
                'menu.text': PALETTE['foreground'],
                'menu.border': '#aabbcc',
                'menu.scrim': '#00000000',
                'menu.selected-background': '#040506',
                'menu.selected-text': PALETTE['muted'],
                'polkit.background': '#111111',
                'polkit.text': PALETTE['foreground'],
                'polkit.text-error': PALETTE['urgent'],
                'polkit.border': '#80aabbcc',
                'polkit.border-error': '#55778899',
                'polkit.accent': PALETTE['accent'],
                'polkit.scrim': '#00000000',
                'image-picker.scrim': PALETTE['background'],
                'image-picker.text': PALETTE['foreground'],
                'image-picker.selected-border': PALETTE['accent'],
                'image-picker.unselected-border': PALETTE['urgent'],
            },
            'style': {'fontBaseSize': 14, 'spacingScale': 0.8},
        })

    # 7. The owned override is merged last and wins key by key.

    def test_the_override_wins_and_a_broken_one_changes_nothing(self):
        base = self.base / 'base'
        self.write_theme(colors=COLORS, directory=base)
        self.write_theme(shell="""\
[popups]
background = "#112233"
text = "#445566"

[menu]
background = "#010203"
text = "#212121"
""", directory=base)
        base_payload = {'palette': PALETTE,
                        'surfaces': {'popups.background': '#112233', 'popups.text': '#445566',
                                     'menu.background': '#010203', 'menu.text': '#212121'},
                        'style': {}}
        argv = ('--theme-dir', str(base))

        # An override that names a role wins it, and may reach into the base
        # shell.toml for the value.
        self.write_override("""\
[menu]
background = "popups.background"
""")
        self.assertPayload({**base_payload, 'surfaces': {
            'popups.background': '#112233', 'popups.text': '#445566',
            'menu.background': '#112233', 'menu.text': '#212121'}}, *argv,
            '--override', str(self.override()))

        # An override that is not TOML at all costs the override and nothing else.
        self.write_override('[menu\nbackground = "#999999"\n')
        self.assertPayload(base_payload, *argv, '--override', str(self.override()))

        # An override that is not UTF-8 costs the override and nothing else.
        self.write_override(b'background = "#999999"\n\xff\xfe')
        self.assertPayload(base_payload, *argv, '--override', str(self.override()))

        # A broken color in the override is an omission, not a silent fallback
        # to the value it replaced, and it costs no other key in that section.
        self.write_override("""\
[menu]
background = 7
border = "no-such-color"
""")
        self.assertPayload({**base_payload, 'surfaces': {
            'popups.background': '#112233', 'popups.text': '#445566',
            'menu.text': '#212121'}}, *argv, '--override', str(self.override()))

    # 8. Aliases resolve; loops, long chains, and dead ends do not.

    def test_aliases_resolve_and_loops_do_not(self):
        def surfaces(shell):
            self.write_theme(colors=COLORS, shell=shell)
            return self.payload('--override', str(self.base / 'none'))['surfaces']

        self.assertEqual(surfaces('[bar]\ntext = "foreground"\n'), {'bar.text': '#d8dee9'})
        self.assertEqual(surfaces('[bar]\ntext = "text"\n'), {'bar.text': '#d8dee9'})
        self.assertEqual(surfaces('[bar]\ntext = "background"\n'), {'bar.text': '#2e3440'})
        self.assertEqual(surfaces('[bar]\ntext = "accent"\n'), {'bar.text': '#81a1c1'})
        self.assertEqual(surfaces('[bar]\ntext = "urgent"\n'), {'bar.text': '#bf616a'})
        self.assertEqual(surfaces('[bar]\ntext = "muted"\n'), {'bar.text': '#4c566a'})
        # An alias into a section the shell owns for other purposes is fine, as
        # long as it ends at a color.
        self.assertEqual(surfaces('[hyprland]\nactive-border = "#445566"\n'
                                  '[bar]\nbackground = "hyprland.active-border"\n'),
                         {'bar.background': '#445566'})
        # Two hops through a chain, and one hop through a surface role, which is
        # a role of its own and lands in the payload as well.
        self.assertEqual(surfaces('[chain]\none = "chain.two"\ntwo = "#0a0b0c"\n'
                                  '[hyprland]\nactive-border = "chain.one"\n'
                                  '[bar]\nbackground = "hyprland.active-border"\n'),
                         {'bar.background': '#0a0b0c'})
        self.assertEqual(surfaces('[menu]\nborder = "#0a0b0c"\n'
                                  '[popups]\nborder = "menu.border"\n'),
                         {'menu.border': '#0a0b0c', 'popups.border': '#0a0b0c'})
        # A name the palette does not have, and a name with no section.
        self.assertEqual(surfaces('[bar]\ntext = "chartreuse"\n'), {})
        self.assertEqual(surfaces('[bar]\ntext = "polkit"\n'), {})
        # A dead end, a section that is not a table, and a target of the wrong type.
        self.assertEqual(surfaces('[bar]\ntext = "chain.absent"\n'), {})
        self.assertEqual(surfaces('[bar]\ntext = "polkit.background"\n'), {})
        self.assertEqual(surfaces('[chain]\nabsent = 7\n[bar]\ntext = "chain.absent"\n'), {})
        self.assertEqual(surfaces('[font]\nbase-size = 12\n[bar]\ntext = "font.base-size"\n'), {})
        # A cycle, and a value that points at itself.
        self.assertEqual(surfaces('[chain]\na = "chain.b"\nb = "chain.a"\n'
                                  '[bar]\ntext = "chain.a"\n'), {})
        self.assertEqual(surfaces('[chain]\na = "chain.a"\n[bar]\ntext = "chain.a"\n'), {})
        # A chain that never ends, and the boundary the contract sets on it: a
        # value may follow sixteen aliases, and the seventeenth is too many.
        self.assertEqual(surfaces(self.chain(16)), {'bar.text': '#0a0b0c'})
        self.assertEqual(surfaces(self.chain(17)), {})

    def chain(self, links):
        """A shell.toml whose bar.text is a chain of `links` aliases deep."""
        hops = {f'h{index}': f'chain.h{index + 1}' for index in range(links - 1)}
        hops[f'h{links - 1}'] = '#0a0b0c'
        body = '\n'.join(f'{key} = "{value}"' for key, value in hops.items())
        return f'[chain]\n{body}\n[bar]\ntext = "chain.h0"\n'

    def test_a_cycle_is_caught_by_name_and_not_by_running_out_of_depth(self):
        # Both guards end a cycle with the same answer, so only the number of
        # lookups tells them apart: a loop caught by name stops at the alias it
        # repeats, one left to the depth limit keeps going until the limit.
        class Counting(dict):
            lookups = 0

            def get(self, key, default=None):
                self.lookups += 1
                return super().get(key, default)

        adapter = self.load_adapter()
        chain = Counting({'a': 'chain.b', 'b': 'chain.a'})
        table = Counting({'chain': chain})
        resolver = adapter.Resolver(table, adapter.build_palette({}))
        self.assertIsNone(resolver.resolve('chain.a'))
        # Each of the two aliases is read once, and the third reference back to
        # the first is refused before it reads anything.
        self.assertLessEqual(chain.lookups, 2, 'the cycle ran past the alias it repeats')

    # 9. An inherited Hyprland gradient is flattened to its first color stop.

    def test_gradient_borders_resolve_to_the_first_stop(self):
        def border(value):
            self.write_theme(colors=COLORS, shell=f'[popups]\nborder = "{value}"\n')
            return self.payload('--override', str(self.base / 'none'))['surfaces']

        self.assertEqual(border('#123456 #abcdef 45deg'), {'popups.border': '#123456'})
        self.assertEqual(border('45deg rgb(123456) rgba(abcdef80)'), {'popups.border': '#123456'})
        self.assertEqual(border('#123456 45deg rgba(abcdef80)'), {'popups.border': '#123456'})
        self.assertEqual(border('#AABBCC #DDEEFF'), {'popups.border': '#aabbcc'})
        self.assertEqual(border('rgba(12345680)'), {'popups.border': '#80123456'})
        self.assertEqual(border('rgb(123456)'), {'popups.border': '#123456'})
        self.assertEqual(border('#12345678'), {'popups.border': '#78123456'})
        self.assertEqual(border('#123456'), {'popups.border': '#123456'})
        self.assertEqual(border('  #123456  '), {'popups.border': '#123456'})
        self.assertEqual(border('transparent'), {'popups.border': '#00000000'})
        self.assertEqual(border('TRANSPARENT'), {'popups.border': '#00000000'})
        # A gradient with no color in it is no color at all.
        self.assertEqual(border('45deg'), {})
        self.assertEqual(border('#fff #000'), {})
        self.assertEqual(border('45deg transparent'), {'popups.border': '#00000000'})

    # 10. Alpha companions multiply, clamp, and never invent a color.

    def test_alpha_companions_clamp_multiply_and_compose(self):
        def surfaces(shell):
            self.write_theme(colors=COLORS, shell=shell)
            return self.payload('--override', str(self.base / 'none'))['surfaces']

        def menu(alpha, color='#123456'):
            return surfaces(f'[menu]\nbackground = "{color}"\nbackground-alpha = {alpha}\n')

        # 0.5 of 255 is 127.5, which rounds up.
        self.assertEqual(menu('0.5'), {'menu.background': '#80123456'})
        self.assertEqual(menu('0.0'), {'menu.background': '#00123456'})
        self.assertEqual(menu('1.0'), {'menu.background': '#123456'})
        # 0.999 of 255 is 254.745, which rounds to a fully opaque byte, so the
        # color comes back in the six-digit form.
        self.assertEqual(menu('0.999'), {'menu.background': '#123456'})
        self.assertEqual(menu('-1'), {'menu.background': '#00123456'})
        self.assertEqual(menu('2'), {'menu.background': '#123456'})
        self.assertEqual(menu('-0.5'), {'menu.background': '#00123456'})
        # The existing alpha is multiplied, not replaced: 128 * 0.5 is 64.
        self.assertEqual(menu('0.5', 'rgba(12345680)'), {'menu.background': '#40123456'})
        self.assertEqual(menu('0.5', '#12345680'), {'menu.background': '#40123456'})
        # Anything that is not a finite number leaves the color alone.
        for alpha in ('"0.5"', 'true', 'nan', 'inf', '-inf', '"nan"'):
            with self.subTest(alpha=alpha):
                self.assertEqual(menu(alpha), {'menu.background': '#123456'})
        # No companion at all is the same as an unusable one.
        self.assertEqual(surfaces('[menu]\nbackground = "#123456"\n'),
                         {'menu.background': '#123456'})
        # The companion is named after the role it belongs to, hyphens and all.
        self.assertEqual(surfaces('[image-picker]\nscrim = "#123456"\nscrim-alpha = 0.5\n'),
                         {'image-picker.scrim': '#80123456'})
        self.assertEqual(surfaces('[menu]\nselected-background = "#040506"\n'
                                  'selected-background-alpha = 0.08\n'),
                         {'menu.selected-background': '#14040506'})
        self.assertEqual(surfaces('[notifications]\nborder = "#123456"\nborder-alpha = 0.25\n'),
                         {'notifications.border': '#40123456'})
        # Upstream documents one border-alpha for both polkit border states,
        # because the two are mutually exclusive in time, so border-error-alpha
        # is a key no one reads.
        self.assertEqual(surfaces('[polkit]\nborder = "#123456"\nborder-error = "#654321"\n'
                                  'border-alpha = 0.5\n'),
                         {'polkit.border': '#80123456', 'polkit.border-error': '#80654321'})
        self.assertEqual(surfaces('[polkit]\nborder-error = "#654321"\nborder-alpha = 1.0\n'
                                  'border-error-alpha = 0.5\n'),
                         {'polkit.border-error': '#654321'})
        # A companion is read from the merged tables, so the override supplies it.
        self.write_theme(colors=COLORS, shell='[menu]\nbackground = "#123456"\n')
        self.write_override('[menu]\nbackground-alpha = 0.5\n')
        self.assertEqual(self.payload()['surfaces'], {'menu.background': '#80123456'})

    # 11. Style numbers are range-checked, and never defaulted.

    def test_style_numbers_are_range_checked_and_never_defaulted(self):
        def style(shell):
            self.write_theme(shell=shell)
            return self.payload('--override', str(self.base / 'none'))['style']

        self.assertEqual(style(''), {})
        self.assertEqual(style('[font]\nbase-size = 12\n[spacing]\nscale = 1.0\n'),
                         {'fontBaseSize': 12, 'spacingScale': 1.0})
        # Both ends of both ranges, and the numbers kept as numbers.
        self.assertEqual(style('[font]\nbase-size = 6\n[spacing]\nscale = 0.5\n'),
                         {'fontBaseSize': 6, 'spacingScale': 0.5})
        self.assertEqual(style('[font]\nbase-size = 48\n[spacing]\nscale = 3\n'),
                         {'fontBaseSize': 48, 'spacingScale': 3})
        self.assertEqual(style('[font]\nbase-size = 13.5\n[spacing]\nscale = 2.25\n'),
                         {'fontBaseSize': 13.5, 'spacingScale': 2.25})
        for value in ('5', '5.9', '48.1', '49', '-6', '0', 'true', 'false', '"12"', 'nan', 'inf'):
            with self.subTest(value=value):
                self.assertEqual(style(f'[font]\nbase-size = {value}\n'), {})
        # A bool is a number to Python, and `scale = true` is 1, which is inside
        # the range: only the type check keeps it out of the payload.
        for value in ('0.49', '3.01', '0', '4', '-1', 'true', 'false', '"1.0"', 'nan', '-inf'):
            with self.subTest(value=value):
                self.assertEqual(style(f'[spacing]\nscale = {value}\n'), {})
        # A section that is not a table, and a key that is not there.
        self.assertEqual(style('font = 12\n'), {})
        self.assertEqual(style('[font]\nsize = 12\n'), {})
        # The override supplies style too, and a broken one does not.
        self.write_theme(shell='[font]\nbase-size = 12\n')
        self.write_override('[font]\nbase-size = 48\n')
        self.assertEqual(self.payload()['style'], {'fontBaseSize': 48})
        self.write_override('[font]\nbase-size = 99\n')
        self.assertEqual(self.payload()['style'], {})

    # 12. Every broken input costs its own file and nothing else.

    def test_broken_inputs_degrade_independently(self):
        empty = {'surfaces': {}, 'style': {}}

        # A shell.toml that is not TOML leaves the foundational colors alone.
        self.write_theme(colors=COLORS, shell='[menu\nbackground = "#123456"\n')
        self.assertPayload({**empty, 'palette': PALETTE})

        # A colors.toml that is not TOML leaves the shell surfaces alone.
        self.write_theme(colors='foreground = "#112233\n', shell='[menu]\nbackground = "#123456"\n')
        self.assertPayload({**empty, 'palette': DEFAULTS,
                            'surfaces': {'menu.background': '#123456'}})

        # Neither a UTF-8 error nor a wrong type is a traceback.
        self.write_theme(colors=COLORS, shell=b'[menu]\nbackground = "#123456"\n\xff\xfe\n')
        self.assertPayload({**empty, 'palette': PALETTE})
        self.write_theme(shell='[menu]\nbackground = "#123456"\n')
        self.assertPayload({**empty, 'palette': PALETTE, 'surfaces': {'menu.background': '#123456'}})

        # A file nobody can read is a file that is not there, and it costs the
        # palette alone: the shell.toml beside it is still read.
        if os.geteuid() == 0:
            self.skipTest('root reads every mode')
        secret = self.theme('colors.toml')
        secret.write_text(COLORS)
        secret.chmod(0o000)
        try:
            self.assertPayload({**empty, 'palette': DEFAULTS,
                                'surfaces': {'menu.background': '#123456'}})
        finally:
            secret.chmod(0o644)

        # An oversize file is empty, even though its first line is a color.
        surviving = {'menu.background': '#123456'}
        self.write(self.theme('colors.toml'),
                   'foreground = "#112233"\n# ' + 'x' * LIMIT + '\n')
        self.assertPayload({**empty, 'palette': DEFAULTS, 'surfaces': surviving})
        # Just under the limit is still read.
        filler = LIMIT - len('foreground = "#112233"\n# \n') - 1
        self.write(self.theme('colors.toml'),
                   'foreground = "#112233"\n# ' + 'x' * filler + '\n')
        self.assertPayload({**empty, 'palette': ONLY_FOREGROUND, 'surfaces': surviving})

        # A directory where a file belongs is not a file, either, and it costs
        # only the file it stands in for.
        for name in ('colors.toml', 'shell.toml'):
            self.theme(name).unlink()
            self.theme(name).mkdir()
        self.assertPayload({'palette': DEFAULTS, 'surfaces': {}, 'style': {}})

    def test_an_oversize_file_is_never_read_past_the_limit(self):
        # A FIFO the writer never closes: a read that stopped at the limit
        # finishes, and one that wanted the whole file would block on the EOF
        # until this test timed out.
        fifo = self.theme('colors.toml')
        fifo.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(fifo)
        body = b'foreground = "#112233"\n# ' + b'x' * LIMIT + b'\n'
        release = threading.Event()

        def feed():
            with open(fifo, 'wb', buffering=0) as handle:
                pending = memoryview(body)
                while pending:
                    pending = pending[os.write(handle.fileno(), pending):]
                release.wait(60)

        writer = threading.Thread(target=feed, daemon=True)
        writer.start()
        try:
            self.assertPayload({'palette': DEFAULTS, 'surfaces': {}, 'style': {}})
        finally:
            release.set()
            writer.join(30)

    def test_paths_with_spaces_are_ordinary_paths(self):
        spaced = self.base / 'a theme dir'
        self.write_theme(colors=COLORS, shell=SHELL, directory=spaced)
        spaced_override = self.base / 'an override file.toml'
        self.write(spaced_override, '[menu]\nbackground = "#0f0f0f"\n')
        expected = self.payload('--theme-dir', str(spaced), '--override', str(spaced_override))
        self.assertEqual(expected['palette'], PALETTE)
        self.assertEqual(expected['style'], {'fontBaseSize': 14, 'spacingScale': 0.8})
        # One changed value is the whole difference from the unspaced run.
        self.write_theme(colors=COLORS, shell=SHELL)
        self.write_override('[menu]\nbackground = "#0f0f0f"\n')
        self.assertEqual(self.payload(), expected)

    # 13. The command line, and the shape of what it does not do.

    def test_defaults_read_the_documented_locations(self):
        self.write_theme(colors=COLORS, shell='[menu]\nbackground = "#112233"\n')
        self.write_override('[menu]\ntext = "#445566"\n')
        self.assertPayload({'palette': PALETTE,
                            'surfaces': {'menu.background': '#112233', 'menu.text': '#445566'},
                            'style': {}})

    def test_theme_default_falls_back_to_home(self):
        del self.env['XDG_STATE_HOME']
        self.write(self.home / '.local' / 'state' / 'tamlinux' / 'current' / 'theme' / 'colors.toml',
                   'foreground = "#123456"\n')
        self.assertEqual(self.payload()['palette']['foreground'], '#123456')

    def test_theme_does_not_read_historical_distribution_state(self):
        self.write(self.home / '.local' / 'state' / 'omarchy' / 'current' / 'theme' / 'colors.toml',
                   'foreground = "#000001"\n')
        self.assertEqual(self.payload()['palette'], DEFAULTS)
        self.write_theme(colors='foreground = "#abcdef"\n')
        self.assertEqual(self.payload()['palette']['foreground'], '#abcdef')

    def test_explicit_paths_beat_the_defaults(self):
        self.write_theme(colors=COLORS)
        self.write_override('[menu]\nbackground = "#111111"\n')
        chosen = self.base / 'chosen theme'
        self.write_theme(colors='foreground = "#010101"\n', directory=chosen)
        chosen_override = self.base / 'chosen override.toml'
        self.write(chosen_override, '[menu]\nbackground = "#020202"\n')
        self.assertPayload({'palette': palette_of('#010101'),
                            'surfaces': {'menu.background': '#020202'}, 'style': {}},
                           '--theme-dir', str(chosen), '--override', str(chosen_override))
        # A theme directory with nothing in it is not an error, and neither is an
        # override path that leads nowhere.
        self.assertPayload({'palette': DEFAULTS, 'surfaces': {}, 'style': {}},
                           '--theme-dir', str(self.base / 'absent theme'),
                           '--override', str(self.base / 'absent override.toml'))

    def test_the_text_size_state_wins_over_the_override(self):
        # Plan 18 step 0.3.2 item 9: Text Size writes machine state, merged
        # last, so the tracked override keeps only the user's own choices.
        self.write_theme(colors=COLORS, shell='[font]\nbase-size = 14\n[spacing]\nscale = 1.5\n')
        self.write_override('[font]\nbase-size = 11\n')
        self.write(self.state_file(), '[font]\nbase-size = 16\n')
        self.assertEqual(self.payload()['style'], {'fontBaseSize': 16, 'spacingScale': 1.5})
        # A state file without the key leaves the override's value.
        self.write(self.state_file(), '[spacing]\nscale = 2\n')
        self.assertEqual(self.payload()['style'], {'fontBaseSize': 11, 'spacingScale': 2})
        # An explicit --state path beats the default, and an absent one is no error.
        chosen = self.base / 'chosen state.toml'
        self.write(chosen, '[font]\nbase-size = 9\n')
        self.assertEqual(self.payload('--state', str(chosen))['style'],
                         {'fontBaseSize': 9, 'spacingScale': 1.5})
        self.assertEqual(self.payload('--state', str(self.base / 'absent.toml'))['style'],
                         {'fontBaseSize': 11, 'spacingScale': 1.5})

    def test_the_state_default_falls_back_to_home(self):
        del self.env['XDG_STATE_HOME']
        self.write(self.home / '.local' / 'state' / 'tamlinux' / 'shell.toml', '[font]\nbase-size = 13\n')
        self.assertEqual(self.payload()['style'], {'fontBaseSize': 13})

    def test_help_is_argparse_usage(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertTrue(result.stdout.startswith('usage: tam-theme-payload [-h]'), result.stdout)
        self.assertIn('--theme-dir', result.stdout)
        self.assertIn('--override', result.stdout)
        self.assertIn('--state', result.stdout)
        # An option it does not have is argparse's business, not a payload.
        self.assertEqual(self.run_cli('--nope').returncode, 2)

    def test_the_adapter_writes_nothing(self):
        self.write_theme(colors=COLORS, shell=SHELL)
        before = self.snapshot(self.base)
        self.payload()
        self.assertEqual(self.snapshot(self.base), before)

    def snapshot(self, root):
        """Every path under a tree with what it holds, so a new file shows up."""
        seen = {}
        for path in sorted(root.rglob('*')):
            if path.is_file() and not path.is_symlink():
                stat = path.stat()
                seen[str(path.relative_to(root))] = (stat.st_size, stat.st_mode)
            else:
                seen[str(path.relative_to(root))] = None
        return seen

    def test_the_adapter_starts_no_process(self):
        if not hasattr(resource, 'RLIMIT_NPROC'):
            self.skipTest('RLIMIT_NPROC is Linux-only')
        self.write_theme(colors='foreground = "#112233"\n')
        ceiling = self.my_process_count()
        self.assertGreater(ceiling, 0)

        def no_fork():
            resource.setrlimit(resource.RLIMIT_NPROC, (ceiling, ceiling))

        # Anything the adapter started would find no room to start.
        result = self.run_cli(preexec_fn=no_fork)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['palette']['foreground'], '#112233')

    def my_process_count(self):
        """How many processes this user is already running."""
        mine = str(os.getuid())
        count = 0
        for entry in os.scandir('/proc'):
            if not entry.name.isdigit():
                continue
            try:
                status = Path(entry.path, 'status').read_text()
            except OSError:
                continue
            if re.search(rf'^Uid:\s+{mine}\s', status, re.M):
                count += 1
        return count

    def test_the_adapter_has_no_way_to_reach_outside_itself(self):
        text = SCRIPT.read_text()
        for forbidden in (r'\bimport\s+subprocess\b', r'\bimport\s+multiprocessing\b',
                          r'\bimport\s+socket\b', r'\bimport\s+urllib\b', r'\bimport\s+http\b',
                          r'\bimport\s+ctypes\b', r'\bimport\s+asyncio\b', r'\bimportlib\b',
                          r'\bos\.(system|popen|spawn|fork|exec|startfile|remove|unlink|rename)\w*\b',
                          r'(?<![.\w])(eval|exec|compile|__import__)\s*\('):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(text, forbidden)
        # Stdlib only, and every file opened for reading.
        self.assertEqual(sorted(set(re.findall(r'^(?:import|from) (\w+)', text, re.M))),
                         ['argparse', 'decimal', 'json', 'math', 'os', 're', 'sys', 'tomllib'])
        self.assertEqual([line.strip() for line in text.splitlines() if 'open(' in line],
                         ["with open(path, 'rb') as handle:"])

    def test_the_script_is_executable_python_with_a_trailing_newline(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK), SCRIPT)
        text = SCRIPT.read_text()
        # Nix replaces the source shebang with its exact Python interpreter.
        self.assertTrue(text.startswith('#!'), text[:40])
        self.assertIn('python3', text.splitlines()[0])
        self.assertTrue(text.endswith('\n'), 'no trailing newline')
        # Compiled in memory, so checking the syntax leaves no .pyc in bin/.
        compile(text, str(SCRIPT), 'exec')



if __name__ == '__main__':
    unittest.main()
