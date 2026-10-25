# Thread 08 — native iOS ARM64 build and app shell (Medium)

Branch `phase-04-ios-build`, 2026-10-25. First Phase C thread
([roadmap.md](../roadmap.md), `workme.md` 15): compile the existing C++
engine as a native iOS app instead of porting or rewriting it. Desktop
builds remain the functional test beds.

Input: `workme.md` 15 and the iOS transition plan
([ios-transition.md](../ios-transition.md)). No game data, Apple
certificate or macOS machine was available to this thread; the macOS
runner is the build environment, as planned.

## What was built

| Piece | Detail |
|---|---|
| Toolchain | `triplets/arm64-ios.cmake`: vcpkg device triplet, `arm64`, static libraries, `iphoneos` sysroot, iOS 15.0 minimum. It shadows vcpkg's community `arm64-ios` triplet, which pins neither the sysroot nor the minimum OS. |
| Dependencies | `ios/vcpkg.json` (`VCPKG_MANIFEST_DIR=ios`): SDL3 3.4.0 (no Vulkan feature), Ogg/Vorbis, zlib, WebP, fmt, glm, pugixml, utfcpp, concurrentqueue, readerwriterqueue, unordered-dense, boost-circular-buffer, toml11, freetype, harfbuzz. Same vcpkg baseline as desktop. A separate manifest, not platform conditions in `vcpkg.json`, because vcpkg installs every manifest entry regardless of the CMake options. |
| Configure | `CMakePresets.json` → `ci-release-ios`: `CMAKE_SYSTEM_NAME=iOS`, `arm64`, `iphoneos`, deployment target 15.0, `VCPKG_TARGET_TRIPLET=arm64-ios`, `VCPKG_MANIFEST_DIR=${sourceDir}/ios`, `IMPACTO_DISABLE_{FFMPEG,OPENAL,LIBASS,VULKAN}=ON`, `install` target into `release/ci-release-ios`. |
| CMake | `IMPACTO_IOS` block: static linkage; ffmpeg/OpenAL/libass/Vulkan disabled for this build; `OpenGLES` framework instead of `FindOpenGL` (which does not resolve the iOS SDK); UIKit bundle with a generated `ios/Info.plist`; assets copied into the `.app` on every build and installed inside the bundle; iOS-specific install branch so assets do not also land next to it. |
| App shell | No new Objective-C++; SDL3 already provides the UIKit entry point, and the engine's existing `SDL_GetBasePath()` + `current_path()` does the right thing because an iOS bundle is flat. `IMPACTO_IOS` additions are limited to: full-screen window handling (like Android), `Borderless` default display mode, native-GLES-only context creation, and a GLES **3.0** request (Apple's driver fails any higher version). Info.plist declares `SDL_FILESYSTEM_BASE_DIR_TYPE=bundle`, so `SDL_GetBasePath()` is the `.app` directory the assets are copied to. |
| CI | `.github/workflows/desktop-ios.yml` (`macos-15`, pinned CMake 3.31.10/Ninja/vcpkg). Runs the asset-free unit tests, configures/builds/installs with `ci-release-ios`, then checks the artifact really is a device build (`lipo -info` = arm64, `xcrun vtool -show-build` = platform IOS, `plutil -lint`) and uploads `impacto-ios-arm64-<sha>` with the zipped unsigned `Impacto.app` and its SHA-256. |
| Signing | [ios-build.md](../ios-build.md): no certificates or secrets in the repository; owner-side re-signing (Sideloadly/AltStore or `codesign` + `devicectl`), free-account 7-day expiry, bundle identifier override. |
| Tests | `tests/compat/test_ios_build_config.py`: 30 asset-free assertions pinning the triplet, manifest, preset, generated plist, CMake wiring (bundle root assets, OpenGLES framework, iOS-only install) and workflow. `python3 -m unittest discover -s tests/compat` → 178 tests, OK (37 runtime probes skipped without `IMPACTO_BIN`). |

## Deliberate limits

- **Audio, video and subtitles are off in this build.** `ffmpegaudioplayer.cpp`
  is compiled with the OpenAL group and needs avcpp/FFmpeg, so enabling audio
  means porting FFmpeg or splitting that file; movie playback is Bink 2 and
  skipped for STEINS;GATE anyway. Thread 10A decides this.
- **Vulkan is off.** MoltenVK was not attempted. Thread 09 compares the
  existing GLES3 renderer with a Metal path on device.
- **No app icon, launch artwork or asset catalogue.** An unsigned CI
  artifact does not need them; they belong with release packaging.
- **No game-data import.** The bundle is read-only; `basepaths.lua`
  (the sample, unless the owner has one) still points `RootGamedataDir` and
  `RootSavesDir` inside it. Files-app import, Documents storage and save
  placement are Thread 10C.
- **No touch mapping.** The launcher receives raw SDL finger events; play
  input is Thread 10B.

## Verification

- **Local (this orb):** `python3 -m unittest discover -s tests/compat` →
  178 tests OK (37 probes skipped, no engine binary built here);
  `cmake --list-presets` parses the new configure/build presets with CMake
  3.31.10; the workflow file parses as YAML; `clang-format --dry-run
  --Werror` is clean on the three changed C++ files.
- **CI (macOS):** see [handoff.md](../handoff.md) "CI" — the run result,
  artifact name and any failure log.
- **Not verified anywhere yet:** installing on a physical device, launching
  in the simulator, and anything that needs STEINS;GATE data. The app's
  first launch, launcher screen and log retrieval are the owner's
  side-loading step ([ios-build.md](../ios-build.md)).

## Status split

- **Synthetic-verified:** the build configuration itself (triplet, manifest,
  preset, plist, bundle assembly, asset-free test suite).
- **CI-verified:** the device arm64 app links and is packaged.
- **Needs the owner's Mac + iPhone:** signing, installation, first launch,
  reading `Impacto_Log.txt`.
