# Project state

Last updated: Thread 05 (2026-10-08). Goal: play the original English Steam
STEINS;GATE on iPhone through a fork of impacto, starting with desktop
compatibility. Thread history: [thread-index.md](thread-index.md). Current
handoff: [handoff.md](handoff.md).

## Where things stand

| Area | State | Evidence |
|---|---|---|
| Desktop build (Linux) | Verified | Ubuntu 24.04 container and GitHub Actions (`desktop.yml`) |
| `sghd` profile / VM start | Working on synthetic data; archive names, start script, sheet ids from the real install listing | `SghdRuntimeProbe`, `test_sghd_profile_evidence.py` |
| SGHD opcode coverage | All 37 known gaps parse correctly; unknown semantics logged | `SghdOpcodeTableAudit`, `SghdTask2RuntimeProbe` |
| Asset-free VM harness | Working, in CI | `profiles/sghd-harness`, `SghdHarnessRuntimeProbe` |
| Save/load engine side | Fork-native round trip works | `SghdSaveRoundTripProbe` |
| Charset | Steam charset generated (sc3tools) | `test_sghd_charset.py` |
| Real Steam boot | Config done; **run needs the owner** (Windows artifact) | [sghd-steam-evidence.md](sghd-steam-evidence.md) |
| Movies | Bink 2 → skipped safely (crash/hang fixed) | `SghdMovieSkipProbe` |
| Audio | Ogg Vorbis BGM/SE/voice path works (synthetic); no-device crash fixed | `SghdOggAudioProbe` |
| Font, dialogue box, LAY, phone/mail | **Blocked on owner census** (`tools/sghd_census.py`) | [handoff.md](handoff.md) |
| iOS | Not started (needs new authorization) | — |

Status per subsystem: [compatibility-matrix.md](compatibility-matrix.md).

## Branches

- `master`: Threads 01–02 (build baseline).
- `phase-02-steins-compatibility`: Thread 03 investigation + tests (not merged).
- `phase-03-sghd-implementation`: Threads 04–05 (this state), based on the
  Thread 03 head. Merging into `master` needs the owner's decision.

## Next step

Owner runs `tools/sghd_census.py` on the Steam install and shares the report
privately; then Thread 06 (Medium) does Tasks 6/7a from it. Prompt in
[handoff.md](handoff.md).
