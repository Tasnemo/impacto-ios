# STEINS;GATE (Steam) compatibility backlog

Prioritised blockers for running the English Steam release in impacto.
Severity: **Critical** = game cannot start or execute meaningful dialogue;
**High** = blocks major gameplay systems, story progression or save/load;
**Medium** = incorrect presentation, audio/video or secondary features;
**Low** = polish.

Each entry: what / why required / files / reusable upstream code / approach /
dependencies / difficulty / verification. "Runtime" evidence was produced in
Thread 03 with synthetic fixtures (see
[steins-gate-compatibility.md](steins-gate-compatibility.md) §6); "external"
facts are unverified against real Steam files. The earlier project-level list
(`docs/blockers.md`, B1–B9) is superseded for SG items by this file; B6–B9
remain valid there.

## Critical

### C1 — No game definition / profile for the Steam release
- **Status (Thread 04 Task 1):** resolved for the asset-free path. `sghd`
  is registered (hidden) in `gamedefinitions.lua`; `profiles/sghd/` reaches
  "Initializing SC3 virtual machine" with the synthetic fixture and no
  patches (`SghdRuntimeProbe`). Sprite ids and `StartScript` are still
  placeholders until the owner's Steam listing exists (C5).
- **Missing:** `gamedefinitions.lua` has no SG entry (runtime: `-g sgps3` →
  `std::out_of_range`, exit 134). `profiles/sgps3` targets the PS3 build and
  is bit-rotted: `Expected member LoadingStar`
  (`src/profile/games/chlcc/sysmesbox.cpp`) then `DelusionADVPosition`
  (`src/profile/games/chlcc/titlemenu.cpp`) abort startup (runtime).
- **Why:** nothing runs before this.
- **Files:** `gamedefinitions.lua`, `profiles/sgps3/**`, new `profiles/sghd/**`,
  `src/profile/profile.cpp:268-289`.
- **Reuse:** `profiles/cc` (Steam Chaos;Child, lowercase `.mpk` vfs) and
  `profiles/chlcc` (HUD member lists that the C++ currently expects).
- **Approach:** create `profiles/sghd/` by copying `sgps3`, fix the vfs to
  Steam names (`bg.mpk`, `bgm.mpk`, `chara.mpk`, `mask.mpk`, `script.mpk`,
  `se.mpk`, `system.mpk`, `voice.mpk`, plus `manual`, `mgsshader`, `shader`
  if needed), add the missing HUD members or switch HUD types to `None`
  until SG-specific menus exist, register `sghd` in `gamedefinitions.lua`.
  Leave `sgps3` untouched.
- **Depends on:** nothing. Real Steam asset ids are needed for sprites but
  the probe fixture layout (`tests/compat/test_runtime_probe.py`) is enough
  to reach the VM.
- **Difficulty:** Low–Medium.
- **Verify:** `impacto -g sghd` with the synthetic fixture reaches
  "Initializing SC3 virtual machine" without `Expected member`; with real
  files, the title spritesheet loads.

### C2 — `UseReturnIds = false` desynchronises every `Call`
- **Status (Thread 04 Task 1):** resolved — `profiles/sghd/game.lua` sets
  `UseReturnIds = true`; runtime probe shows `Return` resumes at Call+6.
- **Missing:** SGHD `Call` (`00 0B`), `CallFar` (`00 0D`), `CallIfFlag` (`00
  54`), `CallFarIfFlag` (`00 56`) carry a u16 return-address id; impacto only
  reads it when `Profile::Vm::UseReturnIds` (`src/vm/inst_controlflow.cpp:59-63`).
- **Evidence:** runtime probe 4 — `Return` jumped to Call+4 and executed the
  id bytes as `End`; unit test
  `test_impacto_without_return_ids_desyncs_after_call`.
- **Files:** `profiles/sghd/game.lua` (`UseReturnIds = true`),
  `src/vm/inst_controlflow.cpp`, `src/vm/vm.cpp:586`.
- **Reuse:** CHLCC/CC profiles already use return ids; code path exists.
- **Approach:** profile flag only.
- **Difficulty:** Low. **Verify:** `test_runtime_probe` expectation flips to
  "Return resumes after Call" (already asserted in the `UseReturnIds=true`
  probe).

