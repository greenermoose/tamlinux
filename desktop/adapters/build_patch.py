"""Build the pinned fred.clock adapter patch for the shell proof."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

PINNED_REVISION = "ed5140ccefc83c0a2fdd5f899bbd290acc35d88a"

BAR_IPC_STUB = '''    function openAddEvent(): void {
      if (root.bar && root.bar.reportUnsupported) root.bar.reportUnsupported("event-edit")
    }
    function closeAddEvent(): void {
      if (panelLoader.item && panelLoader.item.closeAddEvent) panelLoader.item.closeAddEvent()
    }
    function createEvent(summary: string, date: string, allDay: string, startTime: string, endTime: string, location: string): void {
      if (root.bar && root.bar.reportUnsupported) root.bar.reportUnsupported("event-edit")
    }
    function deleteEvent(uid: string): void {
      if (root.bar && root.bar.reportUnsupported) root.bar.reportUnsupported("event-edit")
    }'''


def repo_default() -> Path:
    return Path(__file__).resolve().parents[3] / "clock-fred-tamlinux"


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def adapt_bar(text: str) -> str:
    text = _once(text, "import qs.Commons\nimport qs.Ui\n", "import Tam.Commons\nimport Tam.Ui\nimport \".\"\n", "bar imports")
    text = _once(text, 'moduleName: "omarchy.clock"', 'moduleName: "fred.clock"', "bar module")
    text = _once(
        text,
        """  function runFetch() {
    if (!fetchProc.running) {
      fetchProc.launch()
    }
  }""",
        """  function runFetch() {
    if (Quickshell.env("TAMLINUX_CLOCK_OFFLINE") === "1") {
      console.log("TAMLINUX_EVIDENCE fetch-suppressed")
      return
    }
    if (!fetchProc.running) fetchProc.launch()
  }""",
        "runFetch",
    )
    text = _once(text, "    running: true\n", "    running: Quickshell.env(\"TAMLINUX_CLOCK_OFFLINE\") !== \"1\"\n", "fetch timer")
    text = _once(
        text,
        'else if (b === Qt.MiddleButton) { if (root.bar) root.bar.run("omarchy-menu-timezone") }',
        'else if (b === Qt.MiddleButton) { if (root.bar && root.bar.reportUnsupported) root.bar.reportUnsupported("timezone") }',
        "timezone action",
    )
    text = _once(text, 'target: "omarchy.clock"', 'target: "tamlinux.clock"', "ipc target")
    start = text.find("    function openAddEvent(): void {")
    end = text.find("  }\n\n  IpcHandler {\n    target: \"fred.clock\"", start)
    if start < 0 or end < 0:
        raise SystemExit("bar event IPC block not found")
    # Keep the closing brace of the tamlinux.clock handler that precedes the stub.
    text = text[:start] + BAR_IPC_STUB + "\n" + text[end:]
    fred = text.find('  IpcHandler {\n    target: "fred.clock"')
    widget = text.find("\n  WidgetButton {", fred)
    if fred < 0 or widget < 0:
        raise SystemExit("fred.clock IPC handler not found")
    text = text[:fred] + text[widget + 1:]
    if 'target: "fred.clock"' in text or 'target: "omarchy.clock"' in text:
        raise SystemExit("production IPC target remains")
    if "omarchy-menu-timezone" in text or "qs.Commons" in text:
        raise SystemExit("omarchy coupling remains in BarWidget.qml")
    return text


def adapt_panel(text: str) -> str:
    text = _once(text, "import qs.Commons\nimport qs.Ui\n", "import Tam.Commons\nimport Tam.Ui\nimport \".\"\n", "panel imports")
    text = _once(text, 'moduleName: "omarchy.clock"', 'moduleName: "fred.clock"', "panel module")
    text = _once(
        text,
        '  moduleName: "fred.clock"\n',
        '''  moduleName: "fred.clock"\n  readonly property bool eventEditingEnabled: Quickshell.env("TAMLINUX_CLOCK_OFFLINE") !== "1"\n''',
        "edit flag",
    )
    text = _once(
        text,
        """  function toggleAddEvent() {
    root.addEventOpen = !root.addEventOpen
  }

  function openAddEvent() {
    root.addEventOpen = true
  }""",
        """  function refuseEventEdit() {
    if (root.eventEditingEnabled) return false
    if (root.bar && root.bar.reportUnsupported) root.bar.reportUnsupported("event-edit")
    return true
  }

  function toggleAddEvent() {
    if (root.refuseEventEdit()) return
    root.addEventOpen = !root.addEventOpen
  }

  function openAddEvent() {
    if (root.refuseEventEdit()) return
    root.addEventOpen = true
  }""",
        "add event guards",
    )
    text = _once(
        text,
        """  function submitNewEvent(title, allDay, startTime, endTime, location, targetDate) {
    if (!title || !title.trim()) return""",
        """  function submitNewEvent(title, allDay, startTime, endTime, location, targetDate) {
    if (root.refuseEventEdit()) return
    if (!title || !title.trim()) return""",
        "submit guard",
    )
    text = _once(
        text,
        """  function deleteLocalEvent(eventUid) {
    if (!eventUid) return""",
        """  function deleteLocalEvent(eventUid) {
    if (root.refuseEventEdit()) return
    if (!eventUid) return""",
        "delete guard",
    )
    text = _once(
        text,
        """                  PanelActionButton {
                    id: agendaAddBtn
                    iconText: "󰐕\"""",
        """                  PanelActionButton {
                    id: agendaAddBtn
                    visible: root.eventEditingEnabled
                    iconText: "󰐕\"""",
        "add button",
    )
    text = _once(
        text,
        "visible: !!modelData.isLocal",
        "visible: root.eventEditingEnabled && !!modelData.isLocal",
        "delete button",
    )
    if "qs.Commons" in text or 'moduleName: "omarchy.clock"' in text:
        raise SystemExit("omarchy coupling remains in Panel.qml")
    return text


def adapt_tree(tree: Path) -> None:
    bar = tree / "BarWidget.qml"
    panel = tree / "Panel.qml"
    bar.write_text(adapt_bar(bar.read_text(encoding="utf-8")), encoding="utf-8")
    panel.write_text(adapt_panel(panel.read_text(encoding="utf-8")), encoding="utf-8")
    (tree / "qmldir").write_text("Launch 1.0 Launch.qml\n", encoding="utf-8")


def export_pinned(clock_repo: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(clock_repo), "archive", PINNED_REVISION],
        check=True,
        capture_output=True,
    )
    subprocess.run(["tar", "-x", "-C", str(destination)], input=archive.stdout, check=True)


def build_patch(clock_repo: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="tamlinux-clock-patch-") as temporary:
        root = Path(temporary)
        original = root / "a"
        adapted = root / "b"
        export_pinned(clock_repo, original)
        export_pinned(clock_repo, adapted)
        adapt_tree(adapted)
        diff = subprocess.run(
            ["diff", "-ruN", "a", "b"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if diff.returncode not in (0, 1):
            raise SystemExit(diff.stderr)
        stable = []
        for line in diff.stdout.splitlines(keepends=True):
            if line.startswith("--- ") or line.startswith("+++ "):
                line = line.split("\t", 1)[0]
                if not line.endswith("\n"):
                    line += "\n"
            stable.append(line)
        return "".join(stable)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clock-repo", type=Path, default=repo_default())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    patch_path = Path(__file__).resolve().parent / "clock-step1.patch"
    generated = build_patch(args.clock_repo)
    if args.check:
        current = patch_path.read_text(encoding="utf-8") if patch_path.exists() else ""
        if current != generated:
            raise SystemExit("clock-step1.patch does not match the generator")
        return
    if args.write or not args.check:
        patch_path.write_text(generated, encoding="utf-8")
        print(patch_path)


if __name__ == "__main__":
    main()
