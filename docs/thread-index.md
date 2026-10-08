# Thread index

| # | Thread | Mode | Branch | Status | Report |
|---|---|---|---|---|---|
| 01 | Upstream architecture & feasibility | Ultra | `phase-00-upstream-analysis` | Done, merged | [threads/01-upstream-investigation.md](threads/01-upstream-investigation.md) |
| 02 | Reproducible desktop build | High | `phase-01-desktop-baseline` | Done, merged into `master` | [threads/02-desktop-baseline.md](threads/02-desktop-baseline.md) |
| 03 | STEINS;GATE desktop compatibility investigation | Ultra | `phase-02-steins-compatibility` | Done (not merged) | [threads/03-desktop-compatibility.md](threads/03-desktop-compatibility.md) |
| 04 | STEINS;GATE desktop implementation (plan Tasks 1–8) | Medium | `phase-03-sghd-implementation` | Tasks 1–4 done, Task 6 charset done; **stopped at Task 5 (owner evidence)** | [threads/04-sghd-implementation.md](threads/04-sghd-implementation.md) |
| 05 | Steam evidence → Tasks 5–8 | Medium | `phase-03-sghd-implementation` | Task 5 config, movie skip (3 crash fixes), Ogg audio probe, L4 fixed, census tool, Windows CI; **stopped: needs owner census** | [threads/05-sghd-steam-evidence.md](threads/05-sghd-steam-evidence.md) |
| 06 | Census → decode integrity, font/sheets/LAY/1080p, plain dialogue box, phone catalogue + item bits, save format 2, Windows tools | Medium | `phase-03-sghd-implementation` | Done on synthetic data; **stopped: needs Windows round 3 (sprites, widths, census v2, first boot)** | [threads/06-sghd-census.md](threads/06-sghd-census.md) |
| 07 | Steam gameplay baseline: round-3 evidence (`10 3A`, exe font widths, 720p text styles, sprite checks), roadmap sync, iOS transition plan | Medium | `phase-03-sghd-implementation` | Done; **real boot still needs the owner's log** | [threads/07-gameplay-baseline.md](threads/07-gameplay-baseline.md) |
| 07b | First real Steam boot follow-up: startup stubs triaged, `10 34` title wait + `10 36` layout fixed, fixed-layout audit, stall report, census `--context` | Medium | `phase-03-sghd-implementation` | Done (synthetic); **title pass / first dialogue need owner round 5** | [threads/07b-first-real-boot.md](threads/07b-first-real-boot.md) |
| 08 (next) | Native iOS ARM64 build and app shell | Medium | new branch from `phase-03-sghd-implementation` | Ready | — |
| side | Phone UI (sub-types 0x05-0x1E, PHONE sheets) | High when started | — | Needs RE | [phone-protocol.md](phone-protocol.md) |

Plan: [thread-04-implementation-plan.md](thread-04-implementation-plan.md).
Roadmap: [roadmap.md](roadmap.md). Current state:
[project-state.md](project-state.md).
