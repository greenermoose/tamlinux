# Safe, discoverable input and consistent clipboard

Status: plan approved by Fred, 2026-10-27; implementation in Develop.
Scope: Tamlinux 0.5 (Blue Sparkler) input goals and checklist K22–K25.
Target: Tamlinux 0.5 candidate series.

## Outcome

Keyboard and mouse interaction in Tamlinux is safe, predictable, and ergonomically sound, directly satisfying the approved [0.5 goals](../../../improvements-fred-tamlinux/0.5-GOALS.md#make-everyday-input-safer-and-easier) and [checklist conditions K22–K25](../../../improvements-fred-tamlinux/0.5-CHECKLIST.md#make-everyday-input-safer-and-easier):

1. **Safe keyboard shortcuts (K22):** Destructive chords (closing windows, killing processes) are separated from nearby everyday shortcuts. Specifically, `SUPER + W` is retired for window closure, eliminating the dangerous single-modifier Hamming collision with `SUPER + SHIFT + W` (Micro editor).
2. **Accurate shortcut discovery (K23):** An active shortcut reference viewer reflects the installed bindings without drift, enabling the user to find launch, navigation, clipboard, and window management actions immediately.
3. **Consistent terminal and TUI clipboard (K24):** Standardize on the 25-year PuTTY heritage convention: Left-Mouse Button (LMB) drag automatically copies selected text to the system clipboard upon release, and Right-Mouse Button (RMB) click pastes at the cursor position. In mouse-tracking TUIs (`micro`, `vim`, `htop`), a universal `Shift` bypass restores terminal selection and paste.
4. **Accessible close controls (K25):** Standard titlebar close buttons (`[X]`) and titlebar context actions are accessible on managed application windows so mouse users are never forced to touch the keyboard just to dismiss a window.

---

## Decided Architecture

### 1. The 4-Tier Semantic Modifier Model

Composable keyboard shortcuts follow strict orthogonal semantic axes:

$$\text{Action} = \text{Dimension}(\text{Modifier}) \times \text{Entity}(\text{Key})$$

| Tier | Modifier Chord | Semantic Meaning | Mutability & Risk | Example Actions |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | `SUPER + <Key>` | **Focus & Navigation** | Purely read-only; zero state change | Focus directions (Arrows/HJKL), workspaces 1–10, launcher (`SUPER + Space`) |
| **Tier 1** | `SUPER + SHIFT + <Key>` | **Spatial Relocation & State** | Reversible state alteration; moves objects | Send window to workspace 1–10, swap window direction, move workspace |
| **Tier 2** | `SUPER + CTRL + <Key>` | **Layout & Geometry** | Alters arrangement rules without moving data | Toggle floating/tiling, toggle split orientation, fullscreen |
| **Tier 3** | `SUPER + ALT + <Key>` | **Hardware & Multi-Monitor** | External monitor and workspace routing | Move workspace to next monitor, cycle display layout |
| **Banned** | `SUPER + SHIFT + ALT + CTRL` | *Forbidden* | *Violates human factors guidelines* | Zero four-key hyper-chords permitted |

### 2. Window Closing and Lifecycle

- **Retire `SUPER + W`:** `SUPER + W` is completely removed as a window-closing chord to prevent accidental termination of active work.
- **Persistent Application Windows:** Closed deliberately via **`Shift + Esc`** or standard Tier 1 chord **`SUPER + SHIFT + Q`** (Fred decision, 2026-10-27). Double-tap `Esc` is rejected to keep compositor behavior simple and deterministic.
- **Transient and Ephemeral Windows:** Lightweight viewers (`imv`), dialogs, popups, and the `tam` knowledge browser pager close immediately on a single bare **`Esc`**.
- **Interactive Applications Receive Bare `Esc`:** Persistent tools (text editors like `micro` and `vim`, web browsers, shells) receive bare `Esc` intact for internal command/modal cancellation (Vim normal mode, Micro search dismissal, browser modal escape).
- **Micro Editor Launch Chord:** The decision on the specific launcher chord for Micro is deferred until a complete audit and list of all keybindings is compiled to evaluate how it fits into the overall system (Fred decision, 2026-10-27).

### 3. Purging Commercial SaaS Bookmark Chords

Upstream Omarchy bound 18+ commercial SaaS web applications into global multi-modifier chords (`SUPER + SHIFT + A` for ChatGPT, `SUPER + SHIFT + ALT + A` for Grok, `SUPER + SHIFT + Y` for YouTube, etc.). All commercial SaaS bookmark chords are purged from compositor bindings:
- Web applications remain readily accessible through the fuzzy application launcher (`SUPER + Space` / `tam-menu`).
- Prime alphanumeric keys (`A`, `C`, `E`, `S`, `X`) are reclaimed for core window management and personal user bindings.

### 4. PuTTY-Heritage Mouse Clipboard Convention

Tamlinux standardizes on the battle-tested convention:
1. **LMB Drag Selection:** Selecting text in the terminal immediately populates the system clipboard (`CLIPBOARD` and `PRIMARY`) upon button release without requiring `Ctrl+Shift+C` or menu selection.
2. **RMB Click Paste:** Right-clicking in the terminal immediately pastes the system clipboard at the current cursor position.
3. **Mouse Tracking in TUIs:**
   - When a TUI application enables DECSET 1000/1002/1006 mouse tracking (`vim`, `micro`, `htop`), the universal **`Shift`** bypass modifier bridges the gap:
     - `Shift + LMB Drag`: Bypasses application mouse capture and forces terminal-level text selection and clipboard copy.
     - `Shift + RMB Click`: Bypasses application mouse capture and forces terminal-level clipboard paste.
4. **Terminal Configuration (`foot.ini`):**
   ```ini
   [main]
   selection-target=both

   [mouse-bindings]
   primary-paste=none
   clipboard-paste=BTN_RIGHT
   ```

### 5. Accessible Mouse Close Controls

- Window titlebars/headerbars provide a visible, accessible close button (`[X]`).
- Right-clicking window titlebars provides window management options (Close, Float, Maximize).
- Instant focus follows mouse (`follow_mouse = 1`, Virtue V12) is preserved with high-contrast 2px border visual feedback.

---

## Audit of Existing Bindings & Proposed Disposition

The active Hyprland bindings in `config-fred-tamlinux/config/hypr/tamlinux/bindings/` are audited and mapped into the 4-tier system:

| File | Existing Binding | Existing Action | Proposed Disposition | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `tiling.lua` | `SUPER + W` | Close window | **Retire** $\rightarrow$ replace with `Shift + Esc` and `SUPER + SHIFT + Q` | Eliminates Hamming collision with `SUPER + SHIFT + W` (Micro). |
| `tiling.lua` | `CTRL + ALT + DELETE` | Close all windows | Retain | Emergency clear desktop action. |
| `tiling.lua` | `SUPER + J` | Toggle window split | Retain (Tier 2 alias `SUPER + CTRL + J`) | Layout toggle. |
| `tiling.lua` | `SUPER + T` | Toggle float/tile | Map to `SUPER + CTRL + Space` (or retain `SUPER + T`) | Layout adjustment. |
| `tiling.lua` | `SUPER + F` | Full screen | Retain (or `SUPER + CTRL + F`) | Layout adjustment. |
| `tiling.lua` | `SUPER + [LEFT/RIGHT/UP/DOWN]` | Focus direction | Retain (Tier 0) | Read-only navigation. |
| `tiling.lua` | `SUPER + 1..10` | Switch workspace | Retain (Tier 0) | Read-only navigation. |
| `tiling.lua` | `SUPER + SHIFT + 1..10` | Move window to workspace | Retain (Tier 1) | Spatial relocation. |
| `tiling.lua` | `SUPER + SHIFT + [Arrows]` | Swap window direction | Retain (Tier 1) | Spatial relocation. |
| `tiling.lua` | `SUPER + SHIFT + ALT + [Arrows]`| Move workspace to monitor | Map to `SUPER + ALT + [Arrows]` (Tier 3) | Multi-monitor hardware routing. |
| `applications.lua` | `SUPER + RETURN` | Terminal (`foot`) | Retain | Primary shell tool. |
| `applications.lua` | `SUPER + SHIFT + RETURN` | Browser | Retain | Primary GUI browser. |
| `applications.lua` | `SUPER + SHIFT + W` | Micro editor | **Deferred** | Kept in place pending comprehensive keymap review. |
| `applications.lua` | `SUPER + SHIFT + A` | ChatGPT webapp | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + ALT + A` | Grok webapp | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + Y` | YouTube webapp | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + ALT + G` | WhatsApp webapp | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + CTRL + G` | Google Messages | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + P` | Google Photos | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + S` | Google Maps | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + X` | X webapp | **Purge** | Delegate to launcher (`SUPER + Space`). |
| `applications.lua` | `SUPER + SHIFT + ALT + X` | X Post | **Purge** | Delegate to launcher (`SUPER + Space`). |

---

## Work Steps

1. **Configuration updates in `tamlinux` & `config-fred-tamlinux`:**
   - Update `foot.ini` defaults in `tamlinux/desktop/assets/defaults/foot.ini` to configure `selection-target=both` and `clipboard-paste=BTN_RIGHT`.
   - Update `tiling.lua` in `config-fred-tamlinux/config/hypr/tamlinux/bindings/`:
     - Bind `Shift + Esc` and `SUPER + SHIFT + Q` to `hl.dsp.window.close()`.
     - Remove `SUPER + W`.
   - Update `applications.lua`:
     - Remove the 9 SaaS bookmark web application bindings.
     - Preserve terminal, browser, file manager, and launcher bindings.
2. **Shortcut viewer alignment (K23):**
   - Ensure `tam-menu` keybinding helper (or dedicated `tam-keys` viewer) dynamically reflects the updated bindings.
   - Verify that all active bindings are discoverable by plain-English action name.
3. **Automated and PTY test verification:**
   - Add unit/integration tests verifying that `foot.ini` generates valid syntax and correct mouse binding mappings.
   - Test that transient windows (`imv`, `tam`) close on `Esc`.
   - Test that `micro` and `vim` launch without collision and receive `Esc` without window termination.
   - Test clipboard interoperability across PTY/terminal and Wayland clipboard buffers (`wl-copy` / `wl-paste`).
4. **Physical verification and Fred acceptance:**
   - Verify daily-driver input workflow with Fred on `bosgame` to close K22, K23, K24, and K25.

---

## Acceptance Gates (K22–K25)

| Gate | Verification Method | Pass Criteria |
| :--- | :--- | :--- |
| **K22 Safe shortcuts** | Recorded trial & **Fred:** | `SUPER + W` does not close windows; `Shift + Esc` and `SUPER + SHIFT + Q` close active windows; no accidental window termination when launching editors or navigating; Fred confirms acceptance. |
| **K23 Shortcut discovery** | **Observed:** trial | Active shortcut reference matches active bindings; user can search and find launch, navigation, clipboard, and close actions. |
| **K24 Consistent clipboard** | **Observed:** trial | LMB drag copies text immediately in streaming terminal; RMB click pastes; `Shift + LMB` and `Shift + RMB` work in mouse-tracking TUIs; copy/paste transfers seamlessly between Foot and Wayland GUI apps. |
| **K25 Accessible close** | **Fred:** | Managed windows provide titlebar close buttons (`[X]`); mouse users can close windows without keyboard interaction; Fred confirms acceptance. |
