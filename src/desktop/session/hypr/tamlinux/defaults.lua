-- Tamlinux Hyprland defaults (ported from Omarchy): helpers, defaults, and
-- current theme overrides.

require("hypr.tamlinux.helpers")
local require_optional = require("hypr.tamlinux.require_optional")

-- Use Omarchy defaults, but don't edit these directly.
require("hypr.tamlinux.autostart")
if _G.tamlinux_default_bindings ~= false then
  require("hypr.tamlinux.bindings.media")
  require("hypr.tamlinux.bindings.clipboard")
  require("hypr.tamlinux.bindings.tiling")
  require("hypr.tamlinux.bindings.utilities")
  require("hypr.tamlinux.bindings.voxtype")
  require_optional.module("hypr.tamlinux.bindings.applications")
end
require("hypr.tamlinux.envs")
require("hypr.tamlinux.looknfeel")
require("hypr.tamlinux.input")
require("hypr.tamlinux.windows")

-- Current theme overrides.
local paths = require("hypr.tamlinux.paths")
local path = paths.state_home .. "/tamlinux/current/theme/hyprland.lua"
local file = io.open(path, "r")
if file then file:close(); dofile(path) end
