# Technical Blockers

Ordered by severity. Each entry records what is known, how it was established, and which
thread owns resolution. "Verified" means observed in this project; otherwise the source is
named.

## B1 — Steam SG movies are Bink 2; impacto cannot decode them
- **Evidence:** nipkownix "Steins;Gate Steam – HQ FMV Project" states the Steam videos were
  encoded with Bink 2 and that only Bink 1 is freely encodable. PCGamingWiki lists Bink
  Video 2.5.13.0 for the Steam build. ffmpeg's `bink` decoder supports the `BIK` (Bink 1)
  container revisions only; `KB2` (Bink 2) is not implemented. impacto's only video path is
  ffmpeg (`src/video/ffmpegplayer.cpp`).
- **Not yet verified:** the actual file signatures of the shipped movies (Thread 03 must
  hexdump them).
- **Options:** (a) require users to transcode movies with the RAD tools during asset
  packaging on Windows (legal since they own the files; adds a tool step); (b) use the
  PS3-sourced Bink 1 replacements from the FMV project where they exist (not all videos);
  (c) implement a Bink 2 decoder (reverse engineering, large effort, licensing risk).
  Decision deferred to Thread 03/04.
- **Owner:** Thread 03 (verify), Thread 04 (implement chosen option).

## B2 — No Steam SG (`sghd`) profile, instruction set, or charset
- **Evidence (source-level):** `profiles/` has `sgps3` only; `opcodetables_sgps3.h` is a
  near-copy of `opcodetables_darling.h`; no `InstructionSet::SGPS3` branches in
  `src/vm/inst_*.cpp`; sc3tools maintains a separate `sghd` charset.
- **Risk:** the Steam build may use a different opcode numbering/argument layout from PS3.
  Until the scripts are disassembled against a candidate table, no story progression can be
  assumed.
- **Owner:** Thread 03 (RE with real files), Thread 04 (implement).

## B3 — Phone trigger and mail instructions are stubs
- **Evidence:** `src/vm/inst_gamespecific.cpp:688` (`InstPhoneSG`) and `:765` (`InstMail`)
  only log `VMStub`. The phone UI is the core branching mechanic of STEINS;GATE; its
  textures/layouts in `system.mpk` are unmapped.
- **Owner:** Thread 03 (document expected behaviour from script usage), Thread 04.

## B4 — No save system for SG
- **Evidence:** `profiles/sgps3/savedata.lua` → `SaveDataType.None`; `src/data/` save
  types are CHLCC/CCLCC/MO6TW. The Steam format (`SAVEDATA.DAT`, 80 + 48 slots) is only
  described externally (PCGamingWiki) and not implemented.
- **Owner:** Thread 04.

## B5 — MPK version of the Steam archives unverified
- **Evidence:** `MpkArchive::Create` rejects anything but 2.0 (`src/io/mpkarchive.cpp:64`).
  Chaos;Child Steam MPKs load, and sg-unpack uses the same TOC layout for SG, so 2.0 is
  likely — but unverified.
- **Owner:** Thread 03 (one hexdump resolves it).

## B6 — Upstream CI depends on a private vcpkg binary cache
- **Evidence:** `.github/workflows/impacto.yml:105-106,158` reads
  `nuget.pkg.github.com/committeeofzero`. This fork cannot authenticate; cold vcpkg builds
  of ffmpeg + harfbuzz + others on a GitHub runner are slow (upstream caches for a reason).
- **Owner:** Thread 02 (switch to GitHub Actions cache or `x-gha` binary caching).
- **Thread 02 resolution (Linux):** added independent `desktop.yml`, pinned
  vcpkg and a files cache backed by `actions/cache`. Cold local build used no
  binary cache. Legacy multi-platform `impacto.yml` remains unchanged.

## B7 — No upstream automated tests
- **Evidence:** no `add_test`/`ctest` in `CMakeLists.txt` or workflows. "Run upstream
  tests" in Thread 02 reduces to build + headless/`--help` style smoke execution unless
  tests are added.
- **Owner:** Thread 02.
- **Thread 02 update:** CTest confirmed no tests. Added CLI rejection and real
  Xvfb/Mesa launcher startup/shutdown smoke checks. `--help` is not implemented
  upstream and is not a valid test. Gameplay regression coverage is still absent.

## B8 — iOS graphics API choice (deferred, not yet blocking)
- OpenGL ES is deprecated on iOS since 13 but still ships; whether it remains on iOS 26.x
  must be checked on the device. Alternatives: Vulkan backend via MoltenVK (upstream Vulkan
  backend has 12 of 27 shader pairs — incomplete), ANGLE-on-Metal, or a Metal backend.
- **Owner:** Thread 05.

## B9 — iOS signing and sideloading from a Windows-only workflow (deferred)
- A GitHub Actions macOS runner can build an `.ipa`, but signing needs an Apple ID
  (free 7-day profiles) or a paid developer certificate; install from Windows needs
  AltStore/Sideloadly or similar. None of this has been tried.
- **Owner:** Thread 06.

## Not blockers (ruled out this thread)
- SDL3 abstracts windowing/input/GL context creation; iOS is an SDL3 tier platform.
- Audio formats of the Steam release (Ogg Vorbis) are supported by `vorbisaudiostream.cpp`.
- Texture formats (PNG/DDS) are supported.
- `mio` mmap (`IMPACTO_DISABLE_MMAP` exists as fallback) is not a problem on iOS.
