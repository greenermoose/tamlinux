o.bind("SUPER + SPACE", "Tamlinux menu", "tam-menu toggle")
o.bind("SUPER + ALT + SPACE", "Apps menu", "tam-menu toggle apps")
o.bind("SUPER + CTRL + E", "Emojis", "tam-shell emojis toggle")
o.bind("SUPER + CTRL + C", "Capture menu", "tam-menu toggle capture")
o.bind("SUPER + CTRL + O", "Toggle menu", "tam-menu toggle toggle")
o.bind("SUPER + CTRL + H", "Hardware menu", "tam-menu toggle hardware")
o.bind("SUPER + SHIFT + code:201", "Tamlinux menu", "tam-menu toggle root")
o.bind("SUPER + ESCAPE", "System menu", "tam-menu toggle system")
o.bind("XF86PowerOff", "Power menu", "tam-menu toggle system", { locked = true })
o.bind("SUPER + K", "Keybindings", "tam-menu-keybindings")
o.bind("SUPER + ALT + K", "Tmux keybindings", "tam-menu-tmux-keybindings")
o.bind("SUPER + CTRL + K", "Herdr keybindings", "tam-menu-herdr-keybindings")
o.bind("XF86Calculator", "Calculator", "omacalc")

o.bind("SUPER + SHIFT + SPACE", "Toggle top bar", "tam-shell tamlinux-shell toggleBar")
o.bind("SUPER + CTRL + SPACE", "Background switcher", "tam-menu toggle background")
o.bind("SUPER + SHIFT + T", "Theme menu", "tam-menu toggle theme")
-- Appearance toggles live on U so Backspace stays a close chord without a
-- Hamming collision (missing Shift on gaps would otherwise close the window).
o.bind("SUPER + U", "Toggle window transparency", "tam-hyprland-window-transparency-toggle")
o.bind("SUPER + SHIFT + U", "Toggle window gaps", "tam-hyprland-window-gaps-toggle")
o.bind("SUPER + CTRL + U", "Toggle single-window square aspect", "tam-hyprland-window-single-square-aspect-toggle")

-- Notification shortcuts share N; Alt+H opens history.
o.bind("SUPER + N", "Dismiss last notification", "tam-shell notifications dismissOne")
o.bind("SUPER + SHIFT + N", "Dismiss all notifications", "tam-shell notifications dismissAll")
o.bind("SUPER + CTRL + N", "Toggle silencing notifications", "tam-toggle-notification-silencing")
o.bind("SUPER + ALT + N", "Invoke last notification", "tam-shell notifications invokeLast")
o.bind("SUPER + ALT + H", "Open notification history", "tam-shell notifications showHistory")

o.bind("SUPER + CTRL + I", "Toggle locking on idle", "tam-toggle-idle")
o.bind("SUPER + CTRL + J", "Toggle nightlight", "tam-toggle-nightlight")
o.bind("SUPER + CTRL + Delete", "Toggle laptop display", "tam-hyprland-monitor-internal toggle")
o.bind("SUPER + ALT + Delete", "Toggle laptop display mirroring", "tam-hyprland-monitor-internal-mirror toggle")
o.bind("switch:on:Lid Switch", nil, "tam-system-lid-close", { locked = true })
o.bind("switch:off:Lid Switch", nil, "tam-hyprland-monitor-clamshell", { locked = true })

o.bind("PRINT", "Screenshot", "tam-capture-screenshot")
o.bind("ALT + PRINT", "Screenrecording", "tam-capture-screenrecording --stop-recording || tam-menu toggle trigger.capture.screenrecord")
o.bind("SUPER + ALT + code:34", "Make webcam overlay smaller", "tam-capture-webcam-resize smaller")
o.bind("SUPER + ALT + code:35", "Make webcam overlay larger", "tam-capture-webcam-resize larger")
o.bind("SUPER + PRINT", "Color picker", "pkill hyprpicker || hyprpicker -a")
o.bind("SUPER + CTRL + PRINT", "Extract text (OCR) from screenshot", "tam-capture-text")

