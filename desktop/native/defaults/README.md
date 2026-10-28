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
- **Tamlinux-owned names under cultivar paths (D171, D200).** Gate A is
  complete: there is no longer a requirement to coexist with Omarchy-owned
  files. Defaults use Tamlinux names that collide with no other installed
  package; Omarchy packages and servers are not a runtime dependency.
- **Drop-ins, not whole files.** Settings whose only home is a single file
  owned by another package (`faillock.conf`, `nsswitch.conf`,
  `cups-files.conf`, `/etc/skel/.bashrc`, `dirmngr.conf`, Docker
  `daemon.json`, the desktop MIME and terminal lists) are not here. They need
  a preserving adapter with recovery, and so do their pairs: sudo
  `passwd_tries` with faillock, resolved multicast with nsswitch, and the
  resolved Docker stub listener with `daemon.json`. The explicit
  `tam-native-defaults plan|apply|restore|status` adapter now owns those
  authentication, NSS, CUPS and Docker pairs. It validates all destinations,
  checkpoints originals, refuses administrator conflicts, resumes partial
  writes only when their identity matches, and archives later bytes, mode and
  ownership before rollback. It runs separately from package installation;
  services must be quiescent for application/restoration and reloaded separately.
  Checkpoints live under `/var/lib/tamlinux/native-defaults/<label>` and labels
  are single-use. Existing modes and uid/gid survive. Empty directories created
  for absent files can remain after rollback. CUPS is untouched when absent.
  Bash/keyservers belong to `desktop/user-defaults`; terminal/MIME preferences
  belong to the session initializer and preserve existing user selections.

Two effects need the host as well as these files. `systemd-oomd` is enabled
by `80-tamlinux.preset`, which takes effect only when provisioning runs
`systemctl preset`. The fontconfig rule is linked into `/etc/fonts/conf.d` by
Arch's fontconfig hook from `conf.default/`. `tam-fcitx5` and `tam-bt-agent` are
enabled for every user's graphical session. A user unit of the same name
replaces the vendor one, and `tam-bt-agent` skips itself while any
`bt-agent.service` is active.

The login-only 0.4.4-a package retains the 0.4.3-d sleep-hook set. The new
zram-draining hibernation hook is preserved with its regression tests under
[`../deferred/`](../deferred/README.md) for a later sleep/resume candidate.
It is outside `root/` and is not installed by this package.

The inotify watch limit needs nothing here: Arch's `filesystem` package
already sets `fs.inotify.max_user_watches=524288` in `10-arch.conf`.
