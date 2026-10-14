# tam-desktop-mode

Standalone access to the workspace engine used by `fred.workspaces`.
`status`, `indicator`, `monitors` and `preferences` inspect the selected account;
`switch N`, `move N`, `move-silent N` and the mode/reconciliation operations
use its live native compositor. The command binds the paired immutable backend
and enables its named live actions without depending on the shell process environment.

Personal keypad bindings remain user configuration. The standard command endpoint
replaces consumer links directly to the plugin script; retaining such a link would
bypass this backend setup.
