# Scoped milestone label — 2026-10-20

- Tool: Codex CLI `0.163.0`; model `gpt-6.1-sol`, dynamically checked.
- Transcript: Retained privately by the author.
- Prompt:
  > Please update 0.4.4 so that the top bar display says Tamlinux 0.4.4 instead of 0.4.4l. I know that is a change from the 0.4.4l that was approved to Run. Also, I've changed back my time format to 24 hour.
- Candidate choice:
  > Prepare display-only 0.4.4m (recommended).

`fred.tamversion` 0.1.1 adds `milestoneVersion`, a three-part display setting
that applies only when it matches the running package's version series.
Setting `0.4.4` shows `Tamlinux 0.4.4` for that series while deployment records
retain the exact candidate identity. Another series, malformed settings or
missing package metadata retain the original full-version/unknown behavior.
The clock implementation and its configured 24-hour format are unchanged.

The product takes the selected `0.4.4-m` candidate identity. No native code,
sleep/recovery helper, command or other plugin implementation changes. The
existing component revisions are retained for package preparation; source
tests are not a claim of workstation Test or Run activation.

Verification: all 11 widget-proof tests pass, including actual offscreen
rendering of the milestone label, future candidate label, invalid override
and missing metadata. The complete desktop suite passes 629 tests, with one
historical adapter check skipped. Offscreen tests supply a host-style settings
object to the real widget rather than copying its formatting logic.

Checked against: `desktop/plugins/fred.tamversion/`, shared `BarWidget` settings
API, `desktop/tests/test_widget_proof.py`, actual test output and installed
package-version sourcing. Packaging and activation results are separate.
