# Thread 04 implementation plan — STEINS;GATE (Steam) on desktop

Scope: bounded engineering tasks derived from
[steins-gate-blockers.md](steins-gate-blockers.md). Each task names its
inputs, the files it touches, the test that proves it, and what it must not
do. Tasks 1–4 need **no commercial assets**; tasks 5+ need the owner's Steam
installation on Windows for validation (never in git, never in CI).

## Status after Thread 04 (2026-10-08, branch `phase-03-sghd-implementation`)

| Task | Status | Evidence |
|---|---|---|
| 1 Register `sghd`, reach the VM | **Done** | `SghdRuntimeProbe` |
| 2 SGHD opcode table, layouts | **Done** (byte consumption; unknown semantics stubbed + logged) | `SghdOpcodeTableAudit`, `SghdTask2RuntimeProbe` |
| 3 Asset-free VM harness | **Done** (`profiles/sghd-harness`, self-terminating, script exit status) | `SghdHarnessRuntimeProbe`, CI |
| 4 Save adapter skeleton | **Done** (fork-native format, 80 + 48 slots) | `SghdSaveRoundTripProbe`, `docs/sghd-save-format.md` |
| 5 First real boot | **Blocked** — needs the owner's Steam install evidence | `tools/sghd_evidence.py` prepared |
| 6 Dialogue, charset, font | **Partial** — charset generated + tested; font/dialogue box blocked on Task 5 assets | `test_sghd_charset.py` |
| 7 Phone and mail | **Blocked** — 7a needs the owner's script dump; 7b/7c depend on 7a | — |
| 8 Audio/video details | **Blocked** except L1 (Win32 no-ops, done in Task 2); M2/M3/L2 need real files | — |

Details: [threads/04-sghd-implementation.md](threads/04-sghd-implementation.md).

Ground rules for Thread 04:

- Add a new game id `sghd`; never modify `profiles/sgps3` or
  `opcodetables_sgps3.h` semantics (the audit test
  `tests/compat/test_opcode_table_audit.py` pins the sgps3 table on purpose).
- Guard every C++ change with `InstructionSet::SGHD` or place it in
  `src/games/sghd/` / `profiles/sghd/` so other games are untouched.
- Keep `tests/compat` green: when a probe assertion describes a bug you fix,
  flip the assertion in the same commit and say so in the message.
- Update `docs/compatibility-matrix.md` only with runtime evidence.

## Task 1 — Register `sghd` and make it reach the VM (asset-free)

- **Goal:** `impacto -g sghd` with the synthetic fixture tree from
  `tests/compat/test_runtime_probe.py` reaches "Initializing SC3 virtual
  machine" with no `Expected member` abort and no profile patches.
- **Inputs:** `profiles/sgps3/**` (copy source), `profiles/cc/vfs.lua`
  (lowercase mpk naming), the probe test's patch list (LoadingStar members,
  `TitleMenuType.None`).
- **Changes:** `profiles/sghd/{game,vfs,sprites,charset,font,dialogue,
  savedata,scriptvars,tipssystem}.lua`, `profiles/sghd/hud/*.lua`,
  `gamedefinitions.lua` (+ `sghd` entry), `resources/sghd/icondata/*.png`
  (placeholders are fine), `src/vm/vm.h` (`InstructionSet::SGHD`),
  `src/vm/vm.cpp` table switch, `src/vm/opcodetables_sghd.h` as a verbatim
  copy of sgps3 for now, `UseReturnIds = true`.
- **Test:** generalise `test_runtime_probe.py` with a `game` parameter;
  for `sghd` assert no `Expected member`, mounts as MPK, VM init, and that
  `Return` resumes at Call+6 (C2 fixed). Keep the `sgps3` probes as-is.
- **Do not:** touch sprites ids beyond what the fixture needs; implement
  menus.
- **Blockers resolved:** C1, C2, half of C5.

## Task 2 — `opcodetables_sghd.h`: eliminate Dummy slots and fix layouts

- **Goal:** none of the 16 Dummy slots remain Dummy and all 21 layout
  mismatches consume SGHD-shaped arguments; unknown semantics log once and
  advance.
- **Inputs:** `tests/compat/fixtures/sghd_opcodes.json` (slot names),
  `sgps3_known_gaps.json` (exact differences), sc3ntist SGHD layouts
  (read-only reference; no code copying).
- **Changes:** `src/vm/opcodetables_sghd.h`; `InstructionSet::SGHD` branches
  in `inst_controlflow.cpp` (`CallIfFlag`, new `CallFarIfFlag`, `ReturnIfFlag`
  at `00 57`), `inst_system.cpp` (`Nop`, `00 4B/4C/58/59`, `00 35/41/43/50/52/53`),
  `inst_graphics2d.cpp` (`01 05-0A`, `10 05`), `inst_dialogue.cpp` (`01 12`,
  `01 25`), `inst_sound.cpp` (`00 23/37/38`), `inst_gamespecific.cpp`
  (`10 12/22/23/24/27/33/37`, `10 1A/3F/40/41`). Add a safe default for
  `InstDummy` when `GameInstructionSet == SGHD` (advance 2 bytes, log Error).
