# Start menu for Tamlinux 0.5.10

**Status:** Approved by Fred, 2026-10-29: “Looks good. Make it so.”
Implemented in Develop; packaged Test and physical acceptance remain.

## Behavior

Provide one Start menu with two visible section headings: **Quick Launch**
and **Settings**. Open it with either of these gestures:

- Right-click unused space in the top bar, without a modifier.
- Press SUPER and right-click anywhere on the screen, including over an app.

An occupied widget area keeps its existing right-click action. Clock text,
workspace controls, status indicators and tray items count as occupied, even
when they are not drawn as icons. Gaps between widgets and the bar's unused
background open Start. A single gesture opens or closes the menu once.

Recommend one list with both sections exposed when the menu opens. Headings
are labels, not collapsible controls. App launchers and settings entry points
are immediately available; selecting a setting opens its picker or choice
list. Do not put another category-opening step before every action.

Use compact command rows, readable labels, optional familiar icons and a
clear separator between sections. Preserve stable item ordering. Search
filters actions across both sections and keeps a heading only when that
section has results. Arrow navigation skips headings and separators; Enter
activates the focused action. Preserve the existing search shortcuts.

Start needs its own row density and height budget. The existing menu uses
50 px base rows at the default type scale, which would make the combined
list unnecessarily tall. Aim for roughly 28 logical px command rows at the
12 px base font, growing to fit actual font metrics and comfortable padding.
Never reduce the user's chosen text size to fit more items. Both sections
expose their contents regardless of display size; provide a visible scrollbar and
keep the keyboard selection in view when content exceeds available height.
Do not silently hide entries, reorder them by frequency or auto-collapse a
section. Custom Quick Launch entries remain available through scrolling and
search. Settings should fit with the baseline Quick Launch list on a
1280×720 logical display at the default font and scale; prove this in layout
checks rather than assume the compact row size is sufficient.

Open near the pointer on the display containing it, with the card kept within
that display's usable bounds. For a bar click, place it below the top bar.
Keep its position stable during navigation and resizing. Escape or a click
outside dismisses it; opening it must not launch an entry under the pointer.

## Menu contents

**Quick Launch** presents the existing merged Quick Launch tree, including
user extension entries, order, aliases, app launch commands and session/power
actions. Keep the direct `quicklaunch` route working. Reuse that data rather
than maintaining another copy of the list. Supply a useful packaged Quick
Launch default where there is no user extension.

**Settings** initially provides:

- **Color Palette:** the existing theme picker, including Tamarack dark and
  light and installed user themes. Selecting a theme follows the existing
  theme application behavior across the shell, supported apps and terminals.
- **Text Size:** a graphical choice of the supported sizes, showing the
  current selection and offering a reset. Reuse `tam-display-text-size`
  (currently 9–20 px, default 12). Apply it to shell, supported apps and
  terminals, following the existing command's behavior. Verify each claimed
  consumer; document any application that needs a new window or a restart.
- **Background:** the existing background picker.
- **Bar Position:** the existing top/bottom control.

Appearance changes affect the shell, supported apps and terminals together,
as confirmed in the review direction on 2026-10-29. Use **Settings** as the
section title so it does not imply shell-only effects. Explain the scope
briefly in the Settings heading and text-size picker, along with the current
value and reset behavior; avoid repeating that explanation on every menu row.

Palette and text-size changes should take effect through existing reload
paths and persist across shell restarts and login. Theme changes preserve
the selected text size and unrelated preferences. If a change fails, show
the error and retain or restore the previous working settings. Font-family
selection remains available through its existing route. Adding a coordinated
family selector is a separate follow-up because readable UI text and terminal
monospace text have different roles; this first slice exposes palette and
text size without mislabeling the existing terminal-font selector.

## Design evidence and recommendation

Research reviewed 2026-10-29 supports **one list with section headings** for
this first scope. This is a design recommendation applied to Tamlinux, not
a measured comparison of two Tamlinux prototypes.

