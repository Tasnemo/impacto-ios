# Test Results

Append one section per thread. Record the exact command, environment, and outcome. Do not
record a test that was not executed.

## Thread 01 — 2026-10-08 — branch `phase-00-upstream-analysis`

**No builds or runtime tests were executed.** This thread was research only.

What was executed (read-only inspection, in an Amp orb, Linux x64):

| Action | Command / method | Result |
|---|---|---|
| Unshallow and inspect history | `git fetch --unshallow`; `git log` | 3122 commits; HEAD = upstream `ba51381f` + `bbe53401` (workme.md) |
| Locate SGPS3 handling | `rg -n SGPS3 src` | Only `vm.h`, `vm.cpp`, `opcodetables_sgps3.h` |
| Count stubbed SGPS3 opcodes | throwaway Python over `opcodetables_sgps3.h` + `inst_*.cpp` | 95 of 166 non-dummy entries hit a `VMStub` path (approximate; script not committed) |
| MPK version gate | read `src/io/mpkarchive.cpp` | v2.0 only |
| Test targets | `rg "add_test\|ctest\|enable_testing"` | none |
| Upstream tracker | GitHub issue CommitteeOfZero/impacto#1 | SG PS3 only: 2D gfx, sound, video |
| Steam release facts | PCGamingWiki, CoZ LanguageBarrier/sc3tools repos, nipkownix FMV project | MAGES. engine, D3D9, Bink 2 movies, `.mpk` archives, Vorbis audio, PNG/DDS |

Not done: vcpkg install, CMake configure, compile, engine launch, any asset loading.

## Thread 02 — 2026-10-08 — branch `phase-01-desktop-baseline`

Ubuntu 24.04/GCC 13.3 build and asset-free OpenGL launcher execution verified.
CLI rejection, normal launcher shutdown and relocated installation smoke checks
passed. CTest ran but found no upstream tests. Native Debian/GCC 12 failed in
OpenAL Soft on missing `<format>`; use the documented Ubuntu container.

Full commands, compiler output, CI results, failures and limitations:
[desktop-test-results.md](desktop-test-results.md).
Reproduction: [desktop-build.md](desktop-build.md).
