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

Last updated: Thread 06 (2026-10-08) — Thread 06 used the owner's private
`tools/sghd_census.py` report (all 190 scripts decoded, image/LAY/audio
headers; constants in the same fixture) and new synthetic probes; still no
real game data was executed. Thread 05 used the owner's
`tools/sghd_evidence.py` report (listing/headers of the real install, no
content; constants in `tests/compat/fixtures/sghd_steam_evidence.json`) and
new synthetic probes; still no real game data was executed. Thread 04: rows changed only where the Thread 04
runtime probes (`tests/compat/test_runtime_probe.py`, synthetic fixtures,
real binary) produced new evidence. Thread 03 values are kept in the history
of this file. Full narrative:
[steins-gate-compatibility.md](steins-gate-compatibility.md); backlog:
[steins-gate-blockers.md](steins-gate-blockers.md).

## Subsystem matrix

| Subsystem | Status | Evidence | Source files | Assets needed | Known failures | Missing | Difficulty |
|---|---|---|---|---|---|---|---|
| Game initialization | **Partially Working** | runtime (Thread 04/05, synthetic): `-g sghd` with the committed profile reaches "Initializing SC3 virtual machine"; Thread 05: `StartScript = 2` = `_STARTUP_WIN.SCX` and sheet ids from the real `system.mpk` listing; DXT5 DDS and PNG sheets load (`SghdRuntimeProbe`) | `gamedefinitions.lua`, `profiles/sghd/**`, `src/vm/vm.cpp` | real files for a first boot | `TitleMenuType.None`; sheet sizes/rects are PS3 values | first boot on Windows (`docs/sghd-steam-evidence.md`) | Low |
| Steam archive loading | **Partially Working** | external (owner report, Thread 05): 11 Steam `.mpk` are v2.0, uncompressed, lowercase names = `vfs.lua`; runtime: synthetic MPK v2.0 with those names mount and serve PNG/DDS/SCX/Ogg | `src/io/mpkarchive.cpp`, `profiles/sghd/vfs.lua` | real `*.mpk` at runtime | none on synthetic data | a run against the real archives | Low |
| Script parsing | **Partially Working** | runtime: SCX header/label/return tables resolved on synthetic script; unit: immediates identical to sc3ntist | `src/vm/vm.cpp:551-600`, `src/vm/expression.cpp` | real `script.mpk` to confirm start-script id and opcode usage | none | nothing in the container layer | — |
| Script execution | **Partially Working** | runtime (Thread 04): all 37 previously broken opcodes run through the real VM to `End` on the reference trace (`SghdTask2RuntimeProbe`); external (Thread 06 census): 282 676 instructions of the real scripts decode with the SGHD table except `10 3A` (fixed) and 4 unresolved overruns ([sghd-decode-integrity.md](sghd-decode-integrity.md)) | `src/vm/opcodetables_sghd.h`, `src/vm/inst_sghd.cpp` | real `script.mpk` run | none on synthetic data | semantics of stubbed opcodes (`00 35/41/43/4B/4C/50/53/58/59`, `01 06-0A`, `10 1A/27/3F`, phone UI sub-types) | Medium |
| English dialogue | **Partially Working** | runtime (Thread 06, synthetic): generic `PlainDialogueBox` configured without warnings (`SghdRuntimeProbe`); external (census): `FONT.PNG` 3072×2208 = 64×46 cells of 48 px, 2895 glyphs match the sc3tools charset; profile at 1920×1080 with ink-derived widths | `src/hud/dialoguebox.cpp`, `profiles/sghd/{charset,font,dialogue}.lua`, `tools/gen_sghd_font_widths.py` | `system.mpk` | ADVBox/nametag rectangles are PS3 ×1.5 guesses; widths approximate | real rectangles (`tools/sghd_inspect.py sprites`), exe width table (`widths`) | Medium |
| Background rendering | **Not Tested** | generic `InstBGload`/mask code exists (source) | `src/vm/inst_graphics2d.cpp`, `src/background2d.cpp` | `bg.mpk`, `mask.mpk` | — | Steam ids/`.lay` endianness unverified | Low (if formats match) |
| Character sprites | **Not Tested** | external (census): LAY is little-endian with pixel texture coordinates and one trailing byte per vertex; profile set accordingly (`LayFileBigEndian = false`, multipliers 1); `10 05` CHAload consumes the SGHD u16 (runtime, Thread 04) | `src/character2d.cpp`, `profiles/sghd/game.lua` | `chara.mpk` | — | real sprite run | Low |
| Voice playback | **Partially Working** | runtime (Thread 05, synthetic Ogg Vorbis in `voice.mpk`): `00 37` plays through the Vorbis stream (`SghdOggAudioProbe`); no audio device → silent, no crash (was segfault); external: Steam `voice.mpk` holds 14512 `.OGG` entries ; Thread 06: census confirms all 14512 entries are Ogg Vorbis; lip-sync table `WAVTABLE.DAT` is little-endian, now read as such and bounds-checked (`SghdVoiceTableProbe`) | `src/audio/vorbisaudiostream.cpp`, `src/voicetable.cpp`, `src/vm/inst_sound.cpp` | `voice.mpk` | — | codec of real entries (census), voice/text sync semantics (M3) | Low |
| Background music | **Partially Working** | runtime (Thread 05, synthetic Ogg Vorbis): `00 21` plays from `bgm.mpk` (`SghdOggAudioProbe`); external: Steam `bgm.mpk` holds 83 `.ogg` entries | same | `bgm.mpk` | — | real-file run; `*NL` track variants unexplained | Low |
| Video playback | **Not Implemented** (skipped safely) | external (owner report): 38 movies per resolution, loose `.bk2`, all `KB2j` = Bink 2; runtime (Thread 05, synthetic): unmounted movie and a synthetic Bink 2 file are skipped and the script continues (`SghdMovieSkipProbe`); before, the Bink 2 case crashed (SIGSEGV, then abort) | `src/video/ffmpegplayer.cpp`, `src/vm/inst_movie.cpp`, `profiles/sghd/vfs.lua` | movies | movies are never shown | Bink 2 decoding or owner-side transcode + id→file mapping (census `--exe`) | High (decoder) / Low (transcode) |
| Phone triggers | **Partially Working** | runtime (Thread 06, synthetic): `10 37` 0x00-0x03 item attribute bits set/clear/branch and survive save/load (`SghdPhoneProbe`, `SghdSaveRoundTripProbe`); external (census): all 611 phone/mail instructions catalogued ([phone-protocol.md](phone-protocol.md)) | `src/vm/inst_sghd.cpp`, `src/games/sghd/phone.h` | `system.mpk` `PHONE*.DDS` | polarity inferred, not verified on the real game | phone UI and sub-types 0x05-0x1E (player-driven mails/calls) | High |
| Message responses | **Not Implemented** | source: `InstMail` stub; mail link tokens parsed as ruby | `src/vm/inst_gamespecific.cpp:765`, `src/text/textparser.cpp` | same | — | mail list, reply selection, link tokens | High |
| Story branching | **Partially Working** | runtime (Thread 04, synthetic): `CallIfFlag` (`00 54`) taken/not taken, `CallFarIfFlag` (`00 56`) and `ReturnIfFlag` (`00 57`) follow the reference trace | `src/vm/inst_sghd.cpp`, `src/vm/inst_controlflow.cpp` | scripts | — | real-script validation; phone-driven branches (H1) | Medium |
| Save/load | **Partially Working** | runtime (Thread 04/06, synthetic): fork-native format 2 saves slot 79 incl. phone bits and global system data; a second process restores variables, phone bits, global flags, main-thread IP and call stack (`SghdSaveRoundTripProbe`) | `src/games/sghd/savesystem.cpp`, `profiles/sghd/savedata.lua`, [sghd-save-format.md](sghd-save-format.md) | — | not Steam `SAVEDATA.DAT`; no save/load menu; tips/CG/BGM unlocks not saved | menus, optional Steam import | Medium |
| Chapter transitions | **Not Tested** | source: `ScriptLoad`/`JumpFar` exist; runtime (Thread 04): `01 09` GroupCheckpoint and `10 22` type `0A` consume their ids (checkpoint stored, not acted on) | `src/vm/inst_sghd.cpp`, `src/vm/vm.cpp` | scripts | — | checkpoint semantics with real scripts | Low–Medium |
| Complete routes | **Not Tested** | nothing above executes real scripts | — | full install | — | everything above | — |
| All endings | **Not Tested** | same | — | full install | — | same | — |