### C3 — 16 SGHD opcodes map to `InstDummy` → engine freezes
- **Status (Thread 04 Task 2):** resolved for byte consumption.
  `src/vm/opcodetables_sghd.h` has no `InstDummy`; never-emitted slots use
  `InstUnknownSGHD` (advance 2 bytes, log an error once). `00 57` →
  `InstReturnIfFlag`, `01 05` → `InstCalc`, `00 5F`/`10 12`/`10 40`/`10 41`
  → no-op. `00 4B/4C/58/59`, `01 06-09`, `10 1A/3F` consume their sc3ntist
  layouts and log `STUB … [SGHD, logged once]`: **semantics unknown**.
- **Missing:** `InstDummy` is `{}` (`src/vm/inst_system.cpp:39`); `RunThread`
  loops until a handler blocks, so any Dummy slot spins forever (runtime
  probe 5: `00 5F` executed >1.2 M times in 4 s). Slots: `00 4B`, `00 4C`,
  `00 56`, `00 57`, `00 58`, `00 59`, `00 5F`, `01 05`, `01 06`, `01 07`, `01
  08`, `01 09`, `10 1A`, `10 3F`, `10 40`, `10 41`
  (`tests/compat/fixtures/sgps3_known_gaps.json`).
- **Why:** `Nop` (`00 5F`) and `GroupCheckpoint` (`01 09`) appear in ordinary
  script flow; `ReturnIfFlag`/`CallFarIfFlag` drive route logic.
- **Files:** new `src/vm/opcodetables_sghd.h`, `src/vm/vm.h` (`InstructionSet::SGHD`),
  `src/vm/vm.cpp:116-121` (table selection switch), `src/vm/inst_system.cpp`,
  `inst_controlflow.cpp`, `inst_gamespecific.cpp`.
- **Reuse:** `InstReturnIfFlag` exists (wired at `00 55` for sgps3; SGHD
  needs it at `00 57`); `InstCallFar` + flag test compose `CallFarIfFlag`;
  there is no `InstNop` in any table (grep), so a 2-byte no-op handler must be added.
- **Approach:** copy `opcodetables_sgps3.h` → `opcodetables_sghd.h`; for
  each slot either wire an existing handler or add a handler that at
  minimum consumes the SGHD argument bytes (layouts in sc3ntist, named in
  `sghd_opcodes.json`) and logs `VMStub`. Make `InstDummy` itself safe:
  consume the opcode and log once (upstream behaviour change — keep it
  behind `InstructionSet::SGHD` or log at Error and advance 2 bytes).
- **Depends on:** C1 (profile selects the table).
- **Difficulty:** Medium (argument layouts for `00 4B/4C/58/59`, `01 06-08`,
  `10 1A/3F` need the real scripts to confirm; unknown-layout slots should
  be left as "advance + log" and tracked).
- **Verify:** `test_opcode_table_audit.py` extended to the `sghd` table
  (`dummy_slots_used_by_sghd` must be empty); runtime probe reaches `End`.

