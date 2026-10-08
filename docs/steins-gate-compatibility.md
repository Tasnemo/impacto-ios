# STEINS;GATE (English Steam release) compatibility investigation

Thread 03 report. Target: the original English **Steam** release of STEINS;GATE
(Steam app 412830, MAGES. PC port, sc3tools/sc3ntist game id `sghd`). Not
STEINS;GATE ELITE, not the PS3/Vita builds that impacto's `sgps3` profile was
written against.

Evidence classes used throughout:

- **Runtime** — observed by executing the Thread 02 `impacto` binary
  (`release/ubuntu24/impacto`, built in the `impacto-desktop:ubuntu24`
  container) with synthetic fixtures. Logs are quoted inline; the raw files
  are listed in §9.
- **Source** — read from this repository at commit `208cc56a` (unchanged
  upstream engine sources) or from the reference repositories named below.
- **External** — tool sources or community documentation about the Steam
  files. Nothing in this class has been checked against real game files in
  this project because **no Steam installation is available in the orb**.

Reference repositories read (clones were made in the orb, nothing copied into
git): CommitteeOfZero/impacto (upstream of this fork), CommitteeOfZero/sc3tools
(MIT; `resources/sghd/charset.utf8`, `gamedefs.json`), CommitteeOfZero/sc3ntist
(no license; its SGHD decoder table was used only to derive the opcode *names
and argument layouts* recorded in `tests/compat/fixtures/sghd_opcodes.json`),
CommitteeOfZero/LanguageBarrier (Steam SG hook; used for text/mail token and
texture format facts).

## 1. Short answer

STEINS;GATE does not run in this fork today, for any release:

1. `impacto -g sgps3` aborts before opening a window because
   `gamedefinitions.lua` does not register any SG profile (runtime, §4.1).
2. Once registered, the stock `sgps3` profile aborts during HUD profile load
   with `Expected member LoadingStar` and then `Expected member
   DelusionADVPosition`; the profile predates the current CHLCC HUD code it
   points at (runtime, §4.2).
3. With those two members patched, the VM starts, but it decodes the Steam
   script encoding wrongly: `Call` returns to the wrong address with the
   stock `UseReturnIds = false`, and with `UseReturnIds = true` the first
   `Nop` (`00 5F`, an `InstDummy` slot) never advances the instruction
   pointer, so the engine spins forever (runtime, §4.3–4.4).
4. The Steam archive names/paths, charset, font, dialogue box, phone, mail,
   save system and Bink 2 movies are additionally not covered (source +
   external, §2–§6).

The engine architecture itself is not the problem: the SC3 VM, MPK reader,
texture/audio loaders, dialogue/backlog/sprite systems and three complete save
implementations exist and are reused by every supported game. The missing
pieces are a correct `sghd` profile and opcode table, a handful of
instruction handlers, the phone/mail UI, and a save adapter.

## 2. Environment verification (task §1)

| Check | Result |
|---|---|
| Repo | `Tasnemo/impacto-ios`, default branch `master`, HEAD `208cc56a` at start of thread; history unshallowed. Branches `phase-00-upstream-analysis`, `phase-01-desktop-baseline` exist on origin. |
| Thread 02 build | Rebuilt in the `impacto-desktop:ubuntu24` container from `docs/desktop-build.md`: build OK, `ctest` reports "No tests were found!!!", both asset-free smoke checks PASS (`ci-build/logs/build-ubuntu24.log`, `smoke-ubuntu24.log`, not committed). Binary `release/ubuntu24/impacto` (12.3 MB). |
| Engine version | `VERSION` file and upstream sources unchanged since Thread 01; dependencies pinned in `vcpkg.json` (baseline `62159a45…`), see `docs/architecture.md` §4. ffmpeg (avcodec/avformat, dav1d), OpenAL Soft, SDL3, libvorbis, LibAtrac9 are present. |
| Asset-free launch | Launcher (no `-g`) runs without game data (Thread 02). **Any** `-g <game>` requires that game's spritesheets: `src/profile/sprites.cpp:48` aborts with `CRITICAL Could not open spritesheet …` (runtime, probe 2). |
| Environment limits | Native Debian 12/GCC 12 cannot build (OpenAL `<format>`); Docker is required. No GPU: Mesa software GL under `xvfb-run`. **No audio device: the engine segfaults in `Audio::AudioUpdate` unless `ALSOFT_DRIVERS=null` is exported** (gdb backtrace in `thread03-probe-no-audio-device-segfault-gdb.txt`). No Steam files; no Windows host. |

