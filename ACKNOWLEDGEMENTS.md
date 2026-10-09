# Acknowledgements — tamlinux

Researched 2026-10-09. Thank you to the people whose software, designs, maintenance, testing and public reports make this work possible.

Names are ordered alphabetically by the displayed public name (case and accents ignored for sorting). A self-published profile name is used when available; otherwise the public handle or name in an upstream credit is retained. No private identities, locations, phone numbers or commit-email harvesting are included. Affiliations below are self-reported public profile fields or explicitly attributed project roles; they are not independently verified employment records. Contact links and emails are only those publicly offered by the person or their project.

Tamlinux additions are distributed under GPL-3.0-or-later; see [LICENSE](LICENSE). Upstream works retain their own terms. Copyright notices are attributed to works and their stated holders, not inferred from contributor counts. The Free Software Foundation copyright on a GPL/LGPL license document is not treated as ownership of the software. These thanks supplement, and do not replace, required license and source notices.

[UPSTREAM.md](UPSTREAM.md) records this repository’s code ancestry and design references. A runtime dependency, design inspiration, bug report and copied component are different contributions; the entries say which connection is established.

Each named entry identifies an authored component, a documented design influence, a specific change or public report, or responsibility for a foundation used by this repository. Contributor-roster membership alone is not enough for a named entry. Wider communities are credited collectively below.

