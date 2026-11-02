-- Essential application bindings.
o.bind("META + RETURN", "Terminal", { launcher = "terminal" })
o.bind("META + SHIFT + RETURN", "Browser", { launcher = "browser" })
o.bind("META + F", "File manager", { launcher = "nautilus" })
o.bind("META + D", "File manager (cwd)", { launcher = "nautilus-cwd" })
o.bind("META + SHIFT + B", "Browser", { launcher = "browser" })
o.bind("META + SHIFT + W", "Browser (private)", { launcher = "browser --private" })
o.bind("META + SHIFT + E", "Editor", { launcher = "editor" })

if o.preinstalled_bindings_enabled() then
  -- Bindings for preinstalled Omarchy applications, TUIs, and web apps.
  o.bind("CTRL + F8", "Tmux", { launcher = "terminal-tmux" })
  o.bind("META + CTRL + RETURN", "Herdr", { launcher = "terminal-herdr" })
  o.bind("META + SHIFT + M", "Music", { launcher = "spotify" })
  o.bind("CTRL + F5", "Music TUI", { tui = "cliamp", focus = true })
  o.bind("META + SHIFT + D", "Docker", { tui = "tam-launch-docker-tui" })
  o.bind("META + SHIFT + G", "Signal", { launcher = "signal" })
  o.bind("META + SHIFT + O", "Obsidian", { launch = "obsidian", focus = "^obsidian$" })
  o.bind("META + E", "Micro", { tui = "micro" })
  o.bind("META + SHIFT + SLASH", "Passwords", { launcher = "1password" })

  o.bind("META + SHIFT + A", "ChatGPT", { webapp = "https://chatgpt.com" })
  o.bind("CTRL + F6", "Grok", { webapp = "https://grok.com" })
  o.bind("META + SHIFT + Y", "YouTube", { webapp = "https://youtube.com/" })
  o.bind("CTRL + F7", "WhatsApp", { webapp = "https://web.whatsapp.com/", focus = true })
  o.bind("META + SHIFT + I", "Google Messages", { webapp = "https://messages.google.com/web/conversations", focus = true })
  o.bind("META + SHIFT + P", "Google Photos", { webapp = "https://photos.google.com/", focus = true })
  o.bind("META + SHIFT + S", "Google Maps", { webapp = "https://maps.google.com/", focus = true })
  o.bind("META + SHIFT + X", "X", { webapp = "https://x.com/" })
  o.bind("CTRL + F10", "X Post", { webapp = "https://x.com/compose/post" })
end
