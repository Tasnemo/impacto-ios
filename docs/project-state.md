# Project state

Last updated: Thread 07 (2026-10-08). Goal: play the original English Steam
STEINS;GATE natively and offline on iPhone through a fork of impacto. Desktop
builds are test infrastructure for the shared engine ([roadmap.md](roadmap.md)). Thread history: [thread-index.md](thread-index.md). Current
handoff: [handoff.md](handoff.md).

## Where things stand

| Area | State | Evidence |
|---|---|---|
| Desktop build (Linux) | Verified | Ubuntu 24.04 container and GitHub Actions (`desktop.yml`) |
| Windows build | Built in CI (artifact), not yet run on Windows | `desktop-windows.yml` |
| `sghd` profile / VM start | Working on synthetic data; archive names, start script, sheet ids and **sheet sizes** from the real install | `SghdRuntimeProbe`, `test_sghd_profile_evidence.py` |
| SGHD decoding | Real scripts: every reachable instruction stream decodes (census v2, `10 3A` = six expressions) | [sghd-decode-integrity.md](sghd-decode-integrity.md) |
| SGHD opcode coverage | All known gaps parse; unknown semantics logged | `SghdOpcodeTableAudit`, `SghdTask2RuntimeProbe` |
| Design resolution | 1920×1080 (Steam assets are 1080p; scripts 720p, scaled by impacto) | fixture `design_resolution` |
| Font | Steam `FONT.PNG` 64×46 grid of 48 px; widths from the Game.exe table | `SghdCensusEvidence`, `tools/gen_sghd_font_widths.py --exe-widths` |
| Dialogue box | Generic plain box; ADVBox/nametag/wait-icon rectangles consistent with Steam regions; text styles 720p (scaled) | `SghdRuntimeProbe`, `test_checked_sprites_match_steam_regions` |
| LAY (characters) | Little-endian, pixel texture coordinates | fixture `lay` |
| Phone/mail | Catalogued; item bits set/clear/branch implemented + saved; **phone UI not implemented** | [phone-protocol.md](phone-protocol.md), `SghdPhoneProbe` |
| Save/load | Fork-native format 2: slots + phone bits + global system data | `SghdSaveRoundTripProbe` |
| Movies | Bink 2 → skipped safely | `SghdMovieSkipProbe` |
| Audio | Ogg Vorbis (all 14 794 entries confirmed by the census); lip-sync table little-endian | `SghdOggAudioProbe`, `SghdVoiceTableProbe` |
| Other UI | Inherited CHAOS;HEAD title/backlog sprites removed; selection/system-message/date sprites unverified; SG menus missing | fixture `sprite_checks` |
| Real Steam boot | **Not yet executed — needs the owner's boot log** | [handoff.md](handoff.md) "Windows round 4" |
| iOS | Next: Thread 08 native ARM64 build (Medium) | [ios-transition.md](ios-transition.md) |

Status per subsystem: [compatibility-matrix.md](compatibility-matrix.md).

## Branches

- `master`: equal to the Thread 05 head of `phase-03-sghd-implementation`
  at the start of Thread 06 (owner merged); Thread 06 commits are only on
  `phase-03-sghd-implementation`.
- `phase-02-steins-compatibility`: Thread 03 investigation.
- `phase-03-sghd-implementation`: Threads 04–07 (this state).

## Next step

Thread 08 (Medium): native iOS ARM64 build and minimal app shell
([ios-transition.md](ios-transition.md)). In parallel the owner runs
"Windows round 4" from [handoff.md](handoff.md) (first boot log, optional
sprite naming); its findings get a short Medium follow-up.
