# Lisp Machines (MIT CADR / Symbolics Genera) and Plan 9

*Reference notes from documented MIT CADR / Symbolics Genera (Space-Cadet
keyboard) and Bell Labs Plan 9 (`rio`, `acme`, `sam`) designs.*

## What it is

- **Scope:** Two legendary research operating systems representing
  opposite extremes of input philosophy:
  - **Lisp Machines (MIT CADR, Symbolics Genera):** The birthplace of
    explicit semantic modifier tiers (`Control`, `Meta`, `Super`, `Hyper`),
    where the entire OS — window system, shell, editor (Zmacs), debugger —
    shared one unified command language.
  - **Plan 9 from Bell Labs (`rio`, `acme`, `sam`):** Radical minimalism —
    almost no keyboard shortcuts at all; instead, a 3-button mouse chord
    language and plain editable text serve as the universal interface.
- **Why it matters:** Both systems prove that **rigorous internal logic
  across the whole OS** beats ad-hoc conventions — and show the exact
  ergonomic boundaries of both heavy chording and minimal chording.

## Modifier semantics and chord grammar

### Lisp Machines (Space-Cadet / Symbolics)

| Modifier | Role in Genera / Zmacs |
| --- | --- |
| `Control` | Primary character/basic editing commands |
| `Meta` | Secondary / larger-unit commands (word, sentence, extended) |
| `Super` | Window system / OS-level commands (the direct ancestor of X11/Wayland `Super`/`Meta`!) |
| `Hyper` | User-defined / custom application layer |
| Dedicated keys | `Help`, `Abort`, `Suspend`, `Resume`, `Complete`, `Network`, `Select` (one-press system switches!) |

### Plan 9 (`rio`, `acme`, `sam`)

| Input | Role in Plan 9 |
| --- | --- |
| Keyboard | Almost purely for typing text and a tiny set of universal line-edit controls (`Ctrl+W` delete word, `Ctrl+U` delete line, `Ctrl+F` filename completion, `Esc` select recently typed text, `Del` interrupt). No `Ctrl+C/V/X`, no `Meta` tiling chords. |
| 3-button mouse chords | Button 1: select/sweep text. Button 2: execute command (any text on screen!). Button 3: plumb / search / open file. Holding Button 1 + clicking Button 2 = **Cut**; Button 1 + Button 3 = **Paste**. |

## Ideas worth taking

- **Genera's strict semantic meaning per modifier tier — `adopt`.**
  Assigning each modifier a single, OS-wide *semantic layer* (rather than
  random per-app bindings) is the exact principle Tamlinux wants across
  `tam-pane`, `tam-last`, `tam-clam`, and `tam`.
- **Genera's unified command-name / `Help` model — `adopt`.**
  Every key invokes a named command, and `Help` explains any key or
  command in context (Tamlinux's `Ctrl+G` guidance + `tam`).
- **Plan 9's discipline against shortcut bloat — `consider`.**
  Plan 9 is a healthy counterweight: before inventing a new chord for a
  rare action, ask whether it belongs in a searchable menu/command bar
  instead of consuming a scarce keybinding slot.

## Things to avoid

- **Porting 4-modifier Space-Cadet chords onto a 104-key PC keyboard.**
  The Space-Cadet keyboard put `Control`, `Meta`, `Super`, and `Hyper`
  side by side in symmetric thumb/palm rows. On a PC keyboard, squeezing
  3+ modifiers into one chord causes hand strain (hence Tamlinux P14's
  hard 3-physical-key ceiling).
- **Plan 9's dependence on a 3-button mouse.**
  Mouse chording breaks down on laptop trackpads, touchscreens, and
  text-only Linux VTs (`TERM=linux`). Tamlinux must be 100% keyboard-first.

## Where to look

- Symbolics Genera *User's Guide* (Keyboard and Input Editor chapters).
- Rob Pike, *Acme: A User Interface for Programmers* (1994) and Plan 9
  `rio(1)` / `acme(1)` manual pages.
