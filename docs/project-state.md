# Project state

Last updated: Thread 07c (2026-10-08). Goal: play the original English Steam
STEINS;GATE natively and offline on iPhone through a fork of impacto. Desktop
builds are test infrastructure for the shared engine ([roadmap.md](roadmap.md)). Thread history: [thread-index.md](thread-index.md). Current
handoff: [handoff.md](handoff.md).

## Where things stand

| Area | State | Evidence |
|---|---|---|
| Desktop build (Linux) | Verified | Ubuntu 24.04 container and GitHub Actions (`desktop.yml`) |
| Windows build | Built in CI (artifact); **run by the owner on real Steam data** (Thread 07b) | `desktop-windows.yml` |
| `sghd` profile / VM start | Working on synthetic data; archive names, start script, sheet ids and **sheet sizes** from the real install | `SghdRuntimeProbe`, `test_sghd_profile_evidence.py` |
| SGHD decoding | Real scripts: every reachable instruction stream decodes (census v2, `10 3A` = six expressions) | [sghd-decode-integrity.md](sghd-decode-integrity.md) |
| SGHD opcode coverage | All known gaps parse; unknown semantics logged; every untyped census layout matches its handler (`10 34`, `10 36` fixed in 07b) | `SghdOpcodeTableAudit`, `SghdFixedLayoutAudit`, `SghdTask2RuntimeProbe` |
| Design resolution | 1920×1080 (Steam assets are 1080p; scripts 720p, scaled by impacto) | fixture `design_resolution` |
| Font | Steam `FONT.PNG` 64×46 grid of 48 px; widths from the Game.exe table | `SghdCensusEvidence`, `tools/gen_sghd_font_widths.py --exe-widths` |
| Dialogue box | Generic plain box; ADVBox/nametag/wait-icon rectangles consistent with Steam regions; text styles 720p (scaled) | `SghdRuntimeProbe`, `test_checked_sprites_match_steam_regions` |
| LAY (characters) | Little-endian, pixel texture coordinates | fixture `lay` |
| Phone/mail | Catalogued; item bits set/clear/branch implemented + saved; **phone UI not implemented** | [phone-protocol.md](phone-protocol.md), `SghdPhoneProbe` |
| Save/load | Fork-native format 2: slots + phone bits + global system data | `SghdSaveRoundTripProbe` |
| Movies | Bink 2 → skipped safely | `SghdMovieSkipProbe` |
| Audio | Ogg Vorbis (all 14 794 entries confirmed by the census); lip-sync table little-endian | `SghdOggAudioProbe`, `SghdVoiceTableProbe` |
| Title menu | Protocol reconstructed (SF_TITLEEND/SW_TITLECUR, SW_TITLEMODE 3); `TitleMenuType.SGHD` with keyboard/mouse, START only; **no artwork yet** (TITLE_CHIP regions unnamed); not yet verified on real data | [threads/07c-title-menu.md](threads/07c-title-menu.md), `SghdTitleMenuProbe` |
| Other UI | Inherited CHAOS;HEAD title/backlog sprites removed; selection/system-message/date sprites unverified; SG menus missing | fixture `sprite_checks` |
| Real Steam boot | Rounds 4-5 (owner, Windows): boot, startup scripts and the title instructions run without crash or desync; the title could not be passed (no SF_TITLEEND, UselessJump) — fixed in 07c, **to be confirmed by round 6**; intermittent segfaults seen in earlier launches | [handoff.md](handoff.md) "Windows round 6" |
| iOS | Next: Thread 08 native ARM64 build (Medium) | [ios-transition.md](ios-transition.md) |

Status per subsystem: [compatibility-matrix.md](compatibility-matrix.md).

## Branches

- `master`: equal to the Thread 05 head of `phase-03-sghd-implementation`
  at the start of Thread 06 (owner merged); Thread 06 commits are only on
  `phase-03-sghd-implementation`.
- `phase-02-steins-compatibility`: Thread 03 investigation.
- `phase-03-sghd-implementation`: Threads 04–07c (this state).

## Next step

Thread 08 (Medium): native iOS ARM64 build and minimal app shell
([ios-transition.md](ios-transition.md)). In parallel the owner runs
"Windows round 6" from [handoff.md](handoff.md) (press start + START on
the real title, TITLE_CHIP region names); its findings get a short
follow-up.
