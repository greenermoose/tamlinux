/* GTK 4/libadwaita prototype: generated, but not installed as user CSS. */
:root {
  --window-fg-color: {{ foreground }};
  --window-bg-color: {{ background }};
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
