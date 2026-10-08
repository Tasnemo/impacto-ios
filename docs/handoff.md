# Project Handoff

## Current Milestone
Thread 02 — Reproducible Desktop Build is complete. Linux compilation and
asset-free launcher startup/shutdown are verified locally and in
[GitHub CI run 37733016683](https://github.com/Tasnemo/impacto-ios/actions/runs/37733016683).
See [desktop-test-results.md](desktop-test-results.md) for actual results.
Thread 03 has **not** started. This is not proof of game compatibility.

## Repository State
- Repository: `Tasnemo/impacto-ios`; default integration branch is **master**, not
  `main`. GitHub reports it is **public** despite `workme.md` proposing private.
  No commercial assets or secrets were added; visibility was not changed.
- Thread 01 reports are committed in
  [b468d4fb](https://github.com/Tasnemo/impacto-ios/commit/b468d4fb60314344a1c3b66096b263427b87d4c6)
  and were already on `origin/master` at startup. The prior “not merged” note was stale.
- Thread 02 branch: `phase-01-desktop-baseline`, based on that commit.
- Build/workflow commit:
  [51478a26](https://github.com/Tasnemo/impacto-ios/commit/51478a26).
  Smoke logging fix and Ubuntu Docker recipe:
  [a97fb46c](https://github.com/Tasnemo/impacto-ios/commit/a97fb46c).
  Both are pushed; CI passed on `a97fb46c`. The subsequent documentation-only
  checkpoints record the reports and shipping state (CI skipped because no build
  inputs changed); obtain the exact handoff commit with
  `git log -1 --format=%H -- docs/handoff.md`.
- Thread 02 is integrated into **origin/master** by the user-authorized Ship
  request. Start the next branch from the latest `origin/master`.
- `src/`, profiles, resources and game behavior are unchanged. CMake only pins
  LibAtrac9 instead of fetching moving `master`.

## Completed Work
- Pinned upstream CMake/Ninja/vcpkg Linux build; native Ubuntu 24.04 CI and an
  Ubuntu container recipe for Debian-based orbs. No CoZ cache access required.
- Dependency installer, CLI/launcher smoke harness and GitHub desktop workflow.
- Full build, toolchain and runtime logs under `docs/threads/02-logs/`.
- Reproduction: [desktop-build.md](desktop-build.md).
  Results: [desktop-test-results.md](desktop-test-results.md).
  Milestone report: [threads/02-desktop-baseline.md](threads/02-desktop-baseline.md).

## Verification
- Ubuntu 24.04.5/GCC 13.3, CMake 3.31.10, upstream `ci-release`, target/host
  `x64-linux-ci`: built all 67 dependencies from source and compiled/installed impacto.
- Executable loaded Lua config, created 1280×720 software OpenGL window,
  compiled shaders, ran the launcher for five seconds and exited 0 through SDL quit.
- CLI missing parameter rejected with exit 1. Relocated install passed both checks.
- CTest executed: **No tests were found**. There is no upstream engine test suite.
- Workflow syntax checked with actionlint. Engine warnings-as-errors retained.
- GitHub Ubuntu 24.04 job passed configure, build/install, CTest discovery and
  both smoke checks in 23m32s; diagnostic upload and cache save also passed.

## Known Failures / Limitations
- Native Debian 12/GCC 12 fails OpenAL Soft 1.25.1 on missing `<format>`.
  Use Ubuntu 24.04/GCC 13; do not downgrade dependencies to work around it.
- First CI build passed compilation but its test harness wrongly expected console
  logging. Fixed by explicit `-lf` logs; see results for both CI runs.
- Upstream ImGui compiler and LibAtrac9 CMake install warnings remain nonfatal.
- Legacy `impacto.yml` still uses the CoZ NuGet feed. `desktop.yml` is the fork's
  independent Linux baseline; other platform jobs are not verified here.
- No game data: no game-profile initialization, audio/video playback, script
  execution, saves or SG behavior verified. `characterviewer` is **not asset-free**;
  it inherits CHLCC. Use no `-g` for the launcher. SDL dummy cannot supply OpenGL.
- Steam SG blockers B1–B5 are unchanged: movie format unverified locally,
  missing Steam profile/opcode mapping, phone/mail stubs and absent saves.

## Architectural Decisions
- Preserve the upstream architecture, default Linux features and dependency pins.
  Solve the compiler mismatch with a supported environment, not source rewrites.
- Pin LibAtrac9's current revision. Keep the upstream vcpkg baseline and overlays.
- Headless Xvfb/Mesa launcher testing needs no game assets and changes no engine API.
- Treat successful compilation, launcher startup and game compatibility as separate
  claims. No iOS or missing STEINS;GATE implementation was attempted.
- Prior ADRs remain in [decisions.md](decisions.md); SG profile/transcoding proposals
  are still proposals, not verified implementations.

## Open Questions
1. Steam SG MPK version and movie signatures (`BIK` versus `KB2`).
2. Steam SC3 opcode numbering/argument layouts versus SGPS3; phone/mail semantics.
3. Full game-profile runtime behavior, including real audio/video, saves and routes.
4. iOS renderer/SDK and Windows-driven signing questions remain deferred.

## Next Thread
Thread 03 — STEINS;GATE Desktop Compatibility.

## Recommended Mode
**Ultra**, as specified by `workme.md`, for compatibility investigation and opcode
analysis. Do not begin iOS work. Use High later for bounded implementation fixes.

## Next Objective
Read `workme.md` (lowercase filename), this handoff, the desktop reports and all
Thread 01 architecture/compatibility reports. Start from the latest `origin/master`,
reproduce the build/smoke check, then investigate original English Steam SG using
legally obtained local evidence. Request the Windows install listing, first 64
bytes of archive/movie headers and selected sc3tools output before drawing runtime
conclusions. Keep commercial assets and derivative script dumps out of git.
Prioritize missing-profile/opcode, phone/mail, save and movie blockers; update the
compatibility matrix from evidence. If no game evidence is available, record the
limitation rather than inventing gameplay success.

## Orb state is disposable
This orb has `impacto-desktop:ubuntu24`, a supervised `desktop-docker` daemon,
vcpkg at `/home/user/.local/share/impacto-tools/vcpkg`, build output at
`ci-build/ubuntu24`, and installed files at `release/ubuntu24`. These are **not**
committed and are not assumed to exist in another thread. Follow the documented
container commands; keep the vcpkg mount when rebuilding. No paid/private cache,
local game installation or conversation transcript is required for the baseline.
