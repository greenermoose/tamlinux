"""Keep all agy quota groups, including the separate Pro Argon allowance."""
import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader(
    "antigravity_usage", str(ROOT / "bin/tam-agent-usage-antigravity"))
spec = importlib.util.spec_from_loader(loader.name, loader)
collector = importlib.util.module_from_spec(spec)
loader.exec_module(collector)


def usage_report():
    """The agy 1.4.0 schema, with synthetic readings and reset times."""
    reset = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    groups = []
    for name, prefix, windows in [
        ("Gemini Models", "gemini", ["weekly", "5h"]),
        ("Claude and GPT models", "3p", ["weekly", "5h"]),
        ("Gemini 4 Argon", "gemini-argon-wtu", ["weekly"]),
    ]:
        groups.append({"name": name, "buckets": [
            {"id": f"{prefix}-{window}", "name": "Limit Remaining",
             "window": window, "remaining_fraction": .75, "reset_time": reset}
            for window in windows
        ]})
    return {"command": {"name": "usage", "data": {"groups": groups}}}


class CliTests(unittest.TestCase):
    def probe(self, report):
        proc = subprocess.CompletedProcess([], 0, json.dumps(report), "")
        with patch.object(collector.shutil, "which", return_value="/test/agy"), \
                patch.object(collector.subprocess, "run", return_value=proc) as run:
            result = collector.probe_limits_cli()
        self.assertEqual(run.call_args.args[0],
                         ["/test/agy", "--output-format", "json", "-p", "/usage"])
        self.assertEqual(run.call_args.kwargs["timeout"], 12)
        return result

    def test_all_five_windows_and_distinct_argon_label(self):
        result = self.probe(usage_report())
        self.assertTrue(result["ok"])
        self.assertEqual([entry["title"] for entry in result["limits"]], [
            "Gemini Weekly", "Gemini 5-hour", "Claude & GPT Weekly",
            "Claude & GPT 5-hour", "Gemini 4 Argon Weekly"])
        for entry in result["limits"]:
            self.assertEqual(entry["percent"], .25)
            self.assertTrue(entry["resetsAt"])

    def test_future_gemini_group_keeps_name_and_explicit_window(self):
        report = usage_report()
        group = report["command"]["data"]["groups"][-1]
        group["name"] = "Gemini 5 Special"
        group["buckets"][0]["name"] = "Gemini 5 Special Weekly Limit"
        self.assertEqual(self.probe(report)["limits"][-1]["title"],
                         "Gemini 5 Special Weekly")

    def test_bad_or_missing_fraction_does_not_invent_full_allowance(self):
        for value in [None, "bad", float("nan"), float("inf"), -.1, 1.1]:
            with self.subTest(value=value):
                report = usage_report()
                report["command"]["data"]["groups"][-1]["buckets"][0]["remaining_fraction"] = value
                self.assertFalse(self.probe(report)["ok"])

    def test_empty_wrong_or_malformed_report_is_not_success(self):
        for report in [{}, {"command": {"name": "usage", "data": {"groups": []}}},
                       {"command": {"name": "other"}},
                       {"command": {"name": "usage", "data": {"groups": [{"name": "Gemini"}]}}}]:
            with self.subTest(report=report):
                self.assertFalse(self.probe(report)["ok"])

    def test_missing_cli_and_timeout_are_failures(self):
        with patch.object(collector.shutil, "which", return_value=None):
            self.assertFalse(collector.probe_limits_cli()["ok"])
        with patch.object(collector.shutil, "which", return_value="/test/agy"), \
                patch.object(collector.subprocess, "run",
                             side_effect=subprocess.TimeoutExpired("agy", 12)):
            self.assertFalse(collector.probe_limits_cli()["ok"])


class CollectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cache = self.root / "antigravity-limits.json"
        for patcher in [
            patch.object(collector, "cache_root", return_value=self.root),
            patch.object(collector, "keyring_auth", return_value=("test-token", 0)),
            patch.object(collector, "probe_tier_http", return_value="Google AI Pro"),
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.limits = [collector.format_bucket_entry(group["name"], bucket)
                       for group in usage_report()["command"]["data"]["groups"]
                       for bucket in group["buckets"]]

    def write_cache(self, limits=None, source=collector.LIMITS_SOURCE):
        self.cache.write_text(json.dumps({
            "fetchedAtMs": round(time.time() * 1000), "source": source,
            "limits": self.limits if limits is None else limits,
            "tierLabel": "Google AI Pro"}))

    def test_old_partial_http_cache_is_refreshed_even_when_recent(self):
        self.write_cache(self.limits[2:4], source=None)
        with patch.object(collector, "probe_limits_cli",
                          return_value={"ok": True, "limits": self.limits}) as probe:
            result = collector.collect_limits(False)
        probe.assert_called_once()
        self.assertEqual(result["limits"], self.limits)
        self.assertFalse(result["limitsStale"])
        self.assertTrue(result["limitsUpdatedAt"])
        saved = json.loads(self.cache.read_text())
        self.assertEqual(saved["source"], collector.LIMITS_SOURCE)
        self.assertEqual(saved["limits"], self.limits)

    def test_new_cache_debounces_but_force_fetches(self):
        self.write_cache()
        with patch.object(collector, "probe_limits_cli",
                          return_value={"ok": True, "limits": self.limits}) as probe:
            self.assertEqual(collector.collect_limits(False)["limits"], self.limits)
            probe.assert_not_called()
            collector.collect_limits(True)
            probe.assert_called_once()

    def test_failed_refresh_marks_cache_stale_and_excludes_expired_window(self):
        limits = copy.deepcopy(self.limits)
        limits[0]["resetsAt"] = "2000-01-01T00:00:00Z"
        self.write_cache(limits)
        before = self.cache.read_bytes()
        with patch.object(collector, "probe_limits_cli", return_value={"ok": False}):
            result = collector.collect_limits(True)
        self.assertEqual(result["limits"], limits[1:])
        self.assertTrue(result["limitsStale"])
        self.assertIn("last known", result["usageStatusText"])
        self.assertTrue(result["limitsUpdatedAt"])
        self.assertEqual(self.cache.read_bytes(), before)

    def test_failure_without_cache_is_unavailable(self):
        with patch.object(collector, "probe_limits_cli", return_value={"ok": False}):
            result = collector.collect_limits(False)
        self.assertEqual(result["limits"], [])
        self.assertEqual(result["usageStatusText"], "Antigravity limits unavailable")
        self.assertFalse(self.cache.exists())

    def test_tier_failure_does_not_lose_quotas_or_invent_plan(self):
        with patch.object(collector, "probe_limits_cli",
                          return_value={"ok": True, "limits": self.limits}), \
                patch.object(collector, "probe_tier_http", return_value=""):
            result = collector.collect_limits(True)
        self.assertEqual(result["limits"], self.limits)
        self.assertEqual(result["tierLabel"], "")


if __name__ == "__main__":
    unittest.main()
