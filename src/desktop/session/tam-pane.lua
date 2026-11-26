-- Tamlinux versioned session defaults for tam-pane.
-- Loaded inside tam-pane's sandboxed Lua 5.5 runtime (tp.read_file + load).
-- Personal overrides are included at the end from ~/.config/tam-pane/init.lua
-- and ~/.config/tamlinux/tam-pane/{monitors,macros}.lua and preserved across
-- every live reload.

local function read_vconsole()
  local values = {}
  local content = tp.read_file("/etc/vconsole.conf")
  if not content then
    return values
  end
  for line in content:gmatch("[^\r\n]+") do
    local key, value = line:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
    if key and value then
      value = value:gsub("%s+#.*$", "")
      value = value:gsub('^"(.*)"$', "%1")
      value = value:gsub("^'(.*)'$", "%1")
      values[key] = value
    end
  end
  return values
end

local non_latin_layouts =
  " af am ara bd bg by et ge gr il in iq ir kg kh kz la lk mk mm mn mv np rs ru sy th tj ua "

local vconsole = read_vconsole()
local kb_layout = vconsole.XKBLAYOUT or "us"
local kb_variant = vconsole.XKBVARIANT or ""
local kb_options = "compose:caps,shift:both_capslock_cancel"
local lead_layout = kb_layout:match("^[^,]*") or ""
if lead_layout ~= "" and non_latin_layouts:find(" " .. lead_layout .. " ", 1, true) then
  kb_layout = "us," .. kb_layout
  kb_variant = "," .. kb_variant
  kb_options = kb_options .. ",grp:alts_toggle"
end

tp.config{
  gaps = 8,
  cursor_theme = "Adwaita",
  cursor_size = 24,
  repeat_rate = 40,
  repeat_delay = 250,
  kb_layout = kb_layout,
  kb_variant = kb_variant,
  kb_options = kb_options,
  numlock_by_default = true,
  natural_scroll = false,
  scroll_factor = 1.0,
  terminal = "/usr/bin/tamlinux/tam-launch-terminal --tam-last",
  chord_enabled = true,
  chord_overlay_builtin = true,
  chord_key = "Caps_Lock",
  chord_secondary_key = "Alt_R",
  chord_cancel_key = "Escape",
}

-- Reset compiled-in key bindings so Tamlinux owns the exact default keymap.
tp.clear_binds()

-- Window rules (ported from hypr/tamlinux/apps/{system,localsend,pip,webcam-overlay}.lua).
local floating_apps = {
  "^org%.tamlinux%.journal$",
  "^org%.tamlinux%.btop$",
  "^org%.tamlinux%.terminal$",
  "^org%.gnome%.NautilusPreviewer$",
  "^org%.gnome%.Evince$",
  "^About$",
  "^TUI%.float$",
  "^imv$",
  "^mpv$",
  "^xdg%-desktop%-portal%-gtk$",
}
for _, pat in ipairs(floating_apps) do
  tp.rule{ match = { app_id = pat }, floating = true, size = { 875, 600 }, position = "center" }
end

tp.rule{ match = { app_id = "^org%.tamlinux%.about$" }, floating = true, size = { 920, 480 }, position = "center" }
tp.rule{ match = { app_id = "^dev%.tensaku%.Tensaku$" }, floating = true, position = "center" }
tp.rule{ match = { app_id = "^qalculate%-gtk$" }, floating = true, position = "center" }
tp.rule{ match = { app_id = "^localsend$" }, floating = true, size = { 1100, 700 }, position = "center" }
tp.rule{ match = { app_id = "^Share$" }, floating = true, position = "center" }
tp.rule{ match = { title = "Picture.?in.?[Pp]icture" }, floating = true, size = { 600, 338 } }
tp.rule{ match = { app_id = "^WebcamOverlay%-" }, floating = true }

-- Core window, layout, monitor, and tag bindings.
tp.bind("Meta+q", tp.dsp.close(), { desc = "Close window" })
tp.bind("Meta+BackSpace", tp.dsp.close(), { desc = "Close window" })
tp.bind("Meta+t", tp.dsp.toggle_float(), { desc = "Toggle window floating/tiling" })
tp.bind("Meta+Shift+f", tp.dsp.toggle_fullscreen(), { desc = "Full screen" })
tp.bind("Meta+l", tp.dsp.layout("next"), { desc = "Cycle workspace layout" })
tp.bind("Meta+s", tp.dsp.scratchpad("toggle"), { desc = "Toggle scratchpad" })
tp.bind("Ctrl+Shift+s", tp.dsp.scratchpad("move"), { desc = "Move window to scratchpad" })

