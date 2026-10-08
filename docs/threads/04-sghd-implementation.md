# Thread 04 — STEINS;GATE (Steam) desktop implementation

- Date: 2026-10-08. Mode: **Medium** (autonomous execution of
  [thread-04-implementation-plan.md](../thread-04-implementation-plan.md)).
- Branch: `phase-03-sghd-implementation`, from `phase-02-steins-compatibility`
  (`2f64bdbc`, the Thread 03 head; not yet merged into `master`).
- Environment: Debian 12 orb, `impacto-desktop:ubuntu24` container (Ubuntu
  24.04 / GCC 13.3, CMake 3.31.10, pinned vcpkg), software GL under Xvfb,
  `ALSOFT_DRIVERS=null`. No Steam files, Windows host, GPU or audio device.

## Outcome

Tasks 1–4 are complete and verified against the real engine with synthetic
fixtures. The charset part of Task 6 is complete. **Task 5 is a genuine
blocker**: it requires evidence from the owner's legally obtained Steam
installation, which is not available in this thread. Tasks 6 (font, dialogue
box), 7 (phone/mail) and 8 (except L1) depend on that evidence. No iOS work
was started.

## Commits

| Commit | Task | Summary |
|---|---|---|
| [`de9c74e2`](https://github.com/Tasnemo/impacto-ios/commit/de9c74e2) | 1 | `sghd` game id + profile, `InstructionSet::SGHD`, `UseReturnIds = true`, VM reached unpatched |
| [`91ef6707`](https://github.com/Tasnemo/impacto-ios/commit/91ef6707) | 2 | SGHD opcode table: 37 slots wired, no `InstDummy`, `inst_sghd.cpp`, BacklogMenu crash fix |
| [`73bc351b`](https://github.com/Tasnemo/impacto-ios/commit/73bc351b) | 3 | `profiles/sghd-harness`, self-terminating runs with script exit status, CI on this branch |
| [`16316067`](https://github.com/Tasnemo/impacto-ios/commit/16316067) | 4 | Fork-native save adapter `SaveDataType.SGHD`, cross-process round trip |
| [`de118916`](https://github.com/Tasnemo/impacto-ios/commit/de118916) | 6 (part) | Generated Steam charset from sc3tools data |
| [`1ca03b9f`](https://github.com/Tasnemo/impacto-ios/commit/1ca03b9f) | 5 (prep) | `tools/sghd_evidence.py` owner-side evidence collector |

The documentation checkpoint follows these; find it with
`git log -1 --format=%H -- docs/threads/04-sghd-implementation.md`.

## What changed in the engine

- `src/vm/vm.h`, `vm.cpp`: `InstructionSet::SGHD` (appended; other enum
  values unchanged) selects `src/vm/opcodetables_sghd.h`. Optional
  `Vm.ExitWhenThreadsEnd` / `Vm.ExitCodeScrWork` quit once no script thread
  remains.
- `src/vm/inst_sghd.{h,cpp}`: `InstCallIfFlag`, `InstCallFarIfFlag` (real
  semantics), no-op `InstNopSGHD` (`00 52`, `00 5F`, `10 12`, `10 40`, `10 41`),
  `InstUnknownSGHD` for never-emitted slots, and consume-and-log stubs.
- Guarded SGHD branches: `InstSel` (type 0 u16), `InstSetRevMes` (type 3
  order), `InstCHAload` (type 0 u16), `InstSaveMenu` (type 0A byte),
  `InstLoadData` (type 0A no args), `InstTips` (type 0 second label).
- `src/games/sghd/savesystem.{h,cpp}`, `SaveDataType::SGHD`, profile keys
  `FlagWorkRanges` / `ScrWorkRanges`.
- Shared fixes: generic backlog capacity (`src/profile/ui/backlogmenu.cpp`),
  `Game::ExitCode` used by `main()` and GL/Vulkan `Window::Shutdown`.
- Profiles: `profiles/sghd/**` (from `sgps3`, which is untouched),
  `profiles/sghd/vm.lua`, `profiles/sghd-harness/game.lua`; both registered
  hidden in `gamedefinitions.lua`.

## Verification (actual results)

- Full container build from a fresh orb (67 vcpkg ports from source, engine
  with `-Werror`), then incremental rebuilds after every task.
- `python3 -m unittest discover -s tests/compat`: **65 tests, 47 pass + 18
  probes skipped** without a binary.
- With `IMPACTO_BIN=release/ubuntu24/impacto` in the container: **65/65
  pass** (3 consecutive full runs after the Xvfb change).
- Launcher smoke (`.github/scripts/desktop-smoke.py`): 2/2 PASS after each
  engine change.
- Negative control: loading without a prior save never resumes (timeout 124).
- clang-format 18 clean on new files; touched upstream files have no new
  violations.
- GitHub Actions [run 37749270249](https://github.com/Tasnemo/impacto-ios/actions/runs/37749270249)
  on `1ca03b9f`: success (65 unit tests, build, smoke 2/2, 18 runtime
  probes). Earlier runs were cancelled by newer pushes (concurrency group).

Key runtime facts:
- `SghdRuntimeProbe`: unmodified `sghd` profile mounts 8 `.mpk`, starts the
  VM, `Return` lands at Call+6, `Nop` then `End`.
- `SghdTask2RuntimeProbe`: 55-instruction trace of the 37-opcode fixture
  equals `sghd_reference_trace` exactly; no crash recovery/unknown-opcode
  log; stubs reported.
- `SghdHarnessRuntimeProbe`: harness exits 0 by itself; status 7 from
  `ScrWork[4000] = 7`.
- `SghdSaveRoundTripProbe`: save run exit 110; file parsed in Python
  (slot 79, IP, depth 1, return id 0, ScrWork/FlagWork values, read line);
  load run exit 142 (state verified in the restored subroutine, then the
  restored `Return`).

## Not verified / limitations

- Nothing ran against real Steam data. Synthetic fixture success is not game
  compatibility.
- Stubbed opcode semantics (phone, SystemMes 0A–11, checkpoints, `00 4B/4C/
  50/53/58/59`, `01 06-0A`, `10 1A/27/3F`) are unknown, only parsed.
- Save: fork-native only; ranges unverified; no menus; tips/CG/BGM unlocks,
  thumbnails not saved.
- `font.lua`, `dialogue.lua`, sprite ids, `StartScript` are PS3 values or
  placeholders. Movies are not mounted.
- Windows/macOS builds were not run; the DX9 window was not changed.

## Blocker (Task 5) and evidence

Task 5 requires, from the owner's Windows Steam installation: install
listing, MPK versions, `system.mpk`/`script.mpk` entry ids, movie
signatures, then a first boot log. None of this exists in the repository or
the orb (searched `docs/`, `tests/`, `workme.md`). Continuing without it would
mean guessing archive ids, sprite layouts and phone semantics, which the
plan forbids. `tools/sghd_evidence.py` reduces the owner step to one
command; see the handoff for the continuation prompt.

Recommended mode for the continuation: **Medium** for Task 5/6 once the
evidence exists; **High** for Task 7a only if the script dump leaves phone
semantics ambiguous.
