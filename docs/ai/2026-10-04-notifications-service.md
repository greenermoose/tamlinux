# Session: 2026-10-04 — Notifications service in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > R3 is done. Proceed to R4 of the tamlinux project.

  Fred then chose, from options the agent offered: "Vendor into host
  (Recommended)" for how the shell's service plugins are replaced, and
  "Notifications (Recommended)" as the first function to move.

## Key decisions and implementation notes

- The notification service, its logic, and its card are vendored from the
  Omarchy 4.0.4 shell with the MIT notice, and adapted to `Tam.Commons` and
  `Tam.Ui`. Behavior is kept; state moves to `~/.local/state/tamlinux/`, the
  colors come from the host palette, and the layer namespace is
  `tamlinux-notifications`.
- Focus-on-click goes through a new named compositor operation,
  `focusApp(name)`, on both adapters, instead of a helper script. The name is
  validated; Hyprland focuses by window address, Sway by an `app_id`
  criterion with no backslashes.
- `Services.qml` loads services by static import. A URL loader failed:
  Quickshell had not scanned the service's `components` directory.
- `TAMLINUX_BAR=0` runs the services beside another shell's bar, so functions
  can move one at a time before the bar itself changes.

## Verification

- `python3 -m unittest discover -s desktop/tests`: 53 tests pass.
- On a private D-Bus session: the host owned the notification name; plain,
  glyph-with-argv, and critical toasts persisted; do-not-disturb silenced into
  history; dismiss, dismiss-all, history replay, and the settings file worked;
  `invokeLast` ran the argv action, recorded `focus-app` for a plain toast, and
  rejected a hostile app name. With live actions on, `focusApp` dispatched a
  focus to the already-focused window.
- On the workstation, run as a user service: it claimed the notification name
  after the previous owner released it, and answered IPC.