tp.bind("Meta+Left", tp.dsp.focus("left"), { desc = "Focus on left window" })
tp.bind("Meta+Right", tp.dsp.focus("right"), { desc = "Focus on right window" })
tp.bind("Meta+Up", tp.dsp.focus("up"), { desc = "Focus on above window" })
tp.bind("Meta+Down", tp.dsp.focus("down"), { desc = "Focus on below window" })

tp.bind("Meta+Shift+Left", tp.dsp.swap("left"), { desc = "Swap window to the left" })
tp.bind("Meta+Shift+Right", tp.dsp.swap("right"), { desc = "Swap window to the right" })
tp.bind("Meta+Shift+Up", tp.dsp.swap("up"), { desc = "Swap window up" })
tp.bind("Meta+Shift+Down", tp.dsp.swap("down"), { desc = "Swap window down" })

tp.bind("Alt+Tab", tp.dsp.focus("next"), { desc = "Focus on next window" })
tp.bind("Alt+Shift+Tab", tp.dsp.focus("prev"), { desc = "Focus on previous window" })

tp.bind("Meta+Next", tp.dsp.monitor("focus", "next"), { desc = "Focus on next monitor" })
tp.bind("Meta+Prior", tp.dsp.monitor("focus", "prev"), { desc = "Focus on previous monitor" })
tp.bind("Meta+Shift+Next", tp.dsp.monitor("move", "next"), { desc = "Move window to next monitor" })
tp.bind("Meta+Shift+Prior", tp.dsp.monitor("move", "prev"), { desc = "Move window to previous monitor" })

tp.bind("Meta+Tab", tp.dsp.tag("back"), { desc = "Former tag" })
tp.bind("Meta+Ctrl+Tab", tp.dsp.tag("back"), { desc = "Former tag" })

for tag = 1, 9 do
  local key = "code:" .. tostring(tag + 9)
  tp.bind("Meta+" .. key, tp.dsp.tag("view", tag), { desc = "Switch to tag " .. tag })
  tp.bind("Meta+Shift+" .. key, tp.dsp.tag("move", tag), { desc = "Move window to tag " .. tag })
  tp.bind("Ctrl+Alt+" .. key, tp.dsp.tag("move", tag), { desc = "Move window to tag " .. tag })
  tp.bind("Meta+Ctrl+Shift+" .. key, tp.dsp.tag("toggle_view", tag), { desc = "Toggle tag " .. tag })
end

-- Adjacent unshifted punctuation keys for window resize (US layout).
local resize_steps = {
  { "", 100, "" },
  { "Shift+", 25, " a little" },
  { "Ctrl+", 300, " a lot" },
}
local resize_dirs = {
  { "comma", "left", "Resize window left" },
  { "period", "right", "Resize window right" },
  { "semicolon", "up", "Resize window up" },
  { "apostrophe", "down", "Resize window down" },
}
for _, step in ipairs(resize_steps) do
  for _, item in ipairs(resize_dirs) do
    tp.bind("Meta+" .. step[1] .. item[1], tp.dsp.resize(item[2], step[2]), { desc = item[3] .. step[3] })
  end
end

-- Monitor scaling.
tp.bind("Meta+slash", tp.dsp.spawn("tam-hyprland-monitor-scaling up"), { desc = "Monitor scaling up" })
tp.bind("Meta+Ctrl+slash", tp.dsp.spawn("tam-hyprland-monitor-scaling down"), { desc = "Monitor scaling down" })

-- Universal clipboard shortcuts (synthesized with explicit modifiers).
tp.bind("Meta+c", tp.dsp.send_key("Ctrl+c"), { desc = "Universal copy" })
tp.bind("Meta+v", tp.dsp.send_key("Ctrl+v"), { desc = "Universal paste" })
tp.bind("Meta+x", tp.dsp.send_key("Ctrl+x"), { desc = "Universal cut" })
tp.bind("Meta+Ctrl+v", tp.dsp.spawn("tam-shell clipboard toggle"), { desc = "Clipboard manager" })

