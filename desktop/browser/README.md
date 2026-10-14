# Chromium extensions and native hosts

Copy URL, Download Video and WhatsApp Slim preserve their extension keys,
IDs and shortcuts. Their original MIT license is retained in `LICENSE`.
The native messaging protocol names are `org.tamlinux.copy_url` and
`org.tamlinux.ytdlp`; no prior registration is required.

Delivery installs the three extensions and two exact-origin registrations
from the same product revision. Native messages have a five-second input
deadline, a 64 KiB frame limit and a 16 KiB URL limit. Copy URL accepts plain
text without control characters. Downloads accept HTTP(S) URLs without embedded
credentials and run the selected yt-dlp with its configuration files disabled.
Downloads use `TAMLINUX_YTDLP_DIR` or `~/Videos`, show progress, and offer to
open the saved video through the selected mpv.

The session module exposes an optional Chromium flags file. Existing flags
remain consumer configuration; an existing file must be preserved and
reconciled before enabling managed flags. Native manifests point directly to
the paired commands output. The commands must receive Chromium's matching
extension origin; invoking an endpoint without an origin is refused.
