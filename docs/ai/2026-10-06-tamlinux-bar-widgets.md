# 2026-10-06 — The Tamlinux bar's own widgets (0.3.1)

- **CLI Tool**: Claude Code `2.1.291`.
- **Model**: `claude-opus-5-5`.
- **Role**: implementation and delegation for Tamlinux 0.3.1; agy and
  opencode wrote test suites from Claude's briefs (T18, T17).
- **Commit**: `274a3e7`, `38c9d54`, `eb52bfe`, `282e044`, and this commit.
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > While we're waiting for agy to finish T16, can you get started on the next step of the tamlinux project? What can opencode be doing for you now?

  > Both delegates started; go ahead with your wiring

  > The tooltips for keyboard, monitor and sysinfo disappear off the right side of the screen. It looks like you have not calculated the right edge of the screen and not properly aligned right those tooltip that show when you hover over an icon.

  > I accept 0.3.1

## Work and decisions

- Ported Omarchy's bar layout model (`BarModel.js`) unchanged except the
  tray's id, and drew the bar from a `{ left, center, right }` layout with
  Omarchy's center anchor (`host/BarLayout.qml`). The proof's `--layout`
  draws `bar/default-layout.json`, today's Omarchy bar order.
- Filled the gaps the ported widgets reach: `BarIndicator` and `PopupCard`
  in `Tam.Ui`, the indicator properties on `WidgetButton`, `layoutConfig`,
  the center-hover reveal, `firstPartyServiceFor`, and a night light
  service over `tam-toggle-nightlight`.
- `PopupCard`'s outside-click grab and the keyboard layout widget's
  keyboards and switch come from the compositor facade, so no widget
  imports the compositor; the boundary test's exemption is gone.
- Panel settings are saved in the shell's settings document.
- Fred's test found tooltips running off the right edge: the tooltip was
  aligned to its item's left edge with no right bound. It now centers on the
  item and is clamped inside the bar, and the selftest probes it.

## Verification

- `--selftest` at scale 1, including a layout stage that requires all 15
  entries to register and a long `fred.sysinfo` tooltip to stay on screen
  (it fails on the old placement). Bar screenshots at scale 1 and 1.25.
- 260 desktop tests.
- Fred checked placement, hovers, every widget and panel, the center reveal,
  one popup per screen, outside-click closing, and scale 1.25, and accepted
  0.3.1.
