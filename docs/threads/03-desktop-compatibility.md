# Thread 03 — STEINS;GATE Desktop Compatibility Investigation

Date: 2026-10-08. Branch: `phase-02-steins-compatibility` (from `master`
`208cc56a`). Mode: Ultra. Scope: investigation, tests and planning only; no
Thread 04 implementation, no iOS work.

## Outcome

STEINS;GATE does not launch in this fork and the English Steam release is not
directly supported. This was established by **executing** the Thread 02
binary with synthetic, legally generated fixtures rather than by reading
source alone:

1. No SG game definition → `std::out_of_range` abort.
2. `sgps3` profile is bit-rotted against the CHLCC HUD code it points at
   (`Expected member LoadingStar`, then `DelusionADVPosition`).
3. The VM decodes Steam-encoded scripts wrongly: `Call`/`Return` desync with
   the stock `UseReturnIds = false`; with it fixed, the first `Nop` (`00 5F`,
   an `InstDummy` slot) spins the VM forever (>1.2 M iterations in 4 s).
4. Phone/mail, dialogue box, charset/font, save/load and Bink 2 video are
   absent for SG (source + external evidence).

No architectural blocker was found. The engine's VM, VFS, loaders, text and
save frameworks are reusable; the work is a correct `sghd` profile and opcode
table, a handful of handlers, the phone UI, a save adapter and a movie
strategy. Details and evidence: [steins-gate-compatibility.md](../steins-gate-compatibility.md).

## Deliverables

- [steins-gate-compatibility.md](../steins-gate-compatibility.md) — formats,
  interpreter, SG-specific systems, runtime evidence, feasibility.
- [compatibility-matrix.md](../compatibility-matrix.md) — 17 subsystems with
  the five allowed statuses and evidence class.
- [steins-gate-blockers.md](../steins-gate-blockers.md) — C1–C5, H1–H4,
  M1–M5, L1–L4 with files, reuse, approach, verification.
- [thread-04-implementation-plan.md](../thread-04-implementation-plan.md) —
  Tasks 1–8; Task 1 recommended first.
- `tests/compat/` — 27 asset-free unit tests + 4 runtime probes, fixtures,
  README with the Windows validation procedure.
- `.github/workflows/desktop.yml` — runs the unit tests before the build
  and the probes after it (no proprietary assets).
- [handoff.md](../handoff.md) — updated.

## Tests executed

| Test | Where | Result |
|---|---|---|
| Rebuild + ctest + smoke (Thread 02 recipe) | `impacto-desktop:ubuntu24` container | build OK; ctest "No tests were found"; smoke 2/2 PASS |
| `python3 -m unittest discover -s tests/compat -v` | orb (Python 3.11) | 31 tests: 27 OK, 4 skipped (no `IMPACTO_BIN`) |
| `IMPACTO_BIN=release/ubuntu24/impacto python3 -m unittest tests.compat.test_runtime_probe -v` | container, xvfb, `ALSOFT_DRIVERS=null` | 4/4 OK (assertions describe the current bugs) |
| Manual probes 1–6 (gamedef, no-assets, fixtures, return ids false/true, no-audio gdb) | container | see compatibility doc §6; artifacts in `.amp/in/artifacts/` (orb only) |

Not run: GitHub Actions for this branch (push authorized, CI result not
observed in this thread), any real Steam asset, Windows.

## Tests requiring the owner's Steam files

`tests/compat/README.md` §"Local validation with real Steam files": mpk
header bytes (MPK version), movie signatures (`BIK`/`KB2`), script dump
(start script id, opcode usage vs the gap list), `system.mpk` sheet ids,
first `-g sghd` boot log after Thread 04 Task 1. Only listings, headers and
logs should be shared; no archive contents.

## Decisions made in this thread (veto-able)

- sc3ntist has no license; only opcode *names and layouts* were recorded as
  data (`fixtures/sghd_opcodes.json`), no code copied. sc3tools (MIT) facts
  are cited.
- `sgps3` is treated as frozen/PS3; the plan adds `sghd` instead of editing
  it. The audit test pins the sgps3 table.
- Runtime probes assert present-day bugs so the next thread sees failures
  flip to successes; the README says to flip them in the fixing commit.
- CI runs the probes with `ALSOFT_DRIVERS=null` because the engine segfaults
  without an audio device; this is documented as an engine limitation (L4),
  not fixed.
- `docs/blockers.md` (project-level B1–B9) was left in place; SG items are
  superseded by `steins-gate-blockers.md` and cross-referenced.

## Limits

No Steam installation, no Windows host, no GPU, no audio device in the orb.
Every "external" fact (Steam mpk names/version, Bink 2, save location, PNG
textures, charset size) is from tool sources or community documentation and
must be confirmed with the owner's files before it is treated as verified.