- **Test:** (a) `test_opcode_table_audit.py` gains an `sghd` section whose
  expected gap lists are empty; (b) `test_scx_decoding.py` gains a fixture
  that encodes every one of the 37 affected opcodes and asserts the
  impacto-layout decoder stays in sync with the reference decoder to
  `End`; (c) runtime probe for `sghd` asserts the synthetic script reaches
  `End` and the process exits by itself (not the timeout).
- **Do not:** implement phone/mail semantics here; only argument
  consumption and existing-handler wiring.
- **Blockers resolved:** C3, C4, H3 (control-flow part), M5 (decode part).

## Task 3 — Asset-free VM harness profile

- **Goal:** a committed `profiles/sghd-harness` (or `-harness` flag) that
  starts the VM with no spritesheets, no HUD and `DialogueBoxType.None`, so
  CI can run SCX fixtures end-to-end.
- **Changes:** profile only, plus whatever `src/profile/sprites.cpp:48`
  needs to tolerate an empty `SpriteSheets` table (today it aborts). Guard
  with a profile flag.
- **Test:** `test_runtime_probe.py` runs the SGHD fixture through the
  harness in the GitHub workflow (`desktop.yml` already runs the probes
  with `ALSOFT_DRIVERS=null` under `xvfb-run`).
- **Blockers resolved:** enables CI for everything after this.

## Task 4 — Save adapter skeleton (`SaveDataType.SGHD`)

- **Goal:** round-trip FlagWork, ScrWork, main thread IP/buffer/call
  stack/return ids and read-line bitmaps through a fork-native file.
- **Inputs:** `src/games/chlcc/savesystem.cpp` as template;
  `src/data/savesystem.h` interface.
- **Changes:** `src/games/sghd/savesystem.{h,cpp}`, `src/profile/data/savesystem.cpp`
  (new enum value), `profiles/sghd/savedata.lua`.
- **Test:** unit-level C++ or a Python driver via the harness: run the
  fixture to a label, save, restart, load, assert the trace continues at
  the saved address. Slot count 80 + 48.
- **Do not:** parse Steam `SAVEDATA.DAT` (format unknown).
- **Blockers resolved:** H2 (engine side).

## Task 5 — First real boot on Windows (owner-assisted, not in CI)

- **Inputs:** owner's Steam install; procedure in `tests/compat/README.md`.
- **Steps:** owner records `USRDIR` listing, mpk headers, `system.mpk`
  file ids, start script id (sc3tools/sc3ntist), movie signatures. Thread
  04 fills `profiles/sghd/vfs.lua`, `sprites.lua` ids, `StartScript`, and
  runs `impacto -g sghd -ll Debug -lf sghd.log` on Windows (or the owner
  does and returns the log).
- **Exit criterion:** title screen or first dialogue line visible; log
  lists every `VMStub` and unknown opcode hit, which becomes the Task 6
  input.
- **Blockers resolved:** C5 fully; converts "Not Tested" rows to evidence.

## Task 6 — Dialogue box, charset and font for `sghd`

- **Inputs:** Task 5 log/screenshot; sc3tools `resources/sghd/charset.utf8`.
- **Changes:** `profiles/sghd/charset.lua` generated from the charset file
  (write the generator script under `tools/`), `font.lua`, `dialogue.lua`
  with a `DialogueBoxType` that renders (CC's as a starting point),
  nameplate sprites.
- **Test:** text-token unit test (charset index → glyph) plus Windows
  screenshot comparison.
- **Blockers resolved:** H4, M1.

## Task 7 — Phone and mail (largest task; split further once scripts are known)

- 7a. Catalogue: from the owner's sc3ntist dump, list every `10 37`/`10 38`
  subtype with arguments and the ScrWork/FlagWork touched around them.
  Output: `docs/phone-protocol.md` and a JSON fixture of subtype sequences.
- 7b. State machine in `src/games/sghd/phone.cpp` backed by ScrWork (so
  Task 4 saves it); handlers for all subtypes incl. `10/14/15/1A`.
- 7c. UI: mail list, read view, reply selection, phone menu, incoming-call
  notification using `system.mpk` sprites; link tokens `0x09`/`0x0B` in
  `src/text/textparser.cpp` under `InstructionSet::SGHD`.
- **Test:** state-machine unit tests from the 7a fixture; Windows playthrough
  of chapter 1 to the first branching mail.
- **Blockers resolved:** H1, M4.

## Task 8 — Audio/video details

- SE/voice layouts' semantics (M3) with real files; movies: decide skip vs
  transcode after `ffprobe` (M2); Win32 no-ops (L1); achievements (L2).

## Suggested order and parallelism

Tasks 1 → 2 → 3 → 4 are sequential and asset-free (one thread). Task 5 is
owner-gated and can run as soon as Task 1 lands. Tasks 6 and 7a can start
after Task 5; 7b/7c after 7a; Task 8 last.

## First task for Thread 04

**Task 1.** It is small, unblocks every later task, is verifiable in CI with
existing fixtures, and its definition of done is already encoded in
`tests/compat/test_runtime_probe.py` (reach the VM, mounts as MPK, Return at
Call+6).
