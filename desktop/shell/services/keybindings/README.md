# Keybinding explorer metadata

`BindingCatalog.js` records suggested descriptions and memory aids for the
packaged Hyprland defaults. The rationales are aids to remembering a mapping,
not claims about its historical origin. Entries identify the modifier mask,
key, dispatcher and complete scanned command. Update the entry whenever one
of those changes; run `test_keybinding_defaults.py` to check coverage of
resolvable defaults. Callback bindings whose commands cannot be recovered
from the compositor deliberately have no inferred metadata.

Personal bindings can be described in
`$XDG_CONFIG_HOME/tamlinux/keybindings-metadata.json` (normally
`~/.config/tamlinux/keybindings-metadata.json`). This optional JSON array has
the same fields as a catalog entry, for example:

```json
[
  {
    "mask": 64,
    "key": "K",
    "dispatcher": "exec",
    "arg": "tam-menu-keybindings",
    "action": "Open the shortcut explorer to find a binding.",
    "why": "K groups the keyboard help shortcuts.",
    "mnemonic": "K for keys."
  }
]
```

Masks use Hyprland's modifier bits: Shift 1, Ctrl 4, Alt 8 and Super 64.
Use the key and dispatcher shown by the compositor scan, including `code:`
keys where used. A user entry takes precedence only when its complete chord,
dispatcher and argument match. Invalid or missing files are ignored; the
explorer does not infer an explanation for an unmatched custom command.
Neither a selected row nor a captured chord is executed by the explorer.
