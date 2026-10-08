# Project state

Last updated: Thread 04 (2026-10-08). Goal: play the original English Steam
STEINS;GATE on iPhone through a fork of impacto, starting with desktop
compatibility. Thread history: [thread-index.md](thread-index.md). Current
handoff: [handoff.md](handoff.md).

## Where things stand

| Area | State | Evidence |
|---|---|---|
| Desktop build (Linux) | Verified | Ubuntu 24.04 container and GitHub Actions (`desktop.yml`) |
| `sghd` profile / VM start | Working on synthetic data | `SghdRuntimeProbe` |
| SGHD opcode coverage | All 37 known gaps parse correctly; unknown semantics logged | `SghdOpcodeTableAudit`, `SghdTask2RuntimeProbe` |
| Asset-free VM harness | Working, in CI | `profiles/sghd-harness`, `SghdHarnessRuntimeProbe` |
| Save/load engine side | Fork-native round trip works | `SghdSaveRoundTripProbe` |
| Charset | Steam charset generated (sc3tools) | `test_sghd_charset.py` |
| Real Steam boot | **Blocked on owner evidence** | Task 5 |
| Font, dialogue box, phone/mail, movies, audio semantics | Not implemented (need real files/scripts) | [steins-gate-blockers.md](steins-gate-blockers.md) |
| iOS | Not started (needs new authorization) | — |

Status per subsystem: [compatibility-matrix.md](compatibility-matrix.md).

## Branches

- `master`: Threads 01–02 (build baseline).
- `phase-02-steins-compatibility`: Thread 03 investigation + tests (not merged).
- `phase-03-sghd-implementation`: Thread 04 (this state), based on the
  Thread 03 head. Merging into `master` needs the owner's decision.

## Next step

Owner runs `tools/sghd_evidence.py` on the Steam install and shares the
report; then Task 5 (first boot) continues in a new Medium thread. Prompt in
[handoff.md](handoff.md).
