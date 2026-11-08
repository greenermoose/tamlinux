# Console palette

`tamlinux-vt.vtrgb` is the Tamlinux 16-color palette for the Linux text
console (VT). It replaces the kernel's stock colors, where dark blue is
only about 2.2:1 against black and dark red and dark magenta are not much
better. Every text color here is at least 4.1:1 against the background.

Planned as the default from Tamlinux 0.6.19. How it is loaded at startup
is not decided yet; until then it is source only.

## Format

The file is in `setvtrgb(8)` format: three lines (red, green, blue), each
with 16 comma-separated decimal values, one per color slot 0 to 15.

- Apply to every VT (root): `setvtrgb share/console/tamlinux-vt.vtrgb`
- Apply to the current VT only, without root: print `ESC ] P n rrggbb`
  for each slot `n` (hex digit 0 to f).
- Reset the current VT to the kernel defaults: `printf '\033]R'`

## Colors

Contrast is the WCAG ratio against the background, color 0.

| Slot | Name | Color | Contrast |
| --- | --- | --- | --- |
| 0 | black | `#121212` | 1.0:1 |
| 1 | red | `#e06c6c` | 5.8:1 |
| 2 | green | `#6cc96c` | 9.1:1 |
| 3 | yellow | `#d7b04a` | 9.1:1 |
| 4 | blue | `#6f9bff` | 7.0:1 |
| 5 | magenta | `#c88ae0` | 7.3:1 |
| 6 | cyan | `#4fc4c4` | 8.9:1 |
| 7 | white | `#cccccc` | 11.7:1 |
| 8 | bright black | `#767676` | 4.1:1 |
| 9 | bright red | `#ff8f8f` | 8.5:1 |
| 10 | bright green | `#94e894` | 12.7:1 |
| 11 | bright yellow | `#ffe07a` | 14.4:1 |
| 12 | bright blue | `#a3c2ff` | 10.5:1 |
| 13 | bright magenta | `#e8adf7` | 10.5:1 |
| 14 | bright cyan | `#8eeaea` | 13.5:1 |
| 15 | bright white | `#f4f4f4` | 17.0:1 |

Trade-off: colored backgrounds are lighter than the stock ones, so black
text on them reads well but white text on them is weak. Programs that put
white text on blue (for example `mc` or `dialog`) look washed out.