Previous reports were spot-checked, not trusted: the "no tests" and smoke
results were reproduced; Thread 01's claim that `InstPhoneSG`/`InstMail` are
stubs was confirmed at `src/vm/inst_gamespecific.cpp:688` and `:765`; Thread
01's "`opcodetables_sgps3.h` is a clone of darling" is confirmed and is
quantified below (16 Dummy slots + 21 layout mismatches against SGHD).

## 3. Game format compatibility (task §2)

| Format | Steam release (source of fact) | impacto | Status |
|---|---|---|---|
| Archives | `USRDIR/{bg,bgm,chara,manual,mask,mgsshader,script,se,shader,system,voice}.mpk` (external: LanguageBarrier, MagesPack/mpktools). Header `MPK\0` + u16 minor + u16 major (= 2.0), u32 count at +8, TOC at 0x40, 256-byte entries. | `src/io/mpkarchive.cpp` accepts **only** v2.0 (`// TODO support v1`), same TOC layout. Mount list in `profiles/sgps3/vfs.lua` expects `SCRIPT.CPK, SYSTEM_US.CPK, …` (PS3 names). | **Partially Working**: synthetic v2.0 archives mount and serve files (runtime, probe 3). Real Steam `.mpk` not tested; file names differ from the sgps3 profile. |
| Resource layout | Script ids, system sheet ids, bg/chara ids are archive-id based (`Path = { Mount = "system", Id = 7 }`). Steam ids are **unknown** without the files. | id-based lookup works. | Not Tested |
| Script container | `.scx`: `SC3\0`, string-table ptr @+4, return-table ptr @+8, label table @+12 (sc3ntist `SCXFile.h`, sc3tools `format.rs`). | `src/vm/vm.cpp:551-600` (`ScriptGetLabelAddress/StrAddress/RetAddress`) reads exactly that. | Verified Working on synthetic script (runtime, probe 4). |
| Bytecode encoding | Groups `00` System / `01` Graph / `10` User1, `FE` = expression assignment; expression immediates in four length classes with sign bit `0x10` (sc3ntist). | `vm.cpp:484-503`, `expression.cpp` — identical immediate decoder (`tests/compat/test_scx_decoding.py::ExpressionImmediates`). | Verified Working (unit + runtime). |
| Opcode table | SGHD slot names: `tests/compat/fixtures/sghd_opcodes.json` (154 named slots). | `src/vm/opcodetables_sgps3.h`: 16 SGHD slots are `InstDummy`, 21 slots have a different argument layout, and `UseReturnIds` is wrong (`tests/compat/fixtures/sgps3_known_gaps.json`, enforced by `test_opcode_table_audit.py`). | **Broken** (runtime, probes 4–5). |
| Text encoding | SC3 string tokens; Steam charset = 2895 glyphs (`sc3tools resources/sghd/charset.utf8`); Steam font sheet + western advance widths; mail-link delimiters `0x09`/`0x0B` inside mail text (LanguageBarrier). | `profiles/sgps3/charset.lua` grid 64×37 = 2368 entries, `font.lua` 64×14 sheet with 384 advance widths — the PS3 layout. `0x09`/`0x0B` parse as ruby base/ruby end (`src/text/text.h:40-42`); no link semantics. | Not Implemented for Steam; needs `sghd` charset/font. |
| Textures | PNG (LanguageBarrier replaces them as PNG), `.lay` sprite layouts for chara. | PNG via stb_image in the texture loader registry; `.lay` reader with `LayFileBigEndian = true` in sgps3 (PS3). Steam endianness unverified. | Not Tested |
| Audio | Ogg Vorbis BGM/SE/voice (external). | `src/audio/vorbisaudiostream.cpp`; `InstSEplay`/`InstVoicePlay` argument layouts differ from SGHD (`00 23`, `00 37`, `00 38`). | Not Tested; layout mismatches will desync the script. |
| Video | Bink 2 (`.bk2`, "KB2" signature; external: nipkownix FMV project, PCGamingWiki Bink 2.5). Location of the files inside/outside the mpks unverified. | `src/video/ffmpegplayer.cpp` only; ffmpeg has a Bink 1 decoder, **no Bink 2**. | Not Implemented |
| Config / saves | `Documents\My Games\mages_steam\STEINS;GATE\eng\SAVEDATA.DAT`, 80 normal + 48 quick slots (PCGamingWiki). Format unknown. | `profiles/sgps3/savedata.lua` → `SaveDataType.None` → `Implementation = nullptr` (`src/profile/data/savesystem.cpp:124`). | Not Implemented |
| Steam vs PS3 | Different archive names/casing, charset size, font, resolution assets (1280×720 vs PS3 1920×1080 assets in some sets), opcode table (`sghd` vs PS3 in sc3ntist), Win32-only opcodes (`10 40` SetResolution, `10 41` DestroyWindow), Steam achievements. | sgps3 profile models the PS3 build. | A separate `sghd` profile is required. |

