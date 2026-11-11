# Shared workspace ingress, retry budgets and package gates

- **CLI Tool:** Codex CLI `0.167.1`
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Prompt:**
  > For [redacted: private plan reference], finish shared metadata, remaining queue/retry gates, full Hyprland build and package integration before an exact-candidate Test and Dell trial.

Every bar imports one shared publication/work queue. Serialized fast
publication coalesces unaccepted clicks and runs independently of a slow
compositor worker. A publication failure retries three times, then reports
failure; accepted clicks become persistent intent. Output loss can destroy a
bar without losing the latest queued request. Slow application always reads
current intent; an old completion cannot republish an earlier desktop.

Completion tracks canonical outputs, including absent panels. Each output
gets at most three attempts and a three-second budget starting on its first
present mismatch. Missing panels spend no attempts. Progress persists before
IPC; duplicate repair events and worker death do not replenish a budget.
The helper's compositor calls also share a three-second invocation budget.
Explicit `retry-intent` opens a new generation. An IPC snapshot is never
claimed as proof of physical continuity.

The previous development slice's shared changelog/provenance metadata is
reconciled. Existing native DPMS/idle/connector protections remain required.

Verification at source selection: 57 workspace timeline, intent, focus,
queue and retry cases; 69 plugin cases; 25 compositor adapter cases; 35
host/metadata cases; the workspace widget render. Native package and Nix
integration results are recorded by the delivery repository.

The broad integration suite also exposed the journal Quick note shortcut
missing from the binding catalog; its matching command/rationale row is added.

No installed session change or Test/Run/Release promotion is included.
