# Native iOS build (Thread 08)

The existing C++ engine, built as a UIKit app bundle for arm64 iOS devices.
Desktop Linux/Windows builds remain the test infrastructure
([roadmap.md](roadmap.md)); nothing here converts engine code to Swift,
Metal or a new renderer.

Scope of this first build: the app links and starts the asset-free launcher.
Audio, video, subtitles, touch mapping, game-data import and rendering
validation are later threads ([ios-transition.md](ios-transition.md)).

## What is in the tree

| Piece | Purpose |
|---|---|
| `triplets/arm64-ios.cmake` | vcpkg device triplet: `arm64`, static libraries, `iphoneos` sysroot, iOS 15.0 minimum. |
| `vcpkg-ios.json` | iOS dependency manifest: SDL3 (no Vulkan feature), Ogg/Vorbis, zlib, WebP, fmt, glm, pugixml, utfcpp, concurrentqueue, readerwriterqueue, unordered-dense, boost-circular-buffer, toml11, freetype, harfbuzz. No ffmpeg/avcpp/libass/openal/vulkan. |
| `CMakePresets.json` → `ci-release-ios` | Configure/build preset: `CMAKE_SYSTEM_NAME=iOS`, `arm64`, `iphoneos`, deployment target 15.0, triplet `arm64-ios`, manifest `vcpkg-ios.json`, `IMPACTO_DISABLE_{FFMPEG,OPENAL,LIBASS,VULKAN}=ON`, `install` target. |
| `ios/Info.plist.in` | Bundle identity, `UILaunchScreen`, landscape-only orientations, full screen, Files visibility, `SDL_FILESYSTEM_BASE_DIR_TYPE=bundle`. |
| `CMakeLists.txt` (`if (IMPACTO_IOS)`) | OpenGL ES framework instead of `FindOpenGL`, UIKit bundle properties, asset copy into the `.app`, install rules. |
| `src/renderer/opengl/window.cpp` | On iOS: native GLES only, context version 3.0 (Apple's driver stops there). |
| `src/renderer/window.{h,cpp}` | iOS is full screen like Android: no windowed sizing, `Borderless` default display mode. |
| `.github/workflows/desktop-ios.yml` | `macos-15`: pinned CMake/Ninja, pinned vcpkg, build, bundle checks, unsigned artifact. |
| `tests/compat/test_ios_build_config.py` | Asset-free tests pinning all of the above (no Apple SDK needed). |

## Bundle layout

An iOS bundle is flat; the engine expects its assets next to the executable
because `main()` changes the working directory to `SDL_GetBasePath()`:

```
Impacto.app/
  Impacto                 arm64 device executable
  Info.plist              from ios/Info.plist.in
  profiles/               engine profiles, including profiles/sghd
  shaders/                src/shaders
  resources/              fonts, icons, cursors
  basepaths.lua           basepaths.lua if present, else basepaths.lua.sample
  gamedefinitions.lua
```

Writable state (user config, log file) goes through `SDL_GetPrefPath()` to
`Application Support/Committee of Zero/Impacto/`, outside the read-only
bundle. The sample `basepaths.lua` still points `RootGamedataDir` and
`RootSavesDir` at `./gamedata` and `./saves` inside the bundle, so game data
import and save placement are Thread 10C work, not this build.

## Build it in CI

`.github/workflows/desktop-ios.yml` runs on every push to `phase-04-ios-build`
and on pull requests into `master`/`phase-03-sghd-implementation`. It uploads
`impacto-ios-arm64-<sha>` containing
`impacto-ios-arm64-unsigned-<sha>.zip` (the zipped `Impacto.app`) and
`SHA256SUMS`. The job proves the artifact is a device binary: `lipo -info`
reports `arm64` and `xcrun vtool -show-build` reports `platform IOS`. A
successful build does not install or run the app anywhere.

## Build it on a Mac

Xcode 16 or newer (Command Line Tools installed), CMake 3.31, Ninja, and the
pinned vcpkg checkout:

```bash
export VCPKG_ROOT="$HOME/.local/share/impacto-tools/vcpkg"
git clone https://github.com/microsoft/vcpkg.git "$VCPKG_ROOT"
git -C "$VCPKG_ROOT" checkout 62159a45e18f3a9ac0548628dcaf74fcb60c6ff9
"$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics

python3 -m venv "$HOME/.local/share/impacto-tools/cmake"
"$HOME/.local/share/impacto-tools/cmake/bin/pip" install cmake==3.31.10 ninja==1.13.0
export PATH="$HOME/.local/share/impacto-tools/cmake/bin:$PATH"

cmake --preset ci-release-ios
cmake --build --preset ci-release-ios      # installs release/ci-release-ios/Impacto.app
```

Change the identifier with
`-DIMPACTO_IOS_BUNDLE_IDENTIFIER=com.example.impacto` before configuring if
you sign with your own team. The build is unsigned: Ninja does not sign, and
`XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED=NO` covers the Xcode generator.

## Signing and installing (owner-side, on a Mac)

CI cannot sign: no certificates or provisioning profiles are stored in the
repository or in workflow secrets, and a free Apple ID's personal team is
tied to one Mac.

1. Package the app as an `.ipa` for the re-signing tools:

   ```bash
   mkdir -p Payload
   cp -R release/ci-release-ios/Impacto.app Payload/
   zip -qry impacto-unsigned.ipa Payload
   ```

2. **Sideloadly / AltStore / Apple Configurator** — import
   `impacto-unsigned.ipa`, choose your Apple ID, let the tool create the
   development provisioning profile and re-sign. Free-account limits apply:
   the app expires after 7 days and must be re-signed; a paid developer
   account raises that to a year and adds Wi-Fi installs.
3. **Manual signing with Xcode's account**:

   ```bash
   xcrun devicectl list devices
   codesign --force --sign "Apple Development: you@example.com (TEAMID)" \
       --timestamp=none release/ci-release-ios/Impacto.app
   xcrun devicectl device install app --device <UDID> release/ci-release-ios/Impacto.app
   ```

   The bundle identifier must match a registered App ID
   (`IMPACTO_IOS_BUNDLE_IDENTIFIER`). No special entitlements are required.
4. First launch after signing needs **Settings → General → VPN & Device
   Management → trust** for the developer certificate.

Verify what you installed with `xcrun vtool -show-build` on the device copy;
it must say `platform IOS`, `minos 15.0`, and `lipo -info` must say `arm64`.

## Running on the device

The app starts the asset-free launcher: no game data is present in the bundle,
so no game entry exists yet. Engine arguments can be supplied through an
`args.txt` beside the executable (one line, space separated), the same
mechanism desktop uses, e.g. `-g sghd -ll Info`.

The engine log is at
`Application Support/Committee of Zero/Impacto/Impacto_Log.txt` inside the
app's container. Retrieve it with Xcode's Devices window (download container),
or read it live in Console.app by filtering on the app.

## Known limits of this build

- No audio (OpenAL/FFmpeg disabled), no video playback (Bink 2 is skipped for
  STEINS;GATE anyway), no ASS subtitles. These return in the audio/video
  integration thread.
- OpenGL ES 3.0 through Apple's deprecated OpenGL ES driver; whether that is
  fast enough on device is Thread 09's question (Metal would be a rewrite).
- All Steam sheets are DXT5; iOS GPUs do not sample BC formats, so the CPU
  decoder path is the one to measure in Thread 09.
- No app icon or launch artwork (an unsigned CI artifact does not need them).
- No game-data import: the bundle is read-only and the Files-visible Documents
  directory is not wired into `basepaths.lua` yet.
