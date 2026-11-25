#!/bin/bash

# Copy text to the clipboard, then type or paste it into the focused window.
#
#   paste-text.sh --capture-target
#   paste-text.sh [--target <address|other>] [--shift-insert] [--copy-only] [--history-index <index>|<text>]
#
# Ported from omarchy 4.0.4 bin/omarchy-clipboard-paste-text (MIT, Copyright
# (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changed: the history
# file is the Tamlinux one.

set -eo pipefail

# Capture before the picker takes keyboard focus. Keep the original paste
# route for other applications. An unavailable target permits copying only.
if [[ ${1:-} == --capture-target ]]; then
  timeout 1 hyprctl -j activewindow | jq -er '
    if .class == "tam-last" then .address | select(test("^0x[0-9a-fA-F]+$"))
    elif (.class // "") != "" then "other" else empty end'
  exit
fi

target=other
use_shift_insert=false
copy_only=false
history_index=""
text=""

while (( $# > 0 )); do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || exit 2
      target=$2
      shift 2
      ;;
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
  local copy_args=()
  if [[ $target =~ ^0x[0-9a-fA-F]+$ ]]; then
    copy_args=(--type "text/plain;charset=utf-8")
  fi
  jq -j --argjson index "$history_index" '.[$index].text' "$history_path" | wl-copy "${copy_args[@]}"
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

if [[ $target != other ]]; then
  [[ $target =~ ^0x[0-9a-fA-F]+$ && $target != 0x0 ]] || exit 1
  for attempt in {1..12}; do
    active=$(timeout 1 hyprctl -j activewindow | jq -r '.address // ""')
    if [[ $active == "$target" ]]; then
      send_key() {
        local expression="hl.dsp.send_key_state({ mods = 'CTRL SHIFT', key = 'V', state = '$1', window = 'address:$target' })"
        local reply
        reply=$(timeout 1 hyprctl dispatch "$expression") && [[ ${reply,,} == ok ]]
      }
      # Release the same window even if the down request times out.
      down_status=0
      send_key down || down_status=$?
      send_key up
      exit "$down_status"
    fi
    [[ -z $active || $active == 0x0 ]] || exit 1
    sleep 0.025
  done
  exit 1
fi

sleep 0.15

if [[ $use_shift_insert == "true" ]]; then
  wtype -M shift -k Insert -m shift 2>/dev/null || true
else
  wtype "$text" 2>/dev/null || true
fi
