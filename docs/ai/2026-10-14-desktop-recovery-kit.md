# Desktop recovery preparation — 2026-10-14

- **CLI Tool:** Codex CLI 0.162.1
- **Model:** `gpt-6.1-sol`
- **Transcript:** Retained privately by the author.
- **Prompt (excerpt):**
  > Continue remaining native service/device recovery and prepare the exact normal-account installation/rollback kit.
  > Do not activate normal-account Test, remove packages or change boot until you have proposed doing so and have received my okay to go ahead with that.

Persistent WirePlumber state has a separate finite checkpoint requiring a
quiescent writer. Recovery retains original bytes, modes and absences, archives
later writes, and supports interruption/retry. The live audio checkpoint remains
separate so device values can be collected while their providers are available.
Settings coverage includes the legacy tuning files, Bash live-source targets and
portal preferences. Existing native security/service/device settings are
inventoried for a bounded desktop transition; enrollment, group membership,
firewall changes and device resets require their own recovery transaction.

Verification: 27 focused checkpoint tests pass. The full desktop suite ran 532
checks with 531 passes and one existing skip. An installed native VM proof is
retained separately and exercises actual persistent default changes and recovery
across WirePlumber restarts. The candidate label is prepared as 0.4.3-a in Develop. Native systemd’s empty
is-enabled output for a missing tuning unit is normalized only after confirming
its not-found load state. Candidate preparation changes no account activation,
package ownership or boot selection.
