# STEINS;GATE Compatibility Matrix

Target: original English **Steam** release of STEINS;GATE (Steam app 412830, MAGES. engine
port, internal id `sghd`), not STEINS;GATE ELITE and not the PS3 release.

Legend: **Verified** = observed by running the engine in this project; **Claimed** =
stated by upstream/external docs, not reproduced here; **Source-level** = conclusion drawn
from reading impacto source; **Unknown** = no evidence either way.

As of Thread 01 nothing has been run. Every row below is Claimed, Source-level, or Unknown.

## Engine-side support for the Steam release

| Area | Status | Evidence |
|---|---|---|
| Game profile for Steam SG (`sghd`) | **Missing** (source-level) | `profiles/` has `sgps3` only; `gamedefinitions.lua` does not list any SG profile |
| Game profile for PS3 SG (`sgps3`) | Exists, minimal | `profiles/sgps3/game.lua`; `SaveDataType.None`; system menu include commented out |
| Archive format: Steam `.mpk` | Probably supported, **unverified** | `MpkArchive` accepts only MPK v2.0 (`src/io/mpkarchive.cpp:64-67`). Chaos;Child Steam `.mpk` loads via `profiles/cc/vfs.lua`; Steam SG MPK version field not yet inspected |
| Script format: `.scx` SC3 | Container readable; **opcode set unknown** | sc3tools treats `sghd` as its own game id with its own charset; impacto has no `sghd` opcode tables |
| Instruction set | **Unknown** | `opcodetables_sgps3.h` differs from `opcodetables_darling.h` in ~4 entries and still carries Darling-only ops (`InstTwipo` 10 39, `InstUnk103A`); it appears cloned, not reverse-engineered. Whether Steam SG shares PS3 SG's tables is unknown |
| Charset / text | **Missing** | sc3tools ships `resources/sghd/charset.utf8`; impacto has `resources/sgps3` only |
| Textures | Likely OK | Steam SG uses PNG (+`.lay`) / DDS; impacto has stbi, DDS and `.lay` loaders. `LayFileBigEndian=true` in sgps3 must be `false` for PC (unverified) |
| Audio (Ogg Vorbis BGM/SE/voice) | Likely OK | `src/audio/vorbisaudiostream.cpp` |
| Video (Bink 2) | **Blocked** | Steam SG movies are Bink 2 (nipkownix FMV project write-up); ffmpeg decodes Bink 1 (`BIK`) only |
| Phone triggers (`InstPhoneSG`) | **Stub** | `src/vm/inst_gamespecific.cpp:688` logs `VMStub` and does nothing |
| Mail (`InstMail`) | **Stub** | `src/vm/inst_gamespecific.cpp:765` |
| Save / load | **Missing** | `sgps3/savedata.lua` → `SaveDataType.None`; save implementations exist for CHLCC, CCLCC, MO6TW only. Steam SG format: `SAVEDATA.DAT` (80 slots + 48 quick), location `Documents\My Games\mages_steam\STEINS;GATE\eng\` (PCGamingWiki) |
| System menu / title / backlog / tips UI | Partial (PS3 layouts) | `profiles/sgps3/hud/*.lua`; no `src/games/sgps3` C++ |
| Branching / endings | **Unknown** | depends on VM completeness |
| Achievements | Unknown | |

## Upstream compatibility tracker (CommitteeOfZero/impacto issue #1, read 2026-10-08)

> Steins;Gate (English PS3 version only): 2D graphics display, Sound playback, Video playback

No story progression, saves, menus, or Steam-release support is claimed upstream.

## Platform matrix

| Platform | Upstream status | Project status |
|---|---|---|
| Windows (x64, GL/DX9/Vulkan) | Built in CI | Not built here |
| Linux (x64, GL/Vulkan) | Built in CI (`ubuntu-24.04`) | Not built here — Thread 02 |
| macOS (arm64 + intel, GL) | Built in CI (`macos-15`) | Not built here |
| Android (arm64, GLES3, minSdk 28) | Built in CI | Not built here |
| Nintendo Switch | Built in CI (docker) | Out of scope |
| iOS | **No support** | Feasibility only — see `docs/threads/01-upstream-investigation.md` §6 |

## Next verification steps (Thread 03)

1. Obtain a legitimate Steam install; record `USRDIR/` listing with sizes and the first 16
   bytes of each `.mpk` (version field) and of each movie file (`BIK`/`KB2` signature).
2. Dump `script.mpk` with sc3tools/sg-unpack; diff opcode usage against
   `opcodetables_sgps3.h`.
3. Create `profiles/sghd` and attempt title-screen boot under `-lc VM -ll Debug`; record
   every `VMStub` hit.