- A CHI study with 36 participants found that visual boundaries helped menu
  search when they matched meaningful semantic groups. That supports
  separating launch actions from settings rather than styling an undifferentiated
  list. It does not establish a universal best number of entries.
  [Brumby and Zhuang, Visual grouping in menu interfaces, 2015](https://discovery.ucl.ac.uk/id/eprint/1499240/).
- Apple recommends related command groups and restrained use of submenus,
  because submenus hide choices and add complexity. It also warns about
  long menus. Apply both parts: expose the two groups, keep rows compact
  and support overflow for user-added content.
  [Apple Human Interface Guidelines: Menus](https://developer.apple.com/design/human-interface-guidelines/menus).
- Microsoft's current guidance favors direct access for frequently used
  commands when space permits. Its older desktop menu guide also discourages
  unnecessary submenus and recommends logical grouping. The older guide is
  Windows 7 guidance, not a current quantitative usability rule for Tamlinux.
  [Current menu guidance](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/menus-and-context-menus),
  [desktop menu organization](https://learn.microsoft.com/en-us/windows/win32/uxguide/cmd-menus).
- W3C's menu pattern supplies useful keyboard conventions: arrow navigation,
  Enter activation, Escape dismissal and noninteractive separators. Apply
  the interaction principles through native QML accessibility rather than
  treating a web ARIA pattern as a native-toolkit implementation.
  [WAI-ARIA APG: Menu and Menubar Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/).

Two collapsed categories would give a smaller initial popup, but every app
launch would require revealing Quick Launch first, and available settings
would be hidden. Inline accordions also move later rows when expanded;
cascading submenus add pointer travel. Here the combined baseline is modest:
11 current Quick Launch actions plus four settings entry points. Keep
choice-heavy details, such as the palette list and numeric text sizes, in
their existing pickers instead of placing every possible value in Start.

Separate application launchers and session/power commands within Quick Launch
with a small divider when those groups are identifiable. Preserve custom
ordering and all existing commands. Section labels and separators must have
sufficient contrast and must not look selectable. Keep visible keyboard focus,
full-row pointer targets, and labels that remain understandable without icons.

Validate the recommendation at normal and large text sizes and on the
smallest supported output. If the actual list requires frequent scrolling
for ordinary launch and settings tasks, review that evidence before changing
the hierarchy. Retain a consistent layout during a session.

## Integration

Extend the owned menu service and bar host. Add an explicit `start` menu
route, backed by the same model, action execution and style tokens as the
existing menu. Keep the root menu and direct routes available.

The bar handles right-clicks only in unused space. Test the actual widget
bounds and event propagation so a widget that does not accept right-click
still reserves its area. Left-click, scroll, hover and widget-specific
gestures retain their behavior.

The packaged Hyprland SUPER + right-click binding opens Start. Resolve the
existing resize binding for that exact chord so it cannot also resize a
window. Update the consumer's existing Quick Launch override through the
recorded package/configuration workflow so it does not shadow the new route.
Do not activate changes by editing the running configuration during Develop.

Use the clicked bar's output and coordinates for a bar invocation; resolve
the pointer output and position for the global invocation. Keep placement
changes specific to Start so existing select/input dialogs retain their
placement. Handle output removal, negative output origins and display scaling.

Use the existing settings writers and recovery behavior. Any new selection
UI validates its values before invoking them. Keep menu data, bounded input
handling, user extensions and unrelated settings intact.

## Work and evidence

1. Add the grouped Start model and settings entries. Verify merged Quick
   Launch customizations, stable ordering, headings, separators, cross-section
   search, direct routes, keyboard navigation, accessibility names and
   checkmarks without executing real session/power actions in automated checks.
2. Add bar gap handling and pointer-aware placement. Verify gaps, occupied
   widget areas, screen edges, multiple outputs, scaling, repeat invocation,
   dismissal and focus restoration using isolated shell fixtures. Check
   compact rows against actual text metrics, including default and maximum
   text sizes, a 1280×720 logical output, display scaling, long labels and
   user-added entries. Confirm scrolling and keyboard access to both sections.
3. Wire the packaged global binding and consumer override. Check that the
   effective binding invokes Start exactly once and does not resize windows.
4. Verify palette and text-size changes across the shell, supported app
   adapters and terminals in temporary configuration/state roots. Include
   reset, invalid values, failed application, restart and theme switching;
   report limits for adapters that do not reload live. Coordinate shared
   source paths and stable-tree checks with other active work before integration.

Before including this in the 0.5.10 assembly, record the exact source and
delivery revisions and development check results. If that assembly has
already been prepared, use the next candidate number for changed contents.

Physical acceptance happens on an explicitly requested Test candidate:
exercise both gestures on each display and over an application, check that
widget menus still work, launch apps from the visible Quick Launch section,
reach settings at default and enlarged text sizes, change palette and text
size and return, and verify supported app/terminal effects and persistence
after shell restart and login. Record the previous package/user
generation and affected mutable settings as the way back before Test.

## Review status

Appearance scope is settled: shell, supported apps and terminals together.
The recommended layout is one list with visible Quick Launch and Settings
headings. Fred approved this plan and directed implementation on 2026-10-29.

Plan approval starts Develop. Test, Run and Release require their own exact
candidate instructions under the [versioning policy](../../VERSIONING.md).

## Development result — 2026-10-29

The combined view, pointer placement, bar gap handling, desktop-wide settings
entries, packaged chord and explorer catalog are implemented. Mouse resizing
uses SUPER + ALT + right-click. The existing direct Quick Launch route and
user-owned tree remain intact; packaged starter entries do not extend a
curated user list. Settings uses existing theme writers and adds automatic
text-size failure restoration, including linked terminal configuration.

The desktop suite completed 720 tests with 81 skips using the installed
JSON5-enabled Python. The final bar-clearance refinement then passed the
five Start model/native checks, nine JSONC checks and 19 service checks;
all 22 appearance/control checks passed. The native fixture uses two isolated
outputs, including a scaled output with a negative origin. It verifies both
sections, default/large text and overflow, empty search, pointer events,
keyboard navigation, provider dispatch, global routing and top/bottom bar
clearance. A captured fixture rendering was visually inspected.

Consumer activation is staged to preserve and retire the exact old Quick
Launch chord when a package at 0.5.10 or later is selected. It leaves the
running configuration untouched during Develop and rejects custom overrides
for review. Its four checks and Nix syntax validation pass. Reverting a user
generation alone cannot restore that live-linked source; retain its preserved
settings with the Test rollback record.

Next: include these commits in the recorded 0.5.10 assembly, then request
packaged Test and physical acceptance. No assembly was prepared or activated
by this implementation slice. Existing Foot windows require restart for a
new text size; native app appearance still needs physical review.