## Supporting rows

| Item | Status | Evidence |
|---|---|---|
| Linux build (Ubuntu 24.04 / GCC 13) | Verified Working | Thread 02 + rebuilt in Thread 03 (`docs/desktop-test-results.md`) |
| Asset-free launcher | Verified Working | Thread 02 smoke, re-run in Thread 03 |
| Upstream CTest suite | Not Implemented | `ctest`: "No tests were found" |
| Compatibility unit tests (no assets) | Verified Working | `python3 -m unittest discover -s tests/compat` → 81 pass + 28 skipped probes (Thread 06) |
| Runtime probes (need built binary) | Verified Working | 28 probes: sgps3 probes still assert the frozen PS3 profile's bugs; sghd/harness/save/movie/audio/phone probes assert the fixes (Thread 06, 109/109 with `IMPACTO_BIN`) |
| Asset-free VM harness | Verified Working | `-g sghd-harness` exits by itself with `ScrWork[4000]` as status (Thread 04) |
| Upstream tracker (CoZ impacto issue #1) | external | lists PS3 SG only: 2D graphics, sound, video; no Steam support claimed |

## Platform matrix

| Platform | Upstream status | Project status |
|---|---|---|
| Windows (x64, GL/DX9/Vulkan) | Built in CI | Thread 05: `desktop-windows.yml` builds an artifact for owner-side runs (see handoff for status) |
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
