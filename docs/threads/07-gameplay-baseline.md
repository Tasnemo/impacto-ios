# Thread 07 — Steam gameplay baseline and roadmap synchronisation (Medium)

Branch `phase-03-sghd-implementation`, 2026-10-08. Inputs: the owner's
private `sghd-census-v2.txt`, `sghd-sprites.txt`, `sghd-widths.txt`
(not committed). No first-boot log was attached.

## Done (verified)

| Task | Change | Evidence |
|---|---|---|
| 1 Roadmap | `docs/roadmap.md` rewritten to follow `workme.md` Phases A–D: Threads 01–06 recorded, 07 = Steam gameplay validation, 08 = native iOS build, Medium default, High/Ultra only on demonstrated blockers, desktop = test infrastructure, early iOS feasibility allowed | docs consistent: roadmap, project-state, thread-index, handoff |
| 2 Decoding | census v2: one error in reachable code — `10 3A` takes six expressions (TV[63..67], 128); fixed in C++ and the census; 101 after-end notes cover the 4 Thread 06 overruns | `test_10_3a_six_expressions_census_v2_bytes`, `test_census_wiring`, `SghdPhoneProbe` |
| 2 Font | `font.lua` from the Game.exe table (0x12d7f0, 384 glyphs, 32-unit em, ×1.5) replaces ink estimates | `test_font_grid_and_widths`, `test_exe_width_report_parser` |
| 2 Text styles | all 7 `01 0E` modes are 720p (glyph 32, max line 1280) → engine scaling to 1080p confirmed | `test_text_styles_are_720p` |
| 2 Sprites | ADVBox / left nametag / wait icon consistent with Steam regions; CHAOS;HEAD title sprites, backlog sprites (ScrollbarTrack lay outside BACKLOG.DDS) and unused `systemmenu.lua` removed; every remaining literal sprite lies inside its sheet | `test_checked_sprites_match_steam_regions`, `test_sprites_lie_inside_their_sheets`, `test_no_inherited_chaos_head_title_or_backlog_sprites` |
| 2 Tools | `sghd_inspect.py`: pixel-level split of merged regions, `regions` crop mode | `test_sghd_inspect.py` (9) |
| 3 Real execution | no boot log → nothing to fix; short owner procedure (Windows round 4) | [../handoff.md](../handoff.md) |
| 4 iOS | blockers before/after porting, Thread 08 milestone, dependencies, platform adaptations, macOS CI | [../ios-transition.md](../ios-transition.md) |

Verification: `python3 -m unittest discover -s tests/compat` → 117/117
with the rebuilt binary (89 + 28 probes); launcher smoke PASS;
clang-format clean.

## Not done / limits

- Real Steam execution: not yet (needs the owner's boot log).
- Selection box, system message box, date display, save/loading icons:
  rectangles still unverified (no matching region or inside a merged one).
- Phone UI, movies (Bink 2), SG menus: missing.
