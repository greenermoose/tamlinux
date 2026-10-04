# Session: 2026-10-04 — OSD service in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > R4.1 looks good. Keep going on the tamlinux project. What's next?

## Key decisions and implementation notes

- The on-screen display and its model are vendored from the Omarchy 4.0.4
  shell with the MIT notice. Behavior and layout are kept. The changes are
  `Tam.Commons` and `Tam.Ui` in place of the Omarchy modules, and the
  `tamlinux-osd` layer namespace. The model file is unchanged apart from its
  header.
- It is a second entry in `TAMLINUX_SERVICES` (`osd`), loaded by static import
  like the notification service. It needs nothing from the shell, so none is
  injected.
- The overlay keeps an empty input mask and no keyboard focus, so it never
  takes clicks or keys from the desktop.

## Verification

- `python3 -m unittest discover -s desktop/tests`: 54 tests pass.
- A throwaway copy of the host, run with `TAMLINUX_BAR=0
  TAMLINUX_SERVICES=osd`, answered `osd ping`, opened on `show`, and mapped a
  `tamlinux-osd` layer. Screenshots of a progress card (volume, 40%) and a
  message card (microphone muted) showed the glyph, bar, and text laid out as
  in the source.
- On the workstation, the services unit restarted with
  `TAMLINUX_SERVICES=notifications,osd`, loaded both services, and kept the
  notification name. A no-op volume change through the binding command opened
  the OSD in the host.