**Version scope:** Hyprland and Aquamarine credits describe the temporary Tamlinux 0.x platform and its compatibility patches. Tamlinux’s [public roadmap](https://github.com/greenermoose/tamlinux/blob/main/README.md) removes Hyprland at 1.0 in favor of Sway. Remove these dependency-only entries from future acknowledgements when the stack is no longer used. Historical forks and any retained derived code keep their applicable source notices.

## People

| Public name and brief background / contribution | Public affiliation and contact |
| --- | --- |
| **Aaron Griffin** — Former Arch project leader who succeeded Judd Vinet; acknowledged for stewardship of the current package base. [Work, license and copyright](#arch). [Evidence](https://archlinux.org/news/arch-leadership/) | Arch Linux [Public profile / project contact](https://archlinux.org/news/arch-leadership/) |
| **Aleksandra Samuļenkova** — IBM Plex contributor: Cyrillic and Greek design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Alonso David De León Rodarte (`DataDave-Dev`)** — Reopened Wi-Fi password entry after an incorrect saved password. This improves network recovery in the current desktop shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/f490b69a208d4d0d6bb9520ec90a5aa6490b9fe6) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/DataDave-Dev); [Website](https://portfolio-dev.deleonalonso77.workers.dev/) |
| **Andrew Gaspar (`AndrewGaspar`)** — Author of the upstream wrong-pointer munmap fix backported for GTK4 and later retired from the local patch set. [Work, license and copyright](#gtk). [Evidence](https://github.com/GNOME/gtk/commit/a8a5692ce3c334672ac325cf8f1257a138843bf6) | @facebook [Public profile / project contact](https://github.com/AndrewGaspar) |
| **Andrew Shuttleworth (`ashuttl`)** — Creator of Linecast. Its daylight-shaded curves and simple presentation influenced the tide panel. [Work, license and copyright](#linecast). [Evidence](https://github.com/greenermoose/tides-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/ashuttl); [Public email](mailto:ashuttleworth@gmail.com) |
| **anticapitalista** — Public antiX developer/release author; antiX’s support for older hardware is an explicit Tamlinux inspiration and fallback-base reference. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX Linux [Public profile / project contact](https://antixlinux.com/blog/) |
| **Artem Popov (`artfwo`)** — Corrected keyboard-language labels that could remain stuck on English. This improves layout feedback in the current desktop shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/9d61915b2e2e1d75b58ef9428006d7a13bd65659) | @mozilla [Public profile / project contact](https://github.com/artfwo) |
| **Balázs Orbán (`balazsorban44`)** — Creator of the keybinding coach; its teaching approach influenced the explorer’s learning-oriented design. [Work, license and copyright](#keybinding-coach). Creator of the keyboard minimap; its global-input design was examined when choosing the explorer’s panel-scoped capture. This is prior-art credit, with no code reuse documented. [Work, license and copyright](#keyboard-minimap). [Evidence 1](https://github.com/balazsorban44/omarchy-keyboard-minimap) [Evidence 2](https://github.com/balazsorban44/omarchy-keybinding-coach) | @Unite-AS [Public profile / project contact](https://github.com/balazsorban44); [Website](https://balazsorban.com) |
| **Barbara Bigosińska** — IBM Plex contributor: Font production and Latin design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **BitJam** — Publicly credited antiX contributor: live/build-system development. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Brian Armstrong (`barmstrong`)** — Improved service lifetime handling during plugin hot reload. This supports the Omarchy host used to load and develop fred.* widgets. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/af6f64fa3a7afc9d0bf55bea676f12308a578103) | @coinbase [Public profile / project contact](https://github.com/barmstrong); [Website](https://www.brianarmstrong.org/) |
| **Carlos Armando (`InfeCtlll3`)** — Made long tray menus scrollable. This improves access to application actions in the inherited shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/be71149500bc3f49bdf9282561cafd724cbbf0eb) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/InfeCtlll3); [Public email](mailto:contato.carmando@gmail.com) |
| **Charles Rezac** — Original Lynx developer. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **Chris Mason (`chrismason`)** — Btrfs developer listed as a kernel reviewer. Reviewing changes to the copy-on-write filesystem supports the reliability needed by Tamlinux’s planned snapshot recovery. [Work, license and copyright](#btrfs). [Evidence](https://github.com/torvalds/linux/blob/master/MAINTAINERS) | @Microsoft [Public profile / project contact](https://github.com/chrismason) |
| **Craig Lavender** — Historical Lynx support contributor. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **daiki tagami (`dai199`)** — Creator of omarchy-visual-keybindings. Keyboard capture and interactive exploration prior art. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#visual-keys). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/dai199); [Website](http://tagamidaiki.com) |
| **Daniel Stenberg (`bagder`)** — Creator and maintainer of curl. Its HTTP client is invoked by the weather, tide and agent-usage helpers. [Work, license and copyright](#curl). [Evidence](https://curl.se/docs/copyright.html) | @wolfSSL [Public profile / project contact](https://github.com/bagder); [Website](https://daniel.haxx.se/); [Public email](mailto:daniel@haxx.se) |
| **daniellopez12 (`daniellopez12`)** — Creator of Just Right Weather. Its 48-hour temperature curve, chronological sunrise/sunset placement and combined API requests are documented inspirations for fred.weather. [Work, license and copyright](#weather-art). [Evidence](https://github.com/greenermoose/weather-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/daniellopez12) |
| **dave** — Publicly credited antiX contributor: repository maintenance. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Dave Gandy (`davegandy`)** — Creator of Font Awesome. Its icon-font designs supply recognizable symbols, including the weather sun. [Work, license and copyright](#font-awesome). [Evidence](https://fontawesome.com/v4/license/) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/davegandy); [Public email](mailto:dave@davegandy.com) |
| **David Heinemeier Hansson (`dhh`)** — Creator of Omarchy. Its shell, UI conventions and plugin host form the current base and the documented ancestry of several fred.* components. [Work, license and copyright](#omarchy). Original Omawrite author; the editor source is the base of the Tamlinux patch fork. [Work, license and copyright](#omawrite). [Evidence 1](https://github.com/omacom/omarchy) [Evidence 2](https://github.com/omacom/omawrite) [Evidence 3](https://github.com/omacom/omarchy/commit/b83505d7380bbe0525f56f5dc556c103848d34d5) | 37signals [Public profile / project contact](https://github.com/dhh); [Website](https://dhh.dk); [Public email](mailto:dhh@hey.com) |
| **David Sterba (`kdave`)** — David Sterba maintains Btrfs in the Linux kernel and btrfs-progs. Filesystem snapshots and recovery tooling support the planned checkpoint-and-rollback design. [Work, license and copyright](#btrfs). [Evidence](https://github.com/torvalds/linux/blob/master/MAINTAINERS) | SUSE [Public profile / project contact](https://github.com/kdave); [Public email](mailto:dave@jikos.cz) |
| **Diana Ovezea** — IBM Plex contributor: Font production and Latin design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Diogo Ferreira (`defer`)** — Separated launched applications into their own scopes and improved keyboard-language labels. This contributes to process isolation and input feedback in the current desktop. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/66f3155f0c170120fec3e56895fdfdcefb4ae6c6) [Evidence 2](https://github.com/omacom/omarchy/commit/40f92eabdf8598cebd02451afb4424fe15ee6606) | Cyanogen Inc [Public profile / project contact](https://github.com/defer); [Website](http://www.underdev.org); [Public email](mailto:diogo@underdev.org) |
| **DK (`dkIT25`)** — Public reporter of issue #383, with a matching null-connector diagnosis and proposed guard independently corroborating the local crash fix. This does not assign authorship of Fred’s separately recorded patch. [Work, license and copyright](#aquamarine). [Evidence](https://github.com/hyprwm/aquamarine/issues/383) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/dkIT25) |
| **Dmitrij Batrak** — Named in JetBrains Mono’s public thanks. Their support contributed to the font project used as the installed bar typeface; a more specific task is not established by that credit. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | JetBrains Mono project [Public profile / project contact](https://www.jetbrains.com/lp/mono/) |
| **Doug Lea** — Contributor to the GNU C Library’s memory allocator. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Drew DeVault (`ddevault`)** — Original Sway author. Sway is the planned compositor direction; this credits design/planning influence rather than a completed migration. [Work, license and copyright](#sway). Helped establish wlroots, the reusable compositor library behind Sway. This work supports Tamlinux’s chosen replacement desktop. [Work, license and copyright](#wlroots). [Evidence 1](https://github.com/swaywm/sway) [Evidence 2](https://drewdevault.com/blog/Im-handing-wlroots-and-sway-to-Simon/) | SourceHut [Public profile / project contact](https://github.com/ddevault); [Website](https://git.sr.ht/~sircmpwn) |
| **Duncan Overbruck** — Named XBPS copyright holder and contributor to the package system planned for the Void base. [Work, license and copyright](#xbps). [Evidence](https://github.com/void-linux/xbps/blob/master/COPYING) | XBPS [Public profile / project contact](https://github.com/void-linux/xbps/blob/master/COPYING) |
| **Edgar Walthert** — IBM Plex contributor: Font engineering and Latin design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Eduardo Escobar (`e2escobar`)** — Improved lock-screen behavior during fingerprint authentication. This contributes to the current Omarchy desktop carried by Tamlinux. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/f73740ff07c9d6592be171020da329776849b7d8) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/e2escobar); [Website](https://eduardoescobar.me) |
| **Edwin Catmull** — Co-author of the Catmull–Rom interpolation method, the named mathematical technique used for the tide curve. [Work, license and copyright](#catmull-rom). [Evidence](https://doi.org/10.1016/B978-0-12-079050-0.50020-5) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://doi.org/10.1016/B978-0-12-079050-0.50020-5) |
| **Eelco Dolstra (`edolstra`)** — Creator of Nix. Declarative packaging and atomic rollbacks are named technical inspirations in Tamlinux’s public source record. [Work, license and copyright](#nix). [Evidence](https://nixos.org/blog/stories/2022/the-rise-of-special-project-infra/) | Determinate Systems @DeterminateSystems [Public profile / project contact](https://github.com/edolstra); [Website](http://nixos.org/~eelco/) |
| **Enno Boland** — Named XBPS copyright holder and contributor to the package system planned for the Void base. [Work, license and copyright](#xbps). [Evidence](https://github.com/void-linux/xbps/blob/master/COPYING) | XBPS [Public profile / project contact](https://github.com/void-linux/xbps/blob/master/COPYING) |
| **Eugene Auduchinok** — Named in JetBrains Mono’s public thanks. Their support contributed to the font project used as the installed bar typeface; a more specific task is not established by that credit. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | JetBrains Mono project [Public profile / project contact](https://www.jetbrains.com/lp/mono/) |
| **fehlix** — Publicly credited antiX contributor: live-system improvements. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Felix Sanchez (`felixzsh`)** — Creator of omarchy-key-visualizer. Live keyboard presentation prior art. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#key-visualizer). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | Software Development Engineer [Public profile / project contact](https://github.com/felixzsh); [Public email](mailto:felix.sanchez.dev@gmail.com) |
| **Francisco Cabral (`franciscoaccabral`)** — Stopped Wi-Fi scanning from continuing after the network panel closes. This contributes to resource handling in the current desktop’s shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/5f74a996c75304e1c13dc3cdfd213dc7ce17b0d2) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/franciscoaccabral) |
| **Fred Horch (`greenermoose`)** — Tamlinux creator and maintainer. Directed this repository’s design, implementation, testing and upstream integration, including the separately documented AI-assisted work. [Evidence](https://github.com/greenermoose/tamlinux) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/greenermoose) |
| **fze (`fze-fze`)** — Creator of omarchy-shortcut-sheet. Reverse lookup from command to keybinding prior art. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#shortcut-sheet). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/fze-fze); [Website](https://fze-fze.me); [Public email](mailto:fanzeen451@gmail.com) |
| **Garrett Blythe** — DosLynx creator and later Lynx contributor. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **GebaRoanoke (`GebaRoanoke`)** — Added reporting of Claude’s per-model weekly usage limits to the upstream usage widget. That widget is the documented starting point for fred.agents. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/2b38f7550687f80ed768a026bdebd1070a797080) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/GebaRoanoke) |
| **Gerrit Pape** — Author of runit, the lightweight service supervisor referenced in the planned Void/antiX base. [Work, license and copyright](#runit). [Evidence](https://smarden.org/runit/) | runit [Public profile / project contact](https://smarden.org/runit/); [Public email](mailto:pape@smarden.org) |
| **Grigoriy Sidorov (`glafeara`)** — Fixed application launching for desktop-entry identifiers ending in .desktop. This improves launcher reliability in the current desktop. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/fa6b5fce0d19fd38be60e940d602ba4116bdec6a) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/glafeara); [Public email](mailto:sidorov.grigorii@gmail.com) |
| **Guido van Rossum (`gvanrossum`)** — Creator of Python, the interpreter and standard library used by the suite’s command and data helpers. [Work, license and copyright](#python). [Evidence](https://www.python.org/doc/essays/foreword/) | Microsoft [Public profile / project contact](https://github.com/gvanrossum); [Website](https://python.org/~guido/) |
| **HANCORE (`HANCORE-linux`)** — Marketplace maintainer and named public reviewer. Feedback on subprocess supervision, bounded calendar input and safe cache writes shaped the clock’s hardening and shared suite patterns. [Work, license and copyright](#marketplace). [Evidence](https://github.com/omacom/omarchy-plugin-marketplace/issues/6509#issuecomment-5647408125) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/HANCORE-linux) |
| **Husam (`husamemadH`)** — Implemented cross-monitor dismissal in Omarchy’s stock panel window. That window is the source of the keyboard/monitor adaptations; Tamlinux deliberately omits its dismissal windows on other outputs. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/3cb3861fbc2f6655f8c165ef4c98cec281ba7fb5) [Evidence 2](https://github.com/omacom/omarchy/commit/43c15a401566ff7a069f48faab2227fcbb903d9f) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/husamemadH); [Public email](mailto:husamemad60@gmail.com) |
| **Igor Chubin (`chubin`)** — Creator of wttr.in, whose JSON forecasts are consumed by the weather panel. [Work, license and copyright](#wttr). [Evidence](https://github.com/chubin/wttr.in) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/chubin); [Website](https://twitter.com/igor_chubin); [Public email](mailto:igor@chub.in) |
| **Isaac Freund (`ifreund`)** — River developer whose compositor work is a named desktop inspiration in Tamlinux’s source record. [Work, license and copyright](#river). [Evidence](https://isaacfreund.com/) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/ifreund); [Website](https://isaacfreund.com); [Public email](mailto:mail@isaacfreund.com) |
| **Jakob P. Liljenberg (`aristocratos`)** — Creator of btop, the task manager exposed through the system-information panel. [Work, license and copyright](#btop). [Evidence](https://github.com/aristocratos/btop) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/aristocratos); [Website](https://qvantnet.com); [Public email](mailto:admin@qvantnet.com) |
| **Jasper Terra** — IBM Plex contributor: Font engineering and Latin design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Juan Romero Pardines** — Void Linux founder and original XBPS author; the native package system informs Tamlinux’s planned Void base. [Work, license and copyright](#xbps). [Evidence](https://github.com/void-linux/xbps/blob/master/COPYING) | Void Linux / XBPS [Public profile / project contact](https://github.com/void-linux/xbps/blob/master/COPYING) |
| **Judd Vinet** — Founder of Arch Linux; its package base and rolling-update approach support the current Tamlinux workstation and its stated inspiration. [Work, license and copyright](#arch). [Evidence](https://archlinux.org/news/arch-leadership/) | Arch Linux [Public profile / project contact](https://archlinux.org/news/arch-leadership/) |
| **KazeTachinuu (`KazeTachinuu`)** — Made the keyboard-layout widget follow the physical keyboard being used. This contributes to input feedback in the current desktop shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/66e3f479a61ad4dcb7da02202ad974238e20173a) | TrueFalse [Public profile / project contact](https://github.com/KazeTachinuu); [Website](https://hugosibony.com) |
| **Kenny Levinsen (`kennylevinsen`)** — Author of seatd, which gives Wayland compositors access to seats and devices without tying them to a particular init system. Tamlinux’s Void/Sway plan names this service. [Work, license and copyright](#seatd). [Evidence](https://sr.ht/~kennylevinsen/seatd/) | Levinsen Software [Public profile / project contact](https://github.com/kennylevinsen); [Website](https://kl.wtf/); [Public email](mailto:kl@kl.wtf) |
| **Kevin McConnell (`kevinmcconnell`)** — Corrected bar-surface transparency and panel-array handling, and added an audio-mute interaction. These changes support the shell hosting fred.* widgets. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/5817feb93f4986819fdbff6c2a62ce67b36b1b44) [Evidence 2](https://github.com/omacom/omarchy/commit/d5492db404cacb03536563575b67f5c26b029c83) [Evidence 3](https://github.com/omacom/omarchy/commit/be595c72ad3ff4a85ae639255962db6db3ac9613) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/kevinmcconnell) |
| **Konstantin Bulenkov (`bulenkov`)** — JetBrains Mono project lead; helped make the base typeface used by the installed Nerd Font available. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | @JetBrains [Public profile / project contact](https://github.com/bulenkov); [Website](http://bulenkov.com) |
| **Kristian Høgsberg** — Wayland’s original author and a named copyright holder. Its client/compositor protocol enables both the current shell and the planned Sway desktop. [Work, license and copyright](#wayland). [Evidence](https://github.com/wayland-mirror/wayland/blob/main/COPYING) | Wayland project [Public profile / project contact](https://wayland.freedesktop.org/) |
| **Kyunghyun Park (`khpark43`)** — Removed an obsolete weather-status poller from Omarchy. This is maintenance of the weather component’s upstream lineage, rather than authorship of fred.weather’s forecast design. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/65541c7b4f63d94eb3cce9dce859584617f948a0) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/khpark43) |
| **Lars Knoll** — Longtime Qt engineer and Qt chief maintainer at the time of the project’s 2020 technical conference. His engineering leadership helped develop the UI framework used by Quickshell and Omawrite. [Work, license and copyright](#qt). [Evidence](https://www.qt.io/development/resources/videos/foundation-for-the-future-are-we-excited-qt-virtual-tech-con-2020) | Qt project; historical role stated in the 2020 source [Public profile / project contact](https://www.qt.io/development/resources/videos/foundation-for-the-future-are-we-excited-qt-virtual-tech-con-2020) |
| **Leah Neukirchen (`leahneukirchen`)** — Void Linux contributor and author of a public history of Void, relevant to the chosen base and packaging direction. [Work, license and copyright](#xbps). [Evidence](https://leahneukirchen.org/talks/void-2020/neukirchen2020void.pdf) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/leahneukirchen); [Website](http://leahneukirchen.org/); [Public email](mailto:leah@vuxu.org) |
| **lemachinarbo (`lemachinarbo`)** — Omawrite developer whose source changes improve editor/theme colors, prevent link-paste layout freezes and bound portal D-Bus calls. These changes are part of the editor inherited by the Tamlinux fork. [Work, license and copyright](#omawrite). [Evidence](https://github.com/omacom/omawrite/commit/c885e935c9cd142418364528cc5d48bd52c06d19) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/lemachinarbo) |
| **Linus Torvalds (`torvalds`)** — Creator of Linux. Kernel drivers, /proc and /sys underpin the running workstation and hardware telemetry. [Work, license and copyright](#linux). [Evidence](https://www.kernel.org/) | Linux Foundation [Public profile / project contact](https://github.com/torvalds) |
| **Lorenzo Golluscio (`ssupt`)** — Implemented brightness control for external monitors and improved pointer navigation in Omarchy’s launcher. Display controls are part of the monitor panel’s upstream ancestry. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/c0d40372376e1ff154dfae0ea814a30b7639dabd) [Evidence 2](https://github.com/omacom/omarchy/commit/3481b5614bd47fac9395a2d1ac8adea2674d36cb) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/ssupt) |
| **Lou Montulli** — Original Lynx developer. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **marcelocripe** — Publicly credited antiX contributor: localisation support. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **markbus-ai (`markbus-ai`)** — Improved keyboard-layout query scheduling and prevented clipboard-picker freezes on large pastes. This contributes to responsiveness of the inherited shell. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/5c74f823001b03a4607429681c4e7dfc65b065c0) [Evidence 2](https://github.com/omacom/omarchy/commit/c4dda58ba29a105d9262bfb48b259342beded1bb) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/markbus-ai) |
| **Marko Hrastovec** — IBM Plex contributor: Font production. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | IBM Plex project [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Martin Mares** — PCI Utilities author and maintainer; lspci provides device identities to fred.sysinfo. [Work, license and copyright](#pciutils). [Evidence](https://mj.ucw.cz/sw/pciutils/) | PCI Utilities [Public profile / project contact](https://mj.ucw.cz/sw/pciutils/); [Public email](mailto:mj@ucw.cz) |
| **Michael Grobe** — Original Lynx developer. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **Mike Abbink** — IBM Plex contributor: Creative direction and design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | IBM Design [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **neilerua973 (`neilerua973`)** — Creator of omarchy-keybindings-editor. Modular structure and physical-keyboard fidelity prior art. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#keys-editor). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/neilerua973) |
| **Nico Duldhardt (`klaudworks`)** — Author of the KMS disconnect fix in PR #395, carried historically by Tamlinux before it was superseded; retained here as historical patch credit. [Work, license and copyright](#aquamarine). [Evidence](https://github.com/hyprwm/aquamarine/pull/395) | Self-employed Contractor [Public profile / project contact](https://github.com/klaudworks) |
| **Nikita Prokopov** — Named in JetBrains Mono’s public thanks. Their support contributed to the font project used as the installed bar typeface; a more specific task is not established by that credit. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | JetBrains Mono project [Public profile / project contact](https://www.jetbrains.com/lp/mono/) |
| **OldJobobo (`OldJobobo`)** — Corrected asymmetric rounded shell borders. This contributes to the visual shell foundation of the fred.* suite. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/6675f6b71179d6d3eaff61ccdd95fd573a1ad86a) | Chopping Block Studio [Public profile / project contact](https://github.com/OldJobobo); [Public email](mailto:jsbrown7@gmail.com) |
| **outfoxxed (`outfoxxed`)** — Lead developer of Quickshell, the Qt Quick toolkit that runs the shell, bar widgets, layer surfaces, IPC and helper processes. [Work, license and copyright](#quickshell). [Evidence](https://quickshell.org/) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/outfoxxed); [Website](https://outfoxxed.me); [Public email](mailto:outfoxxed@outfoxxed.me) |
| **Pablo Gámez** — IBM Plex contributor: Font production. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | IBM Plex project [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Patrick Zippenfenig (`patrick-zippenfenig`)** — Open-Meteo founder/developer and publicly named operator of OpenMeteo GmbH. The weather and tide panels use its forecast, marine and geocoding services. [Work, license and copyright](#open-meteo). [Evidence](https://open-meteo.com/en/terms) | OpenMeteo GmbH / @open-meteo [Public profile / project contact](https://github.com/patrick-zippenfenig) |
| **Paul Eggert** — Contributor of mktime, fixes and GNU C Library stewardship. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Paul van der Laan** — IBM Plex contributor: Type direction and design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **Per Bothner** — Contributor of libio, which implements stdio functions. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Philipp Nurullin (`PhilippNurullin`)** — Type designer credited by JetBrains for JetBrains Mono, the base face used in JetBrainsMono Nerd Font. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | JetBrains Mono project [Public profile / project contact](https://github.com/philippnurullin) |
| **Pieter van Rosmalen** — IBM Plex contributor: Type direction and design. Omawrite includes the font family; this credits the upstream typeface project, not authorship of the editor. [Work, license and copyright](#ibm-plex). [Evidence](https://www.ibm.com/plex/specs/) | Bold Monday [Public profile / project contact](https://www.ibm.com/plex/specs/) |
| **ProwlerGR** — Publicly credited antiX contributor: multiple-init integration. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Raphael Rom** — Co-author of the Catmull–Rom interpolation method, the named mathematical technique used for the tide curve. [Work, license and copyright](#catmull-rom). [Evidence](https://doi.org/10.1016/B978-0-12-079050-0.50020-5) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://doi.org/10.1016/B978-0-12-079050-0.50020-5) |
| **Ravikumar Kolli** — Historical DosLynx support contributor. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **Rich Felker (`richfelker`)** — Main author and maintainer of musl. libtam names musl as a lightweight C-runtime compatibility target. [Work, license and copyright](#musl). [Evidence](https://git.musl-libc.org/cgit/musl/tree/COPYRIGHT) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/richfelker) |
| **Richard Stallman** — GNU founder and original GCC author. The compiler toolchain turns libtam and tam’s C source into runnable programs. [Work, license and copyright](#gcc). [Evidence](https://gcc.gnu.org/onlinedocs/gcc/Contributors.html) | GNU project [Public profile / project contact](https://www.stallman.org/) |
| **Robert Helgesson (`rycee`)** — Home Manager developer and author of its public introduction. Its declarative user profiles inform the workstation’s Nix/Home Manager packaging and recoverable configuration. [Work, license and copyright](#home-manager). [Evidence](https://rycee.net/presentations/2019-05-cph-nixos/) | Chaitsa [Public profile / project contact](https://github.com/rycee); [Website](https://rycee.net/) |
| **Robin** — Publicly credited antiX contributor: localisation support. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Roland McGrath** — Original GNU C Library author and contributor. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Rushi chaganti (`RushiChaganti`)** — Added Ctrl+Backspace clearing of shell filters. This contributes to the keyboard interaction conventions used by the current desktop. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/772122831998f8330ea2399cf35ea1356d37e380) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/RushiChaganti); [Website](https://rushichaganti.github.io/RushiChaganti/) |
| **Ryan Hughes (`ryanrhughes`)** — Omarchy shell and plugin-system contributor. The v4.0.4 history records work on widget scaling, theme tokens, built-in plugins and plugin management. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy) [Evidence 2](https://github.com/omacom/omarchy/commit/4f0bdb790b75603a6506daa6603b3576349373d6) [Evidence 3](https://github.com/omacom/omarchy/commit/e8fc2ef08f3aad9f6219b85a8ab8884f27fc953a) | Oodle [Public profile / project contact](https://github.com/ryanrhughes); [Website](https://heyoodle.com); [Public email](mailto:ryan@heyoodle.com) |
| **Ryan L McIntyre (`ryanoasis`)** — Creator of Nerd Fonts. Font patching and collected glyphs provide the installed bar font and icon rendering. [Work, license and copyright](#nerd-fonts). [Evidence](https://github.com/ryanoasis/nerd-fonts) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/ryanoasis); [Website](https://RyanLMcIntyre.com) |
| **Saman Shirdel (`itscallssh`)** — Improved brightness/audio scrolling, on-screen feedback and network-text readability. This work informs the inherited display controls and shell presentation. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/2093d1c9c7a8e205ca904c18465d10fb05eed965) [Evidence 2](https://github.com/omacom/omarchy/commit/5d13b53eb545dc20d4c6bc9fa3393647c434dc8e) [Evidence 3](https://github.com/omacom/omarchy/commit/10459759463ccf05ce5f41561cec31a5a8457b37) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/itscallssh) |
| **Scott Jones (`scottjones`)** — Added AM/PM clock choices and clarified monitor-scale targets in Omarchy. These are useful references for the clock and monitor components from which fred.* was developed. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/72ffd58316265bb770dddfc77983117bf9b91f0a) [Evidence 2](https://github.com/omacom/omarchy/commit/7faf53c4c0dcaa8b69bcc496ab1b376a73f75761) [Evidence 3](https://github.com/omacom/omarchy/commit/567e24cd90eb154150614bf5a092fe0e6e7b75e5) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/scottjones) |
| **Sergey Bugaev (`bugaevc`)** — Author of wl-clipboard, providing the wl-copy command used for panel clipboard actions. [Work, license and copyright](#wl-clipboard). [Evidence](https://github.com/bugaevc/wl-clipboard) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/bugaevc); [Public email](mailto:bugaevc@gmail.com) |
| **Seth Wood (`seth-wood`)** — Creator of keyarchy. Unused-shortcut discovery prior art; scoring is not implemented here. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#keyarchy). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/seth-wood) |
| **Simon Ser (`emersion`)** — Wayland developer who took over Sway maintenance from Drew DeVault in 2020. That stewardship supports the compositor selected to replace Hyprland. [Work, license and copyright](#sway). Took over wlroots maintenance alongside Sway in 2020; its shared display/input infrastructure underpins the planned desktop. [Work, license and copyright](#wlroots). [Evidence](https://drewdevault.com/blog/Im-handing-wlroots-and-sway-to-Simon/) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/emersion); [Website](https://emersion.fr); [Public email](mailto:contact@emersion.fr) |
| **Stephen Dolan** — Original jq author; JSON processing supports shell and helper integration. [Work, license and copyright](#jq). [Evidence](https://github.com/jqlang/jq/blob/master/COPYING) | jq [Public profile / project contact](https://github.com/jqlang/jq/blob/master/COPYING) |
| **Tatiana Tulupenko** — Named in JetBrains Mono’s public thanks. Their support contributed to the font project used as the installed bar typeface; a more specific task is not established by that credit. [Work, license and copyright](#jetbrains-mono). [Evidence](https://www.jetbrains.com/lp/mono/) | JetBrains Mono project [Public profile / project contact](https://www.jetbrains.com/lp/mono/) |
| **taxin-404 (`taxin-404`)** — Added right-click dismissal of notification popups. This contributes to notification interaction in the current desktop shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/35212998b5b932454ad8143d0981d2b6aa7a40d9) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/taxin-404) |
| **Thomas E. Dickey** — Lynx developer and maintainer whose ongoing work supports the optional terminal-browser integration. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/current/) | Lynx / invisible-island.net [Public profile / project contact](https://invisible-island.net/); [Public email](mailto:dickey@invisible-island.net) |
| **Tim Berners-Lee** — Contributor of the CERN WWW client-library foundation acknowledged by Lynx. This credits the optional browser’s lineage; no direct contribution to the tam command is implied. [Work, license and copyright](#lynx). [Evidence](https://lynx.invisible-island.net/lynx_help/about_lynx.html) | Lynx / DosLynx / WWW project, as credited in Lynx’s public history [Public profile / project contact](https://lynx.invisible-island.net/lynx_help/about_lynx.html) |
| **Tobias Lütke (`tobi`)** — Added Wi-Fi QR sharing and clearer switches for panel controls. This contributes to the inherited network UI and interaction conventions. [Work, license and copyright](#omarchy). [Evidence 1](https://github.com/omacom/omarchy/commit/a79d1dc8da0c1ed822eeee56c612671db1348360) [Evidence 2](https://github.com/omacom/omarchy/commit/4cfb2c2faec4feae0c2eed869cee68fbc2a8793c) | Shopify [Public profile / project contact](https://github.com/tobi); [Website](https://tobi.lutke.com) |
| **Toni Nowak (`acidkill`)** — Reworked tray-submenu navigation so submenu items can receive input. This improves application controls in the current desktop shell. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/5b2c02dee3918056038ad6f451dfdf5366b1d233) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/acidkill); [Website](https://toni.nowak.sh) |
| **Torbjörn Granlund** — Contributor of optimized string functions. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Ulrich Drepper** — Contributor across the GNU C Library, including threading, locale, string and formatted-I/O support. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Vaxry (`vaxerski`)** — Hypr Development contributor; upstream display-backend maintenance supports the carried display fixes, including PR #410. [Work, license and copyright](#aquamarine). Creator of Hyprland. Its monitor/workspace control and IPC support the current 0.x desktop while Tamlinux moves to Sway; this dependency credit ends when Hyprland is removed. [Work, license and copyright](#hyprland). [Evidence 1](https://github.com/hyprwm/Hyprland) [Evidence 2](https://github.com/hyprwm/aquamarine/pull/410) | @hyprwm [Public profile / project contact](https://github.com/vaxerski); [Website](https://vaxry.net) |
| **vivek7405 (`vivek7405`)** — Kept the hidden bar mapped so it can appear immediately. This improves the responsiveness of the bar that hosts the plugins. [Work, license and copyright](#omarchy). [Evidence](https://github.com/omacom/omarchy/commit/7633d8dee467a6d5328b07250d08f870e6a7c345) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/vivek7405) |
| **Wallon** — Publicly credited antiX contributor: localisation support. This is credit to the older-hardware inspiration and fallback-base community, rather than a claim that their code has been adopted. [Work, license and copyright](#antix). [Evidence](https://antixlinux.com/blog/) | antiX project [Public profile / project contact](https://antixlinux.com/blog/) |
| **Wolfram Gloger** — Contributor to the GNU C Library’s memory allocator. The system C runtime provides interfaces used by libtam and tam; no source copying into either component is asserted. [Work, license and copyright](#glibc). [Evidence](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) | GNU C Library project [Public profile / project contact](https://sourceware.org/glibc/manual/latest/html_node/Contributors.html) |
| **Woogy (`Woogy7`)** — Creator of Tides for Omarchy, the documented origin and component/design inspiration for fred.tides. [Work, license and copyright](#tides-art). [Evidence](https://github.com/greenermoose/tides-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/Woogy7) |
| **YonatanBaum (`YonatanBaum`)** — Creator of omarchy-app-shortcuts. Per-application reference considered in the design; not adopted as a feature. No code copying is documented in the keyboard plugin’s prior-art record. [Work, license and copyright](#app-shortcuts). [Evidence](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/UPSTREAM.md) | No affiliation stated in the inspected public profile/credit. [Public profile / project contact](https://github.com/YonatanBaum) |

## Works, licenses and stated copyright notices

The source links below are the authority for complete notices and exceptions. A short notice here is a reference, not a replacement license text. Names in a copyright notice are reproduced as the holder wrote them even when the person now uses a different public display name.

<a id="antix"></a>
### antiX Linux

- **Connection:** Older-hardware design inspiration and fallback base under consideration.
- **License:** Distribution of separately licensed packages; no single software license. [License/source notices](https://antixlinux.com/about/).
- **Stated copyright / limits:** Per-package and antiX-component notices; no individual blanket ownership asserted.
- **Source:** [Upstream project](https://antixlinux.com/about/).

<a id="aquamarine"></a>
### Aquamarine

- **Connection:** Display backend of the temporary Hyprland stack and source of the compatibility fork; its dependency-only credits retire with that stack.
- **License:** BSD-3-Clause. [License/source notices](https://github.com/hyprwm/aquamarine/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2024, Hypr Development
- **Source:** [Upstream project](https://github.com/hyprwm/aquamarine). [Wider contributor community](https://github.com/hyprwm/aquamarine/graphs/contributors).

<a id="arch"></a>
### Arch Linux

- **Connection:** Current package base and rolling-update inspiration.
- **License:** Distribution of separately licensed packages; no single software license. [License/source notices](https://archlinux.org/).
- **Stated copyright / limits:** Per-package maintainers and upstream holders; consult package license files.
- **Source:** [Upstream project](https://archlinux.org/).

<a id="btop"></a>
### btop

- **Connection:** Task manager launched by the system information panel.
- **License:** Apache-2.0. [License/source notices](https://github.com/aristocratos/btop/blob/main/LICENSE).
- **Stated copyright / limits:** See upstream source notices; the generic Apache license text is not a project copyright notice.
- **Source:** [Upstream project](https://github.com/aristocratos/btop). [Wider contributor community](https://github.com/aristocratos/btop/graphs/contributors).

<a id="btrfs"></a>
### Btrfs

- **Connection:** Copy-on-write filesystem and snapshot foundation named in the planned recovery/base architecture.
- **License:** GPL-2.0 for btrfs-progs; kernel code and individual files retain their own terms. [License/source notices](https://github.com/kdave/btrfs-progs/blob/master/COPYING).
- **Stated copyright / limits:** Many individual and organizational source-file holders; see kernel fs/btrfs and btrfs-progs notices.
- **Source:** [Upstream project](https://github.com/kdave/btrfs-progs/blob/master/COPYING).

<a id="catmull-rom"></a>
### Catmull–Rom interpolation

- **Connection:** Named interpolation technique in the tide curve.
- **License:** Mathematical-method credit, not a copied-code license; paper copyright remains with its holders. [License/source notices](https://doi.org/10.1016/B978-0-12-079050-0.50020-5).
- **Stated copyright / limits:** No paper text or third-party implementation is reproduced by this acknowledgement.
- **Source:** [Upstream project](https://doi.org/10.1016/B978-0-12-079050-0.50020-5).

<a id="curl"></a>
### curl

- **Connection:** HTTP command used by weather, tide and usage helpers.
- **License:** curl license (MIT/X inspired). [License/source notices](https://github.com/curl/curl/blob/master/COPYING).
- **Stated copyright / limits:** Copyright (c) 1996 - 2026, Daniel Stenberg, and many contributors.
- **Source:** [Upstream project](https://github.com/curl/curl). [Wider contributor community](https://github.com/curl/curl/graphs/contributors).

<a id="font-awesome"></a>
### Font Awesome

- **Connection:** Icon glyphs, including the weather sun, provided through the installed font.
- **License:** OFL-1.1 for fonts; MIT for code; CC-BY-4.0 for current SVG/JS icons. [License/source notices](https://github.com/FortAwesome/Font-Awesome/blob/7.x/LICENSE.txt).
- **Stated copyright / limits:** Copyright (c) 2026 Fonticons, Inc.; older installed editions may carry earlier notices. See the license for the edition distributed.
- **Source:** [Upstream project](https://github.com/FortAwesome/Font-Awesome). [Wider contributor community](https://github.com/FortAwesome/Font-Awesome/graphs/contributors).

<a id="glibc"></a>
### GNU C Library

- **Connection:** System C runtime used when building/running libtam on the current workstation.
- **License:** LGPL-2.1-or-later and per-file notices. [License/source notices](https://sourceware.org/glibc/).
- **Stated copyright / limits:** Free Software Foundation and other source-file holders.
- **Source:** [Upstream project](https://sourceware.org/glibc/).

<a id="gcc"></a>
### GNU Compiler Collection

- **Connection:** C compiler toolchain used to build libtam and tam on the current workstation.
- **License:** GPL-3.0-or-later for compiler code; GCC Runtime Library Exception and per-file terms apply to runtime libraries. [License/source notices](https://gcc.gnu.org/onlinedocs/gcc/Copying.html).
- **Stated copyright / limits:** Free Software Foundation and other source-file holders; compiler and runtime-library terms are distinct.
- **Source:** [Upstream project](https://gcc.gnu.org/onlinedocs/gcc/Copying.html).

<a id="gtk"></a>
### GTK

- **Connection:** Historical GTK4 crash-fix backport recorded in the ecosystem registry.
- **License:** LGPL-2.1-or-later; per-file notices apply. [License/source notices](https://github.com/GNOME/gtk/blob/main/COPYING).
- **Stated copyright / limits:** Many GTK contributors; the fix commit does not establish exclusive ownership.
- **Source:** [Upstream project](https://github.com/GNOME/gtk/blob/main/COPYING).

<a id="home-manager"></a>
### Home Manager

- **Connection:** Declarative user-environment management in the Tamlinux workstation tooling.
- **License:** MIT. [License/source notices](https://github.com/nix-community/home-manager/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2017-2026 Home Manager contributors
- **Source:** [Upstream project](https://github.com/nix-community/home-manager). [Wider contributor community](https://github.com/nix-community/home-manager/graphs/contributors).

<a id="hyprland"></a>
### Hyprland

- **Connection:** Temporary compositor for the Tamlinux 0.x transition and source of the compatibility fork. The public roadmap removes Hyprland at 1.0.
- **License:** BSD-3-Clause. [License/source notices](https://github.com/hyprwm/Hyprland/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2022-2026, vaxerski
- **Source:** [Upstream project](https://github.com/hyprwm/Hyprland). [Wider contributor community](https://github.com/hyprwm/Hyprland/graphs/contributors).

<a id="ibm-plex"></a>
### IBM Plex

- **Connection:** Typeface bundled in the Omawrite fork.
- **License:** OFL-1.1. [License/source notices](https://github.com/omacom/omawrite/blob/master/fonts/OFL.txt).
- **Stated copyright / limits:** Copyright © 2017 IBM Corp. with Reserved Font Name "Plex".
- **Source:** [Upstream project](https://github.com/omacom/omawrite/blob/master/fonts/OFL.txt).

<a id="jetbrains-mono"></a>
### JetBrains Mono

- **Connection:** Base typeface for the installed JetBrainsMono Nerd Font.
- **License:** OFL-1.1. [License/source notices](https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt).
- **Stated copyright / limits:** Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono); copyright statement(s).
- **Source:** [Upstream project](https://github.com/JetBrains/JetBrainsMono). [Wider contributor community](https://github.com/JetBrains/JetBrainsMono/graphs/contributors).

<a id="jq"></a>
### jq

- **Connection:** JSON processing in shell/helper integration.
- **License:** MIT for jq; bundled components have additional notices. [License/source notices](https://github.com/jqlang/jq/blob/master/COPYING).
- **Stated copyright / limits:** jq is copyright (C) 2012 Stephen Dolan; see COPYING for bundled-component notices.
- **Source:** [Upstream project](https://github.com/jqlang/jq). [Wider contributor community](https://github.com/jqlang/jq/graphs/contributors).

<a id="weather-art"></a>
### Just Right Weather

- **Connection:** Documented weather timeline, solar-event and API-bundling inspiration.
- **License:** MIT. [License/source notices](https://github.com/daniellopez12/just-right-weather/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) David Heinemeier Hansson; Copyright (c) 2026 daniellopez12
- **Source:** [Upstream project](https://github.com/daniellopez12/just-right-weather). [Wider contributor community](https://github.com/daniellopez12/just-right-weather/graphs/contributors).

<a id="keyarchy"></a>
### keyarchy

- **Connection:** Unused-shortcut discovery prior art; scoring is not implemented here.
- **License:** MIT. [License/source notices](https://github.com/seth-wood/keyarchy/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Seth Wood
- **Source:** [Upstream project](https://github.com/seth-wood/keyarchy). [Wider contributor community](https://github.com/seth-wood/keyarchy/graphs/contributors).

<a id="linecast"></a>
### Linecast

- **Connection:** Documented daylight-shaded curve and restrained presentation inspiration.
- **License:** MIT. [License/source notices](https://github.com/ashuttl/linecast/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2025 Andrew Shuttleworth
- **Source:** [Upstream project](https://github.com/ashuttl/linecast). [Wider contributor community](https://github.com/ashuttl/linecast/graphs/contributors).

<a id="linux"></a>
### Linux

- **Connection:** Kernel interfaces and drivers underpin the workstation and telemetry probes.
- **License:** GPL-2.0-only with Linux-syscall-note for relevant UAPI headers; individual files may differ. [License/source notices](https://www.kernel.org/doc/html/latest/process/license-rules.html).
- **Stated copyright / limits:** Many individual and organizational holders; consult each file, not a single blanket ownership claim.
- **Source:** [Upstream project](https://www.kernel.org/doc/html/latest/process/license-rules.html).

<a id="lynx"></a>
### Lynx

- **Connection:** Optional browser named by the tam command contract; a separately installed program, not bundled source.
- **License:** GPL-2.0, with historical and constituent-code notices. [License/source notices](https://lynx.invisible-island.net/lynx_help/about_lynx.html).
- **Stated copyright / limits:** University of Kansas, lynx-dev authors, CERN and other source-file holders; see the project’s credit and license records.
- **Source:** [Upstream project](https://lynx.invisible-island.net/lynx_help/about_lynx.html).

<a id="musl"></a>
### musl

- **Connection:** Small C-library target named in libtam documentation; compatibility is a stated target, not certified by these credits.
- **License:** MIT; per-file and third-party exceptions are recorded upstream. [License/source notices](https://git.musl-libc.org/cgit/musl/tree/COPYRIGHT).
- **Stated copyright / limits:** Rich Felker and other musl authors; see upstream COPYRIGHT.
- **Source:** [Upstream project](https://git.musl-libc.org/cgit/musl/tree/COPYRIGHT).

<a id="nerd-fonts"></a>
### Nerd Fonts

- **Connection:** Patched system fonts and icon glyph collection used by the bar.
- **License:** MIT for scripts; OFL-1.1 and other source-font licenses for font assets. [License/source notices](https://github.com/ryanoasis/nerd-fonts/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2014 Ryan L McIntyre; constituent fonts retain their own notices.
- **Source:** [Upstream project](https://github.com/ryanoasis/nerd-fonts). [Wider contributor community](https://github.com/ryanoasis/nerd-fonts/graphs/contributors).

<a id="nix"></a>
### Nix

- **Connection:** Declarative package management and atomic rollback inspiration and workstation tooling.
- **License:** LGPL-2.1; consult individual file notices. [License/source notices](https://github.com/NixOS/nix/blob/master/COPYING).
- **Stated copyright / limits:** No project-specific holder established from the inspected license text; see source notices. The license-text author is not assumed to own the software.
- **Source:** [Upstream project](https://github.com/NixOS/nix). [Wider contributor community](https://github.com/NixOS/nix/graphs/contributors).

<a id="omarchy"></a>
### Omarchy

- **Connection:** Current Tamlinux 0.x base, shell/plugin integration, and documented cloned components.
- **License:** MIT. [License/source notices](https://github.com/omacom/omarchy/blob/quattro/LICENSE).
- **Stated copyright / limits:** Copyright (c) David Heinemeier Hansson
- **Source:** [Upstream project](https://github.com/omacom/omarchy). [Wider contributor community](https://github.com/omacom/omarchy/graphs/contributors).

<a id="marketplace"></a>
### Omarchy Plugin Marketplace

- **Connection:** Plugin registry, distribution discovery and public security review.
- **License:** MIT. [License/source notices](https://github.com/omacom/omarchy-plugin-marketplace/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 HANCORE
- **Source:** [Upstream project](https://github.com/omacom/omarchy-plugin-marketplace). [Wider contributor community](https://github.com/omacom/omarchy-plugin-marketplace/graphs/contributors).

<a id="app-shortcuts"></a>
### omarchy-app-shortcuts

- **Connection:** Per-application reference considered in the design; not adopted as a feature.
- **License:** MIT. [License/source notices](https://github.com/YonatanBaum/omarchy-app-shortcuts/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 funcoder
- **Source:** [Upstream project](https://github.com/YonatanBaum/omarchy-app-shortcuts). [Wider contributor community](https://github.com/YonatanBaum/omarchy-app-shortcuts/graphs/contributors).

<a id="key-visualizer"></a>
### omarchy-key-visualizer

- **Connection:** Live keyboard presentation prior art.
- **License:** MIT. [License/source notices](https://github.com/felixzsh/omarchy-key-visualizer/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Felix
- **Source:** [Upstream project](https://github.com/felixzsh/omarchy-key-visualizer). [Wider contributor community](https://github.com/felixzsh/omarchy-key-visualizer/graphs/contributors).

<a id="keybinding-coach"></a>
### omarchy-keybinding-coach

- **Connection:** Shortcut learning and teaching prior art.
- **License:** MIT. [License/source notices](https://github.com/balazsorban44/omarchy-keybinding-coach/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Balázs Orbán
- **Source:** [Upstream project](https://github.com/balazsorban44/omarchy-keybinding-coach). [Wider contributor community](https://github.com/balazsorban44/omarchy-keybinding-coach/graphs/contributors).

<a id="keys-editor"></a>
### omarchy-keybindings-editor

- **Connection:** Modular structure and physical-keyboard fidelity prior art.
- **License:** MIT. [License/source notices](https://github.com/neilerua973/omarchy-keybindings-editor/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Ming Bao
- **Source:** [Upstream project](https://github.com/neilerua973/omarchy-keybindings-editor). [Wider contributor community](https://github.com/neilerua973/omarchy-keybindings-editor/graphs/contributors).

<a id="keyboard-minimap"></a>
### omarchy-keyboard-minimap

- **Connection:** Global-capture approach considered when choosing panel-scoped capture.
- **License:** MIT. [License/source notices](https://github.com/balazsorban44/omarchy-keyboard-minimap/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Balázs Orbán
- **Source:** [Upstream project](https://github.com/balazsorban44/omarchy-keyboard-minimap). [Wider contributor community](https://github.com/balazsorban44/omarchy-keyboard-minimap/graphs/contributors).

<a id="shortcut-sheet"></a>
### omarchy-shortcut-sheet

- **Connection:** Reverse lookup from command to keybinding prior art.
- **License:** MIT. [License/source notices](https://github.com/fze-fze/omarchy-shortcut-sheet/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 fze
- **Source:** [Upstream project](https://github.com/fze-fze/omarchy-shortcut-sheet). [Wider contributor community](https://github.com/fze-fze/omarchy-shortcut-sheet/graphs/contributors).

<a id="visual-keys"></a>
### omarchy-visual-keybindings

- **Connection:** Keyboard capture and interactive exploration prior art.
- **License:** MIT. [License/source notices](https://github.com/dai199/omarchy-visual-keybindings/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Daiki
- **Source:** [Upstream project](https://github.com/dai199/omarchy-visual-keybindings). [Wider contributor community](https://github.com/dai199/omarchy-visual-keybindings/graphs/contributors).

<a id="omawrite"></a>
### Omawrite

- **Connection:** Qt editor whose source is carried in the Tamlinux patch fork.
- **License:** MIT. [License/source notices](https://github.com/omacom/omawrite/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 David Heinemeier Hansson
- **Source:** [Upstream project](https://github.com/omacom/omawrite). [Wider contributor community](https://github.com/omacom/omawrite/graphs/contributors).

<a id="open-meteo"></a>
### Open-Meteo

- **Connection:** Forecast, geocoding and marine API service.
- **License:** AGPL-3.0 for server software; API data CC-BY-4.0 under the service terms. [License/source notices](https://github.com/open-meteo/open-meteo/blob/main/LICENSE).
- **Stated copyright / limits:** Open-Meteo authors and data providers; individual software ownership is not assigned from a generic AGPL text. [Data terms](https://open-meteo.com/en/terms).
- **Source:** [Upstream project](https://github.com/open-meteo/open-meteo). [Wider contributor community](https://github.com/open-meteo/open-meteo/graphs/contributors).

<a id="pciutils"></a>
### PCI Utilities

- **Connection:** lspci supplies device identities to the hardware telemetry helper.
- **License:** GPL-2.0-or-later, as stated in the upstream README; see individual files. [License/source notices](https://github.com/pciutils/pciutils/blob/master/COPYING).
- **Stated copyright / limits:** Martin Mares and PCI Utilities contributors; consult file notices for years and additional holders.
- **Source:** [Upstream project](https://github.com/pciutils/pciutils). [Wider contributor community](https://github.com/pciutils/pciutils/graphs/contributors).

<a id="python"></a>
### Python

- **Connection:** Interpreter and standard library used by the Tamlinux helper programs.
- **License:** PSF License Version 2 and historical bundled notices. [License/source notices](https://docs.python.org/3/license.html).
- **Stated copyright / limits:** Python Software Foundation and the historical holders recorded in the license.
- **Source:** [Upstream project](https://docs.python.org/3/license.html).

<a id="qt"></a>
### Qt / Qt Quick

- **Connection:** UI, QML, controls and graphics foundations used by the shell and Omawrite.
- **License:** Qt module-specific LGPL/GPL or commercial terms; see installed module licenses. [License/source notices](https://www.qt.io/licensing/open-source-lgpl-obligations).
- **Stated copyright / limits:** The Qt Company and many other contributors; module source files retain their notices.
- **Source:** [Upstream project](https://www.qt.io/licensing/open-source-lgpl-obligations).

<a id="quickshell"></a>
### Quickshell

- **Connection:** Runtime for the QML shell and fred.* widgets.
- **License:** LGPL-3.0; consult file SPDX headers for applicable terms. [License/source notices](https://github.com/quickshell-mirror/quickshell/blob/master/LICENSE).
- **Stated copyright / limits:** No project-specific holder established from the inspected license text; see source notices. The license-text author is not assumed to own the software.
- **Source:** [Upstream project](https://github.com/quickshell-mirror/quickshell). [Wider contributor community](https://github.com/quickshell-mirror/quickshell/graphs/contributors).

<a id="river"></a>
### River

- **Connection:** Compositor inspiration recorded in Tamlinux UPSTREAM.md.
- **License:** See upstream COPYING and per-file notices; no River code reuse established. [License/source notices](https://codeberg.org/river/river).
- **Stated copyright / limits:** See upstream notices; individual copyright ownership not asserted.
- **Source:** [Upstream project](https://codeberg.org/river/river).

<a id="runit"></a>
### runit

- **Connection:** Service-supervision reference for the planned Void/antiX base.
- **License:** BSD-3-Clause style, per upstream FAQ. [License/source notices](https://smarden.org/runit/faq).
- **Stated copyright / limits:** See package/COPYING in the upstream tarball for Gerrit Pape and any additional notices.
- **Source:** [Upstream project](https://smarden.org/runit/faq).

<a id="seatd"></a>
### seatd

- **Connection:** Seat and device-access service named in the planned Void/Sway base.
- **License:** MIT. [License/source notices](https://github.com/kennylevinsen/seatd/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright 2020 Kenny Levinsen
- **Source:** [Upstream project](https://sr.ht/~kennylevinsen/seatd/). [Wider contributor community](https://github.com/kennylevinsen/seatd/graphs/contributors).

<a id="sway"></a>
### Sway

- **Connection:** Chosen compositor direction in the public plan; current released fred.* widgets still use Hyprland/Quickshell.
- **License:** MIT. [License/source notices](https://github.com/swaywm/sway/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2016-2017 Drew DeVault
- **Source:** [Upstream project](https://github.com/swaywm/sway). [Wider contributor community](https://github.com/swaywm/sway/graphs/contributors).

<a id="tides-art"></a>
### Tides for Omarchy

- **Connection:** Documented tide widget origin and component/design reference.
- **License:** MIT. [License/source notices](https://github.com/Woogy7/omarchy-tides/blob/main/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2026 Woogy7
- **Source:** [Upstream project](https://github.com/Woogy7/omarchy-tides). [Wider contributor community](https://github.com/Woogy7/omarchy-tides/graphs/contributors).

<a id="wayland"></a>
### Wayland

- **Connection:** Display protocol used by the current desktop and the planned Sway desktop; a foundation independent of Hyprland.
- **License:** MIT-style license; consult individual file notices. [License/source notices](https://github.com/wayland-mirror/wayland/blob/main/COPYING).
- **Stated copyright / limits:** Copyright © 2008-2012 Kristian Høgsberg; Copyright © 2010-2012 Intel Corporation; Copyright © 2011 Benjamin Franzke; Copyright © 2012 Collabora, Ltd.
- **Source:** [Upstream project](https://wayland.freedesktop.org/). [Wider contributor community](https://github.com/wayland-mirror/wayland/graphs/contributors).

<a id="wl-clipboard"></a>
### wl-clipboard

- **Connection:** wl-copy provides clipboard operations for panels.
- **License:** GPL-3.0; see upstream notices. [License/source notices](https://github.com/bugaevc/wl-clipboard/blob/master/COPYING).
- **Stated copyright / limits:** No project-specific holder established from the inspected license text; see source notices. The license-text author is not assumed to own the software.
- **Source:** [Upstream project](https://github.com/bugaevc/wl-clipboard). [Wider contributor community](https://github.com/bugaevc/wl-clipboard/graphs/contributors).

<a id="wlroots"></a>
### wlroots

- **Connection:** Compositor library underpinning the selected Sway target. This is a planned-platform credit, not a completed desktop migration.
- **License:** MIT. [License/source notices](https://github.com/swaywm/wlroots/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2017, 2018 Drew DeVault; Copyright (c) 2014 Jari Vetoniemi
- **Source:** [Upstream project](https://gitlab.freedesktop.org/wlroots/wlroots). [Wider contributor community](https://github.com/swaywm/wlroots/graphs/contributors).

<a id="wttr"></a>
### wttr.in

- **Connection:** Weather JSON service called by the weather panel.
- **License:** Apache-2.0. [License/source notices](https://github.com/chubin/wttr.in/blob/master/LICENSE).
- **Stated copyright / limits:** See project source-file notices; generic Apache license text alone does not identify a holder.
- **Source:** [Upstream project](https://github.com/chubin/wttr.in). [Wider contributor community](https://github.com/chubin/wttr.in/graphs/contributors).

<a id="xbps"></a>
### XBPS / Void Linux

- **Connection:** Native packaging reference for the planned Void base; not a claim that the migration has shipped.
- **License:** BSD-2-Clause main license; consult additional per-file notices. [License/source notices](https://github.com/void-linux/xbps/blob/master/LICENSE).
- **Stated copyright / limits:** Copyright (c) 2008-2020 Juan Romero Pardines; 2014-2019 Enno Boland; 2016-2019 Duncan Overbruck. See COPYING and file headers.
- **Source:** [Upstream project](https://github.com/void-linux/xbps). [Wider contributor community](https://github.com/void-linux/xbps/graphs/contributors).

## Community credit and coverage

We also thank the wider upstream communities: reviewers, translators, documentation writers, package maintainers, testers, issue reporters and accessibility contributors. The project/community links above recognize their wider work. This researched list emphasizes identifiable connections to this repository; it is not a complete census of every transitive dependency or a claim of endorsement. Public profiles and affiliations can change; the date above identifies this review.

The [Qt contributors](https://code.qt.io/), [Wayland contributors](https://gitlab.freedesktop.org/wayland/wayland), [Arch package maintainers](https://archlinux.org/people/) and their dependency communities provide additional foundations. Their licenses and copyright notices remain in the individual upstream projects and installed packages; no blanket ownership or single license is assigned to those communities.

Weather and marine data credit also belongs to [Open-Meteo’s listed model providers](https://open-meteo.com/en/docs), the [marine providers](https://open-meteo.com/en/docs/marine-weather-api), and [GeoNames](https://www.geonames.org/) for the geocoding dataset. Server software licensing and API/data terms are separate. Provider-specific attribution and dataset terms remain applicable.

## Repository coverage

The public Tamlinux inventory was checked against GitHub on 2026-10-09. Each repository below has its own acknowledgements file, with a contribution scope appropriate to that repository. Unrelated personal repositories are outside this inventory.

| Repository | Acknowledgements |
| --- | --- |
| agents-fred-tamlinux | [File](https://github.com/greenermoose/agents-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| aquamarine | [File](https://github.com/greenermoose/aquamarine/blob/patchset/v0.15.1/ACKNOWLEDGEMENTS.md) |
| clock-fred-tamlinux | [File](https://github.com/greenermoose/clock-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| ecosystem-fred-tamlinux | [File](https://github.com/greenermoose/ecosystem-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| Hyprland | [File](https://github.com/greenermoose/Hyprland/blob/patch/dpms-state-per-monitor/ACKNOWLEDGEMENTS.md) |
| keyboard-fred-tamlinux | [File](https://github.com/greenermoose/keyboard-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| libtam | [File](https://github.com/greenermoose/libtam/blob/main/ACKNOWLEDGEMENTS.md) |
| monitor-fred-tamlinux | [File](https://github.com/greenermoose/monitor-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| omarchy | [File](https://github.com/greenermoose/omarchy/blob/patch/bar-tooltip-scale-safe-size/ACKNOWLEDGEMENTS.md) |
| omawrite | [File](https://github.com/greenermoose/omawrite/blob/patchset/v0.5.0/ACKNOWLEDGEMENTS.md) |
| plugin-fred-tamlinux | [File](https://github.com/greenermoose/plugin-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| sysinfo-fred-tamlinux | [File](https://github.com/greenermoose/sysinfo-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| tam | [File](https://github.com/greenermoose/tam/blob/main/ACKNOWLEDGEMENTS.md) |
| tamlinux | [File](https://github.com/greenermoose/tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| tides-fred-tamlinux | [File](https://github.com/greenermoose/tides-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| weather-fred-tamlinux | [File](https://github.com/greenermoose/weather-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |
| workspaces-fred-tamlinux | [File](https://github.com/greenermoose/workspaces-fred-tamlinux/blob/main/ACKNOWLEDGEMENTS.md) |

To correct a name, attribution, affiliation or contact preference, please open an issue in this repository or contact [Fred’s public account](https://github.com/greenermoose). Only evidence-backed additions should be made; do not infer identities behind pseudonyms.

Research and compilation were AI-assisted by Codex under Fred’s direction. AI systems and provider organizations are not listed as humans; existing AI provenance records, where present, describe their separate role.
