#!/bin/bash

# Copy text to the clipboard, then type or paste it into the focused window.
#
#   paste-text.sh [--shift-insert] [--copy-only] [--history-index <index>|<text>]
#
# Vendored from omarchy 4.0.4 bin/omarchy-clipboard-paste-text (MIT, Copyright
# (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changed: the history
# file is the Tamlinux one.

use_shift_insert=false
copy_only=false
history_index=""
text=""

while (( $# > 0 )); do
  case "$1" in
    --shift-insert)
      use_shift_insert=true
      shift
      ;;
    --copy-only)
      copy_only=true
      shift
      ;;
    --history-index)
      history_index="${2:-}"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

copy_history_entry() {
  local history_path="${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/clipboard/history.json"

  [[ $history_index =~ ^[0-9]+$ ]] || exit
  jq -e --argjson index "$history_index" '.[$index].type == "text" and (.[$index].text | type == "string")' "$history_path" >/dev/null || exit
  jq -j --argjson index "$history_index" '.[$index].text' "$history_path" | wl-copy
}

if [[ -n $history_index ]]; then
  copy_history_entry
  if [[ $copy_only != "true" ]]; then
    use_shift_insert=true
  fi
else
  text=${1:-}
  [[ -n $text ]] || exit
  printf '%s' "$text" | wl-copy
fi

if [[ $copy_only == "true" ]]; then
  exit
fi

sleep 0.15

if [[ $use_shift_insert == "true" ]]; then
  wtype -M shift -k Insert -m shift 2>/dev/null || true
else
  wtype "$text" 2>/dev/null || true
fi