Extraction tools (sc3tools, MagesPack) can read the Steam files; that says
nothing about execution. The execution gaps are in the table above and §4.

## 4. Script interpreter (task §3)

### 4.1 Loading and dispatch (source + runtime)

- Profile selection: `src/profile/profile.cpp:268-289` runs
  `gamedefinitions.lua` and looks the `-g` id up with
  `GameDefinitions.at()`. There is **no SG entry** in the committed file, so
  `-g sgps3` throws `std::out_of_range` and exits 134 (runtime; probe 1 log
  `thread03-launch-sgps3-stock-gamedefs.txt`).
- `Vm::Init` (`src/vm/vm.cpp:63-176`) loads `Profile::Vm::StartScript`
  from mount `script` into `ScriptBuffers[StartScriptBuffer]`, creates the
  startup thread at label 0 and sets `ScrWork[2200] = 1`.
- `RunThread` (`vm.cpp:443-530`): `do { … } while (!BlockCurrentScriptThread)`.
  Byte `0xFE` → `ExpressionEval` (assignment); otherwise group byte → one of
  `OpcodeTableSystem/Graph/Graph3D/User1[opcode]`. Unknown group → "Thread
  CRASH! Unknown opcode" and a pop of the call stack.
- Handlers are macros (`src/vm/inst_macros.inc`): `StartInstruction` saves
  the IP and skips the 2-byte opcode; `PopUint8/16`, `PopExpression`,
  `PopLocalLabel`, `PopFarLabel` consume arguments; `ResetInstruction`
  rewinds to re-execute next frame; `BlockThread` ends the frame.
- Consequence of that loop (runtime, probe 5): a handler that neither
  advances the IP nor blocks — `InstDummy` is `{}` at
  `src/vm/inst_system.cpp:39` — re-executes the same bytes until the process
  is killed. `InstDummy` and `InstSysVoicePlay` are the only sgps3-table
  handlers without `StartInstruction`.

### 4.2 Implemented vs required operations

`docs/architecture.md` §7 already noted zero `InstructionSet::SGPS3`
conditionals in any `inst_*.cpp`. The audit in this thread compared the
sgps3 table against the SGHD slot list:

- **Missing handlers (16 Dummy slots used by Steam scripts):** `00 4B`, `00
  4C`, `00 56` CallFarIfFlag, `00 57` ReturnIfFlag, `00 58`, `00 59`, `00 5F`
  Nop, `01 05` GroupCalc, `01 06-08`, `01 09` GroupCheckpoint, `10 1A`, `10
  3F`, `10 40` Win32_SetResolution, `10 41` Win32_DestroyWindow. Each is a
  guaranteed freeze when reached.
