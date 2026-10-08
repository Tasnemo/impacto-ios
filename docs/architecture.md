# impacto Engine Architecture (as inherited from upstream)

Evidence base: upstream CommitteeOfZero/impacto at commit `ba51381f` (merge of PR #539,
2026-10-05), VERSION `0.10.8`. All paths are relative to the repository root. Line numbers
are from that commit. Nothing in this document has been verified by building or running the
engine; see `docs/test-results.md`.

## 1. Overview

impacto is a C++20 reimplementation of the MAGES. visual novel engine. It is driven by:

- a **Lua game profile** (`profiles/<game>/*.lua`) that declares archive mounts, the VM
  instruction set, screen size, charsets, fonts, sprites and menu layouts;
- the game's own **SC3 bytecode scripts** executed by an in-engine VM;
- the game's original **assets** (textures, audio, video) read through a VFS layer.

The engine is one executable (`impacto`) on desktop, a shared library loaded by an SDL
Java activity on Android, and a `MACOSX_BUNDLE` on macOS (`CMakeLists.txt:1271-1295`).

```diagram
┌────────────────────────────────────────────────────────────────────┐
│ main.cpp  (SDL3 app lifecycle, CLI args, window + renderer create) │
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼───────────────┐   ┌──────────────────────────────┐
│ profile/  (Lua loader,        │   │ game.cpp (frame loop,        │
│  minilua; reads profiles/)    │──▶│  Update/Render dispatch)     │
└───────────────────────────────┘   └──────┬───────────┬───────────┘
                                           │           │
             ┌─────────────────────────────▼──┐  ┌─────▼──────────────────┐
             │ vm/  SC3 VM                     │  │ ui/, hud/, games/<p>/  │
             │  opcodetables_<set>.h           │  │  menus, dialogue, tips │
             │  inst_*.cpp (instruction impls) │  └─────┬──────────────────┘
             └──────┬──────────────────────────┘        │
                    │                                   │
┌───────────────────▼──────────┐  ┌─────────────────────▼──────────────┐
│ io/  VFS + archive readers   │  │ renderer/  BaseRenderer            │
│  cpk, mpk, afs, lnk4, folder │  │  opengl/ (GL3.3 core | GLES3)      │
│  mio mmap streams            │  │  vulkan/ (partial)  dx9/ (Windows) │
└───────────────────┬──────────┘  └────────────────────────────────────┘
                    │
   ┌────────────────┼───────────────────────────┐
┌──▼───────────┐ ┌──▼──────────────┐ ┌──────────▼───────────────┐
│ texture/     │ │ audio/ (OpenAL) │ │ video/ (ffmpeg + avcpp)  │
│ bc/dds/gxt/  │ │ adx/at9/hca/    │ │ sw + hw decode, YUV/NV12 │
│ bntx/webp/   │ │ vorbis/ffmpeg   │ │ upload to renderer       │
│ stbi         │ └─────────────────┘ └──────────────────────────┘
└──────────────┘
```

## 2. Source tree

