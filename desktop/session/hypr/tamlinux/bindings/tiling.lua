o.bind("SUPER + Q", "Close window", hl.dsp.window.close())
o.bind("SUPER + BACKSPACE", "Close window", hl.dsp.window.close())
o.bind("CTRL + ALT + DELETE", "Close all windows", "tam-hyprland-window-close-all")

o.bind("SUPER + J", "Toggle window split", hl.dsp.layout("togglesplit"))
o.bind("SUPER + P", "Pseudo window", hl.dsp.window.pseudo())
o.bind("SUPER + T", "Toggle window floating/tiling", hl.dsp.window.float({ action = "toggle" }))
o.bind("SUPER + SHIFT + F", "Full screen", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
o.bind("SUPER + CTRL + F", "Tiled full screen", "tam-hyprland-window-tiled-fullscreen-toggle")
o.bind("SUPER + O", "Pop window out (float & pin)", "tam-hyprland-window-pop")
o.bind("SUPER + SHIFT + Home", "Save window width", "tam-hyprland-window-width save")
o.bind("SUPER + Home", "Restore window width", "tam-hyprland-window-width restore")
o.bind("SUPER + L", "Toggle workspace layout", "tam-hyprland-workspace-layout-toggle")

o.bind("SUPER + LEFT", "Focus on left window", hl.dsp.focus({ direction = "l" }))
o.bind("SUPER + RIGHT", "Focus on right window", hl.dsp.focus({ direction = "r" }))
o.bind("SUPER + UP", "Focus on above window", hl.dsp.focus({ direction = "u" }))
o.bind("SUPER + DOWN", "Focus on below window", hl.dsp.focus({ direction = "d" }))

for workspace = 1, 10 do
  local key = "code:" .. tostring(workspace + 9)
  o.bind("SUPER + " .. key, "Switch to workspace " .. workspace, hl.dsp.focus({ workspace = tostring(workspace) }))
  o.bind("SUPER + SHIFT + " .. key, "Move window to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace) }))
  o.bind("CTRL + ALT + " .. key, "Move window silently to workspace " .. workspace, hl.dsp.window.move({ workspace = tostring(workspace), follow = false }))
end

o.bind("SUPER + S", "Toggle scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
o.bind("CTRL + SHIFT + S", "Move window to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }))

o.bind("SUPER + TAB", "Next workspace", hl.dsp.focus({ workspace = "e+1" }))
o.bind("SUPER + SHIFT + TAB", "Previous workspace", hl.dsp.focus({ workspace = "e-1" }))
o.bind("SUPER + CTRL + TAB", "Former workspace", hl.dsp.focus({ workspace = "previous" }))

o.bind("ALT + SHIFT + LEFT", "Move workspace to left monitor", hl.dsp.workspace.move({ monitor = "l" }))
o.bind("ALT + SHIFT + RIGHT", "Move workspace to right monitor", hl.dsp.workspace.move({ monitor = "r" }))
o.bind("ALT + SHIFT + UP", "Move workspace to up monitor", hl.dsp.workspace.move({ monitor = "u" }))
o.bind("ALT + SHIFT + DOWN", "Move workspace to down monitor", hl.dsp.workspace.move({ monitor = "d" }))

o.bind("SUPER + SHIFT + LEFT", "Swap window to the left", hl.dsp.window.swap({ direction = "l" }))
o.bind("SUPER + SHIFT + RIGHT", "Swap window to the right", hl.dsp.window.swap({ direction = "r" }))
o.bind("SUPER + SHIFT + UP", "Swap window up", hl.dsp.window.swap({ direction = "u" }))
o.bind("SUPER + SHIFT + DOWN", "Swap window down", hl.dsp.window.swap({ direction = "d" }))

o.bind("ALT + TAB", "Focus on next window", hl.dsp.window.cycle_next())
o.bind("ALT + SHIFT + TAB", "Focus on previous window", hl.dsp.window.cycle_next({ next = false }))
o.bind("ALT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())
o.bind("ALT + SHIFT + TAB", "Reveal active window on top", hl.dsp.window.bring_to_top())

o.bind("SUPER + Next", "Focus on next monitor", hl.dsp.focus({ monitor = "+1" }))
o.bind("SUPER + Prior", "Focus on previous monitor", hl.dsp.focus({ monitor = "-1" }))

-- Adjacent unshifted punctuation keys keep resize chords to three physical
-- keys on a US layout. Shift selects small steps; Ctrl selects large steps.
o.bind("SUPER + comma", "Expand window left", hl.dsp.window.resize({ x = -100, y = 0, relative = true }))
o.bind("SUPER + period", "Shrink window left", hl.dsp.window.resize({ x = 100, y = 0, relative = true }))
o.bind("SUPER + semicolon", "Shrink window up", hl.dsp.window.resize({ x = 0, y = -100, relative = true }))
o.bind("SUPER + apostrophe", "Expand window down", hl.dsp.window.resize({ x = 0, y = 100, relative = true }))
o.bind("SUPER + SHIFT + comma", "Expand window left a little", hl.dsp.window.resize({ x = -25, y = 0, relative = true }))
o.bind("SUPER + SHIFT + period", "Shrink window left a little", hl.dsp.window.resize({ x = 25, y = 0, relative = true }))
o.bind("SUPER + SHIFT + semicolon", "Shrink window up a little", hl.dsp.window.resize({ x = 0, y = -25, relative = true }))
o.bind("SUPER + SHIFT + apostrophe", "Expand window down a little", hl.dsp.window.resize({ x = 0, y = 25, relative = true }))
o.bind("SUPER + CTRL + comma", "Expand window left a lot", hl.dsp.window.resize({ x = -300, y = 0, relative = true }))
o.bind("SUPER + CTRL + period", "Shrink window left a lot", hl.dsp.window.resize({ x = 300, y = 0, relative = true }))
o.bind("SUPER + CTRL + semicolon", "Shrink window up a lot", hl.dsp.window.resize({ x = 0, y = -300, relative = true }))
o.bind("SUPER + CTRL + apostrophe", "Expand window down a lot", hl.dsp.window.resize({ x = 0, y = 300, relative = true }))

o.bind("SUPER + mouse_down", "Scroll active workspace forward", hl.dsp.focus({ workspace = "e+1" }))
o.bind("SUPER + mouse_up", "Scroll active workspace backward", hl.dsp.focus({ workspace = "e-1" }))

o.bind("SUPER + mouse:272", "Move window", hl.dsp.window.drag(), { mouse = true })
o.bind("SUPER + mouse:273", "Start menu", "tam-menu toggle start")
o.bind("SUPER + ALT + mouse:273", "Resize window", hl.dsp.window.resize(), { mouse = true })

o.bind("SUPER + G", "Toggle window grouping", hl.dsp.group.toggle())
o.bind("CTRL + SHIFT + G", "Move active window out of group", hl.dsp.window.move({ out_of_group = true }))

o.bind("CTRL + SHIFT + LEFT", "Move window to group on left", hl.dsp.window.move({ into_group = "l" }))
o.bind("CTRL + SHIFT + RIGHT", "Move window to group on right", hl.dsp.window.move({ into_group = "r" }))
o.bind("CTRL + SHIFT + UP", "Move window to group on top", hl.dsp.window.move({ into_group = "u" }))
o.bind("CTRL + SHIFT + DOWN", "Move window to group on bottom", hl.dsp.window.move({ into_group = "d" }))

o.bind("CTRL + SHIFT + TAB", "Next window in group", hl.dsp.group.next())

o.bind("SUPER + CTRL + LEFT", "Move grouped window focus left", hl.dsp.group.prev())
o.bind("SUPER + CTRL + RIGHT", "Move grouped window focus right", hl.dsp.group.next())

o.bind("CTRL + SHIFT + mouse_down", "Next window in group", hl.dsp.group.next())
o.bind("CTRL + SHIFT + mouse_up", "Previous window in group", hl.dsp.group.prev())

for index = 1, 5 do
  o.bind("CTRL + SHIFT + code:" .. tostring(index + 9), "Switch to group window " .. index, hl.dsp.group.active({ index = index }))
end

o.bind("SUPER + SLASH", "Monitor scaling up", "tam-hyprland-monitor-scaling up")
o.bind("CTRL + SLASH", "Monitor scaling down", "tam-hyprland-monitor-scaling down")
