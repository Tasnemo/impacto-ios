# Project Handoff

## Current Milestone
Thread 01 (Upstream Architecture and Feasibility) is complete. Phase 0 documentation
exists; no engine code has been changed and nothing has been built or run.

## Repository State
- Branch: `phase-00-upstream-analysis` (based on `master` at `bbe53401`, which is upstream
  CommitteeOfZero/impacto `ba51381f` + `workme.md`).
- Changes on this branch: `docs/` tree (architecture, compatibility-matrix, blockers,
  decisions, roadmap, test-results, handoff, threads/01-upstream-investigation) and a
  pointer block at the top of `README.md`.
- Not merged into `master`. Merge after review, or have Thread 02 branch from it.
- Engine source is byte-identical to upstream `ba51381f`.

## Completed Work
Research only. See `docs/threads/01-upstream-investigation.md` for the full report.
Headline facts:
- impacto: C++20, CMake 3.28 + vcpkg, SDL3 3.4.0, OpenAL, ffmpeg 7.1.2; backends GL
  (GL3.3/GLES3), Vulkan (partial), DX9; Android = shared lib + SDLActivity; no iOS code.
- STEINS;GATE support upstream = PS3 release only, "2D gfx, sound, video" (tracker #1).
  `profiles/sgps3` is a scaffold: `SaveDataType.None`, no `src/games/sgps3`, no SGPS3
  branches in `src/vm/inst_*.cpp`, `InstPhoneSG`/`InstMail` are stubs.
- Steam release (`sghd`): `.mpk` archives, SC3 `.scx`, Vorbis, PNG/DDS, **Bink 2 movies**
  (ffmpeg cannot decode Bink 2), own charset, D3D9 engine, saves `SAVEDATA.DAT`.
- No `sghd` profile exists; the Steam opcode set is unverified.
- No upstream test suite; upstream CI depends on a private CoZ NuGet vcpkg cache.

## Verification
None executed. `docs/test-results.md` lists the read-only inspections performed.

## Known Failures
Nothing is known to work. See `docs/blockers.md` B1–B9. Hard blockers for desktop
playability: Bink 2 video (B1), missing `sghd` profile/instruction set (B2), phone/mail
stubs (B3), no save system (B4).

## Architectural Decisions
`docs/decisions.md`: ADR-001 keep impacto; ADR-002 new `sghd` profile (proposed);
ADR-003 defer iOS renderer choice to Thread 05; ADR-004 Bink 2 via asset-prep transcode
(proposed); ADR-005 branch/doc discipline.

## Open Questions
1. MPK version field of Steam SG archives (expect 2.0) — needs one hexdump.
2. Movie file signatures (`BIK` vs `KB2`) and their on-disk location in the Steam install.
3. Does Steam SG share PS3 SG's opcode numbering? Needs `script.mpk` disassembly.
4. Semantics of `PhoneSG`/`Mail` opcodes as used by the scripts.
5. Is OpenGL ES still usable on iOS 26.x on the developer's device?
6. Sideloading route from Windows (AltStore / Sideloadly / paid cert).

## Next Thread
Thread 02 — Reproducible Desktop Build.

## Recommended Mode
High.

## Next Objective
On a new branch `phase-01-desktop-baseline` (from this branch or from `master` after
merge):
1. Produce a Linux x64 build in an orb: apt packages from
   `.github/workflows/impacto.yml` (ubuntu-24.04 job) / `doc/ubuntu_build.md`, vcpkg
   bootstrap, `cmake --preset ci-release` (or `Release`), build. Record exact commands,
   versions, and the full log in `docs/test-results.md`.
2. Prove execution, not just compilation: run `impacto` headless (Xvfb or
   `SDL_VIDEODRIVER=dummy`) with a profile that needs no assets (e.g. `-g characterviewer`
   or any profile with `-ll Debug`) and capture the startup log up to the first asset
   error. No game assets are needed or allowed in the repo.
3. Add a GitHub Actions Linux workflow for this fork that does not depend on the CoZ NuGet
   feed (use GitHub Actions cache / `x-gha` vcpkg binary caching) and runs the smoke
   launch.
4. Document compiler/dependency requirements in `docs/threads/02-desktop-baseline.md`,
   update `docs/handoff.md`, commit, push, stop.

In parallel the developer should prepare (on Windows, outside git) the evidence pack
described in `docs/roadmap.md` for Thread 03: install listing, first 64 bytes of every
`.mpk` and movie file, and sc3tools output for a few scripts.
