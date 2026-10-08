# STEINS;GATE Compatibility Matrix

Target: original English **Steam** release of STEINS;GATE (Steam app 412830,
sc3tools id `sghd`). Not ELITE, not PS3.

Statuses (only these five are used): **Verified Working**, **Partially
Working**, **Broken**, **Not Implemented**, **Not Tested**. A status changes
from the Thread 03 initial value only on evidence; source inspection alone
never produces "Verified Working".

Evidence classes: *runtime* = executed the Thread 02 binary in this project
(synthetic fixtures unless stated); *source* = read in this repo; *external* =
tool sources or community docs, not checked against real files here. Real
Steam assets were **not available**; rows that need them say so.

Last updated: Thread 03 (2026-10-08). Full narrative:
[steins-gate-compatibility.md](steins-gate-compatibility.md); backlog:
[steins-gate-blockers.md](steins-gate-blockers.md).

## Subsystem matrix

| Subsystem | Status | Evidence | Source files | Assets needed | Known failures | Missing | Difficulty |
|---|---|---|---|---|---|---|---|
| Game initialization | **Broken** | runtime: `-g sgps3` → `std::out_of_range` (no gamedef); registered → `Expected member LoadingStar`, then `DelusionADVPosition` | `gamedefinitions.lua`, `src/profile/profile.cpp:268-289`, `profiles/sgps3/game.lua`, `profiles/sgps3/hud/*.lua`, `src/profile/games/chlcc/{sysmesbox,titlemenu}.cpp` | none to reproduce | abort 134 at two stages | `sghd` game definition + profile that matches current HUD member lists | Low–Medium |
| Steam archive loading | **Partially Working** | runtime: 9 synthetic MPK v2.0 archives mount and serve PNG/SCX; external: Steam `.mpk` are v2.0 | `src/io/mpkarchive.cpp`, `profiles/sgps3/vfs.lua` | real `*.mpk` for the untested half | none on synthetic data | lowercase Steam file names in a `sghd` vfs; MPK v1 unsupported (not needed if v2.0 confirmed) | Low |
| Script parsing | **Partially Working** | runtime: SCX header/label/return tables resolved on synthetic script; unit: immediates identical to sc3ntist | `src/vm/vm.cpp:551-600`, `src/vm/expression.cpp` | real `script.mpk` to confirm start-script id and opcode usage | none | nothing in the container layer | — |
| Script execution | **Broken** | runtime: `UseReturnIds=false` → Return hits return-id bytes, executes `End`; `UseReturnIds=true` → `00 5F` Dummy re-executed >1.2 M times in 4 s | `src/vm/opcodetables_sgps3.h`, `src/vm/inst_system.cpp:39`, `src/vm/inst_controlflow.cpp:54-120`, `src/vm/vm.cpp:443-530` | none to reproduce | desync, infinite spin | `opcodetables_sghd.h`: 16 Dummy slots, 21 layout fixes, `UseReturnIds=true` (list: `tests/compat/fixtures/sgps3_known_gaps.json`) | Medium |
| English dialogue | **Not Implemented** | runtime: "Dialogue box is not implemented for the current profile yet!"; source: sgps3 charset 2368 vs Steam 2895 glyphs | `src/profile/dialogue.cpp:207`, `profiles/sgps3/{charset,font,dialogue}.lua`, `src/text/*` | `system.mpk` (font sheet), charset from sc3tools | no box, wrong glyph map | `sghd` charset/font/dialogue box profile; SG ADV/NVL box type | Medium |
| Background rendering | **Not Tested** | generic `InstBGload`/mask code exists (source) | `src/vm/inst_graphics2d.cpp`, `src/background2d.cpp` | `bg.mpk`, `mask.mpk` | — | Steam ids/`.lay` endianness unverified | Low (if formats match) |
| Character sprites | **Not Tested** | `.lay` loader exists; `LayFileBigEndian=true` is PS3 (source) | `src/character2d.cpp`, `profiles/sgps3/game.lua` | `chara.mpk` | — | `10 05` CHAload layout fix (u16 for type 0) | Low–Medium |
| Voice playback | **Not Tested** | Vorbis stream exists; `00 37/00 38` layouts differ from SGHD (source) | `src/audio/vorbisaudiostream.cpp`, `src/vm/inst_sound.cpp` | `voice.mpk` | audio device required (no device → segfault in `Audio::AudioUpdate`, runtime) | PlayVoice/StopVoice layout fix | Low |
| Background music | **Not Tested** | Vorbis stream exists; `00 21/00 22` layouts match (source) | same | `bgm.mpk` | same audio-device note | — | Low |
| Video playback | **Not Implemented** | external: Steam movies are Bink 2; ffmpeg has no Bink 2 decoder (source: vcpkg ffmpeg features, `src/video/ffmpegplayer.cpp`) | `src/video/ffmpegplayer.cpp`, `vcpkg.json` | movie files (location unverified) | — | Bink 2 support or owner-side transcode | High (decoder) / Low (transcode) |
| Phone triggers | **Not Implemented** | source: `InstPhoneSG` all subtypes `VMStub`; subtypes 10/14/15/1A not decoded; no phone UI in `src/` | `src/vm/inst_gamespecific.cpp:688-764`, `src/ui/`, `profiles/sgps3/sprites.lua` | `system.mpk` phone sprites, scripts | — | whole phone UI + state + subtype semantics | High |
| Message responses | **Not Implemented** | source: `InstMail` stub; mail link tokens parsed as ruby | `src/vm/inst_gamespecific.cpp:765`, `src/text/textparser.cpp` | same | — | mail list, reply selection, link tokens | High |
| Story branching | **Not Tested** | source: `If/Jump/Switch` exist; `CallIfFlag` layout wrong, `CallFarIfFlag`/`ReturnIfFlag` Dummy | `src/vm/inst_controlflow.cpp`, `src/mem.h` | scripts | — | flag-conditional call family | Medium (depends on script execution + phone) |
| Save/load | **Not Implemented** | runtime: "Save data type is none, not setting implementation"; source: `Implementation=nullptr` | `profiles/sgps3/savedata.lua`, `src/profile/data/savesystem.cpp:124`, `src/games/chlcc/savesystem.cpp` (template) | scripts (to choose flag/ScrWork ranges) | — | SG save adapter, `10 22` AutoSave/checkpoint ids | Medium–High |
| Chapter transitions | **Not Tested** | source: `ScriptLoad`/`JumpFar` exist; `01 09` GroupCheckpoint is Dummy | `src/vm/inst_controlflow.cpp`, `src/vm/vm.cpp:178` | scripts | — | checkpoint handler | Low–Medium |
| Complete routes | **Not Tested** | nothing above executes real scripts | — | full install | — | everything above | — |
| All endings | **Not Tested** | same | — | full install | — | same | — |

