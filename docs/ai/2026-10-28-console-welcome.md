# Console welcome development

- **CLI Tool**: Codex CLI `0.165.0`
- **Model**: `gpt-6.1-terra`
- **Transcript**: Retained privately by the author.
- **Prompts**:
  > When I switch to tty2, I see this:
  >
  > Arch Linux 7.2.11-arch1-1.1 (tty2)
  >
  > [redacted: personal detail] login:
  >
  > Can we add a friendly banner for Tamlinux? What should a friendly banner say? Do some research into what Linux distros do and propose something fun. I want users to be delighted and know that they are using Tamlinux and which cultivar on which rootstock.
  >
  > Let's include the 7.2.11 etc. number for the rootstock. The rootstock should be fully described.
  >
  > I've edited the console-welcome.md file with an updated design for the Tamlinux logo. And created three sizes of the logo in [redacted: private repository]. Please update the decision and change the banner. Can I test it on tty2 now?

Fred approved the plan and drew the revised tree. Codex wrote the banner
generator and tests, including escaping the tree for agetty. The three focused
tests pass, including a pseudo-terminal render by the host's actual agetty.
Machine-wide selection, updates, rollback and live login remain unfinished.

Fred then said: "Package the banner for Tamlinux 0.5.6. I want it to appear when you first boot up and when you switch to another tty from a graphical shell."
The banner includes the host's build ID as well as its
OS name and running kernel; machine-level delivery is handled separately.
