# SGHD script decoding integrity (Thread 06)

Input: the owner's private first census (`tools/sghd_census.py`, all 190
scripts of `script.mpk`, English Steam release). The report is not
committed; this page keeps only aggregated, non-proprietary results.

## Result

The census decoded 282 676 instructions. It reported 252 "decode errors" in
91 scripts. Classified by hand from the error positions and their first
bytes:

| Class | Count | Layout evidence? |
|---|---|---|
| Last label of a script runs into the 1-3 alignment bytes before the string table (error at `string_table - 1`, or an overrun into it) | 82 | no |
| Label is a data table (u16/u32 lists, `-1` terminated id lists, CHAmove sequence data, coordinate tables) | 136 | no |
| Label starts with `10 0D`, `10 2E` or `10 3A`, missing from the sc3ntist-derived table | 20 | **yes** -- table gap |
| Overrun of a following label | 14 | 10 run into a data label right after the code (padding after a final `Return`); 4 unresolved |

Apart from the 4 unresolved overruns, no error lies inside an otherwise
decodable instruction stream: the 154-slot SGHD layout table is consistent
with the real scripts except for the slots below.

## Layout corrections

| Slot | Finding | Change |
|---|---|---|
| `10 3A` | Its only use starts `10 3A 2D 0A A0 3F 14 00`. Census v2 (Thread 07) showed the full instruction: six expressions (`TV[63]`..`TV[67]`, immediate 128) followed by a decodable `Sleep`. impacto's handler (copied from sgps3) read a type byte first and would desync. | `InstUnk103ASGHD` (six expressions, stub); pinned by `test_census_wiring`, `test_10_3a_six_expressions_census_v2_bytes` and `SghdPhoneProbe` |
| `10 0D` | 18 labels of exactly 13 bytes start `10 0D 01 2D 0A A0 3F 14`: CHAmove type 1 (`E L`), then `Return`. Matches impacto's existing `InstCHAmove`. | none in impacto; census table gained the layout and treats its label as data |
| `10 2E` | One label starts with it; `E` (impacto `InstSetSceneViewFlag`) fits. | census table only |
| `10 37` type `1E` | One use, no arguments (next instruction 3 bytes later). impacto logged "unknown SGHD subtype". | added to `InstPhoneSGHD` |

## Census tool v2

`tools/sghd_census.py` now separates evidence from noise so a re-run is
conclusive:

- bytes after an unconditional end of flow (`EndOfScript`, `Jump`,
  `JumpTable`, `JumpFar`, `Return`) up to the next label are counted as
  padding/data, not errors;
- labels named by `LT` (label-table) expressions, `10 38` type 0, `10 37`
  type 4 and CHAmove type 1 are data;
- labels whose *first* instruction fails are listed separately (data or a
  missing opcode);
- every remaining error is printed with the four preceding instructions and a
  hex window, so a layout mismatch can be fixed from the report alone;
- text-style data (`01 0E`, 24 x u16) is dumped to check whether the Steam
  scripts use 720p or 1080p coordinates for the message window.

Unit tests: `tests/compat/test_sghd_census.py` (`CensusClassification`).

## Census v2 result (Thread 07)

Re-run on the owner's install with the v2 classifier:

- **1** decode error in reachable code (the `10 3A` layout above, fixed);
- **101** "after-end" notes (padding/data after an unconditional end of
  flow), which include the 4 overruns left open in Thread 06 and every
  string-table padding case;
- the rest are label entries that are data tables (`_ATCH`, `_MAIL`,
  `_TIPS`, CHAmove sequence data, MACROSYS2 id lists).

With the six-expression `10 3A`, every instruction stream reachable from a
label decodes. Constants: fixture `census_v2`.