### C4 — 21 argument-layout mismatches desynchronise the byte stream
- **Status (Thread 04 Task 2):** resolved for byte consumption. Runtime probe
  `SghdTask2RuntimeProbe` runs one script containing all 37 affected opcodes
  through the real VM; every executed address equals the reference SGHD
  trace through `End`. Existing handlers with identical layouts are wired
  (CC's `InstSEplay`, `InstVoicePlay`, `InstVoiceStopNew`, `InstAutoSave`);
  `InstSel`, `InstSetRevMes`, `InstCHAload`, `InstSaveMenu`, `InstLoadData`,
  `InstTips` gained `InstructionSet::SGHD` branches; the rest are new
  `src/vm/inst_sghd.cpp` handlers. Stubs (consume + log) remain for `00 35`,
  `00 41`, `00 43` (modes 0A–11 look like SystemMes 0–7 + 10: unverified),
  `00 50`, `00 53`, `01 0A`, `10 27`, `10 37`.
- **Missing:** handlers exist but consume a different byte pattern than the
  SGHD compiler emits: `00 23` SEplay, `00 35`, `00 37` PlayVoice, `00 38`
  StopVoice, `00 41`, `00 43` SystemMessage, `00 50`, `00 52`, `00 53`, `00
  54` CallIfFlag, `01 0A`, `01 12` Sel, `01 25` SetRevMes, `10 05` CHAload,
  `10 12`, `10 22` AutoSave, `10 23`, `10 24`, `10 27`, `10 33` Tips, `10 37`
  PhoneSG (exact differences in `sgps3_known_gaps.json`).
- **Why:** the first mismatch reached corrupts all following execution.
- **Files:** `src/vm/inst_sound.cpp`, `inst_system.cpp`, `inst_controlflow.cpp`,
  `inst_dialogue.cpp`, `inst_graphics2d.cpp`, `inst_gamespecific.cpp`,
  `inst_misc.cpp`.
- **Reuse:** every handler already branches on
  `Profile::Vm::GameInstructionSet` for other games; add `SGHD` branches.
- **Approach:** per slot, add an `InstructionSet::SGHD` branch with the SGHD
  layout; where semantics are unknown, consume and log.
- **Depends on:** C3 (same table work).
- **Difficulty:** Medium.
- **Verify:** extend `tests/compat/test_scx_decoding.py`'s reference decoder
  comparison (`SghdLayoutVersusImpacto`) to walk a fixture containing each
  of the 21 opcodes and require the impacto-layout decoder to stay in sync.

### C5 — Steam VFS/resource mapping unknown
- **Missing:** `profiles/sgps3/vfs.lua` mounts `*.CPK` with PS3 names; Steam
  uses lowercase `*.mpk` (external). Sprite/bg/chara/script ids inside the
  Steam archives are unknown; `resources/sgps3/icondata/*` does not exist
  (runtime warning).
- **Files:** `profiles/sghd/vfs.lua`, `sprites.lua`, `hud/*.lua`, `resources/sghd/`.
- **Approach:** mount by Steam names; take sheet ids from the owner's
  `system.mpk` listing (`tests/compat/README.md`); add placeholder icon
  files under `resources/sghd/`.
- **Depends on:** owner's file listing.
- **Difficulty:** Low once the listing exists. **Verify:** `impacto -g sghd`
  log shows every mount "as MPK" and no "Could not open spritesheet".

## High

### H1 — Phone trigger / mail system does not exist
- **Missing:** `InstPhoneSG` (`src/vm/inst_gamespecific.cpp:688-764`) and
  `InstMail` (`:765`) are log-only; subtypes `10`, `14`, `15`, `1A` are not
  even decoded; no phone UI, sprites, state or save data.
- **Why:** the phone is STEINS;GATE's only branching mechanic; without it
  the script can still run linearly but no route can be chosen.
- **Files:** `src/vm/inst_gamespecific.cpp`, new `src/games/sghd/phone*.cpp`,
  `src/ui/` widgets, `profiles/sghd/hud/phone.lua`, `src/text/textparser.cpp`
  (link tokens `0x09`/`0x0B`).
- **Reuse:** generic `src/ui/menu.cpp`/`widget.cpp`/`selectionmenu.cpp`,
  `src/games/chlcc/delusiontrigger.cpp` as a "script-driven overlay" pattern.
  No phone implementation exists upstream for any game.
- **Approach:** (1) with real scripts, catalogue every PhoneSG/Mail subtype
  and the ScrWork/FlagWork it reads/writes (sc3ntist disassembly); (2)
  implement a state machine backed by ScrWork so it serialises for free;
  (3) build the UI from `system.mpk` sprites.
- **Depends on:** C1–C5, owner's script dump.
- **Difficulty:** High (largest single item).
- **Verify:** unit tests on the state machine with synthetic subtype
  sequences; manual run of chapter 1 first mail on Windows.

### H2 — No save/load
- **Missing:** `SaveDataType.None` → `SaveSystem::Implementation = nullptr`
  (runtime log "Save data type is none"); `10 22` AutoSave/checkpoint ids not
  consumed (C4).
- **Files:** `profiles/sghd/savedata.lua`, new `src/games/sghd/savesystem.cpp`,
  `src/data/savesystem.{h,cpp}`, `src/profile/data/savesystem.cpp`.
- **Reuse:** `src/games/chlcc/savesystem.cpp` (1213 lines) saves thread
  IP/call stack/return ids, FlagWork/ScrWork ranges, read-line bitmaps —
  copy and parametrise ranges.
- **Approach:** fork-native format first (`SaveDataType.SGHD`), 80 + 48
  slots to match Steam counts; reading Steam `SAVEDATA.DAT` is optional
  (format unknown).
- **Depends on:** C2–C4 (call stack must be right before it can be saved),
  H1 for phone state.
- **Difficulty:** Medium–High.
- **Verify:** round-trip unit test (serialise → deserialise → compare
  FlagWork/ScrWork/thread) against synthetic state; quick-save/load at a
  choice on Windows.

### H3 — Flag-conditional call family broken
- **Status (Thread 04 Task 2):** implemented. `InstCallIfFlag` (`00 54`),
  `InstCallFarIfFlag` (`00 56`) call when `GetFlag(flag) == condition` (the
  test `InstFlagOnJump`/`InstReturnIfFlag` use) and push the return id;
  `00 57` is `InstReturnIfFlag`. Runtime probe: taken and not-taken calls and
  the conditional return follow the reference trace.
- Subset of C3/C4 called out because it drives route progression:
  `CallIfFlag` (`00 54`, wrong layout), `CallFarIfFlag` (`00 56`, Dummy),
  `ReturnIfFlag` (`00 57`, Dummy; impacto's handler sits at `00 55`).
- **Verify:** fixture in `test_scx_decoding.py` already encodes
  `CallIfFlag`/`ReturnIfFlag`; add runtime assertion that the guarded label
  executes.

### H4 — Dialogue box / nameplate / ADV layout not implemented for SG
- `DialogueBoxType.Plain` → "Dialogue box is not implemented for the current
  profile yet!" (`src/profile/dialogue.cpp:207`, runtime).
- **Reuse:** `src/profile/games/{chlcc,cc,mo6tw}/dialoguebox.cpp`.
- **Approach:** new `DialogueBoxType.SGHD` or reuse CC's if the sprite
  layout fits; sprites from `system.mpk`.
- **Difficulty:** Medium. **Verify:** screenshot of first line on Windows.

## Medium

### M1 — Charset and font are the PS3 layout
- `profiles/sgps3/charset.lua` (64×37 = 2368) vs sc3tools `sghd` charset
  (2895 glyphs); `font.lua` advance widths for 384 western glyphs only.
- **Approach:** generate `profiles/sghd/charset.lua` from sc3tools
  `resources/sghd/charset.utf8` (MIT) and measure the Steam font sheet.
- **Difficulty:** Medium. **Verify:** render a known string, compare glyphs.

### M2 — Bink 2 movies
- External: Steam movies are Bink 2 (`KB2`); ffmpeg decodes Bink 1 only;
  `src/video/ffmpegplayer.cpp` is the only player.
- **Approach:** owner transcodes to a supported codec during asset
  preparation (documented tool step), or skip movies (`InstMovie*` no-op
  guarded by a profile flag). Implementing Bink 2 is not recommended.
- **Difficulty:** Low (skip/transcode) / High (decoder). **Verify:** `ffprobe`
  on the owner's files (README procedure) decides which.

### M3 — SE / voice argument layouts
- `00 23` SEplay, `00 37` PlayVoice, `00 38` StopVoice (part of C4) — listed
  separately because their semantics (channel, volume, sync flags) matter
  for voice sync, not just for byte alignment.

### M4 — Mail link tokens and SG text extensions
- `0x09`/`0x0B` inside mail bodies mean link start/end (LanguageBarrier);
  impacto treats them as ruby markers. Also check `0x13 GetHardcodedValue`
  and `0x15 EvaluateExpression` usage in SG scripts.

### M5 — Checkpoint / chapter handling
- `01 09` GroupCheckpoint (Dummy) and `10 22` AutoSave type `0A` (u16 id not
  consumed). Needed for chapter transitions and autosave points.

## Low

### L1 — Win32-only opcodes
- `10 40` Win32_SetResolution, `10 41` Win32_DestroyWindow: wire as explicit
  no-ops in the `sghd` table (currently Dummy → freeze, so this is Low only
  once C3's generic Dummy fix lands).

### L2 — Achievements
- `src/data/achievementsystem*` exists; Steam achievement ids unknown.

### L3 — `resources/sgps3/icondata` missing
- Warnings only; add `resources/sghd/icondata/*.png`.

### L4 — Audio-less environments crash
- Engine segfaults in `Audio::AudioUpdate` without an OpenAL device
  (runtime, gdb). Not SG-specific; CI uses `ALSOFT_DRIVERS=null`. Consider
  a guard upstream.

## Dependency order

```diagram
C1 profile/gamedef ─▶ C2 UseReturnIds ─▶ C3 Dummy slots ─▶ C4 layouts ─▶ H3 flag calls
        │                                        │
        └──▶ C5 VFS ids (needs owner listing)    └──▶ M5 checkpoints ─▶ H2 save/load
                      │                                                      ▲
                      └──▶ H4 dialogue box ─▶ M1 charset/font                │
                                                                             │
                      H1 phone/mail (needs owner script dump) ───────────────┘
                      M2 movies (independent)
```
