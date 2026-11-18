# Plain suspend where hibernation is unavailable

- **Date**: 2026-11-01
- **CLI Tool**: Claude Code (`claude`) `2.1.316`
- **Model**: `claude-opus-5-5`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > Read your inbox for messages from both [fleet laptops]. Ask me if you need help.

- **Problem**: A fleet laptop agent reported that `suspend-unless-stay-awake` always ran `systemctl suspend-then-hibernate`. On hosts whose only swap is zram, logind refuses that request ("Not enough suitable swap space for hibernation"), so an idle machine never slept.
- **Implementation**: The command asks logind `CanSuspendThenHibernate` and hibernates only on `yes`; any other answer, or a failed query, uses `systemctl suspend`. The Stay Awake check and the hibernation preflight capture are unchanged; the capture now runs only before a hibernation-capable sleep.
- **Delivery boundary**: Develop only. No assembly or deployment includes this change yet.
- **Verification**: `make check` runs a new stubbed test covering `yes`, `na`, `no`, a failed query and Stay Awake (no sleep). logind answered `yes` on a desktop with disk swap and `na` on two zram-only laptops.
