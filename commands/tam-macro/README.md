# Text macros

`tam-macro` assigns Meta + Alt + a key to text. The explorer provides the
editor; `add`, `remove`, `list`, `replace` (JSON on stdin), and `sync` provide
the same backend for command-line clients.

Keys are validated by libxkbcommon. Punctuation and aliases are normalized:
`/` and `slash` identify one assignment; `Backspace`, `Return`, `F24`,
`KP_Enter`, and `XF86AudioMute` are supported. `code:38` selects a physical
XKB keycode. Record key captures a key under compositor shortcut inhibition;
shifted/keypad keys use physical codes. Generated commands use canonical
names and shell quoting. Macro text never becomes executable code.

Saving validates the complete list, rejects stale editor snapshots, locks
against concurrent writes, writes atomically and checks Hyprland reload and
configuration errors. A failed save restores the previous files. Assigned
macro chords replace existing actions on those chords; the editor shows
which action will be replaced. Retired macro chords remain in the generated
cleanup list, so editing/deleting does not leave old bindings active.

The release handler waits up to two seconds for Meta, Alt, Control and Shift
to be released, without blocking Hyprland. The triggering window identity is carried into the runner; a focus change
cancels delivery, including during process startup.
The runner copies UTF-8 text and uses native Hyprland key dispatch with
explicit modifiers (Ctrl+V, or Shift+Insert in a terminal) and a paired release
to the same application window. Concurrent invocations are rejected rather
than queued into a potentially different target. A failed dispatch is never
retried through another backend, because that can duplicate text.

The macro replaces the clipboard and leaves its text available there. There
is no timed restoration that could race the application. A short post-dispatch
grace period reduces clipboard contention; arbitrary slow applications and
external clipboard writers cannot be acknowledged by this protocol. Targets
must accept paste. Focused layer-shell inputs and applications with custom
paste bindings still need dedicated integration; application-window tests do
not establish those cases. Text containing newlines is pasted verbatim, so
its interpretation belongs to the target application.

## Verification

Run `python3 -B -m unittest discover -s commands/tam-macro/tests -q` and
`python3 -B -m unittest discover -s desktop/tests -p test_keybindings.py -q`
from the repository root. The Lua tests execute generated bindings with a
fake compositor, including held modifiers and focus changes. Injection tests
never send real keyboard input.

`desktop/shell/services/keybindings/proof-macro-save` loads an invisible
Wayland editor and saves Backspace into temporary configuration. It never
reloads Hyprland or injects text.

Physical acceptance requires an ordinary editor, a browser text field and a
terminal editor: Backspace, slash, other punctuation, keypad and function
keys; short and held chords; rapid invocations; focus changes; Unicode and
multiline text; edit, rename, delete and reload. Verify exact text and no
unexpected window or monitor actions. Do not test multiline macros at a
shell prompt.
