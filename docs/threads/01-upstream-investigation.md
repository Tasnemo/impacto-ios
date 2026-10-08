# Thread 01 — Upstream Architecture and Feasibility

Mode: Ultra · Type: research · Branch: `phase-00-upstream-analysis` · Date: 2026-10-08

Scope per `workme.md`: inspect impacto, determine Steam STEINS;GATE compatibility,
compare platform implementations, assess iOS feasibility, identify blockers. No code
changes; no builds.

Companion documents: `docs/architecture.md`, `docs/compatibility-matrix.md`,
`docs/blockers.md`, `docs/decisions.md`, `docs/roadmap.md`, `docs/test-results.md`.

## 1. Repository state

- Fork `Tasnemo/impacto-ios` = upstream `CommitteeOfZero/impacto` at `ba51381f`
  (2026-10-05, merge PR #539 "switch-fixes") + `bbe53401` "Create workme.md". VERSION
  `0.10.8`.
- No fork-specific code. No `docs/` existed before this thread. The checkout was shallow
  and was unshallowed to read history.

## 2. Engine subsystems (evidence in `docs/architecture.md`)

Key facts for the next threads:

- **Entry/lifecycle:** `src/main.cpp` with SDL3; profile chosen with `-g <profile>`;
  logging via `-ll <level> -lc <channels>` (`doc/getting_started.md`). `VM` log channel +
  `VMStub` is the tool for measuring script coverage.
- **Configuration:** `basepaths.lua` (from `basepaths.lua.sample`), `gamedefinitions.lua`,
  `userconfig.toml`. `gamedefinitions.lua` lists chlcc, cclcc, mo6tw, darling, dash, rne
  and the viewers — **not sgps3**, so SG PS3 is launchable only by explicit `-g sgps3`.
- **VFS:** archives are magic-sniffed, so mixing CPK/MPK/folders in one profile is fine.
  MPK reader: `src/io/mpkarchive.cpp` — header `MPK\0`, u16 minor, u16 major; **rejects
  anything but 2.0**; TOC at 0x40, 0x100-byte entries, 224-byte names.
- **VM:** `src/vm/vm.cpp:116-119` binds `InstructionSet::SGPS3` to
  `OpcodeTable{System,Graph,User1}_SGPS3`. No instruction body checks SGPS3.
- **Renderer:** `BaseRenderer` (`src/renderer/renderer.h`); GL backend emits
  `#version 330` or `#version 300 es` (`opengl/shader.cpp:23-27`); context fallback chain
  in `opengl/window.cpp:60-110` (desktop core → desktop GLES → native GLES).
- **Audio:** OpenAL only (`src/audio/openal/`). Vorbis decoder present.
- **Video:** ffmpeg via avcpp; hw decoding (`av_hwdevice_ctx_create`), Android
  `mediacodec` branch (`src/video/ffmpegplayer.cpp`). Decodes only what ffmpeg decodes.
- **Save data:** `src/data/savesystem*.cpp`; implementations for CHLCC, CCLCC, MO6TW.

## 3. Build system and dependencies

- CMake 3.28 + vcpkg manifest. Presets: `Release`, `Debug`, `ci-release`,
  `ci-release-android`, `ci-release-switch`.
- Linux apt prerequisites are enumerated in `.github/workflows/impacto.yml` (ubuntu-24.04
  job) and `doc/ubuntu_build.md`; Thread 02 should copy that list verbatim.
- CI uses a private CoZ NuGet vcpkg cache → must be replaced (B6).
- No tests (B7).

## 4. Platform implementations compared

| | Windows | Linux | macOS | Android | Switch | iOS |
|---|---|---|---|---|---|---|
| Binary | exe | exe | `MACOSX_BUNDLE` | `libimpacto.so` + `SDLActivity` | NRO | — |
| Graphics | GL / DX9 / Vulkan | GL / Vulkan | GL (4.1 compat) | GLES3 + EGL | GLES3 | — |
| Asset access | paths in `basepaths.lua` | same | same | SAF folder picker; copies `resources/`, `profiles/`, `gamedefinitions.lua` to app external dir on first run | SD | — |
| Video hw decode | ffmpeg hwaccel | same | same | mediacodec | sw | — |
| Platform-specific src | `#ifdef _WIN32` in ~6 files | — | `__APPLE__` in `window.cpp`, `log.cpp` | `__ANDROID__` in `main.cpp`, `ffmpegplayer.cpp`, `filemeta.cpp` | `__SWITCH__` | — |

The Android shell (`android/app/src/main/java/.../ImpactoActivity.java`, ~300 lines) is
the template for an iOS shell: SDL app entry, one-time copy of engine resources into a
writable location, user-chosen game-data directory, and GLES3 context.

## 5. STEINS;GATE compatibility assessment

### 5.1 What upstream actually supports
- Tracker issue #1: "Steins;Gate (English PS3 version only): 2D graphics display, Sound
  playback, Video playback". Nothing about progression, menus, saves.
- `profiles/sgps3/` added 2021-05-28 (`24eef632`, "Initial Steins;Gate PS3 version
  support … just because it took less effort"). CPK mounts (`SCRIPT.CPK`,
  `SYSTEM_US.CPK`, `BGM/SE/VOICE/BG/CHARA/MASK/MOVIE.CPK`), 1280x720,
  `LayFileBigEndian=true`, `SaveDataType.None`, `systemmenu.lua` include commented out.
- `opcodetables_sgps3.h` vs `opcodetables_darling.h`: ~4 differing entries; retains
  `InstTwipo` (10 39) and `InstUnk103A` (10 3A) which are Darling-specific. 95/166
  non-dummy entries reach a `VMStub` path. `InstPhoneSG` (10 37) and `InstMail` are stubs.

### 5.2 What the Steam release is (external evidence, not yet inspected locally)
| Fact | Source |
|---|---|
| MAGES. engine port (internal name SGHD), D3D9, 32-bit, max 1920x1080, Bink Video 2.5.13.0 | PCGamingWiki |
| Saves: `%USERPROFILE%\Documents\My Games\mages_steam\STEINS;GATE\eng\SAVEDATA.DAT`, 80 slots + 48 quick | PCGamingWiki |
| `USRDIR/`: `bg.mpk bgm.mpk chara.mpk manual.mpk mask.mpk mgsshader.mpk script.mpk se.mpk shader.mpk system.mpk voice.mpk` | rdavisau/sg-unpack README, CoZ LanguageBarrier file redirection |
| Audio Ogg Vorbis; textures PNG + `.lay` / DDS; scripts SC3 `.scx` with game id `sghd` and its own `charset.utf8` | CoZ sc3tools |
| Movies encoded with **Bink 2** | nipkownix HQ FMV project |

### 5.3 Gap list (desktop)
1. No `sghd` profile / charset / resources.
2. Instruction set unverified; opcode tables likely need real RE from `script.mpk`.
3. Phone/mail stubs.
4. Save system absent.
5. Bink 2 video undecodable by ffmpeg.
6. MPK version unverified (one hexdump).
7. UI layouts (`profiles/sgps3/hud/*.lua`) are PS3 sprite coordinates and may not match
   Steam `system.mpk` textures.

Conclusion: **STEINS;GATE Steam is not playable in impacto today, and the PS3 profile
provides only a scaffold.** Desktop compatibility is the critical path; iOS porting is
secondary and comparatively well-trodden.

## 6. iOS feasibility

Assessment only; nothing attempted.

**Favourable**
- SDL3 (3.4.0 in `vcpkg.json`) supports iOS: UIKit lifecycle, touch, GL ES and Metal
  views. SDL's iOS main wrapper replaces `main()`; impacto already lets SDL own the entry
  point on Android.
- Engine platform surface is ~15 files; most are logging/path helpers.
- GL backend already produces GLES 3.0 shaders and runs on Android/Switch.
- vcpkg has an `arm64-ios` community triplet; ffmpeg, openal-soft, libogg/vorbis,
  freetype, harfbuzz, zlib, libwebp, fmt, glm have iOS ports (unverified in this project).
- C++20 compiles natively with Apple clang; `mio` mmap works on iOS.
- Android's "copy `resources/` + `profiles/` to writable dir, user picks data dir" maps
  directly to iOS "bundle resources + Files-app import into Documents".

**Risks**
- OpenGL ES is deprecated on iOS (since 13). It still exists on iOS 18; status on iOS 26.x
  must be checked on hardware. Fallbacks: ANGLE (GLES→Metal), MoltenVK (needs the
  incomplete Vulkan backend to be finished), or a Metal backend behind `BaseRenderer`.
- Bink 2 (B1) also applies on iOS; VideoToolbox hw decode would work for H.264/HEVC after
  transcoding.
- `IMPACTO_DISABLE_IMGUI` should be set for iOS (ImGui GL3 backend may still work).
- libass on iOS via vcpkg is less commonly exercised; it is optional
  (`IMPACTO_DISABLE_LIBASS`).
- Signing/sideloading from Windows: AltStore/Sideloadly with a free Apple ID (7-day
  profiles, 3-app limit) or a paid developer cert. The macOS GitHub runner can produce an
  unsigned or ad-hoc `.ipa`; signing on the runner needs the cert as a secret. Untested.
- No KVM in orbs: iOS simulators are not available in Amp orbs; only GitHub Actions macOS
  runners can run simulators, and physical-device tests need the developer.

**Verdict:** feasible. The iOS shell is estimated at the same order of effort as the
existing Android shell plus a renderer decision; the game-compatibility work (§5.3) is
larger and gates everything.

## 7. Desktop testing plan (input to Threads 02–03)

1. Thread 02 (High): Linux build in an orb and in GitHub Actions. Deliver: apt + vcpkg
   steps, build log, `impacto --help`-style or headless launch proof (SDL dummy video
   driver / Xvfb), replacement binary cache, smoke-test job. No game assets needed.
2. Thread 03 (Ultra): with the developer's evidence pack (listing, hexdumps, sc3tools
   disassembly), decide MPK/Bink/opcode questions; write `profiles/sghd`; boot the title
   screen in Xvfb inside an orb only if the developer is willing to upload the minimal
   archives (`system.mpk`, `script.mpk`) to the session — never to git.
3. Thread 04 (High): implement VM/phone/mail/saves until a first route is playable on
   Linux.

## 8. Decisions made on the user's behalf (veto here)

- Branch name `phase-00-upstream-analysis` as suggested by `workme.md`.
- Treated "push if authorized" as authorization to push this branch (not to merge).
- Recommended a new `sghd` profile instead of mutating `sgps3` (ADR-002).
- Added a short pointer block to `README.md` rather than replacing upstream README text.
