-- The package owns defaults; user overrides and generated state stay external.
local source = debug.getinfo(1, "S").source:gsub("^@", "")
local root = assert(source:match("^(.*)/entry%.lua$"))
_G.TAMLINUX_HYPR_ROOT = root
for name in pairs(package.loaded) do
  if name == "hypr.tamlinux" or name:sub(1, 14) == "hypr.tamlinux." then
    package.loaded[name] = nil
  end
end
package.path = root .. "/?.lua;" .. package.path
local paths = require("hypr.tamlinux.paths")
package.path = root .. "/?.lua;" .. paths.state_home .. "/?.lua;" .. package.path
require("hypr.tamlinux.defaults")
-- Machine-specific monitors and personal settings are optional, never copied
-- from the computer that built the package.
for _, name in ipairs({"monitors", "input", "bindings", "looknfeel", "autostart", "local"}) do
  local path = paths.config_home .. "/tamlinux/hypr/" .. name .. ".lua"
  local file = io.open(path, "r")
  if file then file:close(); dofile(path) end
end
require("hypr.tamlinux.toggles")
