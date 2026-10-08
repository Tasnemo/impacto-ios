# Roadmap

Mirrors the thread plan in `workme.md`; this file records status and adjustments made
after each thread. Modes: Ultra / High / Medium / Low (see `workme.md`).

| # | Thread | Mode | Branch | Status | Gate |
|---|---|---|---|---|---|
| 01 | Upstream architecture & feasibility | Ultra | `phase-00-upstream-analysis` | **Done** (docs only) | Architecture + blockers understood |
| 02 | Reproducible desktop build | High | `phase-01-desktop-baseline` | **Done**, integrated into `master` | Ubuntu build + asset-free launcher and CI verified; no game tested |
| 03 | SG desktop compatibility (RE with real Steam files) | Ultra | `phase-02-steins-compatibility` | Next; needs legitimate game evidence | MPK version, movie signature, opcode set, phone/mail semantics documented |
| 04 | SG desktop implementation | High | `phase-02-steins-compatibility` | Pending | Title → prologue → first phone trigger → save/load on desktop |
| 05 | iOS architecture & build feasibility | Ultra | `phase-03-ios-feasibility` | Pending | vcpkg `arm64-ios` deps + GL/Metal decision |
| 06 | Minimal iOS build & sideloading | High | `phase-03-ios-feasibility` | Pending | App launches on iPhone from a Windows-driven workflow |
| 07 | iOS rendering backend | High | `phase-04-ios-rendering` | Pending | Scenes render correctly on device |
| 08 | iOS audio, input, lifecycle | High | `phase-05-ios-platform` | Pending | Touch, audio, background/resume |
| 09 | SG iOS integration | High | `phase-06-ios-sg` | Pending | Full route playable on device |
| 10 | Optimisation, offline test, release | Medium | `phase-07-release` | Pending | Acceptance criteria in `workme.md` |

## Adjustments after Thread 01

- Thread 02 must replace the CoZ NuGet binary cache in CI (`docs/blockers.md` B6) and
  should expect no upstream test suite (B7); add a smoke-run target.
- Thread 03 cannot be done from an orb without real game files. The developer must prepare
  a **non-asset evidence pack** on Windows: `dir /s` listing of the Steam install, hexdump of
  the first 64 bytes of every `.mpk` and every movie file, and sc3tools disassembly of a few
  scripts. Scripts/disassembly are derivative of commercial assets — keep them out of git;
  share through the orb session only.
- Bink 2 (B1) likely forces an asset-preparation tool on Windows earlier than planned
  (originally Thread 09/10). Consider scoping a `tools/sg-pack` CLI in Thread 04.
- Thread 05 should check whether OpenGL ES is still linkable/runnable on iOS 26 before
  evaluating MoltenVK/Metal.

## Adjustments after Thread 02

- Use Ubuntu 24.04/GCC 13 or the documented Ubuntu container in Debian-based orbs.
  Native Debian 12/GCC 12 cannot compile the pinned OpenAL Soft version.
- The asset-free launcher is verified; viewer/game profiles were not tested and
  require original data. Do not interpret the green desktop CI as game compatibility.
- Thread 02 was shipped to `origin/master` at the user's request. Branch Thread 03
  from the latest `origin/master`; read the updated handoff first.
