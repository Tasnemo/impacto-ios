# Project Handoff

## Current Milestone
Thread 05 — STEINS;GATE (Steam) desktop Tasks 5–8, Medium mode, branch
`phase-03-sghd-implementation`. Used the owner's first evidence report. All
work that the evidence supports is **done and verified**; the thread
**stopped at a genuine blocker: Tasks 6–7 (and the Task 5 boot itself) need
the second-round census from the owner's install.** No iOS work.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Threads 01–02. Thread 03 on
  `phase-02-steins-compatibility`, Threads 04–05 on
  `phase-03-sghd-implementation` (not merged; owner's decision).
- Thread 05 commits: `a3cf1d61`/`bd019d7c` (Windows CI), `046508b0`
  (Task 5 profile + movie skip), `2a5c6630` (census tool + doc),
  `884146f2` (L4 audio fallback), then docs.
- No commercial assets, script dumps, private reports or secrets are
  committed. Evidence constants only:
  `tests/compat/fixtures/sghd_steam_evidence.json`.

## Completed Work (Thread 05)
- Task 5: `vfs.lua` confirmed, `StartScript = 2` (`_STARTUP_WIN.SCX`),
  sheet ids by name, unmatched sheets `ScriptHandled`; pinned by
  `test_sghd_profile_evidence.py`.
- Task 8: movies unmounted (Bink 2); three crash/hang bugs in the
  undecodable-movie path fixed; Ogg Vorbis BGM/SE/voice path probed; L4
  (no audio device) fixed.
- `tools/sghd_census.py` + `tests/compat/test_sghd_census.py`.
- `.github/workflows/desktop-windows.yml` (Windows artifact).
- Report: [threads/05-sghd-steam-evidence.md](threads/05-sghd-steam-evidence.md);
  decisions: [sghd-steam-evidence.md](sghd-steam-evidence.md).

## Verification
- Orb, `impacto-desktop:ubuntu24`, incremental rebuild (`-Werror`):
  `python3 -m unittest discover -s tests/compat` **86/86** with
  `IMPACTO_BIN` (63 + 23 probes); without a binary 63 pass, 23 skipped.
  Launcher smoke 2/2 PASS. clang-format clean on changed C++.
- GitHub Actions: Linux and Windows both green on `884146f2` (CI section below).

## Known Failures / Limitations
- **No real game data has been executed.** Everything runtime is synthetic.
- Sheet sizes and all sprite rectangles are PS3 values; font grid 64×14 and
  widths are PS3; `LayFileBigEndian = true` is PS3; dialogue box `Plain`.
- Movies never play (Bink 2). Phone/mail: parsed and logged only.
- Stubbed SGHD opcodes unchanged (list in `tools/sghd_census.py`
  `IMPACTO_STUBS`). Save format fork-native, ranges CHLCC defaults.

## Blocker — owner action
1. Run the census (prints names/numbers only; a few minutes):
   ```powershell
   cd <checkout of phase-03-sghd-implementation>
   python tools\sghd_census.py "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE" > sghd-census.txt
   ```
   Share it privately with the next thread. It unblocks Task 6 (sheet
   sizes, font widths, LAY byte order), Task 7a (phone/mail catalogue) and
   Task 8 (codecs, movie ids) and checks every SGHD layout on all 190
   scripts.
2. Optional, Task 5 exit criterion: download the `impacto-windows-x64-<sha>`
   artifact of the latest green `Desktop Windows` run, copy the 8 archives
   to `gamedata\sghd\`, run `.\impacto.exe -g sghd -ll Info -lf sghd.log`,
   share the log (+ screenshot). Steps: [sghd-steam-evidence.md](sghd-steam-evidence.md).
3. Sprite rectangles (dialogue box, nameplate, title, phone) need someone to
   look at the sheets; the census only gives sizes.

## Architectural Decisions
ADR-007…010 unchanged. Thread 05: movies are skipped (not mounted, and an
undecodable movie never blocks the VM); audio falls back to silent channels
per run without touching user config; evidence constants live in one JSON
fixture that tests pin the profile to.

## Next Thread
Thread 06 — census-driven Tasks 6/7 (font, dialogue box, LAY, phone/mail
catalogue). **Mode: Medium.** Escalate to High only if the census phone
catalogue leaves `10 37` semantics ambiguous.

### Continuation prompt
> Read `workme.md`, `docs/handoff.md`, `docs/project-state.md`,
> `docs/sghd-steam-evidence.md` and `tests/compat/README.md`. Branch
> `phase-03-sghd-implementation`. Input: the attached private
> `sghd-census.txt` from `tools/sghd_census.py` (and `sghd.log` if
> available). First check its decode-error section (fix layouts in
> `src/vm/opcodetables_sghd.h`/`tools/sghd_census.py` if any). Then: sheet
> `DesignWidth/Height` and DDS formats, `font.lua` grid/widths (generator
> under `tools/`), `LayFileBigEndian`, save ranges; record new constants in
> `fixtures/sghd_steam_evidence.json` with pinning tests; write
> `docs/phone-protocol.md` + a JSON fixture from the phone/mail catalogue
> (Task 7a) and start 7b only where semantics are clear. Never commit the
> census. Keep `tests/compat` green; commit, push, update handoff. No iOS.

## Orb state is disposable
This orb had Docker image `impacto-desktop:ubuntu24`, vcpkg at
`~/.local/share/impacto-tools/vcpkg`, cache `~/.cache/impacto-vcpkg`, build
`ci-build/ubuntu24`, install `release/ubuntu24`, helpers
`~/bin/impacto-{setup-build,build,probe}.sh`. Not committed; rebuild per
`docs/desktop-build.md` (cold build ≈ 25 min).

## CI
Final code commit `884146f2`:
- Desktop Linux [run 37805385510](https://github.com/Tasnemo/impacto-ios/actions/runs/37805385510):
  **success** — 86 unit tests (63 + 23 skipped), build, launcher smoke 2/2,
  23 runtime probes OK.
- Desktop Windows [run 37805385451](https://github.com/Tasnemo/impacto-ios/actions/runs/37805385451):
  **success** — artifact `impacto-windows-x64-884146f25dc52f9de548c6608d1eab5edb23b40e`
  (≈99 MB, 30-day retention; `impacto.exe`, DLLs, `profiles/`, `resources/`).
  Built only; not run on Windows here. Warm-cache run ≈ 20 min, cold ≈ 38 min.
