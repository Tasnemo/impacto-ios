# Project Handoff

## Current Milestone
Thread 07b — first real Steam boot follow-up (Medium), branch
`phase-03-sghd-implementation`. The owner's first Windows boot on real data
(`sghd-debug.log`, private) started everything and ran `_STARTUP_WIN.SCX`,
then showed no title and no dialogue. Cause found in the opcode table
(`10 34` waited forever for a title menu SGHD does not have, and read the
wrong number of bytes); fixed, with a stall report so the next real run
shows any remaining wait. Report: [threads/07b-first-real-boot.md](threads/07b-first-real-boot.md).
Next major milestone unchanged: **Thread 08 — native iOS ARM64 build (Medium)**.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Thread 07 head (`048210d0`); Threads
  04–07b on `phase-03-sghd-implementation`.
- No commercial assets, script dumps, private reports, logs, screenshots or
  secrets are committed. Evidence constants only:
  `tests/compat/fixtures/sghd_steam_evidence.json`.

## Completed Work (Thread 07b)
- Startup stubs triaged from the log: SystemMes 0/3/2/6/7 (timed notice, no
  input wait), Phone 0x04 (data tables), `10 3F`, `00 53` do not stop
  progression.
- `10 34` (Steam: one type byte, RNE-style `TitleMenu(type)`) was wired to
  CHAOS;HEAD `InstTitleMenuOld` (no byte, blocks until a title menu reports
  a choice; SGHD has `TitleMenuType.None`) → now `InstTitleMenuSGHD`:
  consumes the byte, logs `TitleMenu(type: N)` once, never waits, yields the
  frame. Synthetic reproduction: with the old table the harness hangs at
  `10 34` and the stall report names it.
- `10 36` (Steam `Nop3`, one byte) no longer read by `InstBGeffect`.
- `SghdFixedLayoutAudit`: every untyped census layout vs handler pops.
- Stall report (`root.Vm.StallReportSeconds = 5` for sghd) and Info-level
  script-load log lines for Release builds.
- `tools/sghd_census.py --context=gg:oo,...` for the title protocol.
- Title menu: the Steam title is engine-drawn from `TITLE_CHIP.DDS`
  (START/LOAD/EXTRA/CONFIG/HELP + cursor bar, per the owner's screenshot of
  the original game); not implemented yet — needs chip names and the `10 34`
  protocol. No placeholder artwork added.
- Fresh-config fix reproduced as `-uc <new file>`; root cause of the old
  config's crash still unknown (needs that file).

## Verification
- Orb, `impacto-desktop:ubuntu24`, binary rebuilt from this branch:
  `python3 -m unittest discover -s tests/compat` with `IMPACTO_BIN` →
  **125/125 OK** (93 unit + 32 probes); launcher smoke PASS
  (`ALSOFT_DRIVERS=null`). Old table reverted on purpose: the new probe
  fails (exit 124 hang, stall report `0x10 10:34`) and the audit names
  exactly `10 34`, `10 36`.
- clang-format clean on changed C++ (one pre-existing warning in
  `inst_sghd.cpp` phone code is unrelated).
- GitHub Actions: see CI section.

## Status split
- **Synthetic-verified:** VM/opcodes incl. `10 34`/`10 36`, branching,
  phone item bits, saves (format 2), Ogg audio path, movie skip, voice
  table, profile load, stall report.
- **Verified on real Steam data:** script decoding (census), image/LAY/
  audio formats, font widths, text styles, some sprite rectangles; **real
  boot through `_STARTUP_WIN` startup stubs without crash or desync** (log).
- **Implemented, not validated on real data:** passing the title wait,
  first dialogue, BG/character rendering, voice/BGM.
- **Missing:** SG title menu (TITLE_CHIP), phone UI (0x05-0x1E), movies
  (Bink 2), backlog/system/save menus, selection and system-message sprites,
  Steam save import.

