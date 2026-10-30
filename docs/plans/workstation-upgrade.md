# Easy workstation upgrades

**Status:** Approved by Fred on 2026-10-30; release selection is in development.
Installation, recovery, packaging and physical trials remain pending.
**Target:** Give an existing 0.5.12 workstation a straightforward way to
install a later Tamlinux release without reinstalling the machine.

## Problem

`tam-deploy` can install a recorded package assembly into the local registered
host's Home Manager profile, but its normal upgrade path expects a workspace
of component Git checkouts, an identifiable consumer configuration and an
active graphical session. `tam upgrade` checks the separately versioned tam
command and corpus; it does not upgrade the workstation. A user should not
need to understand source branches or develop on the machine to update it.

## Proposed first scope

- Provide `tam-workstation-upgrade --check` to report the installed assembly and
  the latest eligible released assembly, including the version and exact
  revision, without changing the machine. `tam-workstation-upgrade` presents the
  same selection and asks before installing it. An explicit version selects
  a particular released assembly. A non-interactive mode requires an exact
  selection and explicit confirmation.
- Select only a recorded release from the official package source. Resolve
  the selection to exact immutable revisions before building; validate its
  delivery record and component identities. Installing an already released
  assembly never promotes branches, tags, or creates a release. A Test or Run
  stage move remains a separate, explicitly authorized operation.
- Use the local registered user and host profile; refuse a missing or foreign
  profile. Preserve that workstation's settings, do not copy another host's
  configuration, and report consumer changes or conflicts before writing.
  Avoid requiring clones of each product component. The consumer
  configuration and its prerequisites must be available locally and be
  identified before activation; explain a missing prerequisite and recovery.
- Build and install the exact recorded user-package assembly with Home Manager,
  retaining the previous generation and recording its assembly and settings
  recovery. Verify installed endpoints against the selected assembly. Starting
  with 0.5.12, every upgrade operation, including discovery, confirmation,
  activation, verification and recovery, must work from a text VT with no
  graphical session or graphical shell. On failure, preserve evidence and restore or clearly identify the
  previous usable state. Preserve later writes during settings restoration.
- If a release needs native, boot or login changes, show that requirement and
  stop before claiming a complete upgrade; perform such work only through its
  separately reviewed, approved procedure. An upgrade of user packages alone
  cannot promise that these layers changed.

The initial upgrade to 0.5.12 from an older installation also needs a
host-specific assessment of its actual installed version, configuration and
recovery state. This proposal does not assume that either laptop has the same
starting state as another machine.

## Evidence before including in a candidate

Exercise release discovery, explicit version selection and no-op checks;
missing prerequisites, offline and invalid records; foreign-host refusal;
preservation of customized files; graphical and console paths; interrupted
activation, endpoint verification and recovery. Tests must establish that no
stage branch moves and no native or boot mutation happens. Build the command
in the recorded package assembly. Then try upgrades and recovery on actual
workstations, including the two older installations, before claiming those
machines work. Routine update reliability over time remains later work.

## Decisions

A released-version-only default with an explicit version choice is the desired
interface.

A future upgrade requiring native changes should stop with a clear
procedure.

The command is named `tam-workstation-upgrade`, accepted by Fred on
2026-10-30. The deployment machinery may be reused underneath it.

Fred, 2026-10-30: “Starting with Tamlinux 0.5.12, all upgrade work needs to be
able to be done from a VT. A graphical shell must not be required to do a
Tamlinux upgrade from now on.”

Fred clarified: “The goal is to be able to reboot a machine, get to a terminal,
and do the upgrade from there without having to start the Tamlinux desktop
graphical shell.”