-- Keyboard control for the slurp region picker (see tam-capture-region).
-- The binds live exactly as long as a selection layer is on screen (slurp
-- opens one per monitor), so they cannot leak or get stuck.
-- Unbinding by key would take a same-key binding out of the user's own config
-- with it, so each handle is kept and removed individually.
local selection_layers = 0
local selection_binds = {}

hl.on("layer.opened", function(layer)
  if layer.namespace == "selection" then
    selection_layers = selection_layers + 1
    if selection_layers == 1 then
      selection_binds = {
        hl.bind("RETURN", hl.dsp.exec_cmd("tam-capture-region --take-window"), { description = "Capture highlighted window" }),
        hl.bind("CTRL + RETURN", hl.dsp.exec_cmd("tam-capture-region --take-fullscreen"), { description = "Capture entire screen" }),
        hl.bind("TAB", hl.dsp.exec_cmd("tam-capture-region --select-window next"), { description = "Select next window to capture" }),
        hl.bind("CTRL + TAB", hl.dsp.exec_cmd("tam-capture-region --select-window prev"), { description = "Select previous window to capture" }),
      }
      for _, direction in ipairs({ "left", "right", "up", "down" }) do
        table.insert(
          selection_binds,
          hl.bind(direction:upper(), hl.dsp.exec_cmd("tam-capture-region --select-window " .. direction), { description = "Select window to capture" })
        )
      end
    end
  end
end)

hl.on("layer.closed", function(layer)
  if layer.namespace == "selection" and selection_layers > 0 then
    selection_layers = selection_layers - 1
    if selection_layers == 0 then
      for _, keybind in ipairs(selection_binds) do
        keybind:unbind()
      end
      selection_binds = {}
    end
  end
end)

o.bind("SUPER + CTRL + S", "Share", "tam-menu toggle share")

-- Y leaves the punctuation keys available for window resizing.
o.bind("SUPER + CTRL + Y", "Transcode", "tam-transcode")

o.bind("SUPER + CTRL + R", "Set reminder", "tam-reminder -i")
o.bind("SUPER + ALT + R", "Show reminders", "tam-reminder show")
o.bind("SUPER + SHIFT + R", "Clear reminders", "tam-reminder --confirm-clear")

o.bind("SUPER + ALT + T", "Show time", "tam-notification-time")
o.bind("SUPER + ALT + P", "Show battery remaining", "tam-notification-battery")
o.bind("SUPER + ALT + W", "Toggle weather", "tam-shell tamlinux-shell toggle fred.weather")

o.bind("SUPER + SHIFT + C", "Agent", "tam-agent --pick")
o.bind("SUPER + CTRL + A", "Audio", "tam-shell tamlinux-shell toggle tamlinux.audio")
o.bind("SUPER + CTRL + B", "Bluetooth", "tam-shell tamlinux-shell toggle tamlinux.bluetooth")
o.bind("SUPER + CTRL + D", "Display", "tam-shell tamlinux-shell toggle fred.monitor")
o.bind("SUPER + ALT + D", "Calendar", "tam-shell tamlinux-shell toggle fred.clock")
o.bind("SUPER + CTRL + W", "Network", "tam-shell tamlinux-shell toggle tamlinux.network")
o.bind("SUPER + CTRL + P", "Power", "tam-shell tamlinux-shell toggle tamlinux.power")
o.bind("SUPER + CTRL + T", "Activity", { tui = "btop" })

-- The letters above name a panel; the numbers count them. 1 is the leftmost
-- panel in the bar's right section, and a widget with no panel of its own (the
-- tray) is not counted, so the number matches the icon a user would point at.
-- A bar with fewer panels than this leaves the tail of the range doing nothing.
for panel = 1, 9 do
  o.bind(
    "SUPER + CTRL + code:" .. tostring(panel + 9),
    "Bar panel " .. panel,
    "tam-shell -q tamlinux-shell togglePanelAt right " .. panel
  )
end

o.bind("SUPER + CTRL + Z", "Zoom in", function()
  local zoom = hl.get_config("cursor.zoom_factor") or 1
  hl.config({ cursor = { zoom_factor = zoom + 1 } })
end)

o.bind("SUPER + ALT + Z", "Reset zoom", function()
  hl.config({ cursor = { zoom_factor = 1 } })
end)

o.bind("SUPER + CTRL + L", "Lock system", "tam-system-lock")
