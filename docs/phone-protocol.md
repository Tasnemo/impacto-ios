# STEINS;GATE (Steam) phone / mail instruction protocol

Thread 06. Source: the owner's private `tools/sghd_census.py` report over all
190 scripts of the English Steam release (the report is not committed). Only
opcode layouts, counts and inferred roles are recorded here; counts are also
pinned in `tests/compat/fixtures/sghd_steam_evidence.json` (`phone_subtypes`).

Status legend: **impl** = implemented in `InstPhoneSGHD`
(`src/vm/inst_sghd.cpp`); **parsed** = arguments consumed, stub logged once;
evidence strength in the last column.

## Summary

- `10 37` (`Group1037`, 604 uses) is the phone/mail instruction; the first
  byte after the opcode is a sub-type. `10 38` (7 uses, one per sub-type
  0-6) is a separate small group of unknown purpose (type 0 names a u16
  table in _ATCH.SCX).
- Every sub-type layout decodes cleanly across all scripts (no decode error
  inside a `10 37`; the next instruction always starts where the layout ends).
- Sub-types `0x00`-`0x03` form a per-item attribute store with conditional
  jumps. They are implemented (fork-native state, saved per slot). All other
  sub-types drive the phone UI and wait for engine-side state in
  ScrWork 6800-6856 / flags 2600-2623; they remain stubs because their
  semantics and the phone UI (sheets `PHONE*.DDS`) are not established.
- Consequence: scripted phone *state* and *branching* now work, but the
  player-driven phone UI (reading mails, choosing replies, answering calls)
  does not exist, so phone triggers that depend on player input cannot be
  taken yet. This is the main remaining gameplay gap.

## `10 37` sub-types

| Type | Layout | Uses (sys / scenario) | Role (inferred from context) | Status / evidence |
|---|---|---|---|---|
| 00 | `B E` | 11 / 142 | set attribute bit `B` (0-4) of item `E` | **impl** -- strong structure, polarity medium (see below) |
| 01 | `B E` | 132 / 89 | clear attribute bit `B` of item `E` | **impl** -- reset routines clear lists of items |
| 02 | `B E L` | 12 / 6 | jump to `L` if bit `B` of item `E` is set | **impl** -- gates optional chapter scripts in MAIN00 |
| 03 | `B E L` | 9 / 0 | jump to `L` if bit `B` of item `E` is clear | **impl** -- init-once idiom in _STARTUP_WIN |
| 04 | `L L L L L L` | 1 / 0 | registers six data tables (_MAIL.SCX label 0) | parsed (labels are data) |
| 05 | -- | 9 / 19 | phone open/init (followed by W6802/W6803 resets, `10 3F`) | parsed |
| 06 | -- | 8 / 1 | phone list/menu step; followed by `JumpIf W6807 == W1422` | parsed (UI) |
| 07, 08 | -- | 1 / 0 each | phone shutdown pair in _SYSTEM (flags 2608-2610) | parsed |
| 09 | -- | 1 / 6 | list cursor step; followed by tests on W6813 / W6814 | parsed (UI) |
| 0A | -- | 2 / 0 | like 09 for W6818 / W6819 | parsed (UI) |
| 0F | `E` | 11 / 3 | small index 0-12 (W6828/W6829 nearby) | parsed |
| 10 | `E` | 5 / 0 | pairs with 0F | parsed |
| 11 | -- | 2 / 0 | precedes 0F | parsed |
| 12 | `E E` | 1 / 0 | (W1421, W6825 + W1421) -> W6810 | parsed |
| 13 | -- | 1 / 85 | scenario marker right after dialogue lines | parsed |
| 14 | `E E E E` | 1 / 19 | up to four small ids, 255 = none | parsed |
| 15 | `E E E E` | 1 / 10 | same shape as 14 | parsed |
| 16 | -- | 4 / 1 | list step; tests W6822 == W1423 | parsed (UI) |
| 17 | -- | 0 / 2 | followed by flag 2609 waits | parsed |
| 18 | -- | 3 / 1 | followed by `ResetFlag 2604` | parsed |
| 19 | -- | 1 / 0 | _STARTUP_WIN, before 1A | parsed |
| 1A | `E` | 2 / 0 | item id; _STARTUP_WIN, before setting bits 0/1 of the same item | parsed |
| 1E | -- | 1 / 0 | _SYSTEM phone loop | parsed (**added Thread 06**; impacto logged it as unknown) |

`10 38`: type 0 `L` (data label: u16 table in _ATCH.SCX), types 1-6 no
arguments (MACROSYS2, around W6836-W6839 and flag 1205). All parsed only.

## Attribute store (types 00-03)

Items are numbers up to ~650 (immediates or expressions such as `TV[64]`
from table loops, `W6807`); bits used are 0-4. impacto keeps them in
`SGHD::Phone::ItemBits[1024]` (`src/games/sghd/phone.h`) and saves the block
with every slot (save format 2, `docs/sghd-save-format.md`).

Evidence for the polarity (set/clear, jump-if-set/jump-if-clear):

1. A MACROSYS2 routine calls three table loops that apply type 01 bit 0 to
   every listed item, applies 01 bit 0 to item 0, then 00 bits 0 and 1 to
   item 1, and returns: a reset that clears everything and gives one default
   item. With the opposite polarity it would set every item and clear the
   default one.
2. _STARTUP_WIN: `03 0 (item) -> L`, and `L` applies `1A (item)`, then 00
   bits 0 and 1 to the same item and loops back. With "03 = jump if clear"
   this is an init-once guard; with the opposite reading the guarded block
   would re-run on every pass and the code after the `03` would only run once.
3. MAIN00 (chapter router): `02 b (item) -> L; Jump M` where `L` loads an
   extra chapter script and `M` skips it: optional scenes play only when the
   player has caused the bit to be set, never by default.

The game executable's own storage for these bits is unknown, so scripts that
might read the same state through FlagWork/ScrWork would not see it. If a
real-game comparison shows a branch going the wrong way, flip the polarity in
`InstPhoneSGHD` (one line each) and re-run `SghdPhoneProbe`.

## Engine-side state the stubs would need

- ScrWork 6801-6856 (phone mode W6802/W6803, selected item W6807, cursor and
  list pairs W6813/W6814, W6818/W6819, W6821/W6822, progress W6825/W6826,
  current item W6810) and W1420-W1430.
- Flags 2600-2623 (2604/2606/2612/2623 most common around the phone).
- Sheets `PHONE.DDS`, `PHONE_B..E.DDS`, `PHONE2.DDS`, `PHONE3.DDS`
  (all 3072x1536 DXT5).

Flags 2600-2623 are already inside the per-slot `FlagWorkRanges`. ScrWork
6800+ is not saved; W6825/W6826 are recomputed by MACROSYS2 from the item
bits, the rest looks like transient UI state.

## Next steps (need new evidence)

1. Windows: play to the first phone mail in the original game and compare
   with impacto's `Phone:` debug log (`-ll Debug`) to confirm the polarity.
2. Phone UI: needs the PHONE sheets' layout (`tools/sghd_inspect.py sheets`)
   and the meaning of sub-types 05-1E; likely High-mode reverse engineering of
   the MACROSYS2 phone loops against the executable.
