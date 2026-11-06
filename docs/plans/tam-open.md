# tam-open

Universal file, directory, and URL opener for Tamlinux.

## Behavior

- One target per invocation.
- Graphical lane uses `WAYLAND_DISPLAY` or `DISPLAY`.
- Text console lane uses terminal tools.
- Built-in handlers do not require XDG.
- Optional `xdg-open` is used only for unknown types.

## Handlers

See the target matrix in the 0.6.12 plan: URLs, directories, PDF, images,
audio, video, HTML, text, archives, binary, and unknown types.

## Flags

- `--edit`: use an interactive hex editor for binary files.
- `--help`, `--version`.

## Packaging

Native C command. Links `libmagic`. Runtime tools are declared in
`tamlinux-packages`.
