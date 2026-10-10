"""Exercise real pipes and the collector's last-known reading contract."""
import importlib.machinery
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("codex_usage", str(ROOT / "bin/tam-agent-usage-codex"))
spec = importlib.util.spec_from_loader(loader.name, loader)
collector = importlib.util.module_from_spec(spec)
loader.exec_module(collector)


class PipeTests(unittest.TestCase):
    def start(self, body):
        proc = subprocess.Popen([sys.executable, "-u", "-c", body],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        self.addCleanup(self.stop, proc)
        return collector.RpcReader(proc)

    @staticmethod
    def stop(proc):
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=2)
        proc.stdin.close()
        proc.stdout.close()

    def test_batched_notifications_and_replies_across_requests(self):
        # One write puts both replies in the same read. No later pipe data
        # arrives to rescue a reader that polls before consuming its buffer.
        rpc = self.start('''import os,sys,time
sys.stdin.buffer.readline()
os.write(1, b'{"method":"account/updated"}\\n{"id":1,"result":{"first":true}}\\n{"method":"remoteControl/status/changed"}\\n{"id":2,"result":{"second":true}}\\n')
time.sleep(5)
''')
        self.assertEqual(rpc.request(1, "initialize", timeout=.5), {"first": True})
        self.assertEqual(rpc.request(2, "account/read", timeout=.5), {"second": True})

    def test_fragmented_reply_and_non_object_messages(self):
        rpc = self.start('''import os,sys,time
sys.stdin.buffer.readline()
os.write(1, b'garbage\\n[]\\n{"id":1,"res')
time.sleep(.03)
os.write(1, b'ult":{"ok":true}}\\n')
time.sleep(5)
''')
        self.assertEqual(rpc.request(1, "account/read", timeout=.5), {"ok": True})

    def test_silent_child_times_out_with_request_name(self):
        rpc = self.start("import sys,time;sys.stdin.buffer.readline();time.sleep(5)")
        with self.assertRaisesRegex(TimeoutError, r"Timed out after .* waiting for account/read"):
            rpc.request(1, "account/read", timeout=.05)

    def test_partial_line_cannot_block_past_deadline(self):
        rpc = self.start("import os,sys,time;sys.stdin.buffer.readline();os.write(1,b'{');time.sleep(5)")
        with self.assertRaises(TimeoutError):
            rpc.request(1, "account/read", timeout=.05)

    def test_closed_pipe_is_not_reported_as_timeout(self):
        rpc = self.start("import sys;sys.stdin.buffer.readline()")
        with self.assertRaisesRegex(ConnectionError, "closed the connection"):
            rpc.request(1, "account/read", timeout=.5)

    def test_rpc_error_is_not_an_empty_success(self):
        rpc = self.start('''import os,sys
sys.stdin.buffer.readline()
os.write(1,b'{"id":1,"error":{"code":-32000,"message":"private server detail"}}\\n')
''')
        with self.assertRaisesRegex(RuntimeError, r"account/read failed \(RPC error -32000\)"):
            rpc.request(1, "account/read", timeout=.5)

    def test_unterminated_response_has_size_bound(self):
        rpc = self.start("import os,sys;sys.stdin.buffer.readline();os.write(1,b'x'*(1024*1024+1))")
        with self.assertRaisesRegex(RuntimeError, "1 MiB"):
            rpc.request(1, "account/read", timeout=1)


class LimitsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.state = self.root / "tamlinux/agents/usage/codex.json"
        self.state.parent.mkdir(parents=True)
        self.account = {"type": "chatgpt", "email": "test@example.test", "planType": "pro"}
        self.reset = datetime.now(timezone.utc) + timedelta(hours=1)
        self.limits = {"rateLimits": {"primary": {"usedPercent": 37, "windowDurationMins": 300,
                                                   "resetsAt": int(self.reset.timestamp())}}}
        env = patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root), "CODEX_HOME": str(self.root / "codex")})
        env.start()
        self.addCleanup(env.stop)
        command = patch.object(collector, "find_command", return_value=sys.executable)
        command.start()
        self.addCleanup(command.stop)

    def fetch(self, account=None, failure=None, limits=None):
        account = self.account if account is None else account
        real_popen = subprocess.Popen
        # Popen is still real; only the RPC peer is scripted.
        script = 'import sys,time;sys.stdin.buffer.read()'
        with patch.object(collector.subprocess, "Popen", side_effect=lambda *a, **kw: real_popen([sys.executable, "-u", "-c", script], **kw)):
            def reply(reader, request_id, method, *args, **kwargs):
                if method == "initialize":
                    return {}
                if failure and failure[0] == method:
                    raise failure[1]
                if method == "account/read":
                    return {"account": account}
                return self.limits if limits is None else limits
            with patch.object(collector.RpcReader, "request", reply):
                return collector.fetch_codex_rpc()

    def seed(self):
        record = self.fetch()
        self.state.write_text(json.dumps(record))
        return record

    def test_success_has_timestamp_and_no_stale_warning(self):
        result = self.seed()
        self.assertEqual(result["limits"][0]["percent"], .37)
        self.assertEqual(result["tierLabel"], "pro")
        self.assertTrue(result["limitsUpdatedAt"])
        self.assertFalse(result["limitsStale"])
        self.assertFalse(result["retryAdvised"])
        self.assertEqual(result["authHelpText"], "")

    def test_repeated_failures_keep_original_reading_time(self):
        first = self.seed()
        for method in ("account/read", "account/rateLimits/read", "account/read"):
            result = self.fetch(failure=(method, TimeoutError(f"Timed out waiting for {method}")))
            self.assertEqual(result["limits"], first["limits"])
            self.assertEqual(result["limitsUpdatedAt"], first["limitsUpdatedAt"])
            self.assertTrue(result["limitsStale"])
            self.assertTrue(result["retryAdvised"])
            self.assertIn("last successful reading from", result["authHelpText"])
            self.assertIn(method, result["authHelpText"])
            self.state.write_text(json.dumps(result))

    def test_expired_window_removed_but_weekly_retained(self):
        record = self.seed()
        record["limits"].append(dict(record["limits"][0], label="Weekly (7-day)"))
        record["limits"][0]["resetsAt"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.state.write_text(json.dumps(record))
        result = self.fetch(failure=("account/read", TimeoutError("Timed out")))
        self.assertEqual([e["label"] for e in result["limits"]], ["Weekly (7-day)"])

    def test_recovery_replaces_fallback(self):
        self.seed()
        self.limits["rateLimits"]["primary"]["usedPercent"] = 41
        result = self.fetch()
        self.assertEqual(result["limits"][0]["percent"], .41)
        self.assertFalse(result["limitsStale"])
        self.assertEqual(result["usageStatusText"], "")

    def test_signout_api_key_and_account_switch_do_not_reuse_limits(self):
        for account in ({}, {"type": "apiKey"}, dict(self.account, email="other@example.test")):
            self.seed()
            result = self.fetch(account=account, failure=("account/rateLimits/read", TimeoutError("Timed out")))
            self.assertEqual(result["limits"], [])
            self.assertFalse(result["limitsStale"])
            if account.get("type") != "chatgpt":
                self.assertFalse(result["retryAdvised"])

    def test_missing_or_corrupt_state_does_not_hide_failure(self):
        for text in (None, "{broken", "[]", '{"limitsSource":"wrong"}'):
            if text is not None:
                self.state.write_text(text)
            result = self.fetch(failure=("account/read", TimeoutError("Timed out waiting for account/read")))
            self.assertEqual(result["limits"], [])
            self.assertIn("Timed out", result["authHelpText"])
            self.assertEqual(result["usageStatusText"], "Codex limits unavailable")

    def test_rpc_error_and_empty_windows_are_visible(self):
        for result in (self.fetch(failure=("account/rateLimits/read", RuntimeError("RPC error -32000"))),
                       self.fetch(limits={"rateLimits": {}})):
            self.assertTrue(result["usageStatusText"])
            self.assertTrue(result["authHelpText"])
            self.assertTrue(result["retryAdvised"])

    def test_source_and_future_timestamp_cannot_reuse_limits(self):
        for change in ({"limitsSource": "other"}, {"limitsUpdatedAt": self.reset.isoformat()}):
            record = self.seed()
            record.update(change)
            self.state.write_text(json.dumps(record))
            result = self.fetch(failure=("account/read", TimeoutError("Timed out")))
            self.assertEqual(result["limits"], [])


@unittest.skipUnless(shutil.which("node"), "Node needed for QML formatter checks")
class HoverTests(unittest.TestCase):
    def test_live_stale_and_expired_text(self):
        script = r'''
const fs = require('fs');
const assert = require('assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
const root = {nowMs: Date.now(), pluginVersion: '2.0.1', providers: [],
  formatTimestamp: value => value,
  limitWindow: (label, percent, resetAt) => ({percent, resetAt})};
// QML resolves sibling functions unqualified; mirror that scope here.
globalThis.root = root;
globalThis.limitWindow = root.limitWindow;
for (const name of ['limitWindows', 'bindingWindow', 'formatBarHover']) {
  const start = source.indexOf('  function ' + name + '(');
  const end = source.indexOf('\n  }', start) + 4;
  root[name] = eval('(' + source.slice(start, end).trim() + ')');
  globalThis[name] = root[name];
}
const stamp = new Date(root.nowMs - 60000).toISOString();
const future = new Date(root.nowMs + 60000).toISOString();
const p = {providerName: 'Codex', limits: [{label: '5h window', percent: .37, resetsAt: future}],
           limitsUpdatedAt: stamp, limitsStale: false};
root.providers = [p];
assert.match(root.formatBarHover(), /Codex 37%/);
assert.ok(!root.formatBarHover().includes('last known'));
p.limitsStale = true;
assert.ok(root.formatBarHover().includes('last known ' + stamp));
p.limits[0].resetsAt = stamp;
assert.ok(root.formatBarHover().includes('Codex · unknown'));
assert.ok(!root.formatBarHover().includes('37%'));
assert.ok(root.formatBarHover().endsWith('\n\nfred.agents v2.0.1'));
'''
        result = subprocess.run(["node", "-e", script, str(ROOT / "Panel.qml")],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
