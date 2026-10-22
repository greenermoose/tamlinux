# tam-nut

The read-only welcome and hardware inspection command in Tamlinux bootstrap
media. `tam-nut welcome` explains the next steps; `tam-nut inspect` reports CPU
architecture, memory, firmware mode, model, storage, graphics and network
controllers without serials or network addresses.

The live-media assembly puts this helper at `/tam-nut` so it is available
before the desktop or Home Manager exists. It is also packaged as an ordinary
command. It does not install an operating system or enable remote access.
Boot media are assembled separately by `tamlinux-packages`; installed desktop
software still goes through a recorded package assembly and `tam-deploy`.
