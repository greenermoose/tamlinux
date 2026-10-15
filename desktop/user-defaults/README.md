# Per-user defaults

What a Tamlinux user gets in their own home, rather than system-wide (Fred's
decision, 2026-10-15): the bash defaults and the GnuPG keyserver list.

- `bash/` is installed as `~/.config/bash/tamlinux`. `env` sets the user tool
  paths for every shell; `rc` loads `envs`, `shell`, `aliases`, `functions`
  (`fns/*`), `init` and `inputrc` for interactive shells. Ported from Omarchy
  4.0.4's bash defaults (MIT, `LICENSE-bash`) with the inherited environment,
  paths and command completion removed and Tamlinux launchers in place.
- `gnupg/dirmngr.conf` is the keyserver list and quick-connect timeout used
  when `makepkg` fetches signing keys. GnuPG reads the per-user file when it
  exists and the system file otherwise.
- `apply` runs on each user-layer activation and changes a file at most once:
  - `~/.bashrc`, when it is a regular file without the blocks, gets a marked
    env block at the top and a marked rc block at the end. The original is kept
    once in `$XDG_STATE_HOME/tamlinux/user-defaults/bashrc.original`. A link is
    left alone: another manager (such as a consumer configuration) owns it.
  - `~/.gnupg/dirmngr.conf` is written (0600, directory 0700) only when
    missing, and is not recreated after the user deletes it.
  - `apply --remove` takes out exactly the two blocks, keeping every other
    edit, and deletes `dirmngr.conf` only if it is unchanged.

Both home paths are in the settings recovery checkpoint
(`../migration/recovery-paths.json`).
