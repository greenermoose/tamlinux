#!/usr/bin/env bash
# tam-plugin lifecycle seams: dev on/off safety, restore, legacy test state,
# payload verify against the Tamlinux source, and the moved test/run commands.
# Self-contained: it uses the product's own plugin registry and a temporary
# home, and fails if anything would run Home Manager.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PRODUCT_DIR="$(cd "$ROOT_DIR/../.." && pwd)"
CLI="$ROOT_DIR/tam-plugin"

TEST_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEST_DIR"' EXIT

export TAMLINUX_REGISTRY="$PRODUCT_DIR/desktop/shell/host/registry.py"
[[ -f "$TAMLINUX_REGISTRY" ]] || { echo "FAIL: product registry not found: $TAMLINUX_REGISTRY" >&2; exit 1; }
export HOME="$TEST_DIR/home"
export XDG_STATE_HOME="$HOME/.local/state"
export FRED_LIVE_DIR="$HOME/.config/tamlinux/plugins"
export FRED_STATE_ROOT="$XDG_STATE_HOME/tam-plugin"
export FRED_PUBLISHED_ROOT="$HOME/Code/tamlinux"
export TAMLINUX_SOURCE_REPO="$FRED_PUBLISHED_ROOT/tamlinux"

fail() { echo "FAIL: $*" >&2; exit 1; }

mkdir -p "$HOME/bin" "$FRED_LIVE_DIR" "$TAMLINUX_SOURCE_REPO/desktop/plugins"
BASH_PATH="$(command -v bash)"  # no /usr/bin/env in a build sandbox
for tool in tam-qmlcache-purge tam-restart-shell; do
  printf '#!%s\nexit 0\n' "$BASH_PATH" > "$HOME/bin/$tool"
done
printf '#!%s\necho "home-manager must not run" >&2\nexit 1\n' "$BASH_PATH" > "$HOME/bin/home-manager"
chmod +x "$HOME/bin/"*
export PATH="$HOME/bin:$PATH"

source_dir="$TAMLINUX_SOURCE_REPO/desktop/plugins/fred.demo"
mkdir -p "$source_dir/assets/screenshots"
cat > "$source_dir/manifest.json" <<'EOF'
{
  "schemaVersion": 1,
  "kinds": ["bar-widget"],
  "id": "fred.demo",
  "name": "Demo",
  "version": "1.0.1",
  "author": "Test",
  "license": "GPL-3.0-or-later",
  "entryPoints": { "barWidget": "Main.qml" }
}
EOF
printf 'import QtQuick\nItem { id: root }\n' > "$source_dir/Main.qml"
printf '# Demo\n' > "$source_dir/README.md"
printf 'mock-screenshot\n' > "$source_dir/assets/screenshots/shot.png"

# The installed plugin: a managed copy of the same payload.
live="$FRED_LIVE_DIR/fred.demo"
cp -a "$source_dir" "$live"
printf 'installed\n' > "$live/installed-marker"

echo "=== dev on / dev off / restore ==="
"$CLI" dev fred.demo on >/dev/null
[[ -L "$live" && "$(readlink -f "$live")" == "$(readlink -f "$source_dir")" ]] || fail "dev on did not link the source"
[[ -f "$FRED_STATE_ROOT/dev/fred.demo/active" ]] || fail "dev on did not record state"
"$CLI" dev fred.demo on | grep -q "already linked" || fail "dev on is not idempotent"
"$CLI" dev fred.demo off >/dev/null
[[ -d "$live" && ! -L "$live" && -f "$live/installed-marker" ]] || fail "dev off did not restore the installed plugin"
[[ ! -e "$FRED_STATE_ROOT/dev/fred.demo" ]] || fail "dev off left state behind"

"$CLI" dev fred.demo on >/dev/null
"$CLI" restore fred.demo >/dev/null
[[ -f "$live/installed-marker" && ! -L "$live" ]] || fail "restore did not recover the installed plugin"

mv "$live" "$TEST_DIR/saved"
ln -s "$TEST_DIR/elsewhere" "$live"
if "$CLI" dev fred.demo on >/dev/null 2>&1; then fail "dev on accepted an unknown override link"; fi
"$CLI" restore fred.demo >/dev/null
[[ ! -e "$live" && ! -L "$live" ]] || fail "restore did not remove the unknown link"
mv "$TEST_DIR/saved" "$live"
echo "dev/restore passed"

echo "=== legacy snapshot test state ==="
mkdir -p "$FRED_STATE_ROOT/test/fred.demo"
: > "$FRED_STATE_ROOT/test/fred.demo/active"
if "$CLI" dev fred.demo on >/dev/null 2>&1; then fail "dev on ignored legacy test state"; fi
"$CLI" restore fred.demo >/dev/null
[[ ! -e "$FRED_STATE_ROOT/test/fred.demo" ]] || fail "restore did not clear legacy test state"
echo "legacy state passed"

echo "=== verify against the source ==="
rm -f "$live/installed-marker"
"$CLI" verify fred.demo | grep -q "SUCCESS" || fail "verify rejected identical payloads"
printf '# Changed docs\n' > "$source_dir/README.md"
printf 'other\n' > "$source_dir/assets/screenshots/shot.png"
"$CLI" verify fred.demo | grep -q "SUCCESS" || fail "verify counted documentation as behaviour"
printf 'import QtQuick\nItem { id: changed }\n' > "$source_dir/Main.qml"
if "$CLI" verify fred.demo >/dev/null 2>&1; then fail "verify missed a behaviour change"; fi
"$CLI" diff fred.demo | grep -q "changed" || fail "diff did not show the source change"
echo "verify passed"

echo "=== test and run moved to tam-deploy ==="
for moved in test run; do
  if out="$("$CLI" "$moved" fred.demo 2>&1)"; then fail "$moved still runs"; fi
  grep -q "tam-deploy" <<<"$out" || fail "$moved does not point to tam-deploy"
done
echo "moved commands passed"

echo "All tam-plugin lifecycle tests PASSED"
