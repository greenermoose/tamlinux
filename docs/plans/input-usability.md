# Safe, discoverable input and consistent clipboard

- **Status:** Plan approved by Fred, 2026-10-27; K22 close map accepted on the workstation; walkthrough of remaining chords open.
- **Scope:** Tamlinux 0.5 (Blue Sparkler) input goals and checklist K22–K25.
- **Target:** Tamlinux 0.5 candidate series.
- **Living map:** the workstation binding catalog (the workstation effective chords).

## Outcome

Keyboard and mouse interaction in Tamlinux is safe, predictable, and ergonomically sound, directly satisfying the approved 0.5 input goals and checklist conditions K22–K25:

1. **Safe keyboard shortcuts (K22):** Destructive chords (closing windows, killing processes) are separated from nearby everyday shortcuts. Specifically, `SUPER + W` is retired for window closure, eliminating the dangerous single-modifier Hamming collision with `SUPER + SHIFT + W` (Micro editor).
2. **Accurate shortcut discovery (K23):** An active shortcut reference viewer reflects the installed bindings without drift, enabling the user to find launch, navigation, clipboard, and window management actions immediately.
3. **Consistent terminal and TUI clipboard (K24):** Standardize on the 25-year PuTTY heritage convention: Left-Mouse Button (LMB) drag automatically copies selected text to the system clipboard upon release, and Right-Mouse Button (RMB) click pastes at the cursor position. In mouse-tracking TUIs (`micro`, `vim`, `htop`), a universal `Shift` bypass restores terminal selection and paste.
4. **Accessible close controls (K25):** Standard titlebar close buttons (`[X]`) and titlebar context actions are accessible on managed application windows so mouse users are never forced to touch the keyboard just to dismiss a window.

---

## Decided Architecture

### 1. Modifier patterns

Use these patterns as guides, preserving established useful shortcuts and testing comfort. The current map contains exceptions; no wholesale remapping is implied:

$$\text{Action} = \text{Dimension}(\text{Modifier}) \times \text{Entity}(\text{Key})$$

| Tier | Modifier Chord | Semantic Meaning | Mutability & Risk | Example Actions |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | `SUPER + <Key>` | **Focus & Navigation** | Purely read-only; zero state change | Focus directions (Arrows/HJKL), workspaces 1–10, launcher (`SUPER + Space`) |
| **Tier 1** | `SUPER + SHIFT + <Key>` | **Spatial Relocation & State** | Reversible state alteration; moves objects | Send window to workspace 1–10, swap window direction, move workspace |
| **Tier 2** | `SUPER + CTRL + <Key>` | **Layout & Geometry** | Alters arrangement rules without moving data | Toggle floating/tiling, toggle split orientation, fullscreen |
| **Tier 3** | `SUPER + ALT + <Key>` | **Hardware & Multi-Monitor** | External monitor and workspace routing | Move workspace to next monitor, cycle display layout |


### 2. Window Closing and Lifecycle

- **Retire `SUPER + W`:** `SUPER + W` is completely removed as a window-closing chord to prevent accidental termination of active work.
- **Persistent Application Windows:** Closed deliberately via **`SUPER + Backspace`** (primary, “rub out”) and **`SUPER + Q`** (one-handed alias) (Fred decision, 2026-10-27). `Shift + Esc` was evaluated and rejected due to Chromium Task Manager and chat shortcuts. Appearance toggles move to `U` (`SUPER + U` transparency, `SUPER + SHIFT + U` gaps, `SUPER + CTRL + U` square aspect) so a missed Shift on gaps cannot close a window. Double-tap `Esc` is rejected to keep compositor behavior simple and deterministic.
- **Transient and Ephemeral Windows:** Lightweight viewers (`imv`), dialogs, popups, and the `tam` knowledge browser pager close immediately on a single bare **`Esc`**.
- **Interactive Applications Receive Bare `Esc`:** Persistent tools (text editors like `micro` and `vim`, web browsers, shells) receive bare `Esc` intact for internal command/modal cancellation (Vim normal mode, Micro search dismissal, browser modal escape).
- **Micro Editor Launch Chord:** `SUPER + E` launches Micro; retain `SUPER + SHIFT + W` during the trial and review the alias after daily use (Fred decision, 2026-10-28).

