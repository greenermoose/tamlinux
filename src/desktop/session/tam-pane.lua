-- Tamlinux versioned session defaults for tam-pane.
-- Loaded inside tam-pane's sandboxed Lua 5.5 runtime (tp.read_file + load).

tp.config{
  gaps = 8,
  cursor_theme = "Adwaita",
  cursor_size = 24,
  terminal = "/usr/bin/tamlinux/tam-launch-terminal --tam-last",
}

tp.bind("Meta+Return", tp.dsp.spawn("/usr/bin/tamlinux/tam-launch-terminal --tam-last"), { desc = "Terminal" })
tp.bind("Meta+q", tp.dsp.close(), { desc = "Close window" })
tp.bind("Meta+BackSpace", tp.dsp.close(), { desc = "Close window" })
tp.bind("Meta+Space", tp.dsp.spawn("tam-menu toggle"), { desc = "Tamlinux menu" })
tp.bind("Meta+Escape", tp.dsp.spawn("tam-menu toggle system"), { desc = "System menu" })
tp.bind("Print", tp.dsp.spawn("tam-capture-screenshot"), { desc = "Screenshot" })

tp.on("startup", function()
  -- Export WAYLAND_DISPLAY and TAM_PANE_SOCKET to systemd/D-Bus before session services start.
  tp.spawn("uwsm finalize TAM_PANE_SOCKET")
  tp.spawn("tam-powerprofiles-set autodetect")
end)
