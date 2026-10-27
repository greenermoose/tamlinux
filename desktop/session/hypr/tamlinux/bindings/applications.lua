-- Essential application bindings.
o.bind("SUPER + RETURN", "Terminal", { launcher = "terminal" })
o.bind("SUPER + SHIFT + RETURN", "Browser", { launcher = "browser" })
o.bind("SUPER + SHIFT + F", "File manager", { launcher = "nautilus" })
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)", { launcher = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { launcher = "browser" })
o.bind("SUPER + SHIFT + ALT + B", "Browser (private)", { launcher = "browser --private" })
o.bind("SUPER + SHIFT + N", "Editor", { launcher = "editor" })

if o.preinstalled_bindings_enabled() then
  -- Bindings for preinstalled Omarchy applications, TUIs, and web apps.
  o.bind("SUPER + ALT + RETURN", "Tmux", { launcher = "terminal-tmux" })
  o.bind("SUPER + CTRL + RETURN", "Herdr", { launcher = "terminal-herdr" })
  o.bind("SUPER + SHIFT + M", "Music", { launcher = "spotify" })
  o.bind("SUPER + SHIFT + ALT + M", "Music TUI", { tui = "cliamp", focus = true })
  o.bind("SUPER + SHIFT + D", "Docker", { tui = "tam-launch-docker-tui" })
  o.bind("SUPER + SHIFT + G", "Signal", { launcher = "signal" })
  o.bind("SUPER + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
  o.bind("SUPER + SHIFT + W", "Micro", { tui = "micro" })
  o.bind("SUPER + SHIFT + SLASH", "Passwords", { launcher = "1password" })
end
