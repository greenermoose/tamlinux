-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/

local active_border_color = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 }
local inactive_border_color = "rgba(595959aa)"

hl.config({
  general = {
    gaps_in = 5,
    gaps_out = 10,
    border_size = 2,

    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },

    resize_on_border = false,
    allow_tearing = false,
    layout = "dwindle",
  },

  decoration = {
    rounding = 4,

    shadow = {
      enabled = false,
    },

    blur = {
      enabled = false,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },

    groupbar = {
      font_size = 12,
      font_family = "monospace",
      font_weight_active = "ultraheavy",
      font_weight_inactive = "normal",
      indicator_height = 1,
      indicator_gap = 5,
      height = 22,
      gaps_in = 5,
      gaps_out = 0,
      text_color = "rgb(ffffff)",
      text_color_inactive = "rgba(ffffff90)",
      col = {
        active = "rgba(00000040)",
        inactive = "rgba(00000020)",
      },
      gradients = false,
      gradient_rounding = 0,
      gradient_round_only_edges = false,
    },
  },

  animations = {
    enabled = false,
  },
})

hl.config({
  dwindle = {
    preserve_split = true,
    force_split = 2,
  },

  scrolling = {
    column_width = 0.49,
  },

  master = {
    new_status = "master",
  },

  misc = {
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    disable_scale_notification = true,
    focus_on_activate = true,
    anr_missed_pings = 3,
    on_focus_under_fullscreen = 1,
    initial_workspace_tracking = 0,
    -- Let a fresh shell re-acquire the session lock after the lock client
    -- died, so omarchy-restart-shell can recover the LOCK failsafe.
    allow_session_lock_restore = true,
  },
})

-- K47: Hyprland 0.57+ plays canberra on every xdg-system-bell; mute it so
-- terminal BEL does not chime (Omarchy c019850d). Absent on 0.56.x.
do
  local major, minor = 0, 0
  local handle = io.popen("/usr/bin/Hyprland --version 2>/dev/null")
  if handle then
    local out = handle:read("*a") or ""
    handle:close()
    major = tonumber(out:match("(%d+)%.%d+")) or 0
    minor = tonumber(out:match("%d+%.(%d+)")) or 0
  end
  if major > 0 or minor >= 57 then
    hl.config({
      misc = {
        bell_sound = "none",
      },
    })
  end
end

hl.config({
  cursor = {
    hide_on_key_press = true,
    warp_on_change_workspace = 1,
  },

  binds = {
    hide_special_on_workspace_change = true,
  },
})

-- K25: accessible titlebar Close / Float / Maximize on windows without
-- client decorations. hyprbars has no native right-click menu, so the three
-- actions are explicit bar buttons. Degrades to no bars when the plugin is
-- missing or ABI-stale (see hyprland-plugin-abi runbook).
local hyprbars = "/usr/lib/libhyprbars.so"

local function hyprbars_usable()
  local so = io.open(hyprbars, "r")
  if not so then return false end
  so:close()

  local state = io.open("/var/lib/hyprland-plugin-abi/status", "r")
  if not state then return true end
  local verdict = state:read("*l") or ""
  state:close()

  return verdict:match("^%s*(.-)%s*$") ~= "stale"
end

if hyprbars_usable() then
  hl.plugin.load(hyprbars)

  local function theme_color(name, fallback)
    local path = os.getenv("HOME") .. "/.local/state/tamlinux/current/theme/colors.toml"
    local file = io.open(path, "r")
    if not file then return fallback end

    local value = fallback
    for line in file:lines() do
      local key, hex = line:match('^%s*([%w_]+)%s*=%s*"#(%x%x%x%x%x%x)"')
      if key == name then value = "rgb(" .. hex .. ")" end
    end
    file:close()
    return value
  end

  local bar_bg = theme_color("dark_background", "rgb(1a1a1a)")
  local text = theme_color("foreground", "rgb(cccccc)")
  local close_bg = theme_color("red", "rgb(ff5345)")

  hl.config({
    plugin = {
      hyprbars = {
        bar_height = 26,
        bar_color = bar_bg,
        col = { text = text },
        bar_text_size = 10,
        bar_text_font = "JetBrainsMono Nerd Font",
        bar_text_align = "center",
        bar_buttons_alignment = "right",
        bar_part_of_window = true,
        bar_precedence_over_border = true,
        bar_button_padding = 8,
        on_double_click = "hyprctl dispatch fullscreen 1",
      },
    },
  })

  -- Buttons render right to left; first added sits furthest right.
  local function bar_button(fg, letter, action)
    hl.plugin.hyprbars.add_button({
      bg_color = "rgba(00000000)",
      fg_color = fg,
      size = 18,
      icon = letter,
      action = action,
    })
  end

  bar_button(close_bg, "X", "hyprctl dispatch 'hl.dsp.window.close()'")
  bar_button(text, "F", "hyprctl dispatch 'hl.dsp.window.float({ action = \"toggle\" })'")
  bar_button(text, "M", "hyprctl dispatch fullscreen 1")

  -- Bars only on terminal-tagged windows (foot and friends have no client
  -- headerbar). Chromium, Cursor and other GTK/Electron apps keep their own.
  o.window({ tag = "negative:terminal" }, { ["hyprbars:no_bar"] = true })
end
