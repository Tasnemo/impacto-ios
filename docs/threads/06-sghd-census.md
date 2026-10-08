# Thread 06 — STEINS;GATE desktop compatibility from the census (Medium)

Branch `phase-03-sghd-implementation`, 2026-10-08. Input: the owner's
private `sghd-census.txt` (`tools/sghd_census.py` over the English Steam
install; UTF-16 PowerShell output; not committed). Aggregated facts only are
kept in `tests/compat/fixtures/sghd_steam_evidence.json` and the docs below.

## Done (verified)

| Objective | Change | Evidence |
|---|---|---|
| 1 Decode integrity | 282 676 instructions in 190 scripts; the 252 reported errors classified (82 string-table padding, 136 data labels, 20 labels starting with `10 0D/2E/3A`, 14 overruns: 10 into data, 4 unresolved) | [../sghd-decode-integrity.md](../sghd-decode-integrity.md) |
| 2 Layout fixes | `10 3A` = one expression (`InstUnk103ASGHD`; the sgps3 handler desynced); `10 37` type `0x1E` has no arguments; census table gained `10 0D` (CHAmove), `10 2E`, `10 3A` | `SghdOpcodeTableAudit.test_census_wiring`, `SghdPhoneProbe` |
| 3 Font, sheets, LAY | `DesignWidth/Height` 1920×1080 (full-screen masks are 1080p); sheet sizes = Steam textures (Data 3072×1788, Font 3072×2208, Title 3072×1536, Backlog 2048×1080); `FONT.PNG` grid 64×46 of 48 px, widths from ink extents (`tools/gen_sghd_font_widths.py`); LAY little-endian, pixel texture coordinates (multipliers 1), one ignored trailing byte per vertex | `test_sghd_profile_evidence.SghdCensusEvidence`, `test_sghd_charset` |
| 4 Dialogue box | generic `PlainDialogueBox` (ADVBox sprite + two-piece nametag), no more "not implemented" warning; all UI coordinates and PS3 sprite rectangles scaled ×1.5 to the 1080p design (rectangles unverified) | `SghdRuntimeProbe.test_plain_dialogue_box_configured` |
| 5 Phone catalogue | 611 phone/mail instructions catalogued by sub-type, layout, context and engine state | [../phone-protocol.md](../phone-protocol.md), fixture `phone_subtypes` |
| 6 Phone state | `10 37` 0x00/0x01 set/clear item attribute bit, 0x02/0x03 jump if set/clear (`src/games/sghd/phone.h`); other sub-types stay logged stubs | `SghdPhoneProbe` (exit 42) |
| 7 Saves | format 2: phone block per slot; global system data (`00 2A` type 0/2: FlagWork bytes 100-149, 460-499, ScrWork 600-999); v1 files still load | `SghdSaveRoundTripProbe` (phone bit + global flag/ScrWork survive) |
| 7 Voice table | `WAVTABLE.DAT` header is little-endian on Steam (`b0 38` = 14512 = voice entries); profile flag `VoiceTableLittleEndian`; an oversized count is refused instead of over-reading, lookups are bounds-checked (real-data crash risk removed) | `SghdVoiceTableProbe`, `test_voice_table_is_little_endian` |
| 8 Windows tools | census v2 (evidence vs padding/data, context for real errors, DDS loader checks, text styles); `tools/sghd_inspect.py` (`sheets`/`sprites` opaque-region boxes, `crops` local sprite check, `widths` Game.exe width-table search) | `test_sghd_census.py` (15), `test_sghd_inspect.py` (7) |

Verification in `impacto-desktop:ubuntu24`, binary rebuilt from this
branch: `python3 -m unittest discover -s tests/compat` → **108/108** with
`IMPACTO_BIN` (80 + 28 probes); 80 pass and 28 skip without a binary.
Launcher smoke PASS. clang-format clean on changed C++.

## Not done / limits

- No real game data has been executed in this project; everything runtime
  is synthetic. The first Windows boot is still outstanding.
- Sprite rectangles (dialogue box, nameplate, menus) are PS3 ×1.5
  hypotheses; `DATA01.DDS` (3072×1788) and `BACKLOG.DDS` (2048×1080) are
  not 1.5× PS3 layouts, so some are certainly wrong.
- Font widths are an approximation from ink extents (the executable's own
  table has not been located).
- Phone polarity (set vs clear, jump-if-set vs jump-if-clear) is inferred
  from script idioms, not from the executable. The phone UI and sub-types
  0x05-0x1E (player reading mails, replying, answering calls) are not
  implemented: phone triggers that need player input cannot be taken.
- Movies: still Bink 2 → skipped.
- 4 decode overruns unresolved until a census v2 re-run.

## Next

Owner runs "Windows round 3" (handoff); next thread (Medium) applies the
sprite boxes, width table and census v2 results. Phone UI semantics likely
need High.