## Supporting rows

| Item | Status | Evidence |
|---|---|---|
| Linux build (Ubuntu 24.04 / GCC 13) | Verified Working | Thread 02 + rebuilt in Thread 03 (`docs/desktop-test-results.md`) |
| Asset-free launcher | Verified Working | Thread 02 smoke, re-run in Thread 03 |
| Upstream CTest suite | Not Implemented | `ctest`: "No tests were found" |
| Compatibility unit tests (no assets) | Verified Working | `python3 -m unittest discover -s tests/compat` → 27 pass + 4 skipped probes |
| Runtime probes (need built binary) | Verified Working (they assert the *bugs*) | `IMPACTO_BIN=… python3 -m unittest tests.compat.test_runtime_probe` → 4 pass |
| Upstream tracker (CoZ impacto issue #1) | external | lists PS3 SG only: 2D graphics, sound, video; no Steam support claimed |

## Platform matrix

| Platform | Upstream status | Project status |
|---|---|---|
| Windows (x64, GL/DX9/Vulkan) | Built in CI | Not built here |
| Linux (x64, GL/Vulkan) | Built in CI (`ubuntu-24.04`) | Thread 02: build + software-GL launcher verified; Thread 03: synthetic game-profile probes executed |
| macOS (arm64 + intel, GL) | Built in CI (`macos-15`) | Not built here |
| Android (arm64, GLES3, minSdk 28) | Built in CI | Not built here |
| Nintendo Switch | Built in CI (docker) | Out of scope |
| iOS | No support | Feasibility only — `docs/threads/01-upstream-investigation.md` §6 |

## Rows that need the owner's Steam files

Archive loading (real `.mpk`), script parsing (real `script.mpk`),
backgrounds, sprites, voice, BGM, video signatures, and every row below
"Phone triggers". Procedure: `tests/compat/README.md` §"Local validation with
real Steam files".
