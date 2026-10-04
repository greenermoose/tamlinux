#!/bin/bash

# Type an emoji into the focused window.
#
#   insert.sh <emoji>
#
# Vendored from omarchy 4.0.4 bin/omarchy-menu-emoji-insert (MIT, Copyright (c)
# David Heinemeier Hansson; see ../LICENSE-omarchy). Unchanged apart from these
# comments. The emoji is offered as a sensitive selection, so the clipboard
# history does not record it, and only for as long as the paste takes.

emoji="${1:-}"
copy_pid=""

[[ -n $emoji ]] || exit

printf '%s' "$emoji" | wl-copy --type text/plain --sensitive --foreground &
copy_pid=$!

sleep 0.15
wtype -M shift -k Insert -m shift 2>/dev/null || true
sleep 0.2

kill "$copy_pid" 2>/dev/null || true
