# Plain text journal desktop access

Implement the developer-approved daily text journal, Micro editor and blank
quick-note capture. The data engine is `tam-journal` in `tamlinux-tools`;
product integration is `tam-launch-journal`, calendar actions, Quick Launch
and Meta+Shift+J. No new bar slot or bar reordering.

Calendar text buttons open/capture for its selected YYYY-MM-DD date. Quick
Launch and the shortcut target local today at command start. Keep calendar
events, agenda copying, timezone selection and all existing clock clicks.
The command uses typed argv, a closed plugin environment and a short launcher
deadline. The editor lives in a separate session and has no deadline.

The launcher uses the selected Tamlinux command directory, with the installed
user bin directory for a separately packaged journal utility. A dedicated
terminal app id receives the existing floating treatment on the focused
output. A missing selected dependency reports failure; no arbitrary program
or shell expression is launched. Effective shortcut conflicts stop installation
for review rather than displacing notification/nightlight/window controls.

Acceptance: execute the argument builder and launcher with isolated fake
terminals; test selected dates, invalid input, argv preservation, missing
dependencies and detached lifetime. Load the calendar QML offscreen and check
the unchanged bar layout. Real Micro/VT/focused-output behavior requires
separate packaged human acceptance; no stage move is part of this work.
