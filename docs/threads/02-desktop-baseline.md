# Thread 02 — Reproducible Desktop Build

Date: 2026-10-08. Branch: `phase-01-desktop-baseline`.
Scope: desktop environment, compilation, execution, tests, CI and handoff only.

## Outcome and evidence

The existing engine builds on Ubuntu 24.04 with GCC 13.3, using upstream
`ci-release` and `x64-linux-ci` host/target triplets. Its installed launcher
executes under Xvfb/Mesa, compiles shaders, remains alive for five seconds and
exits 0 through SDL shutdown. Missing CLI input is rejected with exit 1. The
installed directory also works after relocation within Ubuntu. No upstream
CTest tests exist; the new smoke harness is explicitly limited to the launcher.

- [Complete reproduction recipe](../desktop-build.md)
- [Test outcomes, failures, exact compiler/runtime output](../desktop-test-results.md)
- [Raw configure, build and test logs](02-logs/)
- [Repository state and next-thread requirements](../handoff.md)

The first native Debian 12 build failed because pinned OpenAL Soft needs a newer
C++ standard library (`<format>`). A digest-pinned Ubuntu tools container solves
that environment mismatch without changing engine code or dependency versions.
The first GitHub build succeeded but exposed a smoke-harness logging assumption;
explicit file logging fixed the harness. The original failed CI run is retained
in the results report, not reclassified as passing.

## Changes and decisions

- `CMakeLists.txt`: pin LibAtrac9's formerly moving `master` to the exact observed
  upstream revision. No `src/`, profile or resource edits.
- `.github/scripts/install-desktop-deps.sh`: shared apt prerequisite list, based
  on upstream Linux CI; omit Mono/NuGet and add Xvfb/Mesa for asset-free execution.
- `.github/scripts/desktop-smoke.py`: real installed executable, fresh temporary
  config, explicit log files, exit/log assertions, bounded shutdown and cleanup.
  A missing-`basepaths.lua` negative control proves it rejects broken installs.
- `.github/workflows/desktop.yml`: upstream preset, pinned CMake/vcpkg,
  fork-owned file cache, no CoZ secrets, build/CTest/smoke and diagnostic upload.
- `docker/desktop.Dockerfile`: Ubuntu tools environment for Debian-based orbs;
  source and game files are not copied into the image.
- Required desktop docs and this report; handoff and project status pointers updated.

Prior Thread 01 suggestions were corrected from source and execution:
`characterviewer` requires CHLCC data; SDL dummy cannot create GL; `--help` is not
implemented; desktop console logs default off; Thread 01 was already on master.

## Remaining limits and next milestone

No Steam game installation was available or needed for the launcher. No game
profile, VM, audio/video playback, saves, phone/mail or endings were tested.
Vulkan compiled but was not selected at runtime. No iOS development occurred.
Existing game-compatibility blockers and proposed architecture decisions remain.
The upstream multi-platform workflow still needs CoZ infrastructure; the new
Linux workflow is independent, not a claim that every inherited workflow works.

Thread 03 should use **Ultra** for original English Steam STEINS;GATE
compatibility investigation, starting from this branch (or an approved merge).
It needs legitimate game evidence, not merely this successful build. Thread 03
was not started here.