### 3. Commercial SaaS shortcuts

Fred revoked the removal decision on 2026-10-28. Keep the existing web application shortcuts and their current chords in stage 1; consider individual changes only after a later review.

### 4. PuTTY-Heritage Mouse Clipboard Convention

Tamlinux standardizes on the battle-tested convention:
1. **LMB Drag Selection:** Selecting text in the terminal immediately populates the system clipboard (`CLIPBOARD` and `PRIMARY`) upon button release without requiring `Ctrl+Shift+C` or menu selection.
2. **RMB Click Paste:** Right-clicking in the terminal immediately pastes the system clipboard at the current cursor position.
3. **Mouse Tracking in TUIs:**
   - When a TUI application enables DECSET 1000/1002/1006 mouse tracking (`vim`, `htop`, and other tracking TUIs), the universal **`Shift`** bypass modifier bridges the gap:
     - `Shift + LMB Drag`: Bypasses application mouse capture and forces terminal-level text selection and clipboard copy.
     - `Shift + RMB Click`: Bypasses application mouse capture and forces terminal-level clipboard paste.
   - **Micro** is configured for native unmodified PuTTY-style behaviour inside the editor: LMB drag/release copies to the system clipboard, and RMB pastes. Shift bypass remains available for other mouse-tracking TUIs.
4. **Terminal Configuration (`foot.ini`):**
   ```ini
   [main]
   selection-target=both

   [mouse-bindings]
   selection-override-modifiers=Shift
   select-extend=none
   primary-paste=none
   clipboard-paste=BTN_RIGHT
   ```
5. **Micro bindings (`bindings.json`):**
   ```json
   {
     "MouseLeftRelease": "MouseRelease,Copy",
     "MouseRight": "Paste"
   }
   ```
   Existing-user Foot and Micro configs are repaired by explicitly planning,
   reviewing and applying the packaged migrations (`foot-theme` / `micro-bindings`),
   not only by fresh-user defaults. Micro migration accepts JSON5 while retaining
   comments and other personal bindings; fresh defaults remain ordinary JSON.
   Micro bindings are included in the settings checkpoint. Before Test, use a
   checkpoint made with the selected package's recovery manifest; an older
   checkpoint omitting Micro cannot establish coverage for that file.

### 5. Accessible Mouse Close Controls

- Window titlebars/headerbars provide a visible, accessible close button (`[X]`).
- Right-clicking window titlebars provides window management options (Close, Float, Maximize).
- Instant focus follows mouse (`follow_mouse = 1`, Virtue V12) is preserved with high-contrast 2px border visual feedback.

---

## Binding walkthrough (the workstation now → after)

Source of “now”: effective map on the workstation
(the workstation binding catalog).
Work through each line with Fred. Mark the decision on the line when settled.

Legend for the left column:

- `DONE`  — already in effect on the workstation (and usually in product source)
- `KEEP`  — stay as-is unless Fred says otherwise
- `OPEN`  — needs a decision before we change it
- `FIX`   — broken or incomplete; needs a repair choice

Line shape (plain text):

```
TAG  NOW chord                         action now
     → AFTER chord                     note
```

When AFTER is the same chord, the line says `→ same`.

---

### A. What is actually live vs planned

Ground truth: the workstation `tam-menu-keybindings --print` (2026-10-27) and Fred's
chord check. Checkout edits that are not in the running session are not DONE.

