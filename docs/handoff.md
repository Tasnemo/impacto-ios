# Project Handoff

## Current Milestone
Thread 03 — STEINS;GATE Desktop Compatibility Investigation is complete on
branch `phase-02-steins-compatibility`. It established, by executing the
engine, that STEINS;GATE does not launch and that the English Steam release
is not supported; it produced the opcode gap list, a prioritised backlog, an
asset-free test suite and a bounded Thread 04 plan. **No implementation of
Steam support and no iOS work has started.**

## Repository State
- Repository: `Tasnemo/impacto-ios`; integration branch **master** (public).
  No commercial assets, derived script dumps or secrets were added.
- Thread 01: `phase-00-upstream-analysis`, merged. Thread 02:
  `phase-01-desktop-baseline`, merged (`master` = `208cc56a` at Thread 03 start).
- Thread 03: branch `phase-02-steins-compatibility` from `208cc56a`.
  Obtain the Thread 03 commit with
  `git log -1 --format=%H -- docs/threads/03-desktop-compatibility.md`.
  Push status is recorded in that thread report's final section and in the
  Thread 03 chat summary; verify with `git branch -r`.
- Engine sources (`src/`), profiles and resources are **unchanged** since
  Thread 02. Thread 03 added `tests/compat/`, docs, and two CI steps in
  `.github/workflows/desktop.yml`.

## What Thread 03 established (read these, in order)
1. [steins-gate-compatibility.md](steins-gate-compatibility.md) — full
   investigation with runtime evidence (§6) and feasibility (§8).
2. [compatibility-matrix.md](compatibility-matrix.md) — status per subsystem.
3. [steins-gate-blockers.md](steins-gate-blockers.md) — C1–C5, H1–H4, M1–M5,
   L1–L4.
4. [thread-04-implementation-plan.md](thread-04-implementation-plan.md) —
   Tasks 1–8.
5. [threads/03-desktop-compatibility.md](threads/03-desktop-compatibility.md)
   — report, tests run, decisions.
6. `tests/compat/README.md` — how to run tests; Windows validation procedure.

Key runtime facts (synthetic fixtures, real binary):
- `impacto -g sgps3` → `std::out_of_range` (no game definition).
- Registered + fixtures → `Expected member LoadingStar` /
  `DelusionADVPosition` aborts (sgps3 HUD profile out of date).
- VM with `UseReturnIds=false` → `Return` executes return-id bytes as `End`;
  with `true` → `00 5F` (`InstDummy`) spins forever.
- Engine segfaults in `Audio::AudioUpdate` with no audio device; use
  `ALSOFT_DRIVERS=null` headless.

## Verification performed in Thread 03
- Rebuilt Thread 02 binary in `impacto-desktop:ubuntu24`; ctest "No tests
  were found"; smoke 2/2 PASS.
- `python3 -m unittest discover -s tests/compat -v`: 27 OK, 4 skipped.
- `IMPACTO_BIN=release/ubuntu24/impacto python3 -m unittest tests.compat.test_runtime_probe -v`
  (in container): 4/4 OK — these assert the **bugs** listed above.
- GitHub Actions for this branch was not observed in-thread.

## Known Failures / Limitations
- No Steam installation, Windows host, GPU or audio device in the orb. All
  "external" facts (Steam `.mpk` names/version, Bink 2 movies, save
  location, PNG textures, 2895-glyph charset) are unverified against real
  files. Procedure to verify: `tests/compat/README.md`.
- Game profiles are not asset-free: `-g <any>` aborts without spritesheets
  (`src/profile/sprites.cpp:48`). Thread 04 Task 3 proposes a harness profile.
- Upstream `impacto.yml` still depends on CoZ infrastructure (unchanged).
- Native Debian 12/GCC 12 cannot build; use the Ubuntu container/CI.

## Architectural Decisions (Thread 03)
- Add a new game id `sghd` for the Steam release; keep `sgps3` frozen (the
  audit test pins its opcode table).
- All engine changes behind `InstructionSet::SGHD` or in `src/games/sghd/`,
  `profiles/sghd/` — upstream-compatible, no risk to other games.
- Runtime probes assert current bugs; flip assertions in the fixing commit.
- sc3ntist (unlicensed) used only as a reference for opcode names/layouts
  stored as data; sc3tools (MIT) cited for charset/game ids.
- Bink 2: prefer owner-side transcode or movie skip over writing a decoder.

## Open Questions (owner input needed)
1. MPK header bytes of the Steam archives (expect `MPK\0 00 00 02 00`).
2. Movie file locations and signatures (`BIK` vs `KB2`).
3. Startup script archive id and opcode usage counts from a script dump.
4. `system.mpk` entry ids for title/dialogue/phone sprites.

## Next Thread
Thread 04 — STEINS;GATE Desktop Implementation. **Mode: High** (bounded,
test-driven engine/profile work). Use Ultra only for Task 7a (phone protocol
reverse engineering) if the owner's script dump is available.

## Next Objective
Start with **Task 1** of `docs/thread-04-implementation-plan.md`: create
`profiles/sghd/`, register it in `gamedefinitions.lua`, add
`InstructionSet::SGHD` + `opcodetables_sghd.h` (initially a copy of sgps3),
set `UseReturnIds = true`, and make `tests/compat/test_runtime_probe.py`
pass for `sghd` with "VM reached, no `Expected member`, Return resumes at
Call+6". Then Task 2 (Dummy slots + 21 layouts) with the audit test's
`sghd` gap lists empty. Do not touch `sgps3`. Do not start iOS.

## Orb state is disposable
This orb has the `impacto-desktop:ubuntu24` image, build output in
`ci-build/ubuntu24`, binary in `release/ubuntu24/impacto`, reference clones
in `/tmp/ref/{sc3ntist,sc3tools,LanguageBarrier}`, probe scratch in
`/tmp/sgtest`, and evidence logs in `.amp/in/artifacts/`. None of it is
committed or required: rebuild per `docs/desktop-build.md`; the probes
regenerate their fixtures.
