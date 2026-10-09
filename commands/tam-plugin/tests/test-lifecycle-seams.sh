#!/usr/bin/env bash
# Test fixture for plugin lifecycle seams (Seams 1, 2, 3)
# Covers: dev on/off safety, restore command, HM preflight logic,
# exact snapshots (git-aware, no cache leakage), payload manifests,
# deployed-source test snapshots, and verify/run workflows.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI="$ROOT_DIR/tam-plugin"

TEST_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEST_DIR"' EXIT

export TAMLINUX_REGISTRY="${TAMLINUX_REGISTRY:-$HOME/.local/share/tamlinux/shell/host/registry.py}"
export HOME="$TEST_DIR/home"
export XDG_STATE_HOME="$HOME/.local/state"
export FRED_LIVE_DIR="$HOME/.config/tamlinux/plugins"
export FRED_STATE_ROOT="$XDG_STATE_HOME/tam-plugin"
export FRED_TEST_ROOT="$FRED_STATE_ROOT/test"
export FRED_DEV_ROOT="$FRED_STATE_ROOT/dev"
export FRED_PUBLISHED_ROOT="$HOME/Code/tamlinux"
export FRED_CONFIG_REPO="$HOME/Code/tamlinux/workstation-config"

mkdir -p "$HOME/bin" \
  "$FRED_LIVE_DIR" \
  "$FRED_PUBLISHED_ROOT/demo-fred-tamlinux" \
  "$FRED_CONFIG_REPO/config/tamlinux/plugins/fred.demo" \
  "$FRED_CONFIG_REPO/system"

# Mock shell commands and tools
cat > "$HOME/bin/tam-qmlcache-purge" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
cat > "$HOME/bin/tam-restart-shell" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF

cat > "$HOME/bin/home-manager" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
# Mock home-manager switch
if [[ "${1:-}" == "switch" ]]; then
  if [[ -n "${FRED_MOCK_RUN:-}" ]]; then
    cp -a "$FRED_CONFIG_REPO/config/tamlinux/plugins/fred.demo/." "$FRED_LIVE_DIR/fred.demo/"
    rm -f "$FRED_LIVE_DIR/fred.demo/live-marker.txt"
  fi
  echo "mock: home-manager switch succeeded"
  exit 0
fi
exit 0
EOF

chmod +x "$HOME/bin/tam-qmlcache-purge" "$HOME/bin/tam-restart-shell" "$HOME/bin/home-manager"
export PATH="$HOME/bin:$PATH"

# Setup initial bom.json in mock config repo
cat > "$FRED_CONFIG_REPO/system/bom.json" <<'EOF'
{
  "name": "workstation-config",
  "components": {
    "plugins": {
      "fred.demo": "1.0.0"
    }
  }
}
EOF

# Setup git in config repo and published repo
git -C "$FRED_CONFIG_REPO" init -q
git -C "$FRED_CONFIG_REPO" config user.name Test
git -C "$FRED_CONFIG_REPO" config user.email test@example.invalid
cat > "$FRED_CONFIG_REPO/flake.nix" <<'EOF'
{ description = "mock"; }
EOF

pub_repo="$FRED_PUBLISHED_ROOT/demo-fred-tamlinux"
git -C "$pub_repo" init -q
git -C "$pub_repo" config user.name Test
git -C "$pub_repo" config user.email test@example.invalid

echo "=== Setup complete ==="

# 1. Setup deployed files
dep_dir="$FRED_CONFIG_REPO/config/tamlinux/plugins/fred.demo"
mkdir -p "$dep_dir/assets/screenshots" "$dep_dir/bin"
cat > "$dep_dir/manifest.json" <<'EOF'
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
cat > "$dep_dir/Main.qml" <<'EOF'
import QtQuick
Item { id: root }
EOF
cat > "$dep_dir/assets/icon.svg" <<'EOF'
<svg></svg>
EOF
cat > "$dep_dir/assets/screenshots/shot.png" <<'EOF'
mock-screenshot-bytes
EOF
cat > "$dep_dir/preview.png" <<'EOF'
mock-preview-bytes
EOF
cat > "$dep_dir/README.md" <<'EOF'
# Deployed README
EOF
git -C "$FRED_CONFIG_REPO" add config/tamlinux/plugins/fred.demo flake.nix system/bom.json
git -C "$FRED_CONFIG_REPO" commit -qm 'initial deployed commit'

