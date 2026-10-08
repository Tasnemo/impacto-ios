# Project state

Last updated: Thread 06 (2026-10-08). Goal: play the original English Steam
STEINS;GATE on iPhone through a fork of impacto, starting with desktop
compatibility. Thread history: [thread-index.md](thread-index.md). Current
handoff: [handoff.md](handoff.md).

## Where things stand

| Area | State | Evidence |
|---|---|---|
| Desktop build (Linux) | Verified | Ubuntu 24.04 container and GitHub Actions (`desktop.yml`) |
| Windows build | Built in CI (artifact), not yet run on Windows | `desktop-windows.yml` |
| `sghd` profile / VM start | Working on synthetic data; archive names, start script, sheet ids and **sheet sizes** from the real install | `SghdRuntimeProbe`, `test_sghd_profile_evidence.py` |
| SGHD decoding | Real scripts: 282 676 instructions decode; `10 3A` fixed; 4 overruns unresolved | [sghd-decode-integrity.md](sghd-decode-integrity.md) |
| SGHD opcode coverage | All known gaps parse; unknown semantics logged | `SghdOpcodeTableAudit`, `SghdTask2RuntimeProbe` |
| Design resolution | 1920×1080 (Steam assets are 1080p; scripts 720p, scaled by impacto) | fixture `design_resolution` |
| Font | Steam `FONT.PNG` 64×46 grid of 48 px; widths approximated from ink | `SghdCensusEvidence`, `tools/gen_sghd_font_widths.py` |
| Dialogue box | Generic plain box configured; rectangles are PS3 ×1.5 (unverified) | `SghdRuntimeProbe` |
| LAY (characters) | Little-endian, pixel texture coordinates | fixture `lay` |
| Phone/mail | Catalogued; item bits set/clear/branch implemented + saved; **phone UI not implemented** | [phone-protocol.md](phone-protocol.md), `SghdPhoneProbe` |
| Save/load | Fork-native format 2: slots + phone bits + global system data | `SghdSaveRoundTripProbe` |
| Movies | Bink 2 → skipped safely | `SghdMovieSkipProbe` |
| Audio | Ogg Vorbis (all 14 794 entries confirmed by the census) | `SghdOggAudioProbe` |
| Real Steam boot | **Needs the owner** (Windows artifact) | [handoff.md](handoff.md) "Windows round 3" |
| iOS | Not started (needs new authorization) | — |

Status per subsystem: [compatibility-matrix.md](compatibility-matrix.md).

## Branches

- `master`: equal to the Thread 05 head of `phase-03-sghd-implementation`
  at the start of Thread 06 (owner merged); Thread 06 commits are only on
  `phase-03-sghd-implementation`.
- `phase-02-steins-compatibility`: Thread 03 investigation.
- `phase-03-sghd-implementation`: Threads 04–06 (this state).

## Next step

Owner runs "Windows round 3" from [handoff.md](handoff.md) (census v2,
`sghd_inspect.py sprites` + `widths`, first boot log) and shares the text
outputs privately; then Thread 07 (Medium) applies them.
