#!/bin/bash
# suspend-unless-stay-awake picks hibernation only where logind allows it.
# Stubs replace busctl, systemctl and logger; nothing sleeps.
set -u
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin" "$work/state/tamlinux"
cat > "$work/bin/busctl" <<'S'
#!/bin/sh
[ "${CAN:-}" = fail ] && exit 1
printf 's "%s"\n' "$CAN"
S
cat > "$work/bin/systemctl" <<'S'
#!/bin/sh
printf '%s\n' "$*" > "$CALLED"
S
printf '#!/bin/sh\ncat >/dev/null\n' > "$work/bin/logger"
chmod +x "$work/bin/"*
failed=0
check() {  # can-answer stay-awake expected
  rm -f "$work/called" "$work/state/tamlinux/stay-awake"
  [[ $2 == on ]] && : > "$work/state/tamlinux/stay-awake"
  CAN=$1 CALLED="$work/called" XDG_STATE_HOME="$work/state" TAMLINUX_STAY_AWAKE_FILE= \
    PATH="$work/bin:$PATH" bash "$here/suspend-unless-stay-awake" >/dev/null 2>&1
  local got; got="$(cat "$work/called" 2>/dev/null || echo none)"
  if [[ $got == "$3" ]]; then echo "ok: can=$1 stay-awake=$2 -> $got"
  else echo "FAIL: can=$1 stay-awake=$2 -> $got (expected $3)"; failed=1; fi
}
check yes off suspend-then-hibernate
check na off suspend
check no off suspend
check fail off suspend
check yes on none
exit $failed