```
DONE  SUPER + W                        (was close window)
      → unbound                        host unbind; live print has no SUPER+W

DONE  SUPER + Backspace                close window (primary “rub out”)
      → same                           host rebound; live

OPEN  SUPER + Q                        close window (one-handed alias)
      → planned                        not in live print yet

OPEN  SUPER + Shift + Backspace        toggle gaps (live)
      → SUPER + Shift + U              planned move; not live yet

OPEN  SUPER + Ctrl + Backspace         square aspect (live)
      → SUPER + Ctrl + U               planned move; not live yet

OPEN  (transparency)                   missing in live print after Backspace→close
      → SUPER + U                      planned restore on U

DONE  SUPER + Ctrl + Q                 (was omacalc on that chord)
      → unbound on host                live print has no SUPER+Ctrl+Q
                                       (XF86Calculator still launches Calculator)

OPEN  SaaS bookmarks                   ChatGPT / Grok / YouTube / WhatsApp /
                                       Messages / Photos / Maps / X / X Post
      → keep                           STILL LIVE on 0.5.4 (Fred: SUPER+Shift+A
                                       opens ChatGPT; print agrees)

DONE  foot.ini mouse clipboard         LMB copy both, RMB paste, Shift bypass
      → same                           product defaults already set
```

Fred accepted the *planned* close map for K22 on 2026-10-27
(the close-map review);
re-verify against the live print when packaging lands the remaining chords.

---

### B. Open decisions (work these first)

```
OPEN  SUPER + Shift + A                ChatGPT (live)     → keep
OPEN  SUPER + Shift + Alt + A          Grok (live)        → keep
OPEN  SUPER + Shift + Y                YouTube (live)     → keep
OPEN  SUPER + Shift + P                Google Photos (live) → keep
OPEN  SUPER + Shift + S                Google Maps (live) → keep
OPEN  SUPER + Shift + X                X (live)           → keep
OPEN  SUPER + Shift + Alt + X          X Post (live)      → keep
OPEN  SUPER + Shift + Alt + G          WhatsApp (live)    → keep
OPEN  SUPER + Shift + Ctrl + G         Google Messages (live) → keep

OPEN  SUPER + Shift + W                Micro
      → SUPER + E                      retain Shift+W during trial

OPEN  SUPER + Q                        close alias (planned, not live)
OPEN  appearance on U                  move gaps/square/transparency off Backspace

OPEN  SUPER + Shift + Alt + Arrows     move workspace to monitor
      → ? proposed SUPER + Alt + Arrows
                                       CONFLICT: Alt+Arrows = move into group

OPEN  SUPER + T                        toggle float / tile
      → ? keep, or Tier-2 remap
                                       earlier idea SUPER+Ctrl+Space conflicts
                                       with background switcher

OPEN  SUPER + F                        full screen
      → ? keep, or SUPER + Ctrl + F
                                       Ctrl+F is already tiled full screen

OPEN  SUPER + J                        toggle split
      → ? keep, or SUPER + Ctrl + J (free)

OPEN  SUPER + L                        toggle workspace layout
      → ? keep, or Tier-2 remap

OPEN  SUPER + greater (>)              (product: less/greater resize pair)
      → product source uses US </> keysyms for both halves; retain
        SUPER+Ctrl+period for Transcode (Fred, 2026-10-28). Not live until
        packaged; host override still has only the less half.
```

---

### C. Everyday essentials — now in effect