## Blocker — owner action: Windows round 5 (short)
1. Boot again with the new build. Download artifact
   `impacto-windows-x64-<sha>` of the latest green `Desktop Windows` run
   for this branch, unzip, copy your existing `gamedata\sghd` folder into
   it, then in that folder:
   ```powershell
   .\impacto.exe -g sghd -uc .\sghd-test-config.toml -ll Info -lf sghd-boot2.log
   ```
   Wait 20 s without input, press Enter three times (2 s apart), wait 20 s
   more, close the window. Share `sghd-boot2.log` privately and say in one
   line what was visible/audible. Expected lines:
   - `Loading script "_STARTUP_WIN.SCX" (id 2) into buffer 0`, then the next
     scripts it loads;
   - `STUB instruction TitleMenu(type: N)` when the title code is reached;
   - success: `Loading script "MAIN00.SCX" ...` and further scenario
     scripts, a text box on screen;
   - otherwise `Script thread N (group G) has not advanced for 5 s: script
     "X" (buffer B) at 0x..., next opcode gg:oo, ...` — the exact wait.
2. Title protocol (numbers only, ~1 min), from a checkout of this branch:
   ```powershell
   $G = "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE"
   python tools\sghd_census.py $G --context=10:34,00:44 > sghd-context.txt
   ```
   Share `sghd-context.txt` privately.
3. Old-config crash: share the contents of
   `%APPDATA%\Committee of Zero\Impacto\userconfig.toml` (settings only),
   or at least its `ActiveRenderer`, `Display` and resolution lines.
4. Later, for the title menu UI: `python tools\sghd_inspect.py regions $G
   regions`, open `regions\index.html` locally and reply with lines such as
   `title START normal: TITLE_CHIP x y w h` for the menu items (normal and
   selected), cursor bar, background panel, satellite, logo, gears,
   copyright, key hints. Names and numbers only; never share the PNGs.

## Architectural Decisions
ADR-007…010 unchanged. Thread 07: desktop is test infrastructure; inherited
UI from other titles is removed rather than scaled; the font uses the
executable's own table (32-unit em scaled to the 48 px cell). Thread 07b:
an SGHD instruction whose engine UI does not exist yet must never wait for
that UI (consume, log, yield); the census layout table is the reference for
byte consumption.

## Next Thread
Thread 08 — native iOS ARM64 build and minimal app shell. **Mode: Medium.**
Scope and dependency list: [ios-transition.md](ios-transition.md). Apply
the round-5 boot log / context report in a short Medium follow-up (title
protocol, then the SG title menu from `TITLE_CHIP.DDS` once named).
Phone UI stays a separate High task.

### Continuation prompt
> Read `workme.md` (sections 4, 15), `docs/handoff.md`, `docs/roadmap.md`
> and `docs/ios-transition.md`. Start from `phase-03-sghd-implementation`
> (create a new branch for iOS work and record it in the handoff). Goal:
> GitHub Actions `macos-15` builds impacto for arm64 iOS with vcpkg
> (`triplets/arm64-ios.cmake`, static), SDL3 app shell, bundle with
> profiles/shaders/resources; disable ffmpeg/libass/imgui/dx9 if they block;
> upload an unsigned app artifact; document signing/sideloading. Keep the
> Linux/Windows workflows green and `tests/compat` passing. No Metal rewrite,
> no game data in CI. Commit, push, update handoff.

## Orb state is disposable
This orb had Docker image `impacto-desktop:ubuntu24`, vcpkg at
`~/.local/share/impacto-tools/vcpkg`, binary cache `~/.cache/impacto-vcpkg`,
build `ci-build/ubuntu24`, install `release/ubuntu24`, helpers
`~/bin/impacto-{setup-build,build,test}.sh`. Not committed; rebuild per
`docs/desktop-build.md` (cold build ≈ 30 min incl. Docker daemon start).

## CI
Code commit `71ea47b4`, pushed with docs commit `bd1a2264`:
- Desktop Linux [run 37832137704](https://github.com/Tasnemo/impacto-ios/actions/runs/37832137704):
  **success** — 125 unit tests (93 + 32 skipped), build, launcher smoke 2/2,
  32 runtime probes OK (incl. `SghdTitleStartupProbe`).
- Desktop Windows [run 37832137685](https://github.com/Tasnemo/impacto-ios/actions/runs/37832137685):
  **success** — unit tests, build, artifact
  `impacto-windows-x64-bd1a226437c4c9800da24dc31289255772571dd8`
  (expires 2026-11-07). Built only; the owner runs it (round 5).