- **Wrong argument layout (21 slots, handler exists but consumes the wrong
  bytes):** `00 23` SEplay, `00 35`, `00 37` PlayVoice, `00 38` StopVoice,
  `00 41`, `00 43` SystemMessage, `00 50`, `00 52`, `00 53`, `00 54`
  CallIfFlag, `01 0A`, `01 12` Sel, `01 25` SetRevMes, `10 05` CHAload, `10
  12`, `10 22` AutoSave, `10 23`, `10 24`, `10 27`, `10 33` Tips, `10 37`
  PhoneSG. Each desynchronises the byte stream; what happens next is
  arbitrary (usually "Thread CRASH" or a Dummy spin).
- **Semantically empty handlers (correct layout, no effect):** `10 37`
  PhoneSG subtypes 0–4, 15, 18 (`inst_gamespecific.cpp:688-764`), `10 38`
  Mail (`:765`), plus the `VMStub` paths counted in `docs/architecture.md`.

The full lists are the single source of truth in
`tests/compat/fixtures/sgps3_known_gaps.json`; the audit test fails if the
source and the list drift apart.

### 4.3 Conditional branches, flags, variables (source)

- `InstIf` (`00 0A`, `inst_controlflow.cpp`): byte expected-truth,
  expression, local label. Layout matches SGHD.
- `InstJump/JumpFar/Call/CallFar/Return/Loop/JumpTable/Switch/Case` exist.
  `Call`/`CallFar` read a u16 **return id** only when
  `Profile::Vm::UseReturnIds` (`inst_controlflow.cpp:59-63`); the return
  table is resolved by `ScriptGetRetAddress` (`vm.cpp:586`). SGHD always
  emits return ids (sc3ntist), so sgps3's `false` is wrong — **runtime probe
  4 shows `Return` landing on the return-id bytes and executing `End`.**
- Flag-conditional calls used heavily by SG routes: `CallIfFlag` (`00 54`)
  has the wrong layout, `CallFarIfFlag` (`00 56`) and `ReturnIfFlag` (`00
  57`) are Dummy. (impacto has `InstReturnIfFlag` at `00 55`, one slot off.)
- Persistent state: `FlagWork` (1000 bytes, bit-addressed via
  `SetFlag/GetFlag` in `src/mem.cpp`) and `ScrWork` (8000 ints) in
  `src/mem.h`. Script-visible names are in `src/scriptvars.h` and
  `profiles/common/scriptvars.lua` + `profiles/sgps3/scriptvars.lua`.
  Which indices SG's Steam scripts use for route flags is unknown without
  the scripts.

### 4.4 Dialogue progression and interaction (source)

- `InstMesMain` (`inst_dialogue.cpp:594`) drives a `DialoguePage` state
  machine: blocks the thread while the typewriter runs, honours
  `SF_MESSKIP`/`SF_MESALLSKIP`, pushes backlog entries, marks lines read via
  `SaveSystem::SetLineRead`, waits for advance input.
- `InstSel`/`InstSelect` (`:933`, `:986`) implement choice menus; SGHD `Sel`
  type 0 carries an extra u16 that impacto skips only for other instruction
  sets (`01 12` mismatch).
- `profiles/sgps3/dialogue.lua` sets `DialogueBoxCurrentType = Plain`,
  which `src/profile/dialogue.cpp:207` reports as "Dialogue box is not
  implemented for the current profile yet!" (runtime, probe 3 log). Text
  rendering would go through the generic `DialoguePage` renderer with no
  box art, nameplate or ADV/NVL layout for SG.
- Input: `profiles/common/scriptinput.lua` maps pad/keys; `InstKeyWait`,
  `InstKeyOnJump` exist. SG's "phone open" key flag `SF_Phone_Open` is only
  touched by PhoneSG subtype 3.

### 4.5 Reuse from other games

- `src/games/chlcc/`, `cclcc/`, `mo6tw/` implement title/system menus,
  backlog, tips, save menus and save files for the Chaos;Child/Chaos;Head
  NoAH/MO6 family. `sgps3`'s HUD profiles already point at CHLCC types
  (which is why `LoadingStar`/`DelusionADVPosition` are demanded).
- No existing game implements a phone/mail UI; `src/games/*` has nothing
  reusable for the SG phone beyond the generic sprite/animation/menu widgets
  in `src/ui/`.
