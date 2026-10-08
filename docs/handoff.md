# Project Handoff

## Current Milestone
Thread 07 — Steam gameplay baseline and roadmap synchronisation, Medium,
branch `phase-03-sghd-implementation`. The owner's round-3 reports
(census v2, sprite regions, Game.exe width table) are fully applied and
tested. **No first-boot log was provided, so no real game data has been
executed yet.** Next major milestone: **Thread 08 — native iOS ARM64 build
(Medium)**; the first Windows boot runs in parallel on the owner's machine.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Thread 05 head (`3546e4ea`); Threads
  04–07 on `phase-03-sghd-implementation`.
- Thread 07 commits: `1e6b9db0` (evidence: `10 3A`, font widths, text
  styles, sprite checks, `sghd_inspect regions`), `f2d4f729` (roadmap/iOS
  docs), `86acccac` (UTF-8 test fix), plus this docs commit.
- No commercial assets, script dumps, private reports or secrets are
  committed. Evidence constants only: `tests/compat/fixtures/sghd_steam_evidence.json`.

## Completed Work (Thread 07)
Report: [threads/07-gameplay-baseline.md](threads/07-gameplay-baseline.md).
- Roadmap synchronised with `workme.md`: [roadmap.md](roadmap.md) (desktop =
  test infrastructure, Medium default, Thread 08 = iOS build).
- `10 3A` = six expressions (census v2's only reachable decode error); with
  it every reachable instruction stream of the 190 scripts decodes.
- `font.lua` generated from the Game.exe width table (0x12d7f0, 384 glyphs,
  32-unit em, correlation 0.946): `tools/gen_sghd_font_widths.py --exe-widths`.
- Text-style data is 720p → impacto's 1.5× design scaling is right (pinned).
- Sprites checked against Steam opaque regions: ADVBox, left nametag, wait
  icon consistent; inherited CHAOS;HEAD title sprites, backlog sprites and
  `systemmenu.lua` removed; mismatches (selection, system message box)
  recorded in the fixture (`sprite_checks`).
- `tools/sghd_inspect.py`: pixel-level split of merged regions; `regions`
  mode crops every region for naming.
- iOS preparation: [ios-transition.md](ios-transition.md).

## Verification
- Orb, `impacto-desktop:ubuntu24`, rebuilt binary: `python3 -m unittest
  discover -s tests/compat` **117/117** with `IMPACTO_BIN` (89 + 28
  probes); without a binary 89 pass, 28 skipped. clang-format clean.
- GitHub Actions: see CI section.

## Status split
- **Synthetic-verified:** VM/opcodes, branching, phone item bits, saves
  (format 2), Ogg audio path, movie skip, voice table, profile load.
- **Verified against real Steam data (reports, not execution):** script
  decoding, image sizes/DDS headers, LAY, audio codecs, font widths, 720p
  text styles, ADVBox/nametag/wait-icon rectangles.
- **Implemented, not validated:** real boot, title, dialogue rendering,
  BG/character rendering, voice/BGM, phone polarity, system data.
- **Missing:** phone UI (0x05-0x1E), movies (Bink 2), menus, selection and
  system-message sprites, Steam save import.

## Blocker — owner action: Windows round 4 (short)
1. First boot (the only desktop gate before device work). Download artifact
   `impacto-windows-x64-<sha>` of the latest green `Desktop Windows` run,
   unzip, then in that folder:
   ```powershell
   $G = "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE"
   mkdir gamedata\sghd
   foreach ($a in "script","system","bgm","se","voice","bg","chara","mask") { Copy-Item "$G\USRDIR\$a.mpk" gamedata\sghd\ }
   .\impacto.exe -g sghd -ll Info -lf sghd.log
   ```
   Click/press Enter through whatever appears for ~2 minutes, close the
   window, share `sghd.log` privately and say in one line what was visible
   (black screen / title / text box / characters / sound).
2. Optional, sprites: `python tools\sghd_inspect.py regions $G regions`
   (from a checkout of this branch), open `regions\index.html` locally, and
   reply with lines such as `selection background: DATA01 x y w h` for the
   choice box, system message box, date display, save icon (names + numbers
   only; never share the PNGs).

## Architectural Decisions
ADR-007…010 unchanged. Thread 07: desktop is test infrastructure; inherited
UI from other titles is removed rather than scaled; the font uses the
executable's own table (32-unit em scaled to the 48 px cell).

## Next Thread
Thread 08 — native iOS ARM64 build and minimal app shell. **Mode: Medium.**
Scope and dependency list: [ios-transition.md](ios-transition.md). Apply
`sghd.log` findings in a short Medium follow-up when the owner provides it.
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
Final code commit `86acccac`:
- Desktop Linux [run 37822540927](https://github.com/Tasnemo/impacto-ios/actions/runs/37822540927):
  **success** — 117 unit tests (89 + 28 skipped), build, launcher smoke 2/2,
  28 runtime probes OK.
- Desktop Windows [run 37822541335](https://github.com/Tasnemo/impacto-ios/actions/runs/37822541335):
  **success** — unit tests, build, artifact `impacto-windows-x64-86acccac6255eb77fb722ae189cae945f57b6480` (30-day retention).
  Built only; not run on Windows here.
- The previous push (`f2d4f729`) failed on Windows only: a new test read Lua
  with the cp1252 default encoding; fixed by reading UTF-8.
