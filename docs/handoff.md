# Project Handoff

## Current Milestone
Thread 07c — STEINS;GATE title menu (Medium), branch
`phase-03-sghd-implementation`. Windows round 5 (Thread 07b artifact, real
Steam data) reached `TitleMenu(type: 0/1)` but no title and no `MAIN00.SCX`.
The title protocol was reconstructed from `sghd-context.txt`; the engine
side (decisions through SF_TITLEEND/SW_TITLECUR, keyboard + mouse) is
implemented and tested synthetically. **Not yet verified on real data; no
title artwork yet** (TITLE_CHIP regions unnamed). Report:
[threads/07c-title-menu.md](threads/07c-title-menu.md). Thread 07b report:
[threads/07b-first-real-boot.md](threads/07b-first-real-boot.md).
Next major milestone unchanged: **Thread 08 — native iOS ARM64 build (Medium)**.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Thread 07b head (`4eabb721`, shipped);
  Thread 07c on `phase-03-sghd-implementation`.
- No commercial assets, script dumps, private reports, logs, screenshots or
  secrets are committed. Evidence constants only:
  `tests/compat/fixtures/sghd_steam_evidence.json` (Thread 07c adds
  `title_protocol`: variable indices, title types, choice ids).

## Windows round 5 (owner, done)
`menu-retry.log`: fresh config OK, real archives and the eight startup
scripts load, `TitleMenu(type: 0)` and `(type: 1)` reached, title movie 37
missing (Bink 2, skipped), title thread polling, `MAIN00.SCX` not reached,
exit 0 on close. Earlier launches segfaulted intermittently (no log yet).
`sghd-context.txt`: every `10 34`/`00 44` use with context.

## Completed Work (Thread 07c)
- Protocol: `10 34` types 0/1/2/3; both title loops (press start, main
  menu) wait for SF_TITLEEND (1241); main-menu choice in SW_TITLECUR (2139):
  0, 10, 11, 20-24, 30, 40; SW_TITLEMODE (2115) 3 = main menu. The scripts
  use impacto's common variable layout; the PS3 overrides of
  SW_TITLEDISPCT/SW_SYSMENUCT/SW_TITLE were removed.
- `UselessJump` with identical labels is now taken (the press-start loop
  could never advance otherwise).
- `TitleMenuType.SGHD` (`UI::SGHD::TitleMenu`): Enter/Space/click for press
  start; Up/Down, hover and click on START…HELP boxes (measured from the
  owner's screenshot); only START enabled. No sprites until named.
- Not implemented: title artwork, LOAD/EXTRA/CONFIG/HELP, idle attract
  mode, `10 34 3` semantics, title movie.

## Verification
- Orb, `impacto-desktop:ubuntu24`, binary rebuilt from this branch:
  `python3 -m unittest discover -s tests/compat` with `IMPACTO_BIN` →
  **133/133 OK** (96 unit + 37 probes; the 5 new `SghdTitleMenuProbe` cases use
  real X keyboard/mouse events, repeated 4× without a failure).
- clang-format clean on new/changed C++ (pre-existing phone line excepted).
- GitHub Actions: see CI section.

## Status split
- **Synthetic-verified:** title protocol (press start → menu → START →
  next script), keyboard/mouse input, disabled-item skipping, UselessJump,
  title scriptvars, plus everything from 07b.
- **Verified on real Steam data:** boot through the startup scripts to the
  title instructions without crash/desync (round 5).
- **Needs the owner's machine:** START on the real title reaching
  `MAIN00.SCX` and the first dialogue; title artwork once named.
- **Missing:** title artwork, other title items, phone UI, movies (Bink 2),
  backlog/system/save menus, selection/system-message sprites, save import.

## Blocker — owner action: Windows round 6 (short)
1. In Git Bash, download artifact `impacto-windows-x64-<sha>` of the latest
   green `Desktop Windows` run for this branch, unzip, `cd` into it:
   ```bash
   G="/c/Program Files (x86)/Steam/steamapps/common/STEINS;GATE"
   mkdir -p gamedata/sghd
   for a in script system bgm se voice bg chara mask; do cp "$G/USRDIR/$a.mpk" gamedata/sghd/; done
   ./impacto.exe -g sghd -uc ./title-config.toml -ll Info -lf sghd-title.log
   ```
   When the title music starts, wait 3 s, press **Enter** (press start),
   wait 3 s, press **Enter** again (START is preselected; nothing is drawn
   for the menu yet). Wait 20 s, press Enter a few times if a text box
   appears, close. Expected in `sghd-title.log`:
   `TitleMenu: press start (SW_TITLECUR = 0)`, then
   `TitleMenu: main menu choice (SW_TITLECUR = 0)`, then
   `Loading script "..."` lines after the title (ideally `MAIN00.SCX`); any
   `has not advanced for 5 s` line shows the next wait. Share the log and
   one line on what was visible/audible. If it crashes, share the log
   anyway (last lines matter).
2. Title artwork: from a checkout of this branch,
   `python tools/sghd_inspect.py regions "$G" regions`, open
   `regions/index.html` locally, and reply with lines like
   `START normal: TITLE_CHIP x y w h` for: START/LOAD/EXTRA/CONFIG/HELP
   chips (normal and selected), orange cursor bar, background panel,
   satellite, logo, gears, copyright, key hints. Names and numbers only;
   never share the PNGs.

## Architectural Decisions
ADR-007…010 unchanged. Thread 07: desktop is test infrastructure; inherited
UI from other titles is removed rather than scaled; the font uses the
executable's own table (32-unit em scaled to the 48 px cell). Thread 07b:
an SGHD instruction whose engine UI does not exist yet must never wait for
that UI (consume, log, yield); the census layout table is the reference for
byte consumption. Thread 07c: SGHD script variables follow the common
(RNE-era) layout where the scripts prove it; engine menus report decisions
through the scripts' own flags/variables, never by jumping in the script.

## Next Thread
Thread 08 — native iOS ARM64 build and minimal app shell. **Mode: Medium.**
Scope and dependency list: [ios-transition.md](ios-transition.md). Apply
the round-6 log and the TITLE_CHIP region names in a short follow-up
(sprites = Low, mechanical; the path after START = Medium).
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
Code commit `a860ed3c`, pushed with docs commit `15e8de78`:
- Desktop Linux [run 37850634940](https://github.com/Tasnemo/impacto-ios/actions/runs/37850634940):
  **success** — 133 unit tests (96 + 37 skipped), build, launcher smoke 2/2,
  37 runtime probes OK incl. the 5 X-input `SghdTitleMenuProbe` cases.
- Desktop Windows [run 37850635115](https://github.com/Tasnemo/impacto-ios/actions/runs/37850635115):
  **success** — unit tests, build, artifact
  `impacto-windows-x64-15e8de787aa285644f7a4eefcccf8376ec3213be` (expires 2026-11-07). Built only; the owner runs it (round 6).
