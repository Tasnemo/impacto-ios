# Roadmap

Status record of the development plan in `workme.md` (section 7, Phases A–D),
which is authoritative. Updated by every thread; last update: Thread 07
(2026-10-08).

## Goal and strategy

The only end goal is to play the original English Steam STEINS;GATE
natively and offline on an iPhone through an iOS port of impacto.

1. Establish a representative STEINS;GATE gameplay baseline with the
   existing desktop engine.
2. Port that shared C++ engine to native iOS ARM64.
3. Integrate rendering, controls, audio, storage and gameplay on iPhone.
4. Complete remaining game compatibility and verify all routes on iPhone.

**Desktop compatibility is supporting infrastructure, not a product
milestone.** Linux/Windows builds exist to validate the shared engine
(synthetic probes in CI, owner-side runs against the real Steam data). No
polished Windows release is planned, and complete desktop gameplay or all
endings are **not** a precondition for iOS work: small iOS build-feasibility
experiments may run at any time, and the native iOS build (Thread 08) starts
as soon as the open desktop blockers are documented.

## Agent modes

| Mode | Use for |
|---|---|
| Low | Deterministic mechanical work: docs/roadmap sync, regenerating fixtures or generated Lua, CI tweaks with a known fix |
| Medium | Default for implementation and integration, including all planned iOS threads |
| High | Only after a demonstrated blocker: reverse engineering that Medium could not settle (e.g. phone UI semantics) or a real architectural decision (e.g. GLES on iOS proves unusable) |
| Ultra | Exceptional cases that High cannot resolve |

No future thread is assigned High or Ultra by default (`workme.md` 4.2–4.4).
Changing mode needs a committed handoff and a new thread.

## Threads

Thread numbers are milestones; one Medium thread may cover several of the
`workme.md` sub-milestones (04A–12C) when the scope stays clear. The working
branch is chosen at the start of each thread and recorded in
[handoff.md](handoff.md); none is assumed here.

| # | Milestone (`workme.md` ids) | Mode | Status | Gate |
|---|---|---|---|---|
| 01 | Upstream architecture and feasibility | Ultra (historical) | **Done** | architecture and blockers understood |
| 02 | Reproducible desktop build | High (historical) | **Done** | Ubuntu build, asset-free launcher, CI |
| 03 | SG compatibility investigation | Ultra (historical) | **Done** | runtime evidence, opcode gaps, plan |
| 04 | Phase A: profile, opcodes, harness, save foundation (04A–04D) | Medium | **Done** (synthetic) | `sghd` VM runs synthetic SGHD scripts; save round trip |
| 05 | Phase B: Steam evidence, profile ids, movie skip, Ogg audio (05A partial) | Medium | **Done** (synthetic + install listing) | profile matches the real install layout |
| 06 | Phase B: census, font/LAY/1080p, plain dialogue box, phone catalogue + item bits, save format 2 (05B, 06A, 06B partial) | Medium | **Done** (synthetic + census) | real scripts decode; presentation constants from the install |
| 07 | Phase B: representative Steam gameplay validation (07A–07C) | Medium | **Done** (round-3 evidence applied); 07b: first real boot ran, title wait fixed; 07c: title protocol + engine menu; **title pass / first dialogue still owner-side** | real boot → title → dialogue → BG/sprites → voice/BGM on Windows, no desync or hang |
| 08 | Phase C: native iOS ARM64 build and app shell (08A–08C) | Medium | **Next** | iOS ARM64 build of impacto in GitHub Actions macOS; minimal SDL3 app artifact; signing documented |
| 09 | Phase C: iOS rendering (09A–09B) | Medium | Pending | existing GLES3 renderer (or decided fallback) draws a synthetic scene on device |
| 10 | Phase C: iOS platform integration (10A–10C) | Medium | Pending | audio, touch/phone controls, Files import, saves, suspend/resume |
| 11 | Phase D: STEINS;GATE on iPhone (11A–11C) | Medium | Pending | real Steam data imported and playing on device |
| 12 | Phase D: full routes, offline reliability, release docs (12A–12C) | Low/Medium | Pending | `workme.md` 24 definition of done |
| side | Phone UI (06C): sub-types 0x05-0x1E, PHONE sheets | High when started | Open | player-driven mails/calls work; [phone-protocol.md](phone-protocol.md) |

Owner-side Windows runs (first boot, phone polarity, sprite naming) continue
in parallel with Threads 08–10; their results are applied by short Medium
(or Low, if purely mechanical) follow-ups.

## Blocker triage for the iOS transition

Details: [ios-transition.md](ios-transition.md).

- **Before porting** (desktop, needs owner runs): one real Windows boot
  reaching the first dialogue line without crash, desync or hang. Everything
  else can proceed in parallel.
- **Deferred to iOS integration or later:** sprite rectangles still
  unverified (selection, system message box, date, save icon), phone UI,
  Bink 2 movies, backlog/title/system menus, Steam save import.

## History

- Thread 01: CoZ NuGet cache unusable (B6), no upstream tests (B7); evidence
  must come from the owner's Windows install.
- Thread 02: Ubuntu 24.04/GCC 13 (or the Ubuntu container on Debian orbs).
- Thread 03: synthetic MPK/SCX fixtures reproduce the PS3-profile failures;
  new `sghd` game id instead of editing `sgps3`.
- Thread 04: `workme.md` re-planned into Medium sub-milestones; asset-free
  work done on `phase-03-sghd-implementation`.
- Thread 05: Steam install listing; movies are Bink 2 (skipped safely).
- Thread 06: census of all 190 scripts; 1080p design; phone item bits.
- Thread 07: roadmap synchronised with `workme.md` (desktop = test
  infrastructure, Medium default, iOS build next); Game.exe font widths,
  `10 3A` six expressions, Steam sprite checks.
- Thread 07b: first owner boot on real data; `10 34` (title) waited forever
  and misread its byte; fixed with a stall report for the next run.
- Thread 07c: round 5 reached the title instructions; title protocol
  reconstructed from the script context (SF_TITLEEND / SW_TITLECUR, common
  variable layout); engine title menu with keyboard/mouse, artwork pending.
