# Thread 07b — first real Steam boot: title wait and startup diagnostics (Medium)

Branch `phase-03-sghd-implementation`, 2026-10-08. Follow-up to Thread 07;
the iOS roadmap is unchanged (Thread 08 = native iOS build is still next).

Input: the owner's private `sghd-debug.log` (Windows build, real English
Steam data, `-ll Info`, fresh user config `-uc .\sghd-test-config.toml`)
and one screenshot of the original game's title screen (reference only; not
committed). No game data was used in this orb.

## What the log shows

- Profile, all eight archives, renderer, audio, video and the VM start.
- `_STARTUP_WIN.SCX` runs: `DataInit`, `Phone(0x04)`, `Unk103F(0)`,
  SystemMes modes 0, 3 (string 91), 2 (255), 6, 7 within the same second,
  then `Useless0053(1, 80, label 22)` one second later, two texture uploads
  2-3 s later, and then nothing until the owner closes the window ~18 s
  later. No decode error, no unknown opcode, no crash.
- Release builds hide every `ImpLogSlow` stub message: only SGHD-specific
  stubs (logged with `StubOnce`) appear. A shared handler that waits (for
  example a title menu) leaves no trace in the log.

## Findings

| Question | Answer | Evidence |
|---|---|---|
| Which startup stub affects progression? | **None of the logged ones.** SystemMes 0/3/2/6/7 is Init, SetMes, Init2, FadeIn, FadeOut with no mode 5 (Main, the only input wait): a timed notice. Phone 0x04 registers six data tables (Thread 06). `10 3F` has one byte and no observed effect. `00 53` is "Useless" in sc3ntist. All five finished within ~1 s of each other. | log timestamps; `InstSystemMes` mode table; [phone-protocol.md](../phone-protocol.md) |
| What blocks? | **`10 34`, wired to the CHAOS;HEAD `InstTitleMenuOld`.** The Steam scripts encode `10 34` with one type byte (sc3ntist `Unk1034`; the census decoded all 190 scripts with that layout). `InstTitleMenuOld` reads no byte and blocks until an engine title menu reports a choice; with `TitleMenuType.None` the menu is a `NullMenu` whose choice never comes, so the thread waits forever, silently (its log is `ImpLogSlow`). Cancel (B) would release it into a desync. This matches "engine running, no title, no dialogue". Not yet proven on the real script: the next run's stall report will show it. | `SghdFixedLayoutAudit`; sc3ntist `SGHDDisassembler.cpp` |
| How does the Steam game handle its title? | Engine-side. All title artwork is in `system.mpk` `TITLE_CHIP.DDS` (a 1932×1125 full-screen region plus chips; Thread 07 region list), not in `bg.mpk`, and the reference screenshot shows START/LOAD/EXTRA/CONFIG/HELP with an orange cursor bar (`TITLE_CHIP` has a 10×47 region). `10 34 <type>` has RNE's `TitleMenu(type)` layout (Init/Main/Init2), not CHAOS;HEAD's argument-less one. Which ScrWork receives the choice is not known yet. | fixture `sheet_regions`, screenshot |
| Use the engine title-menu abstraction? | Yes, eventually: a `TitleMenuType` for SGHD drawn from `TITLE_CHIP.DDS`, fed by `10 34`. It needs the named chip rectangles and the script protocol around `10 34` first; no placeholder or invented artwork was added. | — |
| Another missed layout | `10 36` is `Nop3` (one byte) in the Steam scripts; impacto used `InstBGeffect`, which reads up to four more expressions for types 0/1/3/5/6/7/9. | `SghdFixedLayoutAudit` |
| Fresh-config fix | Reproducible with `-uc <new file>`: the run creates and uses a default config. The crashing config was the default `%APPDATA%\Committee of Zero\Impacto\userconfig.toml`; without that file and the crash output the cause cannot be identified (candidates: a non-OpenGL `ActiveRenderer`, an old `Display`/resolution). | log line "Configuration file ... doesn't exist, creating now" |

## Changes

| Change | Files | Test |
|---|---|---|
| `10 34` → `InstTitleMenuSGHD`: consumes the type byte, logs `TitleMenu(type: N)` once per type, never waits, yields the frame (a polling loop cannot freeze the engine; the stall report shows it) | `src/vm/inst_sghd.{h,cpp}`, `opcodetables_sghd.h` | `SghdTitleStartupProbe`, `SghdFixedLayoutAudit.test_title_menu_slot_never_waits` |
| `10 36` → `InstByteArgStubSGHD` (one byte) | `opcodetables_sghd.h` | `SghdTitleStartupProbe` |
| Fixed-layout audit: every untyped census layout vs the bytes its handler pops; four reviewed branch-only exceptions | `tests/compat/test_opcode_table_audit.py` | `SghdFixedLayoutAudit` (fails on the old table with exactly `10 34`, `10 36`) |
| Stall report: `root.Vm.StallReportSeconds` (sghd: 5) logs once, at Info, a script thread that ended every frame at the same instruction for that long, with script name, buffer, address, next opcode and call depth | `src/vm/vm.cpp`, `src/profile/vm.{h,cpp}`, `profiles/sghd/vm.lua` | `SghdTitleStartupProbe.test_stall_is_reported_once_with_position` |
| Script loads logged at Info (`Loading script "X" (id N) into buffer B`) | `src/vm/vm.cpp` | `SghdTitleStartupProbe.test_script_load_is_logged_at_info` |
| Census `--context[=gg:oo,...]`: every use of the given opcodes with 6 preceding and 16 following decoded instructions (numbers only) | `tools/sghd_census.py` | `CensusTool.test_context_mode_lists_uses_with_neighbours` |

## Verification

- Orb, `impacto-desktop:ubuntu24`, rebuilt binary: `python3 -m unittest
  discover -s tests/compat` with `IMPACTO_BIN` → 125/125 OK (93 unit + 32
  probes); launcher smoke PASS.
- Regression power, checked by temporarily restoring the old table: the
  new probe hangs (exit 124) and its stall report reads `at 0x10, next
  opcode 10:34` — the silent wait suspected in the real boot (to be
  confirmed by the round-5 log); the audit
  reports exactly `10 34` (`InstTitleMenuOld`, no byte) and `10 36`
  (`InstBGeffect`, `B E E E E E E E`).
- CI: see [handoff.md](../handoff.md) "CI".

## Status split

- **Synthetic-verified:** `10 34`/`10 36` byte consumption and no wait; stall
  report; script-load logging; census context mode.
- **Needs the owner's Windows machine:** whether the real script passes the
  title and reaches `MAIN00.SCX` and the first dialogue line; where it waits
  if not; the title protocol around `10 34`.
