# Session: 2026-10-04 — Image picker in the Tamlinux host

- **CLI Tool**: Claude Code (`claude`) `2.1.289`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Start R4.5 of the tamlinux project.

## Key decisions and implementation notes

- The next step in the private plan was the image picker, the fifth Omarchy
  shell function to move into the host. The carousel, its row model, and its
  list helper are vendored from the Omarchy 4.0.4 shell with the MIT notice,
  together with the shell's IPC handler for the picker, which becomes the
  service's own `imagepicker` target (`open`, `preload`, `cancel`, `count`,
  `ping`). The layer is `tamlinux-imagepicker`.
- The directory and service are named `imagepicker`: Quickshell's QML scanner
  rejects a hyphen in a module path, so `image-picker` would not load.
- Behavior is kept: the skewed carousel, labels and type-to-filter when a
  request asks for them, the arrow, Tab, Escape, and Enter keys, preloading,
  and the answer-file and done-file protocol that requesters wait on.
- The answer and done files are now written by a fixed `sh -c` script that
  takes the paths as arguments, instead of by a shell string built with
  quoting, so a file name cannot become shell text.
- The service has no environment defaults: each request names its images.
  The list helper caches under `~/.cache/tamlinux/image-picker`.
- `Tam.Commons` gained `Color.imagePicker` tokens (scrim, text, and the
  selected and unselected borders).

## Verification

- `python3 -m unittest discover -s desktop/tests`: 58 tests pass.
- A copy of the host ran in a headless nested Sway session with its own
  runtime, cache, and state directories and
  `TAMLINUX_BAR=0 TAMLINUX_SERVICES=imagepicker`. Through IPC, a requester
  script, and synthetic keys: the picker opened with the requested image
  selected and its label shown; typing filtered and Backspace edited the
  filter; Enter returned the chosen path; Escape returned an empty answer;
  Left and Right moved; a request by directory (no rows) listed four images;
  `cancel` released a waiting requester; and a second request answered the
  first one empty. A file named `it's $(touch PWNED) a b.jpg` came back
  intact and nothing was executed. Screenshots matched the source layout.
