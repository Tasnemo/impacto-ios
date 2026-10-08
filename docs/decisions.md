# Architecture Decision Records

Format: ID, date, status, context, decision, consequences. Add new records at the bottom;
never rewrite an accepted record — supersede it.

## ADR-001 — Keep impacto as the engine foundation
- **Date:** 2026-10-08 (Thread 01) — **Status:** Accepted
- **Context:** `workme.md` asks Thread 01 to evaluate whether impacto remains a sensible
  foundation. Findings: SC3 VM, VFS, texture/audio/video pipelines, Lua profile system and
  SDL3-based platform layer are all in place; platform-specific code is confined to ~15
  files; Android proves the shared-library + GLES3 mobile path.
- **Decision:** Build on impacto. Do not rewrite subsystems. Add a `sghd` profile and an iOS
  shell as additive layers.
- **Consequences:** Project effort concentrates on game compatibility (VM, phone/mail,
  saves, Bink 2) rather than engine construction. Upstream merges remain possible if
  changes stay profile- and platform-scoped.

## ADR-002 — Target the Steam release via a new `sghd` profile, not by extending `sgps3`
- **Date:** 2026-10-08 — **Status:** Proposed (confirm in Thread 03)
- **Context:** `sgps3` encodes PS3 specifics (CPK mounts, `LayFileBigEndian=true`, PS3
  charset, 1280x720). The Steam build uses MPK, PC endianness, its own charset, up to
  1920x1080.
- **Decision:** Create `profiles/sghd/`, `resources/sghd/`, and if needed
  `InstructionSet::SGHD` + `opcodetables_sghd.h`, following how `cc` vs `cclcc` coexist.
- **Consequences:** Keeps upstream `sgps3` intact; duplicates some Lua until the two are
  proven identical.

## ADR-003 — Defer the iOS graphics backend choice until Thread 05
- **Date:** 2026-10-08 — **Status:** Accepted
- **Context:** `workme.md` forbids committing to a Metal rewrite up front. The OpenGL
  backend already emits GLES 3.0 shaders and runs on Android; the Vulkan backend is
  incomplete (12/27 shader pairs); GLES on iOS is deprecated but present.
- **Decision:** Thread 05 must test (1) GLES3 via SDL3 on an iOS 26 simulator/device build
  and (2) MoltenVK viability before any backend work. Prefer the smallest change that
  renders correctly.
- **Consequences:** No renderer code changes before Thread 05.

## ADR-004 — Bink 2 handling decided after inspecting real files
- **Date:** 2026-10-08 — **Status:** Proposed
- **Context:** See `docs/blockers.md` B1.
- **Decision:** Thread 03 hexdumps the shipped movies. If `KB2`, the default plan is a
  Windows-side transcode step in the asset-packaging tool (to a format ffmpeg + iOS hw
  decode handle, e.g. H.264/AAC in MP4) rather than implementing Bink 2 in the engine.
- **Consequences:** Adds a user-side preparation step; keeps the engine free of a
  proprietary codec reimplementation.

## ADR-005 — Documentation and branch discipline
- **Date:** 2026-10-08 — **Status:** Accepted
- **Decision:** Each thread works on `phase-NN-<topic>` branches, writes
  `docs/threads/NN-*.md`, and updates `docs/handoff.md` using the template in `workme.md`.
  Claims are tagged Verified / Claimed / Source-level / Unknown.

## ADR-006 — Match upstream Linux toolchain; test launcher separately from games
- **Date:** 2026-10-08 (Thread 02) — **Status:** Accepted
- **Context:** Debian 12/GCC 12 fails pinned OpenAL Soft's `<format>` include.
  Ubuntu 24.04/GCC 13 compiles the unchanged engine. All viewer profiles require
  game data, while the launcher runs asset-free.
- **Decision:** Preserve `ci-release`, `x64-linux-ci` and dependency versions;
  document Ubuntu native/container builds. Pin LibAtrac9's formerly moving branch.
  Use independent GitHub file caching and Xvfb/Mesa launcher smoke checks with
  explicit engine file logs. Leave legacy multi-platform CI unchanged.
- **Consequences:** No engine redesign or compatibility work. The desktop baseline
  does not establish game playability. Native GCC 12 is not a supported recipe;
  future real-game regressions need separate tests and legitimate data.

## ADR-007 — SGHD handlers live in a new file; shared handlers get guarded branches only

Thread 04. Slots whose SGHD layout matches an existing handler reuse it
(mostly CC's: `InstSEplay`, `InstVoicePlay`, `InstVoiceStopNew`, `InstCalc`,
`InstAutoSave`). Sub-type differences in shared handlers are
`InstructionSet::SGHD` branches (`InstSel`, `InstSetRevMes`, `InstCHAload`,
`InstSaveMenu`, `InstLoadData`, `InstTips`). Everything else is in
`src/vm/inst_sghd.cpp`. Opcodes with unknown semantics consume their
sc3ntist layout and log `STUB … [SGHD, logged once]` with `ImpLog` (visible
in Release builds) — they are parsed, not implemented. `InstDummy` itself is
unchanged; the SGHD table uses `InstUnknownSGHD` for never-emitted slots.

## ADR-008 — Asset-free harness = full sghd profile with ScriptHandled sheets

`profiles/sghd-harness` includes `profiles/sghd/game.lua`, marks every
spritesheet `ScriptHandled` and mounts only `script.mpk`. This needed no
change to `src/profile/sprites.cpp` and exercises the real UI configuration.
Termination and pass/fail use two optional VM profile keys
(`ExitWhenThreadsEnd`, `ExitCodeScrWork`) and `Game::ExitCode`, which the
GL/Vulkan `Window::Shutdown` now passes to `exit()` (default 0: other games
unchanged; DX9 window untouched because it cannot be built here).

## ADR-009 — Fork-native save format first

`SaveDataType.SGHD` writes a versioned `IMPSGHD` file
([sghd-save-format.md](sghd-save-format.md)). It is not, and is never
described as, Steam-compatible. Saved FlagWork/ScrWork ranges are profile
data (CHLCC/sgps3 defaults until real scripts show otherwise); files with
different ranges are refused. Raw IP + verbatim call stack are restored.

## ADR-010 — Upstream-relevant fixes found by the probes

The generic `BacklogMenu` was constructed with capacity 0 for every
`BacklogMenuType.None` profile, so the first `SetRevMes` segfaulted;
`MaxEntryCount` is now read before the `None` early return. Candidate for
upstreaming. Probes run one private `Xvfb` instead of `xvfb-run` per engine
run (xvfb-run occasionally replaced the exit status with 5).

## ADR-011 — Steam evidence handling, movies and silent audio (Thread 05)

Private owner reports are never committed; the few constants the profile
needs live in `tests/compat/fixtures/sghd_steam_evidence.json`, and tests pin
the profile to them. Sheets are mapped to `system.mpk` entries by name only;
sheets without a Steam counterpart become `ScriptHandled` rather than
loading an unrelated texture. Movies (Bink 2) are unmounted and skipped; any
movie FFmpeg cannot decode is refused by `FFmpegPlayer::Play` and skipped by
`PlayMovie` (fixes a null-descriptor segfault, an empty-optional abort and an
endless `SF_MOVIEPLAY` wait; generic, upstream candidates). A failed audio
backend falls back to silent channels for the current run without changing
the user's configured backend (`Audio::BackendUnavailable`).