```
KEEP  SUPER + Return                   Terminal
      → same

KEEP  SUPER + Space                    App / Tamlinux menu
      → same

KEEP  SUPER + Escape                   System / power menu
      → same

KEEP  Ctrl + Alt + Delete              close all windows
      → same

KEEP  SUPER + C / V / X                universal copy / paste / cut
      → same

KEEP  SUPER + Ctrl + V                 clipboard history
      → same

KEEP  SUPER + K                        keybindings cheat sheet
      → same

KEEP  SUPER + Tab                      next workspace
      → same

KEEP  SUPER + Shift + Tab              previous workspace
      → same

KEEP  SUPER + Ctrl + Tab               former workspace
      → same

KEEP  SUPER + 1..10                    switch desktop 1..10 (host; +keypad)
      → same

KEEP  SUPER + Shift + 1..10            move window to desktop (host; +keypad)
      → same

KEEP  SUPER + Shift + Alt + 1..10      move window silently (host; +keypad)
      → same

KEEP  Alt + Tab / Alt + Shift + Tab    cycle windows
      → same

KEEP  Ctrl + Alt + Tab                 next / previous monitor
      → same

KEEP  SUPER + mouse:272 (LMB drag)     move window
      → same

KEEP  SUPER + mouse:273 (RMB)          Quick Launch menu (host)
      → same                           replaced default resize-drag

KEEP  SUPER + mouse wheel              scroll workspaces
      → same
```

---

### D. Window focus, layout, geometry — now in effect

```
KEEP  SUPER + Arrows                   focus window in direction
      → same

KEEP  SUPER + Shift + Arrows           swap window in direction
      → same

KEEP  SUPER + Ctrl + F                 tiled full screen
      → same

KEEP  SUPER + Alt + F                  maximize / full width
      → same

KEEP  SUPER + P                        pseudo window
      → same

KEEP  SUPER + O                        pop out (float and pin)
      → same

KEEP  SUPER + S                        toggle scratchpad
      → same

KEEP  SUPER + Alt + S                  move window to scratchpad
      → same

KEEP  SUPER + G                        toggle grouping
      → same

KEEP  SUPER + Alt + G                  move window out of group
      → same

KEEP  SUPER + Alt + Arrows             move window into group
      → same                           blocks Tier-3 remap of monitor move

KEEP  SUPER + Alt + Tab                next / previous in group
      → same

KEEP  SUPER + Ctrl + Left/Right        group focus left / right
      → same

KEEP  SUPER + Alt + 1..5               switch to group tab
      → same

KEEP  SUPER + Home                     restore saved window width
      → same

KEEP  SUPER + Alt + Home               save window width
      → same

KEEP  SUPER + Slash                    monitor scaling up
      → same

KEEP  SUPER + Alt + Slash              monitor scaling down
      → same

KEEP  SUPER + less (<)                 expand window left (host)
      → same

KEEP  SUPER + Shift + less             shrink window up (host)
      → same

KEEP  SUPER + Alt + less               expand left a little (host)
      → same

KEEP  SUPER + Shift + Alt + less       shrink up a little (host)
      → same

KEEP  SUPER + Ctrl + less              expand left a lot (host)
      → same

KEEP  SUPER + Ctrl + Shift + less      shrink up a lot (host)
      → same
```

(See section B for `SUPER + F` / `T` / `J` / `L`, monitor-move chord, and product `>` restore.)

---

### E. Launch applications — now in effect

```
KEEP  SUPER + Shift + Return           Browser
      → same

KEEP  SUPER + Shift + B                Browser (alias)
      → same

KEEP  SUPER + Shift + Alt + B          Browser (private)
      → same

KEEP  SUPER + Shift + F                File manager
      → same

KEEP  SUPER + Alt + Shift + F          File manager (cwd)
      → same

KEEP  SUPER + Shift + N                Editor ($EDITOR)
      → same

OPEN  SUPER + Shift + W                Micro
      → SUPER + E                      retain Shift+W during trial

KEEP  SUPER + Shift + M                Spotify
      → same

KEEP  SUPER + Shift + Alt + M          Music TUI
      → same

KEEP  SUPER + Shift + D                Docker TUI
      → same

KEEP  SUPER + Shift + G                Signal
      → same

KEEP  SUPER + Shift + O                Obsidian
      → same

KEEP  SUPER + Shift + Slash            1Password
      → same

KEEP  SUPER + Alt + Return             Terminal with tmux
      → same

KEEP  SUPER + Ctrl + Return            Herdr
      → same

KEEP  SUPER + Alt + Space              Apps menu
      → same
```

