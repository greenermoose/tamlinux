"""Evaluate the real Lua defaults with a recording compositor, never a live one."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'session'
LUA = shutil.which('lua')
RECORDER = r'''
local function record(name, value)
  print(name .. "\t" .. tostring(value or ""))
end
local function dispatcher(path)
  return setmetatable({}, {
    __index = function(_, key) return dispatcher(path .. "." .. key) end,
    __call = function(_, value) return { dispatcher = path, value = value } end,
  })
end
hl = {
  dsp = dispatcher("hl.dsp"),
  env = function(name, value) record("ENV", name .. "=" .. value) end,
  config = function(_) end, curve = function(_) end, animation = function(_) end,
  window_rule = function(_) end, layer_rule = function(_) end,
  bind = function(key, action, options)
    record("BIND", key .. "=" .. (type(action) == "table" and
      (action.dispatcher == "hl.dsp.exec_cmd" and action.value or action.dispatcher) or "callback"))
  end,
  on = function(name, callback) if name == "hyprland.start" then callback() end end,
  exec_cmd = function(command) record("EXEC", command) end,
}
dofile(arg[1])
'''


@unittest.skipUnless(LUA, 'Lua interpreter unavailable')
class SessionDefaults(unittest.TestCase):
    def test_uwsm_boundary_discards_prior_owner_variables_and_keeps_user_roots(self):
        result = subprocess.run(['/bin/bash', '-c', '. "$1"; /usr/bin/env', 'test',
                                 str(ROOT / 'uwsm-env')],
            env={'HOME': '/user-home', 'PATH': '/usr/bin', 'XDG_CONFIG_HOME': '/personal-config',
                 'OMARCHY_PATH': '/prior-owner', 'OMARCHY_CUSTOM': 'prior-choice',
                 'TAMLINUX_MENU_EXTENSION': '/personal-menu'},
            capture_output=True, text=True, timeout=10, check=True)
        env = dict(line.split('=', 1) for line in result.stdout.splitlines())
        self.assertFalse(any(key.startswith('OMARCHY_') for key in env))
        self.assertEqual(env['XDG_CONFIG_HOME'], '/personal-config')
        self.assertEqual(env['TAMLINUX_MENU_EXTENSION'], '/personal-menu')
        self.assertEqual(env['TAMLINUX_SESSION'], '1')

    def run_defaults(self, prepare=None):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            if prepare:
                prepare(home)
            recorder = home / 'record.lua'
            recorder.write_text(RECORDER)
            result = subprocess.run([LUA, str(recorder), str(ROOT / 'entry.lua')],
                env={'PATH': str(Path(LUA).parent), 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
                                  'XDG_STATE_HOME': str(home / 'state')},
                text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

    def test_empty_state_has_retained_bindings_and_owned_session_environment(self):
        text = self.run_defaults()
        self.assertIn('BIND\tSUPER + W=hl.dsp.window.close', text)
        self.assertIn('BIND\tSUPER + RETURN=tam-launch-terminal', text)
        self.assertIn('BIND\tPRINT=tam-capture-screenshot', text)
        self.assertIn('ENV\tTAMLINUX_SESSION=1', text)
        self.assertIn('EXEC\tuwsm finalize', text)
        self.assertNotIn('OMARCHY_', text)
        self.assertNotIn('/usr/share/omarchy', text)

    def test_generated_theme_and_personal_override_are_applied(self):
        def prepare(home):
            theme = home / 'state/tamlinux/current/theme'
            theme.mkdir(parents=True)
            (theme / 'hyprland.lua').write_text('hl.env("THEME_TEST", "owned")\n')
            overrides = home / 'config/tamlinux/hypr'
            overrides.mkdir(parents=True)
            (overrides / 'input.lua').write_text('hl.env("PERSONAL_TEST", "kept")\n')
        text = self.run_defaults(prepare)
        self.assertIn('ENV\tTHEME_TEST=owned', text)
        self.assertIn('ENV\tPERSONAL_TEST=kept', text)

    def test_owned_toggle_dropin_loads_and_legacy_input_lua_is_excluded(self):
        def prepare(home):
            toggles = home / 'state/tamlinux/toggles/hypr'
            toggles.mkdir(parents=True)
            (toggles / 'tensaku.lua').write_text('hl.env("TOGGLE_TEST", "owned")\n')
            (toggles / 'touchpad-disabled.lua').write_text('error("legacy input must not run")\n')
        text = self.run_defaults(prepare)
        self.assertIn('ENV\tTOGGLE_TEST=owned', text)


if __name__ == '__main__':
    unittest.main()