# Setup simulated live directory (managed store directory)
live_dir="$FRED_LIVE_DIR/fred.demo"
mkdir -p "$live_dir"
echo "store-file" > "$live_dir/live-marker.txt"

echo "=== Testing Seam 1: dev on / dev off / restore ==="

# Test dev on
"$CLI" dev fred.demo on
[[ -L "$live_dir" ]]
[[ "$(readlink -f "$live_dir")" == "$(readlink -f "$dep_dir")" ]]
[[ -d "$FRED_DEV_ROOT/fred.demo/original" ]]
[[ -f "$FRED_DEV_ROOT/fred.demo/original/live-marker.txt" ]]
[[ -f "$FRED_DEV_ROOT/fred.demo/active" ]]

# Test dev on idempotency
"$CLI" dev fred.demo on
[[ -L "$live_dir" ]]

# Test dev off
"$CLI" dev fred.demo off
[[ ! -L "$live_dir" ]]
[[ -d "$live_dir" ]]
[[ -f "$live_dir/live-marker.txt" ]]
[[ ! -e "$FRED_DEV_ROOT/fred.demo/active" ]]
[[ ! -e "$FRED_DEV_ROOT/fred.demo/original" ]]

# Test restore from interrupted dev mode
"$CLI" dev fred.demo on
[[ -L "$live_dir" ]]
"$CLI" restore fred.demo
[[ ! -L "$live_dir" ]]
[[ -d "$live_dir" ]]
[[ -f "$live_dir/live-marker.txt" ]]
[[ ! -e "$FRED_DEV_ROOT/fred.demo/active" ]]

# Test restore from interrupted test mode
cp "$dep_dir/manifest.json" "$dep_dir/Main.qml" "$pub_repo/"
git -C "$pub_repo" add manifest.json Main.qml
git -C "$pub_repo" commit -qm 'initial pub commit'
"$CLI" test fred.demo worktree
[[ -L "$live_dir" ]]
"$CLI" restore fred.demo
[[ ! -L "$live_dir" ]]
[[ -d "$live_dir" ]]
[[ -f "$live_dir/live-marker.txt" ]]
[[ ! -e "$FRED_TEST_ROOT/fred.demo/active" ]]

echo "Seam 1 tests passed!"

echo "=== Testing Seam 3: Exact, reproducible snapshots and payload manifest ==="

# Add .gitignore in pub_repo
cat > "$pub_repo/.gitignore" <<'EOF'
__pycache__/
*.pyc
*.ignored
EOF

mkdir -p "$pub_repo/__pycache__" "$pub_repo/assets/screenshots"
echo "bytecode" > "$pub_repo/__pycache__/cache.pyc"
echo "ignored-content" > "$pub_repo/test.ignored"
echo "extra-qml" > "$pub_repo/Extra.qml"
echo "<svg></svg>" > "$pub_repo/assets/icon.svg"
echo "shot" > "$pub_repo/assets/screenshots/shot.png"
echo "preview" > "$pub_repo/preview.png"
echo "# Public README" > "$pub_repo/README.md"
git -C "$pub_repo" add .gitignore

"$CLI" test fred.demo worktree
[[ -L "$live_dir" ]]

# Verify snapshot contents
snap_target="$(readlink -f "$live_dir")"
[[ -f "$snap_target/Main.qml" ]]
[[ -f "$snap_target/Extra.qml" ]]
[[ -f "$snap_target/assets/icon.svg" ]]
# Ignored files must NOT be in snapshot
[[ ! -e "$snap_target/__pycache__" ]]
[[ ! -e "$snap_target/test.ignored" ]]
# Payload manifest must exist
[[ -f "$snap_target/.payload.manifest" ]]
[[ -f "$snap_target/.payload.digest" ]]

# Manifest must include Extra.qml and assets/icon.svg
grep "Extra.qml" "$snap_target/.payload.manifest"
grep "assets/icon.svg" "$snap_target/.payload.manifest"
# Manifest must NOT include distribution/doc files
! grep "README.md" "$snap_target/.payload.manifest" || false
! grep "assets/screenshots" "$snap_target/.payload.manifest" || false
! grep "preview.png" "$snap_target/.payload.manifest" || false

