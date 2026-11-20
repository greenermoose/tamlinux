-- Restore workspace layouts saved by tam-hyprland-workspace-layout-toggle.

local paths = require("hypr.tamlinux.paths")
local require_all = require("hypr.tamlinux.require_all")

local layouts_dir = paths.state_home .. "/tamlinux/workspace-layouts"

require_all.files(layouts_dir, "tamlinux.workspace-layouts", { reload = true })
