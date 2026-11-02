o.bind("META + Q", "Close window", hl.dsp.window.close())
o.bind("META + BACKSPACE", "Close window", hl.dsp.window.close())
o.bind("CTRL + ALT + DELETE", "Close all windows", "tam-hyprland-window-close-all")

o.bind("META + J", "Toggle window split", hl.dsp.layout("togglesplit"))
o.bind("META + P", "Pseudo window", hl.dsp.window.pseudo())
o.bind("META + T", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
o.bind("META + SHIFT + F", "Full screen", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
o.bind("META + CTRL + F", "Tiled full screen", "tam-hyprland-window-tiled-fullscreen-toggle")
o.bind("META + O", "Pop window out (float & pin)", "tam-hyprland-window-pop")
o.bind("META + SHIFT + Home", "Save window width", "tam-hyprland-window-width save")
o.bind("META + Home", "Restore window width", "tam-hyprland-window-width restore")
o.bind("META + L", "Toggle workspace layout", "tam-hyprland-workspace-layout-toggle")

o.bind("META + LEFT", "Focus on left window", hl.dsp.focus({ direction = "l" }))
o.bind("META + RIGHT", "Focus on right window", hl.dsp.focus({ direction = "r" }))
o.bind("META + UP", "Focus on above window", hl.dsp.focus({ direction = "u" }))
o.bind("META + DOWN", "Focus on below window", hl.dsp.focus({ direction = "d" }))

for workspace = 1, 10 do
  local key = "code:" .. tostring(workspace + 9)
  o.bind("META + " .. key, "Switch to workspace " .. workspace, hl.dsp.focus({ workspace = tostring(workspace) }))
  o.bind("META + SHIFT + " .. key, "Move window to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace) }))
  o.bind("CTRL + ALT + " .. key, "Move window silently to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace), follow = false }))
end

o.bind("META + S", "Toggle scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
o.bind("CTRL + SHIFT + S", "Move window to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }))

o.bind("META + TAB", "Next workspace", hl.dsp.focus({ workspace = "e+1" }))
o.bind("META + SHIFT + TAB", "Previous workspace", hl.dsp.focus({ workspace = "e-1" }))
o.bind("META + CTRL + TAB", "Former workspace", hl.dsp.focus({ workspace = "previous" }))

o.bind("ALT + SHIFT + LEFT", "Move workspace to left monitor", hl.dsp.workspace.move({ monitor = "l" }))
o.bind("ALT + SHIFT + RIGHT", "Move workspace to right monitor", hl.dsp.workspace.move({ monitor = "r" }))
o.bind("ALT + SHIFT + UP", "Move workspace to up monitor", hl.dsp.workspace.move({ monitor = "u" }))
o.bind("ALT + SHIFT + DOWN", "Move workspace to down monitor", hl.dsp.workspace.move({ monitor = "d" }))

o.bind("META + SHIFT + LEFT", "Swap window to the left", hl.dsp.window.swap({ direction = "l" }))
o.bind("META + SHIFT + RIGHT", "Swap window to the right", hl.dsp.window.swap({ direction = "r" }))
o.bind("META + SHIFT + UP", "Swap window up", hl.dsp.window.swap({ direction = "u" }))
o.bind("META + SHIFT + DOWN", "Swap window down", hl.dsp.window.swap({ direction = "d" }))

o.bind("ALT + TAB", "Focus on next window", hl.dsp.window.cycle_next())
o.bind("ALT + SHIFT + TAB", "Focus on previous window", hl.dsp.window.cycle_next({ next = false }))
o.bind("ALT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())
o.bind("ALT + SHIFT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())

o.bind("META + Next", "Focus on next monitor", hl.dsp.focus({ monitor = "+1" }))
o.bind("META + Prior", "Focus on previous monitor", hl.dsp.focus({ monitor = "-1" }))

-- Adjacent unshifted punctuation keys keep resize chords to three physical
-- keys on a US layout. Shift selects small steps; Ctrl selects large steps.
o.bind("META + comma", "Expand window left", hl.dsp.window.resize({ x = -100, y = 0, relative = true }))
o.bind("META + period", "Shrink window left", hl.dsp.window.resize({ x = 100, y = 0, relative = true }))
o.bind("META + semicolon", "Shrink window up", hl.dsp.window.resize({ x = 0, y = -100, relative = true }))
o.bind("META + apostrophe", "Expand window down", hl.dsp.window.resize({ x = 0, y = 100, relative = true }))
o.bind("META + SHIFT + comma", "Expand window left a little", hl.dsp.window.resize({ x = -25, y = 0, relative = true }))
o.bind("META + SHIFT + period", "Shrink window left a little", hl.dsp.window.resize({ x = 25, y = 0, relative = true }))
o.bind("META + SHIFT + semicolon", "Shrink window up a little", hl.dsp.window.resize({ x = 0, y = -25, relative = true }))
o.bind("META + SHIFT + apostrophe", "Expand window down a little", hl.dsp.window.resize({ x = 0, y = 25, relative = true }))
o.bind("META + CTRL + comma", "Expand window left a lot", hl.dsp.window.resize({ x = -300, y = 0, relative = true }))
o.bind("META + CTRL + period", "Shrink window left a lot", hl.dsp.window.resize({ x = 300, y = 0, relative = true }))
o.bind("META + CTRL + semicolon", "Shrink window up a lot", hl.dsp.window.resize({ x = 0, y = -300, relative = true }))
o.bind("META + CTRL + apostrophe", "Expand window down a lot", hl.dsp.window.resize({ x = 0, y = 300, relative = true }))

o.bind("META + mouse_down", "Scroll active workspace forward", hl.dsp.focus({ workspace = "e+1" }))
o.bind("META + mouse_up", "Scroll active workspace backward", hl.dsp.focus({ workspace = "e-1" }))

o.bind("META + mouse:272", "Move window", hl.dsp.window.drag(), { mouse = true })
o.bind("META + mouse:273", "Start menu", "tam-menu toggle start")
o.bind("META + ALT + mouse:273", "Resize window", hl.dsp.window.resize(), { mouse = true })

o.bind("META + G", "Toggle window grouping", hl.dsp.group.toggle())
o.bind("CTRL + SHIFT + G", "Move active window out of group", hl.dsp.window.move({ out_of_group = true }))

o.bind("META + CTRL + LEFT", "Move window to group on left", hl.dsp.window.move({ into_group = "l" }))
o.bind("META + CTRL + RIGHT", "Move window to group on right", hl.dsp.window.move({ into_group = "r" }))
o.bind("META + CTRL + UP", "Move window to group on top", hl.dsp.window.move({ into_group = "u" }))
o.bind("META + CTRL + DOWN", "Move window to group on bottom", hl.dsp.window.move({ into_group = "d" }))

o.bind("META + CTRL + backslash", "Next window in group", hl.dsp.group.next())

o.bind("META + CTRL + Prior", "Move grouped window focus left", hl.dsp.group.prev())
o.bind("META + CTRL + Next", "Move grouped window focus right", hl.dsp.group.next())

o.bind("CTRL + SHIFT + mouse_down", "Next window in group", hl.dsp.group.next())
o.bind("CTRL + SHIFT + mouse_up", "Previous window in group", hl.dsp.group.prev())

for index = 1, 5 do
  o.bind("CTRL + SHIFT + code:" .. tostring(index + 9), "Switch to group window " .. index, hl.dsp.group.active({ index = index }))
end

o.bind("META + SLASH", "Monitor scaling up", "tam-hyprland-monitor-scaling up")
o.bind("META + CTRL + SLASH", "Monitor scaling down", "tam-hyprland-monitor-scaling down")
