# tam-desktop-test

Automated physical desktop test battery for the Tamlinux graphical environment.

## Usage

```bash
# Run the full watchable physical desktop test battery (default pacing):
tam-desktop-test

# Run at double speed:
tam-desktop-test --speed 2.0

# Run specific phases (0..6):
tam-desktop-test --phases 0,1,2,3

# Use a custom staging workspace (default is 10):
tam-desktop-test --workspace 9

# Dry-run without emitting physical inputs:
tam-desktop-test --dry-run

# Emergency Stop (also bound globally to Meta + Shift + Escape):
tam-desktop-test --stop
```

## Emergency Stop Protection

The test battery can be halted immediately at any time by:
1. Pressing the reserved global keybinding **`Meta + Shift + Escape`**.
2. Grabbing or moving the physical mouse (`> 25 px` divergence from synthetic path).
3. Pressing `Ctrl + C` in the controlling terminal.

All held modifiers, keys, and mouse buttons are guaranteed to be released, disposable test windows are closed, and the desktop is restored to its initial workspace and active window.
