hl.on("hyprland.start", function()
  -- Slow app launch fix -- set systemd vars before starting session services.
  hl.exec_cmd("uwsm finalize")

  hl.exec_cmd("tam-powerprofiles-set autodetect")
  hl.exec_cmd("systemctl --user start tamlinux-monitor-watch.service")
  hl.exec_cmd(o.launch("udiskie --automount --no-notify --no-tray"))
end)