SaaS shortcuts remain assigned; do not treat their chords as free.

---

### F. System panels, toggles, capture — now in effect

```
KEEP  SUPER + Ctrl + A                 Audio panel
      → same

KEEP  SUPER + Ctrl + B                 Bluetooth panel
      → same

KEEP  SUPER + Ctrl + D                 Display panel (fred.monitor)
      → same

KEEP  SUPER + Ctrl + W                 Network panel
      → same

KEEP  SUPER + Ctrl + P                 Power panel
      → same

KEEP  SUPER + Ctrl + T                 Activity (btop)
      → same

KEEP  SUPER + Ctrl + L                 Lock screen
      → same

KEEP  SUPER + Ctrl + I                 toggle idle lock
      → same

KEEP  SUPER + Ctrl + N                 toggle night light
      → same

KEEP  SUPER + Ctrl + H                 Hardware menu
      → same

KEEP  SUPER + Ctrl + O                 Quick toggles menu
      → same

KEEP  SUPER + Ctrl + C                 Capture menu
      → same

KEEP  SUPER + Ctrl + E                 Emoji picker
      → same

KEEP  SUPER + Ctrl + S                 Share menu
      → same

KEEP  SUPER + Ctrl + R                 set reminder
      → same

KEEP  SUPER + Ctrl + Alt + R           show reminders
      → same

KEEP  SUPER + Shift + Ctrl + R         clear reminders
      → same

KEEP  SUPER + Ctrl + X                 dictation toggle (voxtype)
      → same

KEEP  F9 hold/release                  dictation push-to-talk
      → same

KEEP  SUPER + Ctrl + Z                 zoom in
      → same

KEEP  SUPER + Ctrl + Alt + Z           reset zoom
      → same

KEEP  SUPER + Ctrl + M                 Mac/Windows desktop mode (host)
      → same

KEEP  SUPER + Ctrl + Shift + D         retrain MSI display link (host)
      → same

KEEP  SUPER + Ctrl + 1..9              toggle bar panel at position
      → same

KEEP  SUPER + Shift + Space            toggle top bar
      → same

KEEP  SUPER + Ctrl + Space             background switcher
      → same                           blocks earlier float remap idea

KEEP  SUPER + Shift + Ctrl + Space     theme menu
      → same

KEEP  SUPER + comma                    dismiss last notification
      → same

KEEP  SUPER + Shift + comma            dismiss all notifications
      → same

KEEP  SUPER + Ctrl + comma             toggle notification silencing
      → same

KEEP  SUPER + Alt + comma              invoke last notification
      → same

KEEP  SUPER + Shift + Alt + comma      notification history
      → same

KEEP  Print                            screenshot
      → same

KEEP  Alt + Print                      screen recording
      → same

KEEP  SUPER + Print                    color picker
      → same

KEEP  SUPER + Ctrl + Print             OCR from screenshot
      → same

KEEP  SUPER + Ctrl + Period            transcode
      → same

KEEP  SUPER + Shift + Ctrl + A         agent picker
      → same

KEEP  SUPER + Ctrl + Alt + T/B/W       show time / battery / weather
      → same

KEEP  SUPER + Ctrl + Alt + D           calendar (fred.clock)
      → same

KEEP  SUPER + Ctrl + Delete            toggle laptop display
      → same

KEEP  SUPER + Alt + K                  tmux keybindings help
      → same

KEEP  SUPER + Ctrl + K                 Herdr keybindings help
      → same

KEEP  XF86* media / brightness / vol   hardware keys (media.lua)
      → same
```

---

### G. Non-chord work still open (not a key move)

- **K23** Shortcut viewer must match this map after each change.
- **K24** foot.ini already configured; still need observed trial on the workstation.
- **K25** Titlebar `[X]` and titlebar context menu — mouse close without keyboard.
- **Esc** Transient windows close on bare Esc; editors/browsers/shells keep Esc.