| Directory | Responsibility | Notes |
|---|---|---|
| `src/main.cpp` | Process entry, SDL3 init, CLI parsing (`-g`, `-ll`, `-lc`, …), window/renderer creation | Platform `#ifdef`s live here |
| `src/game.cpp`, `src/game.h` | Main loop, feature gating (`GameFeature.*` flags from profile) | |
| `src/profile/` | Lua profile loader (vendored `minilua`), typed accessors for every profile table | `profile/games/<p>/` holds per-game menu/profile parsers |
| `src/vm/` | SC3 VM: threads, script buffers, expression evaluator, instruction tables | ~8k LOC; one `opcodetables_<set>.h` per `InstructionSet` enum value (`src/vm/vm.h:15-24`: RNE, Darling, CHLCC, MO6TW, MO7, Dash, CC, SGPS3, MO8, CHN) |
| `src/io/` | VFS with magic-sniffed archive drivers: CPK (`cpkarchive.cpp`), MPK (`mpkarchive.cpp`), AFS, LNK4, text archives, plain folders; mmap via `mio` | `MpkArchive::Create` accepts only MPK **2.0** (`src/io/mpkarchive.cpp:64-67`, `// TODO support v1`) |
| `src/renderer/` | `BaseRenderer` abstract interface (`renderer.h`); backends `opengl/`, `vulkan/`, `dx9/`; `3d/` character model renderer | GL shader header selects `#version 330` or `#version 300 es` at runtime (`src/renderer/opengl/shader.cpp:23-27`) |
| `src/audio/` | `AudioSystem` + channels; OpenAL backend (`audio/openal/`); stream decoders ADX, ATRAC9 (LibAtrac9), HCA (clHCA), Vorbis, ffmpeg | OpenAL is the only backend |
| `src/video/` | `VideoSystem` → `FFmpegPlayer`; decode threads, A/V clock, hw-decode via `av_hwdevice_ctx_create`, Android `mediacodec` special-case | Decodes whatever the linked ffmpeg build supports |
| `src/texture/` | Texture loaders: BC (squish), DDS, GXT (Vita), BNTX (Switch), plain, stbi (PNG), WebP | |
| `src/text/`, `src/ui/`, `src/hud/` | Text layout (freetype/harfbuzz/libass), generic widgets, HUD elements | |
| `src/games/<profile>/` | Game-specific menu/UI code: `cc`, `cclcc`, `chlcc`, `darling`, `dash`, `mo6tw`, `mo8`, `rne` | **No `sgps3` directory** |
| `src/data/` | Save system, tips system, achievements | Save types implemented: CHLCC, CCLCC, MO6TW only |
| `profiles/` | Lua profiles: cc, cclcc, chlcc, chn, common, darling, dash, mo6tw, mo7, mo8, rne, sgps3, viewers | |
| `resources/` | Engine-supplied icons, charsets, shaders, fonts per profile | |
| `vendor/` | clHCA, glad, imgui_custom, minilua, mio, mspack, pcg, squish, vma | |
| `android/` | Gradle project; `ImpactoActivity.java` extends `SDLActivity` | Only mobile platform today |
| `macos/` | `Impacto.plist.in` for the bundle | No iOS |
| `windows/`, `docker/`, `portfiles*/`, `triplets/` | Windows resources, Switch docker build, custom vcpkg ports/triplets | |

## 3. Build system

- CMake ≥ 3.28, vcpkg manifest mode (`vcpkg.json`, `vcpkg-configuration.json`), presets in
  `CMakePresets.json`: `Release`, `Debug`, `ci-release`, `ci-release-android`,
  `ci-release-switch`.
- FetchContent: LibAtrac9, magic_enum, ImGui.
- Feature switches (all `CMakeLists.txt`): `IMPACTO_DISABLE_VULKAN`, `_DX9`, `_MMAP`,
  `_IMGUI`, `_OPENAL`, `_FFMPEG`, `_LIBASS`, `_MSPACK`, `_OPENGL`.
- Platform branches: `APPLE` → `CMAKE_OSX_DEPLOYMENT_TARGET 11.0` (line 11-12) and
  `MACOSX_BUNDLE` (1274-1295); `ANDROID` → `add_library(impacto SHARED …)` (1271-1272),
  static deps, GLES3 + EGL linking (904-910), ffmpeg mediacodec (1193); `NX` → Switch.
- Nothing references iOS, `CMAKE_SYSTEM_NAME iOS`, or an `arm64-ios` triplet.
- Upstream CI (`.github/workflows/impacto.yml`): windows-2025, ubuntu-24.04, macos-15
  (arm64 + intel), Android NDK (minSdk 28), Switch via docker. It relies on a **private
  CommitteeOfZero NuGet vcpkg binary cache** (`impacto.yml:105-106,158`), which this fork
  cannot read; CI must be re-pointed (Thread 02).
- There is **no test target**: no `add_test`, `enable_testing`, or `ctest` anywhere in
  `CMakeLists.txt` or the workflows.

## 4. Dependencies (`vcpkg.json` baseline `62159a45…`, plus vendored)

