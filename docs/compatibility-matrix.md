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

Last updated: Thread 04 (2026-10-08) — rows changed only where the Thread 04
runtime probes (`tests/compat/test_runtime_probe.py`, synthetic fixtures,
real binary) produced new evidence. Thread 03 values are kept in the history
of this file. Full narrative:
[steins-gate-compatibility.md](steins-gate-compatibility.md); backlog:
[steins-gate-blockers.md](steins-gate-blockers.md).

## Subsystem matrix

| Subsystem | Status | Evidence | Source files | Assets needed | Known failures | Missing | Difficulty |
|---|---|---|---|---|---|---|---|
| Game initialization | **Partially Working** | runtime (Thread 04): `-g sghd` with the committed `profiles/sghd` + `gamedefinitions.lua`, unmodified, mounts all `.mpk` and reaches "Initializing SC3 virtual machine" (`SghdRuntimeProbe`); `-g sghd-harness` needs only `script.mpk` | `gamedefinitions.lua`, `profiles/sghd/**`, `src/vm/vm.cpp` | real Steam files for sprite ids / start script | none on synthetic data; `TitleMenuType.None`, placeholder sprite ids and `StartScript = 2` | real `system.mpk`/`script.mpk` ids (owner evidence) | Low |
| Steam archive loading | **Partially Working** | runtime: synthetic MPK v2.0 archives with the Steam lowercase names in `profiles/sghd/vfs.lua` mount and serve PNG/SCX; external: Steam `.mpk` are v2.0 | `src/io/mpkarchive.cpp`, `profiles/sghd/vfs.lua` | real `*.mpk` for the untested half | none on synthetic data | confirmation of names/version (`tools/sghd_evidence.py`); movies not mounted | Low |
| Script parsing | **Partially Working** | runtime: SCX header/label/return tables resolved on synthetic script; unit: immediates identical to sc3ntist | `src/vm/vm.cpp:551-600`, `src/vm/expression.cpp` | real `script.mpk` to confirm start-script id and opcode usage | none | nothing in the container layer | — |
| Script execution | **Partially Working** | runtime (Thread 04): one script with all 37 previously broken opcodes runs through the real VM to `End`; every executed address equals the reference SGHD trace (`SghdTask2RuntimeProbe`, also via the harness); `Return` resumes at Call+6; no `InstDummy` left (`SghdOpcodeTableAudit`) | `src/vm/opcodetables_sghd.h`, `src/vm/inst_sghd.cpp`, SGHD branches in `inst_dialogue/graphics2d/misc.cpp` | real `script.mpk` | none on synthetic data | semantics of stubbed opcodes (`00 35/41/43/4B/4C/50/53/58/59`, `01 06-0A`, `10 1A/27/37/3F`) are logged, not implemented | Medium |
| English dialogue | **Not Implemented** | runtime: "Dialogue box is not implemented for the current profile yet!"; Thread 04: Steam charset (2895 glyphs, sc3tools) generated into `profiles/sghd/charset.lua`, cross-checked against the PS3 glyph-id lists | `src/profile/dialogue.cpp:207`, `profiles/sghd/{charset,font,dialogue}.lua`, `tools/gen_sghd_charset.py` | `system.mpk` (font sheet, box sprites) | no box; font grid is the PS3 64×14 sheet | font sheet/widths, SG dialogue box type | Medium |
| Background rendering | **Not Tested** | generic `InstBGload`/mask code exists (source) | `src/vm/inst_graphics2d.cpp`, `src/background2d.cpp` | `bg.mpk`, `mask.mpk` | — | Steam ids/`.lay` endianness unverified | Low (if formats match) |
| Character sprites | **Not Tested** | `.lay` loader exists; `LayFileBigEndian=true` is PS3 (source); `10 05` CHAload consumes the SGHD u16 (runtime, Thread 04) | `src/character2d.cpp`, `profiles/sghd/game.lua` | `chara.mpk` | — | real sprite data | Low–Medium |
| Voice playback | **Not Tested** | Vorbis stream exists; `00 37/00 38` now use CC's `InstVoicePlay`/`InstVoiceStopNew` (layout-checked at runtime, semantics unverified, M3) | `src/audio/vorbisaudiostream.cpp`, `src/vm/inst_sound.cpp` | `voice.mpk` | audio device required (no device → segfault in `Audio::AudioUpdate`, runtime) | voice semantics with real files | Low |
| Background music | **Not Tested** | Vorbis stream exists; `00 21/00 22` layouts match (source) | same | `bgm.mpk` | same audio-device note | — | Low |
| Video playback | **Not Implemented** | external: Steam movies are Bink 2; ffmpeg has no Bink 2 decoder (source: vcpkg ffmpeg features, `src/video/ffmpegplayer.cpp`) | `src/video/ffmpegplayer.cpp`, `vcpkg.json` | movie files (location unverified) | — | Bink 2 support or owner-side transcode | High (decoder) / Low (transcode) |
| Phone triggers | **Not Implemented** | runtime (Thread 04): `InstPhoneSGHD` consumes every SGHD `10 37` subtype (incl. 10/14/15/1A) and logs it; no phone state or UI | `src/vm/inst_sghd.cpp`, `src/ui/`, `profiles/sghd/sprites.lua` | `system.mpk` phone sprites, owner's script dump | — | subtype semantics (Task 7a, needs script dump), state, UI | High |
| Message responses | **Not Implemented** | source: `InstMail` stub; mail link tokens parsed as ruby | `src/vm/inst_gamespecific.cpp:765`, `src/text/textparser.cpp` | same | — | mail list, reply selection, link tokens | High |
| Story branching | **Partially Working** | runtime (Thread 04, synthetic): `CallIfFlag` (`00 54`) taken/not taken, `CallFarIfFlag` (`00 56`) and `ReturnIfFlag` (`00 57`) follow the reference trace | `src/vm/inst_sghd.cpp`, `src/vm/inst_controlflow.cpp` | scripts | — | real-script validation; phone-driven branches (H1) | Medium |
| Save/load | **Partially Working** | runtime (Thread 04, synthetic): fork-native `SaveDataType.SGHD` saves slot 79 in one process and a second process restores variables, main-thread IP and call stack and returns through it (`SghdSaveRoundTripProbe`) | `src/games/sghd/savesystem.cpp`, `profiles/sghd/savedata.lua`, [sghd-save-format.md](sghd-save-format.md) | scripts (to confirm saved ranges) | not Steam `SAVEDATA.DAT`; no save/load menu; tips/CG/BGM unlocks not saved | menus, real ranges, optional Steam import | Medium |
| Chapter transitions | **Not Tested** | source: `ScriptLoad`/`JumpFar` exist; runtime (Thread 04): `01 09` GroupCheckpoint and `10 22` type `0A` consume their ids (checkpoint stored, not acted on) | `src/vm/inst_sghd.cpp`, `src/vm/vm.cpp` | scripts | — | checkpoint semantics with real scripts | Low–Medium |
| Complete routes | **Not Tested** | nothing above executes real scripts | — | full install | — | everything above | — |
| All endings | **Not Tested** | same | — | full install | — | same | — |

## Supporting rows

| Item | Status | Evidence |
|---|---|---|
| Linux build (Ubuntu 24.04 / GCC 13) | Verified Working | Thread 02 + rebuilt in Thread 03 (`docs/desktop-test-results.md`) |
| Asset-free launcher | Verified Working | Thread 02 smoke, re-run in Thread 03 |
| Upstream CTest suite | Not Implemented | `ctest`: "No tests were found" |
| Compatibility unit tests (no assets) | Verified Working | `python3 -m unittest discover -s tests/compat` → 47 pass + 18 skipped probes (Thread 04) |
| Runtime probes (need built binary) | Verified Working | 18 probes: sgps3 probes still assert the frozen PS3 profile's bugs; sghd/harness/save probes assert the fixes (Thread 04, 65/65 with `IMPACTO_BIN`) |
| Asset-free VM harness | Verified Working | `-g sghd-harness` exits by itself with `ScrWork[4000]` as status (Thread 04) |
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