---

## Work Steps

1. **Walk remaining section B decisions with Fred** (optional modifier remaps and missing `>`).
   Record each decision on the matching `OPEN` / `FIX` line above.
2. **Apply agreed chord changes** in product
   (`tamlinux/desktop/session/hypr/tamlinux/bindings/`) and deliver via a recorded package assembly, then update
   the workstation binding catalog.
3. **Already live on the workstation:** `SUPER + W` unbound, `SUPER + Backspace` close,
   `SUPER + Ctrl + Q` unbound, `foot.ini` PuTTY mouse clipboard. **Not live yet:**
   appearance on `U`, `SUPER + Q` close and `SUPER + E` Micro (checkout/plan only). SaaS shortcuts remain live and are restored in product source.
4. **Shortcut viewer alignment (K23):** cheat sheet / `tam-menu-keybindings`
   matches the effective map; actions findable by plain-English name.
5. **Verification:** Esc lifecycle, Micro/vim safety, clipboard trial (K24),
   titlebar close (K25); Fred daily-driver acceptance on the workstation.

---

## Acceptance Gates (K22–K25)

| Gate | Verification Method | Pass Criteria |
| :--- | :--- | :--- |
| **K22 Safe shortcuts** | Recorded trial & **Fred:** | `SUPER + W` does not close windows; `SUPER + Backspace` and `SUPER + Q` close active windows; appearance toggles on `U` do not collide with close; no accidental window termination when launching editors or navigating; Fred confirms acceptance. |
| **K23 Shortcut discovery** | **Observed:** trial | Active shortcut reference matches active bindings; user can search and find launch, navigation, clipboard, and close actions. |
| **K24 Consistent clipboard** | **Observed:** trial | LMB drag copies text immediately in bare Foot; RMB click pastes; Foot selection pastes into Micro via RMB; within Micro, unmodified LMB drag copies and RMB pastes; `Shift + LMB` and `Shift + RMB` work in other mouse-tracking TUIs; copy/paste transfers seamlessly between Foot and Wayland GUI apps. |
| **K25 Accessible close** | **Fred:** | Managed windows provide titlebar close buttons (`[X]`); mouse users can close windows without keyboard interaction; Fred confirms acceptance. |

## Input trial preparation

0.5.6 failed K24 on physical trial because existing Foot configs lacked `[mouse-bindings]` (defaults only publish when absent) and Micro had no mouse copy/paste bindings. 0.5.7 adds preserving migrations for Foot mouse keys and Micro bindings. Terminal titlebars may depend on an ABI-sensitive hyprbars plugin; applications with their own decorations must be checked individually. The product source inspected here does not establish a titlebar context menu or universal Escape handling. The installed imv manual lists `q` as its default quit binding, so Escape requires verification or configuration. These are open verification items, not passes.

On the exact packaged candidate, record its assembly revision and test the following with Fred:

1. In a fresh Foot window, select text with left drag and paste with right click; transfer text in both directions between Foot and a graphical application.
2. From Foot into Micro: select in Foot, right-click paste into Micro. Within Micro: unmodified LMB drag/release must copy, and RMB must paste.
3. With mouse tracking in Vim and htop, check Shift-left-drag selection and Shift-right-click paste; also check ordinary application mouse actions still work.
4. Check bare Escape dismisses representative image viewers, menus, dialogs and the tam pager, while Micro, Vim, a shell and a browser receive Escape without closing their windows. Record each exception by application.
5. Check representative terminal and graphical windows have a usable mouse close control; check the titlebar right-click menu for Close, Float and Maximize. Record missing controls and whether hyprbars is loaded.

Record observed results and Fred's acceptance against K24 and K25; source configuration alone does not close either gate. Investigate failures in their owning component before proposing a change.
