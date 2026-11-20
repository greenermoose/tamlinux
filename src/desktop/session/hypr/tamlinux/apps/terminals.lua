-- Define terminal tag so themes and bindings can single terminals out. TUIs and
-- menu terminals run under dedicated app-ids (org.tamlinux.btop,
-- org.tamlinux.terminal, the inherited org.omarchy.*, TUI.float, ...), so
-- match those too.
-- The class is matched in full, so foot's other app-id needs spelling out.
o.window(
  "(Alacritty|kitty|com.mitchellh.ghostty|foot|org\\.codeberg\\.dnkl\\.foot|wezterm|org\\.tamlinux\\..*|TUI\\..*)",
  { tag = "+terminal" }
)