# Check status reports digest and verified
status_out="$("$CLI" test fred.demo status)"
[[ "$status_out" == *"payload-digest:"* ]]
[[ "$status_out" == *"payload-integrity: verified"* ]]

"$CLI" test fred.demo off

echo "Seam 3 tests passed!"

# A committed deployed subtree must be rooted at the plugin, regardless of
# config/tamlinux/plugins depth, and ignore subsequent working-tree edits.
printf 'uncommitted body\n' >> "$dep_dir/Main.qml"
"$CLI" test fred.demo HEAD --source deployed
snap_target="$(readlink -f "$live_dir")"
[[ -f "$snap_target/manifest.json" ]]
[[ -f "$snap_target/assets/icon.svg" ]]
! grep -q 'uncommitted body' "$snap_target/Main.qml"
"$CLI" test fred.demo off
git -C "$FRED_CONFIG_REPO" show HEAD:config/tamlinux/plugins/fred.demo/Main.qml > "$dep_dir/Main.qml"

echo "=== Testing Seam 2: Deployed source, payload verify, and Run transition ==="

# Test snapshot from deployed source
# Make sure dep_dir has matching Extra.qml
cp "$pub_repo/Extra.qml" "$dep_dir/"
git -C "$FRED_CONFIG_REPO" add config/tamlinux/plugins/fred.demo/Extra.qml
git -C "$FRED_CONFIG_REPO" commit -qm 'add Extra.qml to deployed'

"$CLI" test fred.demo --source deployed worktree
[[ -L "$live_dir" ]]
snap_dep="$(readlink -f "$live_dir")"
grep -q "source-type: deployed" "${snap_dep}.meta"
"$CLI" test fred.demo off

# Test tam-plugin verify
# 1. Matching payloads:
"$CLI" verify fred.demo

# 2. Permitted difference: change README.md in pub_repo
echo "# Different README" > "$pub_repo/README.md"
echo "new-shot" > "$pub_repo/assets/screenshots/shot2.png"
"$CLI" verify fred.demo

# 3. Behavior-bearing drift: change Extra.qml in pub_repo
echo "modified-code" > "$pub_repo/Extra.qml"
if "$CLI" verify fred.demo >/dev/null 2>&1; then
  echo "verify unexpectedly succeeded with code drift!" >&2
  exit 1
fi
echo "verify correctly rejected code drift!"

# Revert code drift
cp "$dep_dir/Extra.qml" "$pub_repo/Extra.qml"
"$CLI" verify fred.demo

# Test tam-plugin run
export FRED_MOCK_RUN=1
"$CLI" run fred.demo
[[ ! -L "$live_dir" ]]

# Check system/plugin-runs/fred.demo.json
run_record="$FRED_CONFIG_REPO/system/plugin-runs/fred.demo.json"
[[ -f "$run_record" ]]
cat "$run_record"
grep -q '"id": "fred.demo"' "$run_record"
grep -q '"version": "1.0.1"' "$run_record"

# Check system/bom.json updated
bom_ver="$(jq -r '.components.plugins["fred.demo"]' "$FRED_CONFIG_REPO/system/bom.json")"
[[ "$bom_ver" == "1.0.1" ]]

echo "Seam 2 tests passed!"
echo "All lifecycle seams tests PASSED successfully!"



# A rejected snapshot must preserve the running installation.
cp "$live_dir/Main.qml" "$TEST_DIR/prior.qml"
printf '{"schemaVersion": 999}' > "$pub_repo/manifest.json"
if "$CLI" test fred.demo worktree > /dev/null 2>&1; then
  echo "invalid manifest unexpectedly entered test mode" >&2; exit 1
fi
cmp "$live_dir/Main.qml" "$TEST_DIR/prior.qml"
[[ ! -L "$live_dir" ]]
for removed in install remove update; do
  if "$CLI" "$removed" fred.demo > /dev/null 2>&1; then
    echo "removed command $removed unexpectedly succeeded" >&2; exit 1
  fi
done
# Turning test mode off must preserve the digest gate for Run.
printf 'changed after testing' > "$dep_dir/Main.qml"
git -C "$FRED_CONFIG_REPO" add config/tamlinux/plugins/fred.demo/Main.qml
git -C "$FRED_CONFIG_REPO" commit -qm 'candidate drift'
if "$CLI" run fred.demo > /dev/null 2>&1; then
  echo "Run unexpectedly accepted a different candidate" >&2; exit 1
fi
