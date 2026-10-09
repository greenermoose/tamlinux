"""Challenge the real QML logger and conservative shadow evidence accounting."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

DESKTOP = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("protocol_shadow", str(DESKTOP / "protocol-shadow"))
spec = importlib.util.spec_from_loader(loader.name, loader)
shadow = importlib.util.module_from_spec(spec)
loader.exec_module(shadow)
IDENTITY = "a" * 64
REVISION = "b" * 40


def entry(number, when, status="equal", identity=IDENTITY, invocation="one"):
    return {"__CURSOR": str(number), "__REALTIME_TIMESTAMP": str(int(when * 1000000)),
            "_BOOT_ID": "boot", "_SYSTEMD_INVOCATION_ID": invocation,
            "MESSAGE": "qml: " + shadow.MARKER + json.dumps({
                "schema": 1, "identity": identity, "revision": REVISION,
                "sequence": number + 1, "comparisons": number + 1, "status": status,
                "differences": [] if status == "equal" else ["workspaces"],
                "problems": [], "outputs": 3, "workspaces": 4})}


class ShadowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "evidence.sqlite3"
        self.db = shadow.database(self.path)
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.db.close)

    def insert(self, *entries):
        self.db.executemany("INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                            [shadow.parse_record(json.dumps(row)) for row in entries])
        self.db.commit()

    def complete_trial(self):
        self.insert(*(entry(i, 1000 + i * 60) for i in range(14 * 24 * 60 + 1)))
        for kind in shadow.KINDS:
            self.db.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                                [(kind, 1100 + i * 120, 1110 + i * 120, IDENTITY, "observed") for i in range(3)])

    def test_complete_period_needs_time_health_and_all_events(self):
        self.complete_trial()
        result = shadow.summarize(self.db, 1000 + 14 * 86400)
        self.assertTrue(result["readyForAuthority"], result)
        self.assertEqual(result["events"], dict.fromkeys(shadow.KINDS, 3))
        self.assertFalse(shadow.summarize(self.db, 1000 + 14 * 86400 + 181)["readyForAuthority"])

    def test_difference_cannot_be_hidden_by_later_agreement(self):
        self.complete_trial()
        row = entry(100, 7000, "different")
        self.db.execute("UPDATE records SET payload=? WHERE cursor='100'", (shadow.parse_record(json.dumps(row))[-1],))
        result = shadow.summarize(self.db, 1000 + 14 * 86400)
        self.assertFalse(result["readyForAuthority"])
        self.assertEqual(result["nonEqualRecords"], 1)

    def test_code_change_and_return_restart_period(self):
        self.insert(entry(0, 1000), entry(1, 2000, identity="c" * 64), entry(2, 3000))
        result = shadow.summarize(self.db, 3000)
        self.assertEqual(result["firstEqual"], 3000)
        self.assertEqual(result["observedDays"], 0)

    def test_logging_gap_requires_supported_sleep_or_boot_note(self):
        self.insert(entry(0, 1000), entry(1, 1060), entry(2, 5000, invocation="two"))
        self.assertEqual(shadow.summarize(self.db, 5000)["unexplainedGapCount"], 1)
        self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                        ("suspend-resume", 1100, 4980, IDENTITY, "observed sleep"))
        self.assertEqual(shadow.summarize(self.db, 5000)["unexplainedGapCount"], 0)

    def test_overlapping_or_unsupported_notes_do_not_inflate_coverage(self):
        self.insert(*(entry(i, 1000 + i * 60) for i in range(10)))
        for start, end in ((1100, 1200), (1150, 1250), (3000, 3010)):
            self.db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                            ("workspace-move", start, end, IDENTITY, "observation"))
        result = shadow.summarize(self.db, 4000)
        self.assertEqual(result["events"]["workspace-move"], 1)
        self.assertEqual(result["unsupportedEvents"], 1)

    def test_collector_retries_are_idempotent_and_failure_is_atomic(self):
        rows = [entry(0, 1000), entry(1, 1060)]
        def journal(argv, **kwargs):
            for row in rows:
                kwargs["stdout"].write((json.dumps(row) + "\n").encode())
        with patch.object(shadow.subprocess, "run", side_effect=journal):
            self.assertEqual(shadow.collect(self.db), 2)
            self.assertEqual(shadow.collect(self.db), 0)
            rows.append(dict(entry(2, 1120), MESSAGE=shadow.MARKER + "{}"))
            with self.assertRaises(ValueError):
                shadow.collect(self.db)
        self.assertEqual(self.db.execute("SELECT count(*) FROM records").fetchone()[0], 2)

    def test_missing_identity_invalid_counters_and_symlink_are_rejected(self):
        for field, value in (("identity", "development"), ("outputs", True), ("status", "equal")):
            row = entry(0, 1000, "different")
            payload = json.loads(row["MESSAGE"].split(shadow.MARKER)[1])
            payload[field] = value
            row["MESSAGE"] = shadow.MARKER + json.dumps(payload)
            with self.assertRaises(ValueError):
                shadow.parse_record(json.dumps(row))
        link = self.path.parent / "link.sqlite3"
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            shadow.database(link)

    def test_timezone_is_required(self):
        with self.assertRaises(ValueError):
            shadow.timestamp("2026-10-09T12:00:00")

    def test_journal_binary_color_messages_are_decoded_and_checked(self):
        row = entry(0, 1000)
        expected = shadow.parse_record(json.dumps(row))
        row["MESSAGE"] = list(("\x1b[34m DEBUG\x1b[0m " + row["MESSAGE"]).encode())
        self.assertEqual(shadow.parse_record(json.dumps(row)), expected)
        for invalid in ([True], [256], [-1], ["text"], [255], [0] * 4097):
            row["MESSAGE"] = invalid
            with self.assertRaises(ValueError):
                shadow.parse_record(json.dumps(row))

    def test_dropped_difference_is_detected_even_between_healthy_heartbeats(self):
        self.insert(entry(0, 1000), entry(2, 1060))
        result = shadow.summarize(self.db, 1060)
        self.assertEqual(result["sequenceGaps"], 1)
        self.assertIn("missing or reordered journal sequences", result["blockers"])


class ShadowQmlTests(unittest.TestCase):
    def test_actual_settling_transitions_and_heartbeats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "host").mkdir()
            shutil.copyfile(DESKTOP / "fixtures/protocol-shadow/shell.qml", root / "shell.qml")
            for name in ("ProtocolShadow.qml", "protocol_model.js"):
                shutil.copyfile(DESKTOP / "shell/host" / name, root / "host" / name)
            result = subprocess.run(["/usr/bin/quickshell", "--no-color", "-p", str(root)],
                                    env={"PATH": "/usr/bin", "HOME": directory, "XDG_RUNTIME_DIR": directory,
                                         "QT_QPA_PLATFORM": "offscreen", "QSG_RENDER_LOOP": "basic"},
                                    capture_output=True, text=True, timeout=15)
        log = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, log)
        self.assertIn("SHADOW_FIXTURE_OK", log)
        self.assertNotIn("SHADOW_FIXTURE_FAILED", log)
        self.assertNotIn("TypeError", log)
        self.assertNotIn("ReferenceError", log)
        records = [json.loads(line.split(shadow.MARKER)[1]) for line in log.splitlines() if shadow.MARKER in line]
        self.assertEqual(records[0]["status"], "equal")
        self.assertIn("different", [row["status"] for row in records])
        self.assertIn("unready", [row["status"] for row in records])
        self.assertGreaterEqual(sum(row["status"] == "equal" for row in records), 3)
        self.assertTrue(all(len(json.dumps(row)) < 1024 for row in records))


if __name__ == "__main__":
    unittest.main()
