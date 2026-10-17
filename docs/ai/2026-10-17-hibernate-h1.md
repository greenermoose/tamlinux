# 0.4.4f hibernate-time zram drain

- **Date**: 2026-10-17
- **CLI Tool**: Codex CLI (`codex`) `0.163.0`, checked live
- **Models**: `gpt-6-luna` for the initial read-only investigation;
  `gpt-6.1-sol` for the reviewed plan, implementation and verification
- **Transcript**: Retained privately by the author.
- **Authorship**: Fred edited and approved the work plan; Codex implemented
  the selected integration and restoration changes under his direction.
- **Prompts**:
  > Start Fault G's H1 trial.

  > We need to start the Fault G's H1 trial. Prepare a work plan to make this happen and then let's review.

  > I have reviewed, edited, and approved the plan. Close the review window and start work on Tamlinux 0.4.4f now.

The [approved plan](../plans/0.4.4-hibernate-h1.md) selects a new Test candidate
and keeps the minimum image target for H1. Move the deferred hook into native
vendor defaults as `tam-hibernate-swap`, retaining its journal and runtime-state
namespace. Native packaging records its executable mode and digest.

Fix restoration failure handling: retain the saved device/priority state if
`swapon` fails, then retry on a later post or suspend-pre hook invocation.
Already active devices are skipped on retry. Report the drained zram amount
and observed disk-swap usage without asserting that all drained pages went
to disk. The capacity guard budgets ordinary swapped pages; deployment must
also verify image headroom on the actual resume device.

Verification: 16 actual-hook regressions pass, including a real 60-second
timeout, failed restoration and retry, S3/S4 dispatch, fallback restoration,
capacity skips and preserved priorities. Eight native-default checks pass,
including recorded hashes/modes and the approved executable name.

No installed hook execution, sleep trial, Test/Run promotion or activation
has occurred in this development change. Physical sleep/resume and the H1
success count begin only after the exact candidate's Test approval.
