# Wire desktop systemd user unit wants into format-2 bundle target drop-ins

Updates format-2 bundle staging so desktop user units installed under
`/usr/lib/systemd/user/` are pulled in by their declared `[Install] WantedBy=`
targets cleanly alongside vendor default services:

- **`wanted_targets()` & `install()` (`desktop/install-bundle-layout.py`):**
  Reads `[Install] WantedBy=` directives from the staged user units in
  `usr/lib/systemd/user/` (including `tamlinux-shell.service` and
  `tam-crash-watch.service` for `graphical-session.target`, and
  `tamlinux-protocol-shadow-collect.timer` for `timers.target`), merges them
  with vendor `.wants` links from `desktop/native/defaults/origins.json` via
  `copy_vendor_defaults()`, and emits sorted `<target>.d/50-tamlinux-services.conf`
  `[Unit]\nWants=...` drop-ins under `usr/lib/systemd/user/`.
- **Regression test (`desktop/tests/test_product_install.py`):** Asserts that
  `graphical-session.target.d/50-tamlinux-services.conf` wants
  `tam-bt-agent.service`, `tam-crash-watch.service`, `tam-fcitx5.service`, and
  `tamlinux-shell.service`, and that `timers.target.d/50-tamlinux-services.conf`
  wants `tamlinux-protocol-shadow-collect.timer`.

Verification: `test_product_install.py` (4 tests), `test_native_defaults.py`
(8 tests), and `commands/tam-deploy/tests` (130 tests) passed.

- **Date:** 2026-11-14
- **CLI Tool:** Antigravity CLI (`agy`) `1.5.9`
- **Transcript:** Retained privately by the author.
- **Authorship:** AI-assisted implementation and tests.

## Guiding prompts

> Did not come up normally. Mouse on a blank desktop.