- `src/games/chlcc/savesystem.cpp` (1213 lines) serialises `FlagWork`
  ranges, `ScrWork` ranges, thread IP/call stack and per-script read-line
  bitmaps — the closest template for an SG save adapter.

## 5. STEINS;GATE-specific functionality (task §4)

### 5.1 Phone trigger system

| Feature | Status | Evidence |
|---|---|---|
| Incoming mail notification, read, reply selection, phone menu | Not Implemented | `InstPhoneSG` (`10 37`) and `InstMail` (`10 38`) only log `VMStub`; no `src/games/*/phone*` or `src/ui/*phone*` files; no phone sprites in `profiles/sgps3/sprites.lua`. |
| Phone subtypes decoded | Partially (layout only) | impacto handles subtypes 0–5, 15, 18; SGHD additionally emits `10`, `14`, `15`, `1A` (gap list). |
| Timing-sensitive events (mail window closes after N lines) | Not Implemented | would depend on `SW_PHONE_DISP_CT`-style counters; only subtype 3 writes `SW_PHONE_DISP_CT`. |
| Story flags modified by replies | Not Implemented | flag writes happen in the script after the phone UI returns a selection; with no UI the script never receives one. |
| Mail text link tokens (`0x09`/`0x0B`) | Not Implemented | parsed as ruby markers by `src/text/textparser.cpp`; no mail-link handling (LanguageBarrier documents the Steam semantics). |
| Route selection | Not Tested | cannot be exercised until branching + phone work. |

### 5.2 Dialogue and presentation

| Feature | Status | Evidence |
|---|---|---|
| Dialogue rendering engine | exists (used by CHLCC etc.) | `src/text/`, `DialoguePage`. For SG: `DialogueBoxType.Plain` → warning; no SG box/nameplate sprites. |
| Character sprites (`.lay` + textures) | Not Tested | loaders exist; Steam ids/endianness unknown. |
| Background transitions / masks | Not Tested | `MASK.CPK` mount exists; `InstBGload`/mask transitions are generic. |
| Text effects (ruby, colours, delusion trigger text) | Not Tested | generic SC3 token renderer. |
| Backlog | exists for CHLCC/CC profiles | sgps3 `hud/backlogmenu.lua` references CHLCC-type backlog; not run. |
| Script animations (`InstCHAmove…`, layered sprites) | Not Tested | |
| Voice sync | Not Tested; SGHD `PlayVoice` layout differs (`00 37`). | |

### 5.3 Save and load

| Aspect | Status | Evidence |
|---|---|---|
| Any save/load | Not Implemented | `SaveDataType.None`; `SaveSystem::Implementation == nullptr`, every call is a no-op (`src/profile/data/savesystem.cpp:124-127`, runtime log "Save data type is none"). |
| Thread IP / call stack serialisation | exists (CHLCC/CCLCC/MO6TW) | `src/games/chlcc/savesystem.cpp` saves `MainThread` IP, buffer id, call stack, `ReturnIds`/`ReturnAddresses`. |
| Flag / ScrWork persistence | exists in those adapters; ranges are per game | SG ranges unknown. |
| Phone state in saves | Not Implemented | no phone state exists to save. |
| Steam `SAVEDATA.DAT` format | Not Implemented, format unknown | external description only. A fork-native format is the realistic target; reading Steam saves is optional. |

## 6. Runtime evidence (what was actually executed)

All probes used the Thread 02 binary in the `impacto-desktop:ubuntu24`
container, `xvfb-run -a`, `LIBGL_ALWAYS_SOFTWARE=1`, `ALSOFT_DRIVERS=null`,
`-ll Trace`, and synthetic fixtures generated by
`tests/compat/sc3fixtures.py` (MPK v2.0 archives named like the sgps3 mounts,
64×64 PNGs at the system sheet ids, and a 2-label SGHD-encoded script:
`Assign; SetFlag 1770; Call label1 (ret 0); Nop; End` / `Assign; Return`).

