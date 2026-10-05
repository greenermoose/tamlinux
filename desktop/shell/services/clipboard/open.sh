#!/bin/bash

# Open a clipboard history entry: an image in the annotation editor, a URL in
# the default browser, and other text in $VISUAL/$EDITOR in a terminal.
#
#   open.sh --history-index <index>
#
# Each program starts in its own session scope (uwsm-app), so it outlives a
# restart of the shell services that launched it.
#
# Ported from omarchy 4.0.4 bin/omarchy-clipboard-open (MIT, Copyright (c)
# David Heinemeier Hansson; see ../LICENSE-omarchy). Changed: the Tamlinux
# history and state paths; the browser is xdg-open and the editor runs through
# xdg-terminal-exec.

history_index=""
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/tamlinux/clipboard"
history_path="$state_dir/history.json"

while (( $# > 0 )); do
  case "$1" in
    --history-index)
      history_index="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: open.sh --history-index <index>" >&2
      exit 1
      ;;
  esac
done

[[ $history_index =~ ^[0-9]+$ ]] || exit 1
[[ -r $history_path ]] || exit 1

entry_type=$(jq -er --argjson index "$history_index" '.[$index].type' "$history_path") || exit 1

open_image() {
  local path="$1"

  [[ -r $path ]] || exit 1
  exec setsid uwsm-app -- tensaku-edit "$path"
}

open_text() {
  local text="$1"
  local url=""
  local open_dir=""
  local open_file=""
  local -a editor=()

  url=$(grep -Eom1 'https?://[^[:space:]"'\''<>]+' <<<"$text" || true)
  if [[ -z $url && $text =~ ^[[:space:]]*([[:alnum:]][[:alnum:].-]+\.[[:alpha:]]{2,})(/[^[:space:]]*)?[[:space:]]*$ ]]; then
    url="https://${BASH_REMATCH[1]}${BASH_REMATCH[2]}"
  fi

  if [[ -n $url ]]; then
    exec setsid uwsm-app -- xdg-open "$url"
  fi

  open_dir="$state_dir/open"
  mkdir -p "$open_dir"
  open_file=$(mktemp --tmpdir="$open_dir" clipboard.XXXXXX.txt) || exit 1
  printf '%s' "$text" >"$open_file"

  # $EDITOR may carry arguments, so split it into words like a shell would.
  read -ra editor <<<"${VISUAL:-${EDITOR:-nvim}}"
  (( ${#editor[@]} > 0 )) || editor=(nvim)
  exec setsid uwsm-app -- xdg-terminal-exec --app-id=tamlinux.clipboard -e "${editor[@]}" "$open_file"
}

case "$entry_type" in
  image)
    path=$(jq -er --argjson index "$history_index" '.[$index].path' "$history_path") || exit 1
    open_image "$path"
    ;;
  text)
    text=$(jq -er --argjson index "$history_index" '.[$index].text' "$history_path") || exit 1
    open_text "$text"
    ;;
  *)
    exit 1
    ;;
esac