| Dependency | Role | iOS availability (unverified, from vcpkg port knowledge) |
|---|---|---|
| sdl3 3.4.0 (`vulkan` feature) | Window, input, GL context, app lifecycle, audio device enumeration | SDL3 officially supports iOS |
| vulkan / vma | Vulkan backend | Needs MoltenVK on iOS |
| openal-soft 1.25.1 | Audio output | Builds for iOS |
| libogg, libvorbis | Vorbis BGM/voice (Steam SG audio format) | Yes |
| ffmpeg 7.1.2 (avcodec, avformat, swresample, swscale, dav1d), avcpp | Video + ffmpeg audio streams | Builds for iOS; **no Bink 2 decoder** |
| libwebp, zlib, freetype, harfbuzz, libass, fmt, glm, pugixml, utfcpp, toml11 | Textures, text, config | Expected yes; libass/harfbuzz on iOS unverified |
| concurrentqueue, readerwriterqueue, unordered-dense, boost-circular-buffer | Containers | Header-only |
| Vendored: clHCA, glad, imgui_custom, minilua, mio, mspack, pcg, squish | Codecs, GL loader, Lua, mmap, LZX, DXT | glad needs a GLES3 loader path on iOS |

## 5. Platform abstraction surface

SDL3 carries almost all platform work. Files containing OS `#ifdef`s in `src/`:
`main.cpp`, `log.cpp/.h`, `util.cpp/.h`, `workqueue.cpp`, `overlay.cpp`,
`io/filemeta.cpp/.h`, `video/ffmpegplayer.cpp`, `video/ffmpegstream.h`,
`renderer/window.cpp/.h`, `renderer/{opengl,vulkan,dx9}/window.cpp`,
`renderer/vulkan/renderer.cpp`, `renderer/opengl/shader.cpp`. That is a small surface, and
the Android path (shared library + SDL activity + GLES3 + external-storage asset copy in
`android/app/src/main/java/.../ImpactoActivity.java`) is the closest existing analog for an
iOS shell.

## 6. Rendering backends

| Backend | LOC | Shader pairs | Status |
|---|---|---|---|
| OpenGL (`src/renderer/opengl/`) | ~1400 | 27 | Primary; GL 3.3 core or GLES 3.0/3.2 chosen at runtime (`opengl/window.cpp:72-97`) |
| Vulkan (`src/renderer/vulkan/`) | ~2000 | 12 | Incomplete feature parity (fewer shaders) |
| DirectX 9 (`src/renderer/dx9/`) | ~860 | — | Windows only |

The GLES path is exercised today on Android and Switch, which is the basis for the
"GLES-first on iOS" option in `docs/decisions.md` (not yet decided).

## 7. Script execution (SC3 VM)

- `profiles/<p>/game.lua` sets `GameInstructionSet` → `vm.cpp:116-119` selects the three
  256-entry tables (`System`, `Graph`, `User1`) from `opcodetables_<set>.h`.
- Instructions are implemented once in `src/vm/inst_*.cpp` and branch on
  `Profile::Vm::GameInstructionSet` where games differ. **There are zero
  `InstructionSet::SGPS3` conditionals** in any `inst_*.cpp`; SGPS3 only exists in
  `vm.h`, `vm.cpp` and its opcode table.
- Many instruction bodies are `VMStub` log-only placeholders. Of 166 non-dummy entries in
  `opcodetables_sgps3.h`, 95 route to at least one stubbed path (counted by a throwaway
  script in this thread; not committed).
- `InstPhoneSG` (`inst_gamespecific.cpp:688`, opcode User1 `10 37`) and `InstMail`
  (`inst_gamespecific.cpp:765`) are pure stubs — these are the STEINS;GATE phone-trigger
  mechanics.

## 8. What this means for the project

- The engine is modular enough that a new game profile (`sghd`, Steam SG) and a new platform
  shell (iOS) are both additive work rather than rewrites.
- The hard parts are **game compatibility** (Steam SG instruction set, phone/mail, saves,
  Bink 2 video) rather than platform plumbing. See `docs/blockers.md`.
