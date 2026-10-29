// Default shortcut catalog. Rationales are suggested memory aids, not historical claims.
// Entries match chord, dispatcher and complete command; review when defaults change.
var entries = [
  {
    "mask": 0,
    "key": "XF86AudioRaiseVolume",
    "dispatcher": "exec",
    "arg": "tam-audio-output-volume raise",
    "action": "Volume up. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the volume up key."
  },
  {
    "mask": 0,
    "key": "XF86AudioLowerVolume",
    "dispatcher": "exec",
    "arg": "tam-audio-output-volume lower",
    "action": "Volume down. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the volume down key."
  },
  {
    "mask": 0,
    "key": "XF86AudioMute",
    "dispatcher": "exec",
    "arg": "tam-audio-output-volume mute-toggle",
    "action": "Mute or restore sound from the current output.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the mute key."
  },
  {
    "mask": 0,
    "key": "XF86AudioMicMute",
    "dispatcher": "exec",
    "arg": "tam-audio-input-mute",
    "action": "Mute or restore microphone input for privacy.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the mute microphone key."
  },
  {
    "mask": 0,
    "key": "XF86MonBrightnessUp",
    "dispatcher": "exec",
    "arg": "tam-brightness-display +5%",
    "action": "Brightness up. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness up key."
  },
  {
    "mask": 0,
    "key": "XF86MonBrightnessDown",
    "dispatcher": "exec",
    "arg": "tam-brightness-display 5%-",
    "action": "Brightness down. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness down key."
  },
  {
    "mask": 1,
    "key": "XF86MonBrightnessUp",
    "dispatcher": "exec",
    "arg": "tam-brightness-display 100%",
    "action": "Brightness maximum. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness maximum key with Shift for the alternate action."
  },
  {
    "mask": 1,
    "key": "XF86MonBrightnessDown",
    "dispatcher": "exec",
    "arg": "tam-brightness-display 1%",
    "action": "Brightness minimum. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness minimum key with Shift for the alternate action."
  },
  {
    "mask": 0,
    "key": "XF86KbdBrightnessUp",
    "dispatcher": "exec",
    "arg": "tam-brightness-keyboard up",
    "action": "Keyboard brightness up. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the keyboard brightness up key."
  },
  {
    "mask": 0,
    "key": "XF86KbdBrightnessDown",
    "dispatcher": "exec",
    "arg": "tam-brightness-keyboard down",
    "action": "Keyboard brightness down. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the keyboard brightness down key."
  },
  {
    "mask": 0,
    "key": "XF86KbdLightOnOff",
    "dispatcher": "exec",
    "arg": "tam-brightness-keyboard cycle",
    "action": "Cycle keyboard lighting levels to suit the room.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the keyboard backlight cycle key."
  },
  {
    "mask": 0,
    "key": "XF86TouchpadToggle",
    "dispatcher": "exec",
    "arg": "tam-toggle-input-device touchpad",
    "action": "Toggle touchpad. Use it to switch this setting or view.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the toggle touchpad key."
  },
  {
    "mask": 0,
    "key": "XF86TouchpadOn",
    "dispatcher": "exec",
    "arg": "tam-toggle-input-device touchpad on",
    "action": "Enable touchpad input when you need it.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the enable touchpad key."
  },
  {
    "mask": 0,
    "key": "XF86TouchpadOff",
    "dispatcher": "exec",
    "arg": "tam-toggle-input-device touchpad off",
    "action": "Disable touchpad input to prevent accidental touches.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the disable touchpad key."
  },
  {
    "mask": 8,
    "key": "XF86AudioRaiseVolume",
    "dispatcher": "exec",
    "arg": "tam-audio-output-volume +1",
    "action": "Volume up precise. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the volume up precise key with Alt for a finer adjustment."
  },
  {
    "mask": 8,
    "key": "XF86AudioLowerVolume",
    "dispatcher": "exec",
    "arg": "tam-audio-output-volume -1",
    "action": "Volume down precise. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the volume down precise key with Alt for a finer adjustment."
  },
  {
    "mask": 8,
    "key": "XF86MonBrightnessUp",
    "dispatcher": "exec",
    "arg": "tam-brightness-display +1%",
    "action": "Brightness up precise. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness up precise key with Alt for a finer adjustment."
  },
  {
    "mask": 8,
    "key": "XF86MonBrightnessDown",
    "dispatcher": "exec",
    "arg": "tam-brightness-display 1%-",
    "action": "Brightness down precise. Use this to adjust the current level.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the brightness down precise key with Alt for a finer adjustment."
  },
  {
    "mask": 0,
    "key": "XF86AudioNext",
    "dispatcher": "exec",
    "arg": "tam-shell media next",
    "action": "Skip to the next track in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the next track key."
  },
  {
    "mask": 8,
    "key": "XF86AudioPlay",
    "dispatcher": "exec",
    "arg": "tam-shell media next",
    "action": "Skip to the next track in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the next track key with Alt for a finer adjustment."
  },
  {
    "mask": 0,
    "key": "XF86AudioPause",
    "dispatcher": "exec",
    "arg": "tam-shell media playPause",
    "action": "Pause playback in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the pause key."
  },
  {
    "mask": 0,
    "key": "XF86AudioPlay",
    "dispatcher": "exec",
    "arg": "tam-shell media playPause",
    "action": "Start or resume playback in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the play key."
  },
  {
    "mask": 0,
    "key": "XF86AudioPrev",
    "dispatcher": "exec",
    "arg": "tam-shell media previous",
    "action": "Return to the previous track in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the previous track key."
  },
  {
    "mask": 0,
    "key": "XF86AudioStop",
    "dispatcher": "exec",
    "arg": "tam-shell media stop",
    "action": "Stop playback in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the stop key."
  },
  {
    "mask": 9,
    "key": "XF86AudioPlay",
    "dispatcher": "exec",
    "arg": "tam-shell media previous",
    "action": "Return to the previous track in the active media player.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the previous track key with Alt for a finer adjustment."
  },
  {
    "mask": 0,
    "key": "XF86Eject",
    "dispatcher": "exec",
    "arg": "eject",
    "action": "Eject removable media when supported.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the eject media key."
  },
  {
    "mask": 1,
    "key": "XF86AudioMute",
    "dispatcher": "exec",
    "arg": "tam-audio-output-switch",
    "action": "Cycle audio outputs, such as speakers and headphones.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the switch audio output key with Shift for the alternate action."
  },
  {
    "mask": 1,
    "key": "XF86AudioPause",
    "dispatcher": "exec",
    "arg": "tam-audio-source-switch",
    "action": "Choose which media player receives playback controls.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the switch media source key with Shift for the alternate action."
  },
  {
    "mask": 1,
    "key": "XF86AudioPlay",
    "dispatcher": "exec",
    "arg": "tam-audio-source-switch",
    "action": "Choose which media player receives playback controls.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the switch media source key with Shift for the alternate action."
  },
  {
    "mask": 68,
    "key": "V",
    "dispatcher": "exec",
    "arg": "tam-shell clipboard toggle",
    "action": "Open clipboard history to find and reuse copied items.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember V for clipboard manager."
  },
  {
    "mask": 64,
    "key": "Q",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.close()",
    "action": "Close the focused window when you are finished with it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember Q for close window."
  },
  {
    "mask": 64,
    "key": "BACKSPACE",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.close()",
    "action": "Close the focused window when you are finished with it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use BACKSPACE for close window."
  },
  {
    "mask": 12,
    "key": "DELETE",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-close-all",
    "action": "Close all windows on the current workspace.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use DELETE for close all windows."
  },
  {
    "mask": 64,
    "key": "J",
    "dispatcher": "lua",
    "arg": "hl.dsp.layout(\"togglesplit\")",
    "action": "Toggle window split. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember J for toggle window split."
  },
  {
    "mask": 64,
    "key": "P",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.pseudo()",
    "action": "Toggle the pseudo-tiled size of the focused window.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember P for pseudo window."
  },
  {
    "mask": 64,
    "key": "T",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.float({ action = \"toggle\" })",
    "action": "Toggle window floating/tiling. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember T for toggle window floating/tiling."
  },
  {
    "mask": 64,
    "key": "F",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.fullscreen({ mode = \"fullscreen\" })",
    "action": "Toggle fullscreen for the focused window.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember F for full screen."
  },
  {
    "mask": 68,
    "key": "F",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-tiled-fullscreen-toggle",
    "action": "Expand a tiled window within the workspace while retaining the bar.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember F for tiled full screen."
  },
  {
    "mask": 72,
    "key": "F",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.fullscreen({ mode = \"maximized\" })",
    "action": "Maximize the focused window without using true fullscreen.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember F for full width."
  },
  {
    "mask": 64,
    "key": "O",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-pop",
    "action": "Float and pin the focused window so it stays visible across workspaces.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember O for pop window out (float & pin)."
  },
  {
    "mask": 72,
    "key": "Home",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-width save",
    "action": "Remember the current window width for later restoration.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Home for save window width."
  },
  {
    "mask": 64,
    "key": "Home",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-width restore",
    "action": "Restore the previously saved window width.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Home for restore window width."
  },
  {
    "mask": 64,
    "key": "L",
    "dispatcher": "exec",
    "arg": "tam-hyprland-workspace-layout-toggle",
    "action": "Toggle workspace layout. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember L for toggle workspace layout."
  },
  {
    "mask": 64,
    "key": "LEFT",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ direction = \"l\" })",
    "action": "Focus left window, so you can work there.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 64,
    "key": "RIGHT",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ direction = \"r\" })",
    "action": "Focus right window, so you can work there.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 64,
    "key": "UP",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ direction = \"u\" })",
    "action": "Focus above window, so you can work there.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 64,
    "key": "DOWN",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ direction = \"d\" })",
    "action": "Focus below window, so you can work there.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 64,
    "key": "code:10",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"1\" })",
    "action": "Switch to workspace 1 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:10",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"1\" })",
    "action": "Move the focused window to workspace 1 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:10",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"1\" })",
    "action": "Move the focused window to workspace 1 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:11",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"2\" })",
    "action": "Switch to workspace 2 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:11",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"2\" })",
    "action": "Move the focused window to workspace 2 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:11",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"2\" })",
    "action": "Move the focused window to workspace 2 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:12",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"3\" })",
    "action": "Switch to workspace 3 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:12",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"3\" })",
    "action": "Move the focused window to workspace 3 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:12",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"3\" })",
    "action": "Move the focused window to workspace 3 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:13",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"4\" })",
    "action": "Switch to workspace 4 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:13",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"4\" })",
    "action": "Move the focused window to workspace 4 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:13",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"4\" })",
    "action": "Move the focused window to workspace 4 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:14",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"5\" })",
    "action": "Switch to workspace 5 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:14",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"5\" })",
    "action": "Move the focused window to workspace 5 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:14",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"5\" })",
    "action": "Move the focused window to workspace 5 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:15",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"6\" })",
    "action": "Switch to workspace 6 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:15",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"6\" })",
    "action": "Move the focused window to workspace 6 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:15",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"6\" })",
    "action": "Move the focused window to workspace 6 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:16",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"7\" })",
    "action": "Switch to workspace 7 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:16",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"7\" })",
    "action": "Move the focused window to workspace 7 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:16",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"7\" })",
    "action": "Move the focused window to workspace 7 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:17",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"8\" })",
    "action": "Switch to workspace 8 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:17",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"8\" })",
    "action": "Move the focused window to workspace 8 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:17",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"8\" })",
    "action": "Move the focused window to workspace 8 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:18",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"9\" })",
    "action": "Switch to workspace 9 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:18",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"9\" })",
    "action": "Move the focused window to workspace 9 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:18",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"9\" })",
    "action": "Move the focused window to workspace 9 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "code:19",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"10\" })",
    "action": "Switch to workspace 10 to view its windows.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Super switches there."
  },
  {
    "mask": 65,
    "key": "code:19",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ workspace = \"10\" })",
    "action": "Move the focused window to workspace 10 and follow it.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Shift moves the window."
  },
  {
    "mask": 12,
    "key": "code:19",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"10\" })",
    "action": "Move the focused window to workspace 10 while staying on this workspace.",
    "why": "Number keys identify the destination workspace; modifiers distinguish switching and moving.",
    "mnemonic": "Choose the workspace number; Ctrl+Alt moves without following."
  },
  {
    "mask": 64,
    "key": "S",
    "dispatcher": "lua",
    "arg": "hl.dsp.workspace.toggle_special(\"scratchpad\")",
    "action": "Toggle scratchpad. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember S for toggle scratchpad."
  },
  {
    "mask": 72,
    "key": "S",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ follow = false, workspace = \"special:scratchpad\" })",
    "action": "Move window to scratchpad. Use this to arrange your workspace.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember S for move window to scratchpad."
  },
  {
    "mask": 64,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"e+1\" })",
    "action": "Switch to the next workspace.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for next workspace."
  },
  {
    "mask": 65,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"e-1\" })",
    "action": "Switch to the previous workspace.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for previous workspace."
  },
  {
    "mask": 68,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"previous\" })",
    "action": "Return to the workspace you used previously.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for former workspace."
  },
  {
    "mask": 9,
    "key": "LEFT",
    "dispatcher": "lua",
    "arg": "hl.dsp.workspace.move({ monitor = \"l\" })",
    "action": "Move workspace to left monitor. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 9,
    "key": "RIGHT",
    "dispatcher": "lua",
    "arg": "hl.dsp.workspace.move({ monitor = \"r\" })",
    "action": "Move workspace to right monitor. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 9,
    "key": "UP",
    "dispatcher": "lua",
    "arg": "hl.dsp.workspace.move({ monitor = \"u\" })",
    "action": "Move workspace to up monitor. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 9,
    "key": "DOWN",
    "dispatcher": "lua",
    "arg": "hl.dsp.workspace.move({ monitor = \"d\" })",
    "action": "Move workspace to down monitor. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 65,
    "key": "LEFT",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.swap({ direction = \"l\" })",
    "action": "Swap window to the left. Use this to adjust the active layout.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 65,
    "key": "RIGHT",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.swap({ direction = \"r\" })",
    "action": "Swap window to the right. Use this to adjust the active layout.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 65,
    "key": "UP",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.swap({ direction = \"u\" })",
    "action": "Swap window up. Use this to adjust the active layout.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 65,
    "key": "DOWN",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.swap({ direction = \"d\" })",
    "action": "Swap window down. Use this to adjust the active layout.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 8,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.cycle_next()",
    "action": "Focus next window, so you can work there.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for focus on next window."
  },
  {
    "mask": 9,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.cycle_next({ next = false })",
    "action": "Focus previous window, so you can work there.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for focus on previous window."
  },
  {
    "mask": 8,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.bring_to_top()",
    "action": "Raise the focused window so it is visible.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for reveal active window on top."
  },
  {
    "mask": 9,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.bring_to_top()",
    "action": "Raise the focused window so it is visible.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for reveal active window on top."
  },
  {
    "mask": 72,
    "key": "Next",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ monitor = \"+1\" })",
    "action": "Focus next monitor, so you can work there.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Next for focus on next monitor."
  },
  {
    "mask": 72,
    "key": "Prior",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ monitor = \"-1\" })",
    "action": "Focus previous monitor, so you can work there.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Prior for focus on previous monitor."
  },
  {
    "mask": 64,
    "key": "comma",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = -100, y = 0 })",
    "action": "Expand window left. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the left key moves the edge left or up."
  },
  {
    "mask": 64,
    "key": "period",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 100, y = 0 })",
    "action": "Shrink window left. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the right key moves the edge right or down."
  },
  {
    "mask": 64,
    "key": "semicolon",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = -100 })",
    "action": "Shrink window up. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the left key moves the edge left or up."
  },
  {
    "mask": 64,
    "key": "apostrophe",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = 100 })",
    "action": "Expand window down. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the right key moves the edge right or down."
  },
  {
    "mask": 72,
    "key": "comma",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = -25, y = 0 })",
    "action": "Expand window left a little. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the left key moves the edge left or up."
  },
  {
    "mask": 72,
    "key": "period",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 25, y = 0 })",
    "action": "Shrink window left a little. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the right key moves the edge right or down."
  },
  {
    "mask": 72,
    "key": "semicolon",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = -25 })",
    "action": "Shrink window up a little. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the left key moves the edge left or up."
  },
  {
    "mask": 72,
    "key": "apostrophe",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = 25 })",
    "action": "Expand window down a little. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the right key moves the edge right or down."
  },
  {
    "mask": 68,
    "key": "comma",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = -300, y = 0 })",
    "action": "Expand window left a lot. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the left key moves the edge left or up."
  },
  {
    "mask": 68,
    "key": "period",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 300, y = 0 })",
    "action": "Shrink window left a lot. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Comma and period adjust width; the right key moves the edge right or down."
  },
  {
    "mask": 68,
    "key": "semicolon",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = -300 })",
    "action": "Shrink window up a lot. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the left key moves the edge left or up."
  },
  {
    "mask": 68,
    "key": "apostrophe",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize({ relative = true, x = 0, y = 300 })",
    "action": "Expand window down a lot. Use this to adjust the active layout.",
    "why": "Adjacent punctuation keys form a direction pair; Alt makes a small step and Ctrl a large step.",
    "mnemonic": "Semicolon and apostrophe adjust height; the right key moves the edge right or down."
  },
  {
    "mask": 64,
    "key": "mouse_down",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"e+1\" })",
    "action": "Switch forward through workspaces with the mouse wheel.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use mouse_down for scroll active workspace forward."
  },
  {
    "mask": 64,
    "key": "mouse_up",
    "dispatcher": "lua",
    "arg": "hl.dsp.focus({ workspace = \"e-1\" })",
    "action": "Switch backward through workspaces with the mouse wheel.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use mouse_up for scroll active workspace backward."
  },
  {
    "mask": 64,
    "key": "mouse:272",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.drag()",
    "action": "Move window. Use this to arrange your workspace.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use mouse:272 for move window."
  },
  {
    "mask": 64,
    "key": "mouse:273",
    "dispatcher": "exec",
    "arg": "tam-menu toggle start",
    "action": "Open Start with Quick Launch and desktop appearance settings.",
    "why": "The same menu is available over apps and on unused bar space.",
    "mnemonic": "Super plus right-click opens Start anywhere."
  },
  {
    "mask": 72,
    "key": "mouse:273",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.resize()",
    "action": "Drag the focused window edge to resize it.",
    "why": "Alt distinguishes resizing from the Start menu on Super plus right-click.",
    "mnemonic": "Add Alt to Super plus right-drag to resize."
  },
  {
    "mask": 64,
    "key": "G",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.toggle()",
    "action": "Toggle window grouping. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember G for toggle window grouping."
  },
  {
    "mask": 72,
    "key": "G",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ out_of_group = true })",
    "action": "Move active window out of group. Use this to arrange your workspace.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember G for move active window out of group."
  },
  {
    "mask": 72,
    "key": "LEFT",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ into_group = \"l\" })",
    "action": "Move window to group on left. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 72,
    "key": "RIGHT",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ into_group = \"r\" })",
    "action": "Move window to group on right. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 72,
    "key": "UP",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ into_group = \"u\" })",
    "action": "Move window to group on top. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 72,
    "key": "DOWN",
    "dispatcher": "lua",
    "arg": "hl.dsp.window.move({ into_group = \"d\" })",
    "action": "Move window to group on bottom. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 72,
    "key": "TAB",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.next()",
    "action": "Select the next window in the current window group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use TAB for next window in group."
  },
  {
    "mask": 68,
    "key": "LEFT",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.prev()",
    "action": "Move grouped window focus left. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 68,
    "key": "RIGHT",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.next()",
    "action": "Move grouped window focus right. Use this to arrange your workspace.",
    "why": "Arrow keys map directly to the direction of the action.",
    "mnemonic": "Press the arrow pointing where you want to go."
  },
  {
    "mask": 72,
    "key": "mouse_down",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.next()",
    "action": "Select the next window in the current window group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use mouse_down for next window in group."
  },
  {
    "mask": 72,
    "key": "mouse_up",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.prev()",
    "action": "Select the previous window in the current window group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use mouse_up for previous window in group."
  },
  {
    "mask": 72,
    "key": "code:10",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.active({ index = 1 })",
    "action": "Select window 1 within the current group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 10 for switch to group window 1."
  },
  {
    "mask": 72,
    "key": "code:11",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.active({ index = 2 })",
    "action": "Select window 2 within the current group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 11 for switch to group window 2."
  },
  {
    "mask": 72,
    "key": "code:12",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.active({ index = 3 })",
    "action": "Select window 3 within the current group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 12 for switch to group window 3."
  },
  {
    "mask": 72,
    "key": "code:13",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.active({ index = 4 })",
    "action": "Select window 4 within the current group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 13 for switch to group window 4."
  },
  {
    "mask": 72,
    "key": "code:14",
    "dispatcher": "lua",
    "arg": "hl.dsp.group.active({ index = 5 })",
    "action": "Select window 5 within the current group.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 14 for switch to group window 5."
  },
  {
    "mask": 64,
    "key": "SLASH",
    "dispatcher": "exec",
    "arg": "tam-hyprland-monitor-scaling up",
    "action": "Increase display scaling to make interface elements larger.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SLASH for monitor scaling up."
  },
  {
    "mask": 72,
    "key": "SLASH",
    "dispatcher": "exec",
    "arg": "tam-hyprland-monitor-scaling down",
    "action": "Decrease display scaling to fit more on the screen.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SLASH for monitor scaling down."
  },
  {
    "mask": 64,
    "key": "SPACE",
    "dispatcher": "exec",
    "arg": "tam-menu toggle",
    "action": "Open the main menu to find applications and system actions.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SPACE for tamlinux menu."
  },
  {
    "mask": 72,
    "key": "SPACE",
    "dispatcher": "exec",
    "arg": "tam-menu toggle apps",
    "action": "Open the applications menu to launch an app.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SPACE for apps menu."
  },
  {
    "mask": 68,
    "key": "E",
    "dispatcher": "exec",
    "arg": "tam-shell emojis toggle",
    "action": "Open the emoji picker and insert a symbol.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember E for emojis."
  },
  {
    "mask": 68,
    "key": "C",
    "dispatcher": "exec",
    "arg": "tam-menu toggle capture",
    "action": "Open screen capture options for a screenshot or recording.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember C for capture menu."
  },
  {
    "mask": 68,
    "key": "O",
    "dispatcher": "exec",
    "arg": "tam-menu toggle toggle",
    "action": "Toggle menu. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember O for toggle menu."
  },
  {
    "mask": 68,
    "key": "H",
    "dispatcher": "exec",
    "arg": "tam-menu toggle hardware",
    "action": "Open controls for hardware and devices.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember H for hardware menu."
  },
  {
    "mask": 65,
    "key": "code:201",
    "dispatcher": "exec",
    "arg": "tam-menu toggle root",
    "action": "Open the main menu to find applications and system actions.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 201 for tamlinux menu."
  },
  {
    "mask": 64,
    "key": "ESCAPE",
    "dispatcher": "exec",
    "arg": "tam-menu toggle system",
    "action": "Open session and power actions.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use ESCAPE for system menu."
  },
  {
    "mask": 0,
    "key": "XF86PowerOff",
    "dispatcher": "exec",
    "arg": "tam-menu toggle system",
    "action": "Open session and power actions.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the power menu key."
  },
  {
    "mask": 64,
    "key": "K",
    "dispatcher": "exec",
    "arg": "tam-menu-keybindings",
    "action": "Open this explorer to find and inspect shortcuts.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember K for keybindings."
  },
  {
    "mask": 72,
    "key": "K",
    "dispatcher": "exec",
    "arg": "tam-menu-tmux-keybindings",
    "action": "Show shortcuts available inside tmux.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember K for tmux keybindings."
  },
  {
    "mask": 68,
    "key": "K",
    "dispatcher": "exec",
    "arg": "tam-menu-herdr-keybindings",
    "action": "Show shortcuts available inside Herdr.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember K for herdr keybindings."
  },
  {
    "mask": 0,
    "key": "XF86Calculator",
    "dispatcher": "exec",
    "arg": "omacalc",
    "action": "Open the calculator for a quick calculation.",
    "why": "The dedicated hardware key gives quick access to this device control.",
    "mnemonic": "Use the calculator key."
  },
  {
    "mask": 65,
    "key": "SPACE",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggleBar",
    "action": "Toggle top bar. Use it to switch this setting or view.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SPACE for toggle top bar."
  },
  {
    "mask": 68,
    "key": "SPACE",
    "dispatcher": "exec",
    "arg": "tam-menu toggle background",
    "action": "Choose a desktop background.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SPACE for background switcher."
  },
  {
    "mask": 65,
    "key": "T",
    "dispatcher": "exec",
    "arg": "tam-menu toggle theme",
    "action": "Choose a desktop theme.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember T for theme menu."
  },
  {
    "mask": 64,
    "key": "U",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-transparency-toggle",
    "action": "Toggle window transparency. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember U for toggle window transparency."
  },
  {
    "mask": 65,
    "key": "U",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-gaps-toggle",
    "action": "Toggle window gaps. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember U for toggle window gaps."
  },
  {
    "mask": 68,
    "key": "U",
    "dispatcher": "exec",
    "arg": "tam-hyprland-window-single-square-aspect-toggle",
    "action": "Toggle single-window square aspect. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember U for toggle single-window square aspect."
  },
  {
    "mask": 64,
    "key": "N",
    "dispatcher": "exec",
    "arg": "tam-shell notifications dismissOne",
    "action": "Dismiss last notification. Use this to manage notifications.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember N for dismiss last notification."
  },
  {
    "mask": 65,
    "key": "N",
    "dispatcher": "exec",
    "arg": "tam-shell notifications dismissAll",
    "action": "Dismiss all notifications. Use this to manage notifications.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember N for dismiss all notifications."
  },
  {
    "mask": 68,
    "key": "N",
    "dispatcher": "exec",
    "arg": "tam-toggle-notification-silencing",
    "action": "Toggle silencing notifications. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember N for toggle silencing notifications."
  },
  {
    "mask": 72,
    "key": "N",
    "dispatcher": "exec",
    "arg": "tam-shell notifications invokeLast",
    "action": "Invoke last notification. Use this to manage notifications.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember N for invoke last notification."
  },
  {
    "mask": 72,
    "key": "H",
    "dispatcher": "exec",
    "arg": "tam-shell notifications showHistory",
    "action": "Open notification history. Use this to manage notifications.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember H for open notification history."
  },
  {
    "mask": 68,
    "key": "I",
    "dispatcher": "exec",
    "arg": "tam-toggle-idle",
    "action": "Toggle locking on idle. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember I for toggle locking on idle."
  },
  {
    "mask": 68,
    "key": "J",
    "dispatcher": "exec",
    "arg": "tam-toggle-nightlight",
    "action": "Toggle nightlight. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember J for toggle nightlight."
  },
  {
    "mask": 68,
    "key": "Delete",
    "dispatcher": "exec",
    "arg": "tam-hyprland-monitor-internal toggle",
    "action": "Toggle laptop display. Use it to switch this setting or view.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Delete for toggle laptop display."
  },
  {
    "mask": 72,
    "key": "Delete",
    "dispatcher": "exec",
    "arg": "tam-hyprland-monitor-internal-mirror toggle",
    "action": "Toggle laptop display mirroring. Use it to switch this setting or view.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use Delete for toggle laptop display mirroring."
  },
  {
    "mask": 0,
    "key": "PRINT",
    "dispatcher": "exec",
    "arg": "tam-capture-screenshot",
    "action": "Capture a screen region as an image.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use PRINT for screenshot."
  },
  {
    "mask": 8,
    "key": "PRINT",
    "dispatcher": "exec",
    "arg": "tam-capture-screenrecording --stop-recording || tam-menu toggle trigger.capture.screenrecord",
    "action": "Start or stop recording the screen.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use PRINT for screenrecording."
  },
  {
    "mask": 72,
    "key": "code:34",
    "dispatcher": "exec",
    "arg": "tam-capture-webcam-resize smaller",
    "action": "Shrink the webcam overlay during a recording.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 34 for make webcam overlay smaller."
  },
  {
    "mask": 72,
    "key": "code:35",
    "dispatcher": "exec",
    "arg": "tam-capture-webcam-resize larger",
    "action": "Enlarge the webcam overlay during a recording.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 35 for make webcam overlay larger."
  },
  {
    "mask": 64,
    "key": "PRINT",
    "dispatcher": "exec",
    "arg": "pkill hyprpicker || hyprpicker -a",
    "action": "Pick a color from the screen and copy its value.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use PRINT for color picker."
  },
  {
    "mask": 68,
    "key": "PRINT",
    "dispatcher": "exec",
    "arg": "tam-capture-text",
    "action": "Extract text from a selected screen region.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use PRINT for extract text (ocr) from screenshot."
  },
  {
    "mask": 68,
    "key": "S",
    "dispatcher": "exec",
    "arg": "tam-menu toggle share",
    "action": "Open sharing options for files or captured content.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember S for share."
  },
  {
    "mask": 68,
    "key": "Y",
    "dispatcher": "exec",
    "arg": "tam-transcode",
    "action": "Convert a selected image or video to another format.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember Y for transcode."
  },
  {
    "mask": 68,
    "key": "R",
    "dispatcher": "exec",
    "arg": "tam-reminder -i",
    "action": "Open the reminder prompt to schedule a notification.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember R for set reminder."
  },
  {
    "mask": 72,
    "key": "R",
    "dispatcher": "exec",
    "arg": "tam-reminder show",
    "action": "List currently scheduled reminders.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember R for show reminders."
  },
  {
    "mask": 65,
    "key": "R",
    "dispatcher": "exec",
    "arg": "tam-reminder --confirm-clear",
    "action": "Ask before cancelling all scheduled reminders.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember R for clear reminders."
  },
  {
    "mask": 72,
    "key": "T",
    "dispatcher": "exec",
    "arg": "tam-notification-time",
    "action": "Display the current time in a notification.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember T for show time."
  },
  {
    "mask": 72,
    "key": "P",
    "dispatcher": "exec",
    "arg": "tam-notification-battery",
    "action": "Display remaining battery charge in a notification.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember P for show battery remaining."
  },
  {
    "mask": 72,
    "key": "W",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle fred.weather",
    "action": "Toggle weather. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember W for toggle weather."
  },
  {
    "mask": 65,
    "key": "C",
    "dispatcher": "exec",
    "arg": "tam-agent --pick",
    "action": "Open Agent so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember C for agent."
  },
  {
    "mask": 68,
    "key": "A",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle tamlinux.audio",
    "action": "Open the audio panel to manage sound devices and volume.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember A for audio."
  },
  {
    "mask": 68,
    "key": "B",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle tamlinux.bluetooth",
    "action": "Open Bluetooth controls to manage devices.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember B for bluetooth."
  },
  {
    "mask": 68,
    "key": "D",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle fred.monitor",
    "action": "Open display controls to manage monitors.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember D for display."
  },
  {
    "mask": 72,
    "key": "D",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle fred.clock",
    "action": "Open the calendar to inspect dates.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember D for calendar."
  },
  {
    "mask": 68,
    "key": "W",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle tamlinux.network",
    "action": "Open network controls to manage connections.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember W for network."
  },
  {
    "mask": 68,
    "key": "P",
    "dispatcher": "exec",
    "arg": "tam-shell tamlinux-shell toggle tamlinux.power",
    "action": "Open power controls to inspect power settings.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember P for power."
  },
  {
    "mask": 68,
    "key": "T",
    "dispatcher": "exec",
    "arg": "tam-launch-tui 'btop'",
    "action": "Open a terminal activity monitor to inspect system usage.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember T for activity."
  },
  {
    "mask": 68,
    "key": "code:10",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 1",
    "action": "Toggle panel 1 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 10 for bar panel 1."
  },
  {
    "mask": 68,
    "key": "code:11",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 2",
    "action": "Toggle panel 2 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 11 for bar panel 2."
  },
  {
    "mask": 68,
    "key": "code:12",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 3",
    "action": "Toggle panel 3 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 12 for bar panel 3."
  },
  {
    "mask": 68,
    "key": "code:13",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 4",
    "action": "Toggle panel 4 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 13 for bar panel 4."
  },
  {
    "mask": 68,
    "key": "code:14",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 5",
    "action": "Toggle panel 5 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 14 for bar panel 5."
  },
  {
    "mask": 68,
    "key": "code:15",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 6",
    "action": "Toggle panel 6 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 15 for bar panel 6."
  },
  {
    "mask": 68,
    "key": "code:16",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 7",
    "action": "Toggle panel 7 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 16 for bar panel 7."
  },
  {
    "mask": 68,
    "key": "code:17",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 8",
    "action": "Toggle panel 8 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 17 for bar panel 8."
  },
  {
    "mask": 68,
    "key": "code:18",
    "dispatcher": "exec",
    "arg": "tam-shell -q tamlinux-shell togglePanelAt right 9",
    "action": "Toggle panel 9 in the bar to view its controls.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use keycode 18 for bar panel 9."
  },
  {
    "mask": 68,
    "key": "L",
    "dispatcher": "exec",
    "arg": "tam-system-lock",
    "action": "Lock the session when leaving the computer.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember L for lock system."
  },
  {
    "mask": 68,
    "key": "X",
    "dispatcher": "exec",
    "arg": "voxtype record toggle",
    "action": "Toggle dictation. Use it to switch this setting or view.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember X for toggle dictation."
  },
  {
    "mask": 0,
    "key": "F9",
    "dispatcher": "exec",
    "arg": "voxtype record start",
    "action": "Start voice dictation while the key is held.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use F9 for start dictation (push-to-talk)."
  },
  {
    "mask": 0,
    "key": "F9",
    "dispatcher": "exec",
    "arg": "voxtype record stop",
    "action": "Stop voice dictation when the key is released.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use F9 for stop dictation (push-to-talk)."
  },
  {
    "mask": 64,
    "key": "RETURN",
    "dispatcher": "exec",
    "arg": "tam-launch-terminal",
    "action": "Open Terminal so you can use it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use RETURN for terminal."
  },
  {
    "mask": 65,
    "key": "RETURN",
    "dispatcher": "exec",
    "arg": "tam-launch-browser",
    "action": "Open Browser so you can use it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use RETURN for browser."
  },
  {
    "mask": 65,
    "key": "F",
    "dispatcher": "exec",
    "arg": "tam-launch-nautilus",
    "action": "Open File manager so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember F for file manager."
  },
  {
    "mask": 72,
    "key": "E",
    "dispatcher": "exec",
    "arg": "tam-launch-nautilus-cwd",
    "action": "Open File manager (cwd) so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember E for file manager (cwd)."
  },
  {
    "mask": 65,
    "key": "B",
    "dispatcher": "exec",
    "arg": "tam-launch-browser",
    "action": "Open Browser so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember B for browser."
  },
  {
    "mask": 72,
    "key": "B",
    "dispatcher": "exec",
    "arg": "tam-launch-browser --private",
    "action": "Open Browser (private) so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember B for browser (private)."
  },
  {
    "mask": 65,
    "key": "E",
    "dispatcher": "exec",
    "arg": "tam-launch-editor",
    "action": "Open Editor so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember E for editor."
  },
  {
    "mask": 72,
    "key": "RETURN",
    "dispatcher": "exec",
    "arg": "tam-launch-terminal-tmux",
    "action": "Open Tmux so you can use it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use RETURN for tmux."
  },
  {
    "mask": 68,
    "key": "RETURN",
    "dispatcher": "exec",
    "arg": "tam-launch-terminal-herdr",
    "action": "Open Herdr so you can use it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use RETURN for herdr."
  },
  {
    "mask": 65,
    "key": "M",
    "dispatcher": "exec",
    "arg": "tam-launch-spotify",
    "action": "Open Music so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember M for music."
  },
  {
    "mask": 72,
    "key": "M",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus-tui 'cliamp'",
    "action": "Open Music TUI so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember M for music tui."
  },
  {
    "mask": 65,
    "key": "D",
    "dispatcher": "exec",
    "arg": "tam-launch-tui 'tam-launch-docker-tui'",
    "action": "Open Docker so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember D for docker."
  },
  {
    "mask": 65,
    "key": "G",
    "dispatcher": "exec",
    "arg": "tam-launch-signal",
    "action": "Open Signal so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember G for signal."
  },
  {
    "mask": 65,
    "key": "O",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus '^obsidian$' 'uwsm-app -- obsidian'",
    "action": "Open Obsidian so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember O for obsidian."
  },
  {
    "mask": 64,
    "key": "E",
    "dispatcher": "exec",
    "arg": "tam-launch-tui 'micro'",
    "action": "Open Micro so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember E for micro."
  },
  {
    "mask": 65,
    "key": "W",
    "dispatcher": "exec",
    "arg": "tam-launch-tui 'micro'",
    "action": "Open Micro so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember W for micro."
  },
  {
    "mask": 65,
    "key": "SLASH",
    "dispatcher": "exec",
    "arg": "tam-launch-1password",
    "action": "Open Passwords so you can use it.",
    "why": "The key keeps this action near related controls or uses a dedicated key.",
    "mnemonic": "Use SLASH for passwords."
  },
  {
    "mask": 65,
    "key": "A",
    "dispatcher": "exec",
    "arg": "tam-launch-webapp 'https://chatgpt.com'",
    "action": "Open ChatGPT so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember A for chatgpt."
  },
  {
    "mask": 72,
    "key": "A",
    "dispatcher": "exec",
    "arg": "tam-launch-webapp 'https://grok.com'",
    "action": "Open Grok so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember A for grok."
  },
  {
    "mask": 65,
    "key": "Y",
    "dispatcher": "exec",
    "arg": "tam-launch-webapp 'https://youtube.com/'",
    "action": "Open YouTube so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember Y for youtube."
  },
  {
    "mask": 72,
    "key": "I",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus-webapp 'WhatsApp' 'https://web.whatsapp.com/'",
    "action": "Open WhatsApp so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember I for whatsapp."
  },
  {
    "mask": 65,
    "key": "I",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus-webapp 'Google Messages' 'https://messages.google.com/web/conversations'",
    "action": "Open Google Messages so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember I for google messages."
  },
  {
    "mask": 65,
    "key": "P",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus-webapp 'Google Photos' 'https://photos.google.com/'",
    "action": "Open Google Photos so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember P for google photos."
  },
  {
    "mask": 65,
    "key": "S",
    "dispatcher": "exec",
    "arg": "tam-launch-or-focus-webapp 'Google Maps' 'https://maps.google.com/'",
    "action": "Open Google Maps so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember S for google maps."
  },
  {
    "mask": 65,
    "key": "X",
    "dispatcher": "exec",
    "arg": "tam-launch-webapp 'https://x.com/'",
    "action": "Open X so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember X for x."
  },
  {
    "mask": 72,
    "key": "X",
    "dispatcher": "exec",
    "arg": "tam-launch-webapp 'https://x.com/compose/post'",
    "action": "Open X Post so you can use it.",
    "why": "The letter groups this action with related shortcuts while its modifiers distinguish the variant.",
    "mnemonic": "Remember X for x post."
  }
]
if (typeof module !== "undefined" && module.exports) module.exports = { entries: entries }
