local paths = require("hypr.tamlinux.paths")
local require_all = require("hypr.tamlinux.require_all")

local toggles_dir = paths.state_home .. "/tamlinux/toggles/hypr"
package.path = toggles_dir .. "/?.lua;" .. package.path

-- touchpad-disabled.lua / touchscreen-disabled.lua were generated Lua in older
-- versions and could carry an injected USB device name. They must never be loaded
-- as code again: exclude them so a not-yet-migrated install cannot execute a
-- leftover payload on reload. The migration recovers the name and deletes them.
require_all.files(toggles_dir, nil, {
  reload = true,
  exclude = {
    ["touchpad-disabled"] = true,
    ["touchscreen-disabled"] = true,
  },
})

local disabled_input_device = require("hypr.tamlinux.disabled-input-device")
disabled_input_device("touchpad")
disabled_input_device("touchscreen")

require("hypr.tamlinux.workspace-layouts")
