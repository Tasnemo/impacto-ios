# Project Handoff

## Current Milestone
Thread 08 — native iOS ARM64 build and minimal app shell (Medium), branch
`phase-04-ios-build`. The existing C++ engine now has an iOS build path:
static `arm64-ios` vcpkg triplet, iOS-only dependency manifest,
`ci-release-ios` CMake preset, UIKit bundle packaging and a `macos-15`
workflow that builds, bundle-checks and uploads the unsigned `Impacto.app`.
Audio, video, subtitles, Vulkan and touch mapping stay off for this build.
Report: [threads/08-ios-build.md](threads/08-ios-build.md). Build, artifact
and signing details: [ios-build.md](ios-build.md).
Previous milestone: Thread 07c title menu
([threads/07c-title-menu.md](threads/07c-title-menu.md)).
Next major milestone: **Thread 09 — iOS rendering (Medium)**.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Thread 07b head (`4eabb721`); Threads
  04–08 on `phase-04-ios-build`, branched from `phase-03-sghd-implementation`
  (`dd20ec31`, includes the merged Thread 07c title menu and the Steam
  background-control fix). Thread 07c/08 are **not merged into `master`**.
- New in Thread 08: `triplets/arm64-ios.cmake`, `ios/vcpkg.json`,
  `ios/Info.plist.in`, `.github/workflows/desktop-ios.yml`,
  `tests/compat/test_ios_build_config.py`, `docs/ios-build.md`.
- No commercial assets, script dumps, private reports, logs, screenshots,
  certificates or secrets are committed.

## Completed Work (Thread 08)
- Toolchain/dependencies: device triplet (static, `iphoneos`, iOS 15.0) and
  a manifest without ffmpeg/avcpp/libass/OpenAL/Vulkan (vcpkg installs every
  manifest entry regardless of CMake options, so a separate manifest was
  needed).
- CMake: `IMPACTO_IOS` detection before `project()`; the macOS deployment
  default no longer overrides an explicitly set target; `OpenGLES` framework
  instead of `FindOpenGL`; `IMPACTO_DISABLE_{FFMPEG,OPENAL,LIBASS,VULKAN}`;
  flat bundle with generated `ios/Info.plist`, assets copied to the `.app`
  root on build and installed inside the bundle only.
- Engine: no new Objective-C++. `src/main.cpp`'s existing
  `SDL_GetBasePath()` working-directory change is correct for a flat bundle;
  the iOS-specific code is full-screen handling, `Borderless` default display
  mode, native-GLES-only context creation and a GLES 3.0 request (Apple's
  driver rejects 3.2).
- CI: `desktop-ios.yml` (macos-15) — unit tests, configure/build/install,
  bundle checks (`lipo`, `vtool -show-build` platform IOS, `plutil -lint`),
  unsigned zip artifact + SHA-256, diagnostics on failure.
- Signing/sideloading documented; no repository secrets, no certificates.

## Verification
- `python3 -m unittest discover -s tests/compat` → 178 tests OK
  (37 runtime probes skipped: no engine binary built in this orb).
  30 of them are the new asset-free iOS build-configuration tests.
- `cmake --list-presets` (CMake 3.31.10) lists `ci-release-ios` for
  configure and build; `.github/workflows/desktop-ios.yml` parses as YAML.
- `clang-format --dry-run --Werror` clean on
  `src/renderer/opengl/window.cpp`, `src/renderer/window.cpp`,
  `src/renderer/window.h`.
- CI: see "CI" below.

## Status split
- **CI-verified:** the iOS build configuration and the unsigned arm64 device
  app bundle (see "CI").
- **Not verified:** app launch (simulator or device), signing, installation,
  rendering, audio, input, game data. Those are Threads 09–11 and the
  owner's side-loading step.
- **Missing on purpose (this build):** audio (needs FFmpeg or a split
  `ffmpegaudioplayer`), video, ASS subtitles, Vulkan/Metal, touch mapping,
  game-data import, app icon/launch artwork.

## Blocker — owner action: install and first launch (optional, short)
On a Mac with Xcode 16+ (see [ios-build.md](ios-build.md)):
1. Download the `impacto-ios-arm64-<sha>` artifact of the latest green
   "iOS ARM64" run, unzip, and sign/install it (Sideloadly/AltStore or
   `codesign` + `xcrun devicectl device install app`). Bundle identifier:
   `com.committeeofzero.impacto` unless overridden at configure time.
2. Launch it once on the iPhone. Expected: the asset-free launcher (empty
   game list) and no crash. Report one line on what is visible.
3. Retrieve `Application Support/Committee of Zero/Impacto/Impacto_Log.txt`
   from the app container (Xcode → Devices → Download Container) and share
   the last ~40 lines privately if it did not start.
No game data is needed for this step; importing STEINS;GATE is Thread 10C/11A.

## Architectural Decisions
ADR-007…010 unchanged. Thread 07: desktop is test infrastructure; inherited
UI from other titles is removed rather than scaled. Thread 07b: an SGHD
instruction whose engine UI does not exist yet must never wait for it.
Thread 07c: SGHD script variables follow the common layout where the scripts
prove it; engine menus report decisions through the scripts' own flags.
Thread 08: the iOS port reuses the C++ engine, SDL3's UIKit shell and the
existing GLES-capable OpenGL renderer; the first iOS build disables what it
cannot link instead of porting it, and each disabled subsystem returns in its
own thread. Flat iOS bundle, assets at the `.app` root, `IMPACTO_IOS` guards
only where a platform difference actually exists.

## Next Thread
Thread 09 — iOS rendering (Medium; High only if GLES proves unusable on
device). Gate: the existing GLES3 renderer draws a synthetic scene on device
(or the fallback is decided). Start from `phase-04-ios-build`. Inputs:
[ios-transition.md](ios-transition.md), [ios-build.md](ios-build.md).
Also open, in parallel: applying Windows round 6 (title pass, TITLE_CHIP
region names) — [threads/07c-title-menu.md](threads/07c-title-menu.md);
phone UI stays a separate High task.

### Continuation prompt
> Read `workme.md` (sections 4, 16), `docs/handoff.md`,
> `docs/roadmap.md`, `docs/ios-build.md` and
> `docs/threads/08-ios-build.md`. Start from `phase-04-ios-build` (create a
> new branch and record it in the handoff). Goal: get the existing GLES3
> renderer to draw an asset-free synthetic scene in the iOS build (simulator
> if possible on the macOS runner, otherwise the device path plus CPU-side
> checks), measure the DXT5→RGBA CPU decode path, and document what a Metal
> fallback would cost. Keep Linux/Windows CI and `tests/compat` green. No
> Metal rewrite without a demonstrated blocker. Commit, push, update handoff.

## Orb state is disposable
This orb had no Docker access and no engine build; only Python and a pip
CMake/Ninja/clang-format install in `/tmp/cmaketools`. Nothing committed.
Build per [desktop-build.md](desktop-build.md) (Linux) or
[ios-build.md](ios-build.md) (iOS).

## CI
Thread 08 commit `41717895` on `phase-04-ios-build`:
- iOS ARM64 [run 40218497731](https://github.com/Tasnemo/impacto-ios/actions/runs/40218497731)
  — see the run for the result (result is recorded in the thread report once
  known).
- Desktop Linux/Windows are not triggered by this branch; they still run on
  `phase-03-sghd-implementation` and pull requests.
