/* GTK 4/libadwaita prototype: generated, but not installed as user CSS. */
:root {
  --window-fg-color: {{ foreground }};
  --window-bg-color: {{ background }};
  --view-fg-color: {{ foreground }};
  --view-bg-color: {{ dark_background }};
  --headerbar-fg-color: {{ foreground }};
  --headerbar-bg-color: {{ dark_background }};
  --headerbar-backdrop-color: {{ dark_background }};
  --sidebar-fg-color: {{ foreground }};
  --sidebar-bg-color: {{ dark_background }};
  --sidebar-backdrop-color: {{ dark_background }};
  --secondary-sidebar-fg-color: {{ foreground }};
  --secondary-sidebar-bg-color: {{ dark_background }};
  --secondary-sidebar-backdrop-color: {{ dark_background }};
  --card-fg-color: {{ foreground }};
  --card-bg-color: {{ dark_background }};
  --dialog-fg-color: {{ foreground }};
  --dialog-bg-color: {{ dark_background }};
  --popover-fg-color: {{ foreground }};
  --popover-bg-color: {{ dark_background }};
  --overview-fg-color: {{ foreground }};
  --overview-bg-color: {{ background }};
  --thumbnail-fg-color: {{ foreground }};
  --thumbnail-bg-color: {{ dark_background }};
  --accent-bg-color: {{ accent }};
  --accent-fg-color: {{ selection_foreground }};
  --error-bg-color: {{ red }};
  --error-fg-color: {{ background }};
  --error-color: {{ red }};
  --destructive-bg-color: {{ red }};
  --destructive-fg-color: {{ background }};
  --destructive-color: {{ red }};
}

text selection {
  background-color: {{ accent }};
  color: {{ selection_foreground }};
}

button.destructive-action {
  background-color: {{ red }};
  color: {{ background }};
}
