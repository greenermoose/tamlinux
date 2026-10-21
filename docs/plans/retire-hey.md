# Retire the inherited HEY integration

**Status:** Accepted by Fred, 2026-10-21. The installed 0.4.6 application
checks are complete. Ready for implementation in a later candidate.

The inherited desktop assumes HEY for email and calendar. The developer has
explicitly retired that choice. Remove the HEY-specific integration without
choosing another provider or email/calendar application. Replacement research
belongs to a later version; 1.0 is tentative.

## Result

- Stop delivering `tam-webapp-handler-hey` and its package dependency entry.
- Remove the default HEY Calendar, Email and New email keybindings.
  These shortcuts remain unassigned until a replacement is chosen. Apply the
  same disposition to consumer copies through controlled activation.
- Retire the known inherited/owned `HEY.desktop` launcher through the finite
  migration journal, preserving its original bytes and later edits for
  recovery. Fresh installations create no HEY launcher or handler.
- Remove only `HEY.desktop` tokens from MIME defaults/associations in the
  selected user's `mimeapps.list` files. Preserve other applications, ordering,
  sections and unrelated content. Leave email unassigned when no other
  explicit choice exists; do not select a replacement automatically.
- Keep generic webapp installation, email links and user-selected email
  applications available. Retiring a built-in integration does not ban a
  user from adding a webapp. Retain legal attribution and dated evidence.

## Implementation

Extend the existing finite migration with a named HEY-launcher retirement
and MIME-entry cleanup. The launcher retirement accepts only the known
`HEY.desktop` with an exact inherited/owned handler command; unexpected
content, links or owner mismatches require review rather than deletion.
The journal records an absent post-state for the retired launcher, validates
that state when applying/resuming, and preserves post-retirement user files
before rollback. MIME conversion changes only the retired desktop-ID tokens.
Both removal and MIME cleanup must be retryable and reversible.

Remove the HEY forwarding mapping from generic launcher conversion so it
cannot generate a reference to an undelivered handler. Move the shared Zoom
handler tests into Zoom's own command directory and retain their coverage.
Update keybinding fixtures, package probes and the compatibility contract to
record the explicit retirement. Use a generic icon name in installer examples.

There is no new service or background task. An upgrade's explicit migration
refreshes the desktop database using the installed tools after mutation.
Before that migration, preserve current launcher/MIME files and user bindings.
Do not delete mail, browser profiles, account credentials or user data.

## Verification and delivery

Verify fresh absence, inherited and already-owned launcher retirement, custom
launcher refusal, MIME preservation, interruption/retry and rollback with later
user writes. Verify that Zoom and generic webapps still work and package
outputs contain no HEY-specific executable or default binding.

The installed 0.4.6 assembly and its recovery journals keep their identities.
Development changes do not mutate that installation. Package the retirement
in the next candidate the developer chooses; a prepared number is never
reused. Its Test needs an exact instruction, current mutable-state checkpoint,
installed launcher/MIME/keybinding checks and a preserving return route.
No email replacement research, package removal, boot or login change forms
part of this retirement plan.