| # | Setup | Observed | Conclusion |
|---|---|---|---|
| 1 | stock `gamedefinitions.lua`, `-g sgps3` | `terminate called after throwing … std::out_of_range … unordered_dense::map::at()`, exit 134 | no SG game definition |
| 2 | `sgps3` registered, no gamedata | 9 mount failures logged (non-fatal), icon warnings, `CRITICAL Could not open spritesheet Title`, exit 134 | game profiles are not asset-free |
| 3 | + synthetic archives | all 9 mounted "as MPK"; spritesheets load; "Dialogue box is not implemented…"; "Initializing SC3 virtual machine"; then `Expected member LoadingStar` abort; after patch `Expected member DelusionADVPosition` abort; after `TitleMenuType.None` the VM runs | sgps3 profile is bit-rotted against current CHLCC HUD code |
| 4 | probe 3 + `UseReturnIds=false` (stock) | trace `0x18 00:12 → 0x1e 00:0b → 0x2c 00:0e → 0x22 00:00` (Return → End at Call+4, Nop never executed) | wrong Call encoding for Steam scripts |
| 5 | probe 3 + `UseReturnIds=true` | `0x24 00:5f` repeated 1,215,409–1,315,531 times in 4 s, killed by timeout (exit 124) | Dummy slots freeze the engine |
| 6 | probe 3 without `ALSOFT_DRIVERS=null` | SIGSEGV in `Audio::AudioUpdate` (gdb) | environment limitation, documented for CI |

Probes 3–5 are automated in `tests/compat/test_runtime_probe.py` (4 tests,
PASS against the ubuntu24 build; skipped when `IMPACTO_BIN` is unset).

## 7. What cannot be verified without the Steam installation

Everything in the "External" class above. The owner can resolve these on
Windows with the procedure in `tests/compat/README.md` §"Local validation
with real Steam files": archive header hexdumps (MPK version, 10 s), script
dump with sc3tools/sc3ntist to confirm opcode usage and start-script id,
movie signatures (`BIK` vs `KB2`), and a first `impacto -g sghd` boot log once
Thread 04 Task 1 exists. None of this requires committing game data.

## 8. Feasibility (task §8)

Adapting impacto to the Steam release is achievable within the existing
architecture and should stay upstream-compatible:

- Reusable as-is: VM core, expression evaluator, SCX loader, MPK reader,
  VFS, texture/audio/video pipelines, `DialoguePage`/backlog/typewriter,
  sprite/animation systems, CHLCC-family UI as a template, three save
  adapters as templates.
- Must be added: `profiles/sghd/*` (vfs with lowercase `.mpk` names,
  charset 2895 glyphs, font, sprites, dialogue box type, HUD), a
  `gamedefinitions.lua` entry, `opcodetables_sghd.h` (+ `InstructionSet::SGHD`
  in `vm.h`) with 16 new/renamed handlers and 21 layout fixes guarded by
  `InstructionSet::SGHD` conditionals, phone/mail UI (`src/games/sghd/`),
  an SG save adapter, and a Bink 2 strategy for movies.
- Risk to other games: low if every change is behind `InstructionSet::SGHD`
  or lives in `profiles/sghd` / `src/games/sghd`; the audit test guards the
  sgps3 table so it is not silently edited.
- Maintenance: the fork would carry one new game the way upstream carries
  `cc`, `chlcc`, `mo6tw`; upstream has expressed interest in Steam SG
  (issue #1 lists only PS3 SG), so the work is a plausible contribution.
- Architectural blockers: **none found.** Bink 2 is a format/legal problem,
  not an engine one (transcode on the owner's machine, or play without
  movies).

The relative effort ranking is in `docs/steins-gate-blockers.md`; the bounded
task sequence is in `docs/thread-04-implementation-plan.md`.

## 9. Artifacts

Saved in the orb at `.amp/in/artifacts/` (not committed; quoted excerpts
are reproduced in this document and the probe test asserts them):
`thread03-launch-sgps3-stock-gamedefs.txt`,
`thread03-launch-sgps3-registered.log/.stdout.txt`,
`thread03-probe-useReturnIds-false-desync.log`,
`thread03-probe-useReturnIds-true-dummy-hang.log`,
`thread03-probe-no-audio-device-segfault-gdb.txt`,
`thread03-runtime-probe-results.txt`.