-- Essential application bindings.
tp.bind("Meta+Return", tp.dsp.spawn("/usr/bin/tamlinux/tam-launch-terminal --tam-last"), { desc = "Terminal" })
tp.bind("Meta+Shift+Return", tp.dsp.spawn("tam-launch-browser"), { desc = "Browser" })
tp.bind("Meta+Shift+b", tp.dsp.spawn("tam-launch-browser"), { desc = "Browser" })
tp.bind("Meta+Shift+w", tp.dsp.spawn("tam-launch-browser --private"), { desc = "Browser (private)" })
tp.bind("Meta+f", tp.dsp.spawn("uwsm-app -- nautilus --new-window"), { desc = "File manager" })
tp.bind("Meta+d", tp.dsp.spawn("uwsm-app -- nautilus --new-window \"$(tam-cmd-terminal-cwd)\""), { desc = "File manager (cwd)" })
tp.bind("Meta+Shift+e", tp.dsp.spawn("tam-launch-editor"), { desc = "Editor" })
tp.bind("Meta+e", tp.dsp.spawn("tam-launch-tui micro"), { desc = "Micro" })
tp.bind("Ctrl+F8", tp.dsp.spawn("tam-launch-terminal-tmux"), { desc = "Tmux" })
tp.bind("Meta+Ctrl+Return", tp.dsp.spawn("tam-launch-terminal-herdr"), { desc = "Herdr" })

-- Menus, notifications, capture, and utilities.
tp.bind("Meta+Space", tp.dsp.spawn("tam-menu toggle"), { desc = "Tamlinux menu" })
tp.bind("Ctrl+F12", tp.dsp.spawn("tam-menu toggle apps"), { desc = "Apps menu" })
tp.bind("Meta+Ctrl+e", tp.dsp.spawn("tam-shell emojis toggle"), { desc = "Emojis" })
tp.bind("Meta+Ctrl+c", tp.dsp.spawn("tam-menu toggle capture"), { desc = "Capture menu" })
tp.bind("Meta+Ctrl+o", tp.dsp.spawn("tam-menu toggle toggle"), { desc = "Toggle menu" })
tp.bind("Meta+Ctrl+h", tp.dsp.spawn("tam-menu toggle hardware"), { desc = "Hardware menu" })
tp.bind("Meta+Escape", tp.dsp.spawn("tam-menu toggle system"), { desc = "System menu" })
tp.bind("Meta+Shift+Escape", tp.dsp.spawn("tam-desktop-test --stop"), { locked = true, desc = "Stop automated desktop test" })
tp.bind("XF86PowerOff", tp.dsp.spawn("tam-menu toggle system"), { locked = true, desc = "Power menu" })
tp.bind("Meta+k", tp.dsp.spawn("tam-menu-keybindings"), { desc = "Keybindings" })
tp.bind("Meta+Shift+k", tp.dsp.spawn("tam-menu-tmux-keybindings"), { desc = "Tmux keybindings" })
tp.bind("Meta+Ctrl+k", tp.dsp.spawn("tam-menu-herdr-keybindings"), { desc = "Herdr keybindings" })
tp.bind("XF86Calculator", tp.dsp.spawn("uwsm-app -- qalculate-gtk"), { desc = "Calculator" })

tp.bind("Meta+Shift+Space", tp.dsp.spawn("tam-shell tamlinux-shell toggleBar"), { desc = "Toggle top bar" })
tp.bind("Meta+Ctrl+Space", tp.dsp.spawn("tam-menu toggle background"), { desc = "Background switcher" })
tp.bind("Meta+Shift+t", tp.dsp.spawn("tam-menu toggle theme"), { desc = "Theme menu" })

tp.bind("Meta+n", tp.dsp.spawn("tam-shell notifications dismissOne"), { desc = "Dismiss last notification" })
tp.bind("Meta+Shift+n", tp.dsp.spawn("tam-shell notifications dismissAll"), { desc = "Dismiss all notifications" })
tp.bind("Meta+Ctrl+n", tp.dsp.spawn("tam-toggle-notification-silencing"), { desc = "Toggle silencing notifications" })
tp.bind("Ctrl+F11", tp.dsp.spawn("tam-shell notifications invokeLast"), { desc = "Invoke last notification" })
tp.bind("Meta+Shift+h", tp.dsp.spawn("tam-shell notifications showHistory"), { desc = "Open notification history" })

tp.bind("Meta+Ctrl+i", tp.dsp.spawn("tam-toggle-idle"), { desc = "Toggle locking on idle" })
tp.bind("Meta+Ctrl+j", tp.dsp.spawn("tam-toggle-nightlight"), { desc = "Toggle nightlight" })
tp.bind("Meta+Ctrl+l", tp.dsp.spawn("tam-system-lock"), { desc = "Lock system" })
tp.bind("Meta+Shift+j", tp.dsp.spawn("tam-launch-journal add"), { desc = "Quick note" })

