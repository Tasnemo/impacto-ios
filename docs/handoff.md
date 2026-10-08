# Project Handoff

## Current Milestone
Thread 06 — STEINS;GATE (Steam) desktop compatibility from the owner's
census, Medium mode, branch `phase-03-sghd-implementation`. Everything the
census supports is **done and verified on synthetic data**; the thread
**stopped at a genuine blocker: sprite rectangles, the exact font width
table, the phone UI and the first real boot need owner-side runs (Windows
round 3 below) or High-mode reverse engineering.** No iOS work.

## Repository State
- `Tasnemo/impacto-ios`; `master` = Thread 05 head (`3546e4ea`). Threads
  04–06 on `phase-03-sghd-implementation`.
- Thread 06 commits: `e8192a1d` (census v2 + `sghd_inspect.py`),
  `8af7a807` (profile 1080p/font/sheets/LAY, `10 3A`, phone bits, save
  format 2), then dialogue-box + docs commits (see `git log`).
- No commercial assets, script dumps, private reports or secrets are
  committed. Evidence constants only:
  `tests/compat/fixtures/sghd_steam_evidence.json`.

## Completed Work (Thread 06)
Report: [threads/06-sghd-census.md](threads/06-sghd-census.md).
- Decode integrity of all 190 scripts: [sghd-decode-integrity.md](sghd-decode-integrity.md).
- `10 3A` → one expression (`InstUnk103ASGHD`); `10 37` type `0x1E` parsed.
- Profile: 1920×1080 design; Steam sheet sizes; font 64×46/48 px with
  ink-derived widths (`tools/gen_sghd_font_widths.py --census|--install`);
  LAY little-endian, tex multipliers 1; UI/sprite coordinates PS3 ×1.5.
- Dialogue: generic `PlainDialogueBox`, no per-game configure needed.
- Phone: catalogue [phone-protocol.md](phone-protocol.md); item bits
  (`10 37` 0x00-0x03) implemented (`src/games/sghd/phone.h`).
- Saves: format 2 (phone block per slot, global system data
  FlagWork bytes 100-149/460-499 + ScrWork 600-999, `00 2A` types 0/2).
- Tools: census v2; `tools/sghd_inspect.py` (`sheets`, `sprites`, `crops`,
  `widths`).

## Verification
- Orb, `impacto-desktop:ubuntu24`, binary rebuilt from this branch
  (`-Werror`): `python3 -m unittest discover -s tests/compat` **106/106**
  with `IMPACTO_BIN` (80 + 26 probes); without a binary 80 pass, 26 skipped.
  Launcher smoke PASS. clang-format clean on changed C++.
- GitHub Actions: see CI section.

## Known Failures / Limitations
- **No real game data has been executed.** Everything runtime is synthetic.
- Sprite rectangles are PS3 ×1.5 guesses (DATA01 3072×1788 and BACKLOG
  2048×1080 are not 1.5× PS3 layouts). Font widths approximate.
- Whether the Steam scripts' text-style data (`01 0E`) is 720p (assumed,
  scaled by impacto) is unchecked — census v2 dumps it.
- Phone polarity inferred from script idioms; phone UI and sub-types
  0x05-0x1E not implemented → player-driven phone triggers impossible.
- Movies never play (Bink 2). Save format is fork-native, not SAVEDATA.DAT.
- 4 decode overruns unresolved (`_MAIL` 4/27, `ANIME` 11, `SG07_01` 0).

## Blocker — owner action: Windows round 3
From a checkout of `phase-03-sghd-implementation` (Python 3.9+, no extra
packages; `$G = "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE"`):

```powershell
python tools\sghd_census.py $G > sghd-census-v2.txt          # ~5 min, numbers/names only
python tools\sghd_inspect.py sprites $G > sghd-sprites.txt   # opaque-region boxes of the 4 profile sheets
python tools\sghd_inspect.py widths $G > sghd-widths.txt     # exe glyph width table candidates
python tools\sghd_inspect.py crops $G crops                  # LOCAL ONLY: open crops\index.html, do not share
```
Share the three `.txt` files privately (all numbers/names). From
`crops\index.html`, note which profile sprites look wrong (names only).

Optional first boot: download artifact `impacto-windows-x64-<sha>` of the
latest green `Desktop Windows` run, copy the 8 mounted archives (`script`,
`system`, `bgm`, `se`, `voice`, `bg`, `chara`, `mask` `.mpk`) to
`gamedata\sghd\`, run `.\impacto.exe -g sghd -ll Debug -lf sghd.log`, play
to the first dialogue line and the first phone mail, share `sghd.log` (and
optionally describe what is visible). Steps: [sghd-steam-evidence.md](sghd-steam-evidence.md).

What each output unblocks: census v2 → remaining layout evidence and the
720p/1080p text-style question; `sprites` → real ADVBox/nametag/menu
rectangles; `widths` → exact font widths (replace the generated table);
`sghd.log` → phone polarity (`Phone:` debug lines vs what the game shows),
real-data crashes.

## Architectural Decisions
ADR-007…010 unchanged. Thread 06: the Steam profile uses a 1920×1080 design
like cclcc/mo8 (scripts stay 720p, impacto scales them); phone item state is
fork-native and lives in `SGHD::Phone::ItemBits`, saved per slot; global
system data follows the CHLCC ranges; census-proven layout changes are
pinned separately from the Thread 03 gap list (`CENSUS_WIRING`).

## Next Thread
Thread 07 — apply Windows round 3 (sprite rectangles, width table, census v2
fixes, boot-log issues). **Mode: Medium.** Phone UI (sub-types 0x05-0x1E,
`PHONE*.DDS` layout, MACROSYS2 phone loops) is a separate thread at **High**.

### Continuation prompt
> Read `workme.md`, `docs/handoff.md`, `docs/project-state.md`,
> `docs/phone-protocol.md`, `docs/sghd-decode-integrity.md` and
> `tests/compat/README.md`. Branch `phase-03-sghd-implementation`. Inputs:
> the owner's private `sghd-census-v2.txt`, `sghd-sprites.txt`,
> `sghd-widths.txt` (and `sghd.log` if available). Fix any layout the census
> v2 "Decode errors in reachable code" section proves wrong; replace sprite
> rectangles in `profiles/sghd/**` with boxes from `sghd-sprites.txt` (record
> them in `fixtures/sghd_steam_evidence.json` with pinning tests); if
> `widths` found a table with correlation > 0.9, generate `font.lua` from it;
> check the text-style dump (glyph height 32 = 720p). Never commit the private
> files. Keep `tests/compat` green; commit, push, update handoff. No iOS.

## Orb state is disposable
This orb had Docker image `impacto-desktop:ubuntu24`, vcpkg at
`~/.local/share/impacto-tools/vcpkg`, binary cache `~/.cache/impacto-vcpkg`,
build `ci-build/ubuntu24`, install `release/ubuntu24`, helpers
`~/bin/impacto-{setup-build,build,test}.sh`. Not committed; rebuild per
`docs/desktop-build.md` (cold build ≈ 30 min incl. Docker daemon start).

## CI
See the end of this file for the run results of the final Thread 06 commit.
