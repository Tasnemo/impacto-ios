# Thread 05 — STEINS;GATE Steam evidence, Tasks 5–8 (Medium)

Branch `phase-03-sghd-implementation`, 2026-10-08. Input: the owner's
private `sghd-evidence.txt` (listing, MPK tables of contents and file
signatures of the Steam install; not committed). Details and decisions:
[../sghd-steam-evidence.md](../sghd-steam-evidence.md).

## Done (verified)

| Task | Change | Evidence |
|---|---|---|
| 5 | `vfs.lua` names confirmed; `StartScript = 2` = `_STARTUP_WIN.SCX`; sheet ids by name (Backlog 2, Data 6, Font 9, Title 30); Menu/TitleBg1/TitleBg2 → `ScriptHandled` | `test_sghd_profile_evidence.py` pins each value to `fixtures/sghd_steam_evidence.json`; `SghdRuntimeProbe` loads the ids incl. DXT5 DDS |
| 8 (M2) | Movies unmounted. Undecodable movie: fixed SIGSEGV in `findDecoderCodec` (null descriptor for codec `none`), abort in `OpenCodec` (empty `optional<Codec>`), refuse a stream without video, `PlayMovie` skips a movie that did not start | `SghdMovieSkipProbe` (unmounted; synthetic `KB2j` file): exit status from the script, trace `01:22 01:23 00:00` |
| 8 (M3 groundwork) | none needed | `SghdOggAudioProbe`: BGM/SE/voice Ogg Vorbis from MPK, 3 Vorbis streams |
| 8 (L4) | No audio device → silent channels for that run (no config change) | probe with `ALSOFT_DRIVERS=no-such-driver`: exit 34, was SIGSEGV |
| Tooling | `tools/sghd_census.py`: full 154-slot SGHD decoder (decode integrity, opcode/stub counts, phone/mail catalogue, movie ids, ScrWork/flag ranges), image/font/LAY/audio headers, Game.exe movie order; stdlib only, prints no strings | `test_sghd_census.py` (11 tests, synthetic) |
| CI | `desktop-windows.yml`: Windows x64 artifact for owner-side runs, vcpkg cache via actions/cache | see handoff for run status |

Verification in `impacto-desktop:ubuntu24` with the rebuilt binary:
`python3 -m unittest discover -s tests/compat` → 86/86 (63 without a
binary + 23 probes); launcher smoke 2/2 PASS. clang-format clean.

## Not done (blocked on evidence)

- Task 5 exit criterion (title/first line visible): needs a run on the
  owner's machine.
- Task 6 font grid/widths, sheet sizes, dialogue box/nameplate rectangles,
  `LayFileBigEndian`: need `sghd_census.py --assets` (and a look at the
  sheets for rectangles).
- Task 7 phone/mail: needs the census phone/mail catalogue (7a).
- Task 8: real audio codecs, voice sync semantics, achievements (L2),
  movie id → file mapping.

No real game data was executed. Synthetic probe success does not prove real
Steam compatibility.
