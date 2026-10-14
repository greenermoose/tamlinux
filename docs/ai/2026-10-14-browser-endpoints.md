# 2026-10-14 — Owned Chromium extensions and native messaging

- **CLI Tool**: Codex CLI `0.162.1`, dynamically checked.
- **Model**: `gpt-6.1-sol`, verified from runtime metadata.
- **Transcript**: Retained privately by the author.
- **Prompt**:
  > Resume from the Tamlinux 0.4.3 handoff.

Moved Copy URL, Download Video and WhatsApp Slim into the product with their
MIT attribution, extension keys and shortcuts retained. Native registrations
and callers use org.tamlinux names. The new frame reader bounds input size and
read duration, validates URL types and origins, and isolates protocol stdout
from tool output. Copy uses stdin; download jobs use a detached argument array
and ignore unrelated yt-dlp configuration. Added Chromium flags and native-host
registrations to the finite settings checkpoint.

Verification: seven native-host regressions pass; 513 desktop checks pass with
one existing skip; all 16 recovery checks pass outside the filesystem/socket
sandbox. Actual Chromium service workers in an isolated Arch VM invoke the
owned hosts, copy the expected URL to Wayland, and download a loopback video
whose file hash matches the source. The delivery session contract builds.

Protocol behavior follows the [Chrome native messaging documentation](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging).
The complete Desktop Test tuple, physical acceptance and native recovery owners
remain in the existing independence gate.
