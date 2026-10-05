#!/bin/bash

# Set, list, and clear desktop reminders. Each reminder is a transient systemd
# user timer (tamlinux-reminder-*) that sends a notification when it fires.
#
#   reminder.sh <minutes> [message]
#   reminder.sh show [-j|--json]
#   reminder.sh clear
#
# Used by the reminder card and its timers:
#
#   reminder.sh toast <headline> [body]
#   reminder.sh due <message> <message-file>
#
# Ported from omarchy 4.0.4 bin/omarchy-reminder (MIT, Copyright (c) David
# Heinemeier Hansson; see ../LICENSE-omarchy). Changes: the timer and message
# names; notifications go straight to D-Bus; minutes are read as decimal and
# capped at 99999; a reminder set in the same second as another gets its own
# unit; and the card opens through the host's reminders target, not here.

set -euo pipefail

self=$(readlink -f "${BASH_SOURCE[0]}")
reminder_dir="${XDG_RUNTIME_DIR:-/tmp}/tamlinux-reminders"
glyph="󰢌"

# Send a toast through org.freedesktop.Notifications. busctl takes the
# headline and body as typed values, so they cannot become options or hints.
# The app name and glyph hint are the ones the host's notification service
# recognises; that app name is let through do-not-disturb.
toast() {
  busctl --user -- call \
    org.freedesktop.Notifications /org/freedesktop/Notifications \
    org.freedesktop.Notifications Notify susssasa{sv}i \
    omarchy-action 0 "" "$1" "${2:-}" 0 \
    2 urgency y 0 omarchy-glyph s "$glyph" \
    -1 >/dev/null
}

format_remaining() {
  local seconds=$1
  local minutes=$((seconds / 60))
  local remainder=$((seconds % 60))

  if ((minutes > 0 && remainder > 0)); then
    echo "${minutes}m ${remainder}s"
  elif ((minutes > 0)); then
    echo "${minutes}m"
  else
    echo "${remainder}s"
  fi
}

active_reminder_timers() {
  local now=${1:-$(date +%s)}
  local timer next

  while IFS=$'\t' read -r timer next; do
    [[ -z $timer || -z $next ]] && continue

    next=$((next / 1000000))
    ((next <= now)) && continue

    printf "%s\t%s\n" "$timer" "$next"
  done < <(systemctl --user list-timers --all --output=json "tamlinux-reminder-*.timer" 2>/dev/null | jq -r '.[] | [.unit, .next] | @tsv')
}

reminder_message() {
  local file="$reminder_dir/$1.message"
  [[ -f $file ]] && cat "$file"
  return 0
}

reminder_minutes() {
  local minutes=${1#tamlinux-reminder-}
  minutes=${minutes%%m-*}
  [[ $minutes =~ ^[0-9]+$ ]] || minutes=0
  echo "$minutes"
}

show_reminders() {
  local timer next unit message body=""
  local now
  now=$(date +%s)

  while IFS=$'\t' read -r timer next; do
    unit=${timer%.timer}
    message=$(reminder_message "$unit")

    if [[ -n $message ]]; then
      body+="$message in $(format_remaining $((next - now))) ($(date -d "@$next" +%-H:%M))"$'\n'
    else
      body+="$(reminder_minutes "$unit")-min reminder in $(format_remaining $((next - now))) ($(date -d "@$next" +%-H:%M))"$'\n'
    fi
  done < <(active_reminder_timers "$now")

  if [[ -z $body ]]; then
    toast "Upcoming reminders" "No outstanding reminders"
  else
    toast "Upcoming reminders" "${body%$'\n'}"
  fi
}

show_json() {
  local timer next unit minutes message label remaining
  local now count=0 tooltip="Set Reminder" reminders_json="[]"
  now=$(date +%s)

  while IFS=$'\t' read -r timer next; do
    count=$((count + 1))
    unit=${timer%.timer}
    minutes=$(reminder_minutes "$unit")
    remaining=$((next - now))
    message=$(reminder_message "$unit")
    label=${message:-"${minutes}-min reminder"}

    reminders_json=$(jq -cn \
      --argjson reminders "$reminders_json" \
      --arg unit "$unit" \
      --arg timer "$timer" \
      --arg label "$label" \
      --arg message "$message" \
      --arg remaining "$(format_remaining "$remaining")" \
      --arg atTime "$(date -d "@$next" +%-H:%M)" \
      --argjson minutes "$minutes" \
      --argjson at "$next" \
      --argjson remainingSeconds "$remaining" \
      '$reminders + [{unit:$unit,timer:$timer,minutes:$minutes,message:$message,label:$label,remaining:$remaining,remainingSeconds:$remainingSeconds,at:$at,atTime:$atTime}]')
  done < <(active_reminder_timers "$now")

  if ((count == 1)); then
    tooltip="1 reminder"
  elif ((count > 1)); then
    tooltip="$count reminders"
  fi

  jq -cn --argjson count "$count" --arg tooltip "$tooltip" --argjson reminders "$reminders_json" \
    '{count:$count,active:($count > 0),tooltip:$tooltip,reminders:$reminders}'
}

clear_reminders() {
  local units

  units=$(systemctl --user list-timers --all --output=json "tamlinux-reminder-*.timer" 2>/dev/null | jq -r '.[] | .unit, .activates')
  if [[ -n $units ]]; then
    xargs -r systemctl --user stop <<<"$units" || true
  fi

  rm -f "$reminder_dir"/tamlinux-reminder-*.message 2>/dev/null || true
  toast "All reminders have been cleared"
}

usage() {
  echo "Usage: reminder.sh <minutes> [message]"
  echo "       reminder.sh show [-j|--json]"
  echo "       reminder.sh clear"
}

case ${1:-} in
show | list)
  case ${2:-} in
  -j | --json) show_json ;;
  "") show_reminders ;;
  *) usage >&2; exit 1 ;;
  esac
  exit 0
  ;;
clear)
  clear_reminders
  exit 0
  ;;
toast)
  (($# >= 2)) || { usage >&2; exit 1; }
  toast "$2" "${3:-}"
  exit 0
  ;;
due)
  (($# == 3)) || { usage >&2; exit 1; }
  toast "Reminder" "$2"
  [[ $3 == "$reminder_dir"/tamlinux-reminder-*.message ]] && rm -f -- "$3"
  exit 0
  ;;
-h | --help)
  usage
  exit 0
  ;;
esac

minutes=${1:-}
shift || true
message="$*"
custom_message="$message"

if [[ ! $minutes =~ ^[0-9]{1,5}$ ]] || ((10#$minutes == 0)); then
  usage >&2
  exit 1
fi
minutes=$((10#$minutes))

if [[ -z $message ]]; then
  message="Your ${minutes} minutes are up"
fi

set_at=$(date +%s)
remind_at=$(date -d "+${minutes} minutes" +%H:%M)
unit="tamlinux-reminder-${minutes}m-$set_at-$$"
message_file="$reminder_dir/$unit.message"
confirmation="You'll be reminded at $remind_at"
confirmation_title="Reminder set for ${minutes} minutes"

mkdir -p -m 0700 "$reminder_dir"

if [[ -n $custom_message ]]; then
  printf "%s" "$custom_message" >"$message_file"
  confirmation_title="$custom_message in ${minutes} minutes"
fi

systemd-run --user --quiet --collect --on-active="${minutes}m" --unit="$unit" \
  "$self" due "$message" "$message_file"

toast "$confirmation_title" "$confirmation"
