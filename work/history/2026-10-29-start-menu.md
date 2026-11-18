# Start menu development — 2026-10-29

- **CLI Tool**: Codex CLI (`codex`) `0.165.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: AI-assisted implementation and documentation directed and approved by the maintainer.
- **Implementation commit**: `7d53a9a`.

## Guiding prompts

> For Tamlinux 0.5.10, right-clicking the top bar anywhere there is not an icon should launch a start menu that includes two sections: a) the Quick Launch menu, and b) a configuration settings menu that lets you do things like change the color palette, font size, etc. of the graphical shell. This should be available anywhere on the screen via SUPER + Right Mouse Click, but works without SUPER in any area of the topbar not already devoted to another app. Ask if you have questions about this new menu.

> Do research on front end design, HCI, and UI/UX design. What do you recommend after that, two expandable sections or one list with section headings?
> 
> Appearance changes should affect the shell, supported apps, and terminals.
> 
> Revise the plan before showing it to me.

> Looks good. Make it so. Close the review window. Then proceed to implement the plan.

## Decisions and implementation

The approved plan recommends a single list with visible Quick Launch and
Settings headings, based on menu grouping research and desktop interface
guidance. Appearance changes cover the shell, supported apps and terminals.
The existing Quick Launch model, actions, aliases and user ordering are reused;
a user-owned tree replaces the packaged starter list. Direct Quick Launch
access remains available.

An ancestor tap handler checks occupied widget bounds before opening Start.
Global pointer sampling stays behind the compositor facade, with a closed
environment, output cap and deadline in the Hyprland adapter. Start keeps its
card within the selected output and clear of a clicked top or bottom bar.
The keybinding explorer catalog reflects Start on SUPER + right-click and
resizing on SUPER + ALT + right-drag.

The text-size provider exposes 9–20 px and reset. Failed writes restore the
saved files, linked terminal configuration and GTK selection where possible;
the recovery snapshot remains available. Palette failures report a notification.
The consumer activation retirement of the exact old chord is separately
staged; no live configuration or deployment was changed during development.

## Verification

- Desktop suite: 720 tests, 81 skipped, using the installed Python environment
  with JSON5. Initial runs exposed the compositor boundary, catalog and service
  wiring expectations; those were corrected before the successful suite.
- Final bar-clearance refinement: 5 Start model/native checks, 9 JSONC checks
  and 19 service checks passed; all 22 appearance/control checks passed.
- The native fixture uses two isolated Sway outputs, including fractional
  scaling and a negative origin. It checks pointer events, keyboard navigation,
  grouping, empty search, large text, scroll layout, provider dispatch, global
  routing and top/bottom bar clearance. Actions are recorded, not executed.
- A fixture rendering was visually inspected. Consumer activation has four
  passing checks and Nix syntax validation.

At the end of the implementation phase, no candidate assembly was prepared,
deployed, Run or Released. Physical
appearance, login persistence and recovery acceptance remain for packaged Test.
Existing Foot windows need restarting to pick up a new terminal text size.

## Package preparation follow-up

The maintainer reported:

> It doesn't work. I tried right mouse click on the top bar. Nothing.

Inspection confirmed that the running package was 0.5.9 and contained no bar
Start handler. The source implementation had not been delivered. Preparation
now sets the product version to 0.5.10 for a recorded candidate; activation
still requires an explicit Test instruction. Other component selections are
retained. Preparation is not physical acceptance.