tp.bind("Print", tp.dsp.spawn("tam-capture-screenshot"), { desc = "Screenshot" })
tp.bind("Alt+Print", tp.dsp.spawn("tam-capture-screenrecording --stop-recording || tam-menu toggle trigger.capture.screenrecord"), { desc = "Screenrecording" })
tp.bind("Meta+Print", tp.dsp.spawn("pkill hyprpicker || hyprpicker -a"), { desc = "Color picker" })
tp.bind("Meta+Ctrl+Print", tp.dsp.spawn("tam-capture-text"), { desc = "Extract text (OCR) from screenshot" })

tp.bind("Meta+Ctrl+s", tp.dsp.spawn("tam-menu toggle share"), { desc = "Share" })
tp.bind("Meta+Ctrl+y", tp.dsp.spawn("tam-transcode"), { desc = "Transcode" })
tp.bind("Meta+Ctrl+r", tp.dsp.spawn("tam-reminder -i"), { desc = "Set reminder" })
tp.bind("Ctrl+F9", tp.dsp.spawn("tam-reminder show"), { desc = "Show reminders" })
tp.bind("Meta+Shift+r", tp.dsp.reload(), { desc = "Reload tam-pane configuration" })

tp.bind("Ctrl+F1", tp.dsp.spawn("tam-notification-time"), { desc = "Show time" })
tp.bind("Ctrl+F2", tp.dsp.spawn("tam-notification-battery"), { desc = "Show battery remaining" })
tp.bind("Ctrl+F3", tp.dsp.spawn("tam-shell tamlinux-shell toggle fred.weather"), { desc = "Toggle weather" })
tp.bind("Ctrl+F4", tp.dsp.spawn("tam-shell tamlinux-shell toggle fred.clock"), { desc = "Calendar" })

tp.bind("Meta+Shift+c", tp.dsp.spawn("tam-agent --pick"), { desc = "Agent" })
tp.bind("Meta+Ctrl+a", tp.dsp.spawn("tam-shell tamlinux-shell toggle tamlinux.audio"), { desc = "Audio" })
tp.bind("Meta+Ctrl+b", tp.dsp.spawn("tam-shell tamlinux-shell toggle tamlinux.bluetooth"), { desc = "Bluetooth" })
tp.bind("Meta+Ctrl+d", tp.dsp.spawn("tam-shell tamlinux-shell toggle fred.monitor"), { desc = "Display" })
tp.bind("Meta+Ctrl+w", tp.dsp.spawn("tam-shell tamlinux-shell toggle tamlinux.network"), { desc = "Network" })
tp.bind("Meta+Ctrl+p", tp.dsp.spawn("tam-shell tamlinux-shell toggle tamlinux.power"), { desc = "Power" })
tp.bind("Meta+Ctrl+t", tp.dsp.spawn("tam-launch-tui btop"), { desc = "Activity" })

for panel = 1, 9 do
  tp.bind(
    "Meta+Ctrl+code:" .. tostring(panel + 9),
    tp.dsp.spawn("tam-shell -q tamlinux-shell togglePanelAt right " .. panel),
    { desc = "Bar panel " .. panel }
  )
end

