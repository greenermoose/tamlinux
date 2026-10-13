-- App-specific tweaks.
local paths = require("hypr.tamlinux.paths")
local require_all = require("hypr.tamlinux.require_all")

require_all.files(paths.tamlinux_hypr .. "/apps", "hypr.tamlinux.apps")
