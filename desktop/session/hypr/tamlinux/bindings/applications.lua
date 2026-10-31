-- Essential application bindings.
o.bind("SUPER + RETURN", "Terminal", { launcher = "terminal" })
o.bind("SUPER + SHIFT + RETURN", "Browser", { launcher = "browser" })
o.bind("SUPER + F", "File manager", { launcher = "nautilus" })
o.bind("SUPER + D", "File manager (cwd)", { launcher = "nautilus-cwd" })
o.bind("SUPER + SHIFT + B", "Browser", { launcher = "browser" })
o.bind("SUPER + SHIFT + W", "Browser (private)", { launcher = "browser --private" })
o.bind("SUPER + SHIFT + E", "Editor", { launcher = "editor" })

if o.preinstalled_bindings_enabled() then
  -- Bindings for preinstalled Omarchy applications, TUIs, and web apps.
  o.bind("CTRL + F8", "Tmux", { launcher = "terminal-tmux" })
  o.bind("SUPER + CTRL + RETURN", "Herdr", { launcher = "terminal-herdr" })
  o.bind("SUPER + SHIFT + M", "Music", { launcher = "spotify" })
  o.bind("CTRL + F5", "Music TUI", { tui = "cliamp", focus = true })
  o.bind("SUPER + SHIFT + D", "Docker", { tui = "tam-launch-docker-tui" })
  o.bind("SUPER + SHIFT + G", "Signal", { launcher = "signal" })
  o.bind("SUPER + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
  o.bind("SUPER + E", "Micro", { tui = "micro" })
  o.bind("SUPER + SHIFT + SLASH", "Passwords", { launcher = "1password" })

  o.bind("SUPER + SHIFT + A", "ChatGPT", { webapp = "https://chatgpt.com" })
  o.bind("CTRL + F6", "Grok", { webapp = "https://grok.com" })
  o.bind("SUPER + SHIFT + Y", "YouTube", { webapp = "https://youtube.com/" })
  o.bind("CTRL + F7", "WhatsApp", { webapp = "https://web.whatsapp.com/", focus = true })
  o.bind("SUPER + SHIFT + I", "Google Messages", { webapp = "https://messages.google.com/web/conversations", focus = true })
  o.bind("SUPER + SHIFT + P", "Google Photos", { webapp = "https://photos.google.com/", focus = true })
  o.bind("SUPER + SHIFT + S", "Google Maps", { webapp = "https://maps.google.com/", focus = true })
  o.bind("SUPER + SHIFT + X", "X", { webapp = "https://x.com/" })
  o.bind("CTRL + F10", "X Post", { webapp = "https://x.com/compose/post" })
end
