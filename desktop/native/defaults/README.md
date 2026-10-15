# Native system defaults

Generic host defaults that a Tamlinux desktop needs on a clean Arch/Hyprland
host. The `tamlinux-native` package installs `root/` verbatim. Values match the
behavior the workstation has today (plan 18, D145, D146); `origins.json`
records each file's source, digest and mode, and `LICENSE-defaults` carries the
MIT notice for the derived files.

Rules this directory keeps:

- **Vendor locations only** (`/usr/lib`, `/usr/share`). An administrator's file
  in `/etc` overrides or masks each one, and removing the package leaves
  nothing behind in `/etc`.
- **Tamlinux names that collide with no other package.** The previous owner's
  files stay installed until Cutover, so both sets must coexist; their values
  are identical, so precedence between them does not matter.
- **Drop-ins, not whole files.** Settings whose only home is a single file
  owned by another package (`faillock.conf`, `nsswitch.conf`,
  `cups-files.conf`, `/etc/skel/.bashrc`, `dirmngr.conf`, Docker
  `daemon.json`, the desktop MIME and terminal lists) are not here. They need
  a preserving adapter with recovery, and so do their pairs: sudo
  `passwd_tries` with faillock, resolved multicast with nsswitch, and the
  resolved Docker stub listener with `daemon.json`.

Two effects need the host as well as these files. `systemd-oomd` is enabled
by `80-tamlinux.preset`, which takes effect only when provisioning runs
`systemctl preset`. The fontconfig rule is linked into `/etc/fonts/conf.d` by
Arch's fontconfig hook from `conf.default/`. `tam-fcitx5` and `tam-bt-agent` are
enabled for every user's graphical session. A user unit of the same name
replaces the vendor one, and `tam-bt-agent` skips itself while any
`bt-agent.service` is active.

The inotify watch limit needs nothing here: Arch's `filesystem` package
already sets `fs.inotify.max_user_watches=524288` in `10-arch.conf`.
