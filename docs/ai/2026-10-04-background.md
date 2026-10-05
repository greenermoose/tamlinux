# Session: 2026-10-04 — Desktop background in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Take the next step on the tamlinux project.

  Asked whether the background should go to `swaybg` or be vendored like the
  other services, Fred chose "Vendor into host".

## Key decisions and implementation notes

- The next step in the private plan was the desktop background, the eighth
  shell function to move into the host. An earlier note had sent it to
  `swaybg`, but the shell's background also opens the background picker
  (left double-click) and the theme picker (right double-click) from the bare
  desktop, and reveals a new image with a slanted wipe, and `swaybg` does
  neither. Fred chose to vendor it like the other services, so those keep
  working and it still runs on Sway.
- Vendored from the Omarchy 4.0.4 shell with the MIT notice, together with
  the helper that remaps a surface when its output moves. The IPC target is
  `background` (`refresh`, `set`, `setInstant`, `transition`,
  `themeTransition`, plus `current` and `ping`); the layer is
  `tamlinux-background`.
- The source read its link only at start and when called over IPC. The
  vendored service also watches the link's directory with an `inotifywait`
  child (stopped with the host by `setpriv --pdeathsig`, restarted if it
  exits), so any command that repoints the link changes the background
  without calling the host. `ln -nsf` appears as a rename onto the link
  name, which is the event it filters on.
- The double-clicks open the host menu's `background` and `theme` routes
  instead of running the switcher commands from QML, so the actions are the
  menu's own and run in its scope. The menu service is injected, as the OSD is
  injected into the menu.
- `themeTransition` keeps its five arguments and runs the reveal, but does
  not reload colours, because the host palette comes from `Tam.Commons`.

## Verification

- `python3 -m unittest discover -s desktop/tests`: 61 tests pass.
- A copy of the host ran in a headless nested Sway session with
  `TAMLINUX_BAR=0 TAMLINUX_SERVICES=menu,background`, a scratch link and
  menu tree, and a recording stub for `systemd-run`. Repointing the link with
  `ln -nsf` revealed the new image with the slanted wipe (captured midway and
  at the end), including a file named `two it's $(touch PWNED).jpg`, and
  nothing ran. `setInstant` replaced the image without a wipe. A
  `themeTransition` whose old image had been deleted still wiped from the
  displayed frame. After the watcher was killed it came back within five
  seconds and picked up the change made while it was down.
- Clicks came from a throwaway client on the wlr virtual-pointer protocol
  inside the nested session, because the headless seat has no pointer.
  Single clicks did nothing; a left double-click ran the menu's `background`
  action and a right double-click its `theme` action, each in the scope
  command.
