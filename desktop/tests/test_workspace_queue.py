"""Execute the production shared queue with fake bars and asynchronous helpers."""
from pathlib import Path
import shutil
import subprocess
import unittest

QUEUE = Path(__file__).resolve().parents[1] / 'plugins/fred.workspaces/ActionQueue.js'


@unittest.skipUnless(shutil.which('node'), 'Node required for shared JS queue regression')
class WorkspaceQueueTests(unittest.TestCase):
    def run_case(self, case):
        script = "const assert = require('node:assert/strict');\n" + QUEUE.read_text().replace('.pragma library', '') + r'''
const calls = [], rejected = [];
function bar(name) { return {
  desktopIngressOrigin: () => 'ACTIVE',
  startPublication: args => calls.push([name, 'publish', args]),
  startQueuedAction: args => calls.push([name, 'work', args]),
  queueRejected: args => rejected.push(args)
}; }
const a = bar('A'), b = bar('B'); register(a); register(b);
''' + case
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_two_bars_and_more_than_five_clicks_coalesce_to_latest_in_ingress_order(self):
        self.run_case(r'''
submit(a, ['switch','1'], true);
for (let n=2; n<=10; n++) submit(n%2 ? a:b, ['switch',String(n)], true);
assert.deepEqual(calls, [['A','publish',['accept-switch','1','ACTIVE']]]);
published(a, true);
assert.deepEqual(calls[1], ['A','publish',['accept-switch','10','ACTIVE']]);
published(a, true);
assert.deepEqual(calls[2], ['A','work',['apply-intent']]);
assert.equal(rejected.length, 0); assert.equal(pending.length, 0);
''')

    def test_new_click_is_published_while_slow_worker_runs_and_follow_is_removed(self):
        self.run_case(r'''
submit(a, ['switch','2'], true); published(a,true);
submit(b, ['switch','1','follow-timer'], true);
submit(b, ['switch','3'], true);
assert.deepEqual(calls.at(-1), ['A','publish',['accept-switch','3','ACTIVE']]);
published(a,true); finished(a,false,false);
assert.deepEqual(calls.at(-1), ['A','work',['apply-intent']]);
assert.equal(calls.filter(c=>c[2][2]==='follow-timer').length,0);
''')

    def test_bar_destruction_replays_latest_publisher_on_survivor(self):
        self.run_case(r'''
submit(a, ['switch','2'], true); submit(b, ['switch','3'], true);
unregister(a);
assert.deepEqual(calls.at(-1), ['B','publish',['accept-switch','3','ACTIVE']]);
published(a,true); // stale completion ignored
assert.equal(working, null);
published(b,true);
assert.deepEqual(calls.at(-1), ['B','work',['apply-intent']]);
''')

    def test_busy_worker_retries_three_times_without_republishing_or_infinite_loop(self):
        self.run_case(r'''
submit(a,['switch','3'],true); published(a,true);
for (let i=0;i<5;i++) finished(a,true,false);
assert.equal(calls.filter(c=>c[1]==='work').length,3);
assert.equal(calls.filter(c=>c[1]==='publish').length,1);
assert.equal(rejected.length,1); assert.equal(working,null);
''')

    def test_incomplete_apply_retries_but_reconcile_event_and_dpms_are_coalesced(self):
        self.run_case(r'''
submit(a,['switch','3'],true); published(a,true);
for (let i=0;i<3;i++) finished(a,false,true);
assert.equal(calls.filter(c=>c[1]==='work').length,3);
submit(a,['dpms-on','HP'],false);
for (let i=0;i<20;i++) submit(b,['reconcile','output-change'],false);
submit(b,['dpms-off','HP'],false); submit(b,['dpms-on','HP'],false);
assert.equal(pending.filter(r=>r.args[0]==='reconcile').length,1);
assert.equal(pending.filter(r=>r.key==='dpms:HP').length,1);
''')

    def test_all_bars_can_disappear_and_latest_click_survives_until_new_bar(self):
        self.run_case(r'''
submit(a,['switch','2'],true); submit(b,['switch','3'],true);
unregister(a); unregister(b);
const c=bar('C'); register(c);
assert.deepEqual(calls.at(-1),['C','publish',['accept-switch','3','ACTIVE']]);
''')

    def test_queue_overflow_reports_rejection(self):
        self.run_case(r'''
submit(a,['switch','2'],true);
for (let i=0;i<65;i++) submit(a,['realign','OUT'+i,'2'],true);
assert.equal(pending.length,64); assert.equal(rejected.length,1);
''')
