# Daily compositor protocol shadow monitoring

- **CLI Tool**: Codex CLI `0.162.0`
- **Model**: `gpt-6.1-sol`
- **Transcript**: Retained privately by the author.
- **Authorship**: Codex implementation, tests, deployment configuration and evidence
  records directed by Fred. No subagents or delegate work in this task.
- **Prompts**:
  > We have opencode working on tam and agy working on tam-file-select. Take a look at the status of the tamlinux project and decide what you can work on next. Choose the most high-impact task you can do now.

  > Make it so

## Change and decisions

The next approved workstation step is 0.4.1, milestone B of the compositor
protocol plan. The existing isolated comparison becomes a daily, read-only
shadow path with 750 ms settling, bounded status transitions and minute
health records. Hyprland IPC retains every published facade field and action,
including display power. The default proof path remains available.

The collector archives production records transactionally in private XDG
SQLite state. Journal cursor deduplication makes overlap/retry harmless.
Source identity hashes the protocol source, model, logger, Hyprland adapter
and evidence tool. Unrelated shell revisions preserve the identity; trial
code changes and returns to an earlier identity restart the evidence span.

The summary keeps differences, unavailable state, sequence loss, logging gaps,
stale heartbeats and incomplete time/event coverage visible. Physical event
notes require equal records on both sides and cannot inflate coverage through
overlapping entries. Readiness is evidence for Fred, not milestone acceptance.

## Verification

- All 409 desktop tests passed, including real offscreen QML timing fixtures
  and positive/negative evidence-accounting cases.
- The isolated read-only Hyprland shadow proof passed on three outputs and
  four workspaces; it created no surfaces and dispatched no actions.
- All 494 workstation configuration tests passed with normal user access.
  The initial sandbox run could not bind its socket fixtures and could not
  perform several installed-command checks; that failed run is retained.
- The first daily activation exposed journald's byte-array encoding for
  colored Quickshell messages: the logger agreed, but collection skipped
  records. A separate correction decodes bounded UTF-8 byte arrays and tests
  valid and invalid encodings. The 409-test rerun passed. The corrected
  collector changes the trial identity and starts a fresh observation period.
- **Commits**: initial development `fa540bb`; collector correction and deployed
  candidate `a0d7737`. Deployment/provenance documentation follows separately.
- The corrected candidate is deployed in daily shadow Test. The first equal
  production comparison is **2026-10-09 12:41:35 UTC**. Minute heartbeats and
  the scheduled collector are active; initial records have no differences,
  missing sequences or unexplained gaps. All six event counts remain zero.
- The live passive/panel checker passed 161 checks on three outputs. All eight
  plugin store paths and file digests, layout and preferences match the saved
  baseline. Three checker warnings were present before deployment; a fourth,
  startup CPU warning, was followed by a settled five-second sample of 0.60%.
- The accepted 0.4.0 generation remains the rollback target and the normal
  shell pin is unchanged. A committed configuration snapshot excluded unrelated
  working changes from the activation. No public push, release or milestone
  acceptance occurred. The accepted version remains 0.4.0; Fred's acceptance
  of this Test candidate and the event-covered 14-day period are pending.