-- Media, volume, and brightness controls (active while locked).
tp.bind("XF86AudioRaiseVolume", tp.dsp.spawn("tam-audio-output-volume raise"), { locked = true, desc = "Volume up" })
tp.bind("XF86AudioLowerVolume", tp.dsp.spawn("tam-audio-output-volume lower"), { locked = true, desc = "Volume down" })
tp.bind("XF86AudioMute", tp.dsp.spawn("tam-audio-output-volume mute-toggle"), { locked = true, desc = "Mute" })
tp.bind("XF86AudioMicMute", tp.dsp.spawn("tam-audio-input-mute"), { locked = true, desc = "Mute microphone" })
tp.bind("Alt+XF86AudioRaiseVolume", tp.dsp.spawn("tam-audio-output-volume +1"), { locked = true, desc = "Volume up precise" })
tp.bind("Alt+XF86AudioLowerVolume", tp.dsp.spawn("tam-audio-output-volume -1"), { locked = true, desc = "Volume down precise" })
tp.bind("Shift+XF86AudioMute", tp.dsp.spawn("tam-audio-output-switch"), { locked = true, desc = "Switch audio output" })
tp.bind("XF86MonBrightnessUp", tp.dsp.spawn("tam-brightness-display +5%"), { locked = true, desc = "Brightness up" })
tp.bind("XF86MonBrightnessDown", tp.dsp.spawn("tam-brightness-display 5%-"), { locked = true, desc = "Brightness down" })
tp.bind("Shift+XF86MonBrightnessUp", tp.dsp.spawn("tam-brightness-display 100%"), { locked = true, desc = "Brightness maximum" })
tp.bind("Shift+XF86MonBrightnessDown", tp.dsp.spawn("tam-brightness-display 1%"), { locked = true, desc = "Brightness minimum" })
tp.bind("Alt+XF86MonBrightnessUp", tp.dsp.spawn("tam-brightness-display +1%"), { locked = true, desc = "Brightness up precise" })
tp.bind("Alt+XF86MonBrightnessDown", tp.dsp.spawn("tam-brightness-display 1%-"), { locked = true, desc = "Brightness down precise" })
tp.bind("XF86KbdBrightnessUp", tp.dsp.spawn("tam-brightness-keyboard up"), { locked = true, desc = "Keyboard brightness up" })
tp.bind("XF86KbdBrightnessDown", tp.dsp.spawn("tam-brightness-keyboard down"), { locked = true, desc = "Keyboard brightness down" })
tp.bind("XF86KbdLightOnOff", tp.dsp.spawn("tam-brightness-keyboard cycle"), { locked = true, desc = "Keyboard backlight cycle" })
tp.bind("XF86AudioNext", tp.dsp.spawn("tam-shell media next"), { locked = true, desc = "Next track" })
tp.bind("XF86AudioPrev", tp.dsp.spawn("tam-shell media previous"), { locked = true, desc = "Previous track" })
tp.bind("XF86AudioPlay", tp.dsp.spawn("tam-shell media playPause"), { locked = true, desc = "Play" })
tp.bind("XF86AudioPause", tp.dsp.spawn("tam-shell media playPause"), { locked = true, desc = "Pause" })
tp.bind("XF86AudioStop", tp.dsp.spawn("tam-shell media stop"), { locked = true, desc = "Stop" })

-- Dictation (voxtype).
tp.bind("Meta+Ctrl+x", tp.dsp.spawn("voxtype record toggle"), { desc = "Toggle dictation" })
tp.bind("F9", tp.dsp.spawn("voxtype record start"), { desc = "Start dictation (push-to-talk)" })
tp.bind("F9", tp.dsp.spawn("voxtype record stop"), { release = true, desc = "Stop dictation (push-to-talk)" })

-- Mouse bindings: Meta+Right-click opens Start menu; Meta+Alt+Right-drag resizes.
tp.mouse_bind("Meta+mouse:272", tp.dsp.mouse_move(), { desc = "Move window" })
tp.mouse_bind("Meta+mouse:273", tp.dsp.spawn("tam-menu toggle start"), { desc = "Start menu" })
tp.mouse_bind("Meta+Alt+mouse:273", tp.dsp.mouse_resize(), { desc = "Resize window" })
tp.mouse_bind("Meta+mouse_up", tp.dsp.tag("back"), { desc = "Previous tag" })
tp.mouse_bind("Meta+mouse_down", tp.dsp.tag("back"), { desc = "Previous tag" })

-- Session autostart (runs once after Wayland + IPC sockets are up).
tp.on("startup", function()
  -- Export WAYLAND_DISPLAY and TAM_PANE_SOCKET to systemd/D-Bus before session services start.
  tp.spawn("uwsm finalize TAM_PANE_SOCKET")
  -- Grant xdg-desktop-portal-wlr an authorized WAYLAND_SOCKET for PipeWire ScreenCast/Screenshot.
  tp.capture{"/usr/lib/xdg-desktop-portal-wlr"}
  tp.spawn("tam-powerprofiles-set autodetect")
end)

-- Load managed monitor overrides, personal ~/.config/tam-pane/init.lua,
-- and tam-macro generated bindings. All three re-run cleanly on every reload.
if tp.config_dir and tp.config_dir ~= "" then
  tp.include(tp.config_dir .. "/tamlinux/tam-pane/monitors.lua", true)
  tp.include(tp.config_dir .. "/tam-pane/init.lua", true)
  tp.include(tp.config_dir .. "/tamlinux/tam-pane/macros.lua", true)
end
