local paths = require("hypr.tamlinux.paths")
local require_optional = require("hypr.tamlinux.require_optional")

-- GUM environment variables for styling purposes.
local function apply_theme_file(name)
  local path = paths.state_home .. "/tamlinux/current/theme/" .. name .. ".lua"
  local file = io.open(path, "r")
  if file then file:close(); dofile(path) end
end
apply_theme_file("gum_env")

-- Cursor size.
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Force all apps to use Wayland.
hl.env("GDK_BACKEND", "wayland,x11,*")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "gtk3")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "wayland")
hl.env("OZONE_PLATFORM", "wayland")
hl.env("XDG_SESSION_TYPE", "wayland")

-- Allow better support for screen sharing (Google Meet, Discord, etc).
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-- Use XCompose file.
hl.env("XCOMPOSEFILE", paths.home .. "/.XCompose")

-- The key dispatcher and bar execute the same installed workspace engine.
-- Keep mutation permission explicit; isolated proofs leave it off.
hl.env("TAMLINUX_COMPOSITOR_COMMANDS", paths.home .. "/.local/share/tamlinux/shell/host")
hl.env("TAMLINUX_COMPOSITOR_LIVE_ACTIONS", "1")
hl.env("TAMLINUX_BIN", paths.home .. "/.local/bin")

-- The owned session and its native shortcut writer share this explicit signal.
hl.env("TAMLINUX_SESSION", "1")
local bin_dir = paths.home .. "/.local/bin"
local kept = {}
for entry in (os.getenv("PATH") or "/usr/local/bin:/usr/bin"):gmatch("[^:]+") do
  if entry ~= bin_dir then table.insert(kept, entry) end
end
table.insert(kept, 1, bin_dir)
hl.env("PATH", table.concat(kept, ":"))

hl.config({
  xwayland = {
    force_zero_scaling = true,
  },

  ecosystem = {
    no_update_news = true,
  },
})
