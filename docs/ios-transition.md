# iOS transition plan (prepared in Thread 07)

Desktop builds are test infrastructure for the shared engine
([roadmap.md](roadmap.md)). This page lists what must be settled on desktop
before porting, what is deferred, and the scope of the next thread
(Thread 08, native iOS ARM64 build, **Medium**).

## Status split

| Class | Items |
|---|---|
| Verified on synthetic fixtures (Linux CI) | SGHD VM and all census opcode layouts, call/return ids, flags/branching, phone item bits, save format 2 round trip, Ogg Vorbis audio path, movie skip, little-endian voice table, profile load at 1920x1080 |
| Verified against real Steam data (owner reports, no execution) | archive names/versions, script decoding of all 190 scripts (census v2: no reachable errors after the `10 3A` fix), image sizes/formats (DXT5, DDS header passes impacto's checks), LAY byte order, audio codecs, Game.exe font width table, 720p text styles, ADVBox/nametag/wait-icon rectangles |
| Implemented, not yet validated on real data | first boot and title, dialogue rendering with the Steam font, BG/character rendering, voice/BGM playback, phone item-bit polarity, system-data persistence |
| Missing | phone UI (sub-types 0x05-0x1E), movies (Bink 2), title/backlog/system/save menus, selection and system-message sprites, Steam save import |

## Must be solved on desktop before porting

Only one gate, because every later problem is cheaper to debug on desktop:

1. **One real Windows boot** of the `sghd` profile reaching the first
   dialogue line without crash, decode desync or blocking loop (owner
   procedure in [handoff.md](handoff.md) "Windows round 4"). Any crash or
   hang in that log is fixed on desktop first.

Thread 08 does not wait for this: the iOS build work is independent of game
data. Thread 09+ (rendering on device with real data) should wait for it.

## Deferred to iOS integration or later

- Sprite rectangles still unverified (selection, system message box, date,
  save/loading icons) — needs owner naming via `sghd_inspect.py regions`.
- Phone UI — separate High-mode task ([phone-protocol.md](phone-protocol.md)).
- Movies — Bink 2; decide transcode vs skip during Thread 10 (video).
- Menus (title/backlog/system/save) — SG-specific UI, after first device run.
- Steam `SAVEDATA.DAT` import — optional.

## Thread 08 milestone: native iOS ARM64 build

Gate: GitHub Actions `macos-15` job builds `impacto` for `arm64-ios`
(device) and produces an unsigned `.app`/`.ipa` artifact containing
`profiles/`, `shaders/`, `resources/`, `basepaths.lua`,
`gamedefinitions.lua`; the asset-free launcher path starts in the iOS
Simulator (arm64) or the build log proves the device binary links. Signing
and installation are documented; device installation is verified by the
owner separately (sideloading).

### Dependencies to investigate (vcpkg baseline `62159a45`)

| Dependency | iOS question |
|---|---|
| sdl3 | iOS supported by vcpkg; provides the UIKit app shell, `SDL_main`, GLES/EAGL or Metal views |
| openal-soft | CoreAudio backend on iOS; audio session category/interruption handling later (Thread 10) |
| libogg, libvorbis, zlib, fmt, glm, pugixml, utfcpp, toml11, unordered-dense, concurrentqueue, readerwriterqueue, boost-circular-buffer, freetype, harfbuzz, libwebp | expected to build as static `arm64-ios` libraries |
| ffmpeg / avcpp | heavy; movies are skipped for SG (Bink 2), so first try `IMPACTO_DISABLE_FFMPEG` |
| libass | try `IMPACTO_DISABLE_LIBASS` (subtitles unused by SG) |
| vulkan / sdl3[vulkan] | needed only if the Vulkan renderer (via MoltenVK) is chosen; otherwise drop for iOS |
| libatrac9, magic_enum (FetchContent) | plain C/C++, should build |

New files expected: `triplets/arm64-ios.cmake` (static linkage,
`VCPKG_CMAKE_SYSTEM_NAME iOS`), an iOS CMake preset, an `if(IOS)` block next
to the existing `if(APPLE)` bundle settings (Info.plist, bundle resources,
`IMPACTO_DISABLE_DX9/IMGUI/MMAP` as for Switch/Emscripten where needed).

### Platform adaptations to investigate

- **Renderer:** impacto's OpenGL path uses desktop GL or GLES3 (Android,
  Switch). On iOS, OpenGL ES 3.0 is deprecated but still shipped; the
  alternative is the existing Vulkan renderer on MoltenVK. Thread 08 only
  checks what links; the decision belongs to Thread 09 (High only if both
  fail).
- **Texture formats:** all Steam sheets are DXT5 (BC3). iOS GPUs do not
  sample BC formats in GLES; impacto has a CPU BC decoder
  (`src/texture/bcdecode.cpp`) — measure memory (a 4096x4096 sheet is 64 MB
  as RGBA) in Thread 09.
- **File system:** desktop startup changes the working directory to the
  executable; on iOS, resources live in the read-only bundle and game data /
  saves in the app's Documents directory (`basepaths.lua` per platform,
  Files-app import via `UIFileSharingEnabled`).
- **Lifecycle and input:** SDL3 app events for background/foreground, touch
  to click/advance mapping, phone-button mapping (Thread 10).
- **Threads/mmap:** keep `IMPACTO_HAVE_THREADS`; check `mmap` on iOS
  sandbox paths or disable as on Switch.

### CI infrastructure

- New workflow `desktop-ios.yml` (name to taste) on `macos-15`: Xcode
  toolchain, pinned vcpkg, `actions/cache` for the vcpkg binary cache (same
  pattern as `desktop-windows.yml`), CMake with the iOS toolchain, upload the
  unsigned app as an artifact. The upstream `impacto.yml` already builds
  `macos_arm64` with `triplets/arm64-osx-ci.cmake`; reuse its steps.
- Signing: no certificates in the repository or CI secrets unless the owner
  provides them; document AltStore/Sideloadly-style personal sideloading of
  the unsigned artifact.
