# Thread 07c — STEINS;GATE title menu: protocol and engine side (Medium)

Branch `phase-03-sghd-implementation`, 2026-10-08. Inputs (private, not
committed): the owner's Windows round-5 log `menu-retry.log` (Thread 07b
artifact, real Steam data) and `sghd-context.txt`
(`tools/sghd_census.py --context=10:34,00:44`). Only variable indices,
opcode types and choice ids are recorded here and in the fixture
`title_protocol`; no script code.

## Round-5 evidence

- Fresh config, all archives, `_STARTUP_WIN`, `_SYSTEM`, `ANIME`, `_TIPS`,
  `MACROSYS`, `MACROSYS2`, `_MAIL`, `_ATCH` load; `TitleMenu(type: 0)` and
  `(type: 1)` are reached (Thread 07b fixes work on real data).
- At `10 34 0` the script starts movie 37 (`01 22` type 0x0D); it is
  missing (Bink 2 not mounted) and skipped. Title BGM starts.
- Stall report after 5 s: thread 0 in a `Sleep` in `_STARTUP_WIN`, eight
  `ANIME.SCX` threads in `Sleep`, five `_SYSTEM` threads waiting on flags
  (background threads). The title thread is not listed because its poll
  loop alternates between two addresses (`Sleep 1` / `10 34 1`).
- `MAIN00.SCX` is never loaded; exit status 0 when the window is closed.
  Earlier launches segfaulted intermittently (no crash log; open).

## Protocol (from `sghd-context.txt`)

Addresses are in `_STARTUP_WIN.SCX`.

| Step | Script (numbers only) | Reading |
|---|---|---|
| Init, label40 | `10 3F 0`; `SetFlag 1836`; **`10 34 0`**; `W3503 = 0`; reset flags 1800, **1241**, 2400, 1844; `W2113 = 0`; **`SetFlag 1240`**; `W6330 = 4000`; play movie 37; `W2119++` to 32 | title init, SF_TITLEMODE on, SW_GAMESTATE 0, title movie, fade-in counter |
| Press start, label45/46 | `W2119 = 60`; **`W2116 = 0`**; BGM; `SetFlag 1219`; loop: `Sleep 1`; **`10 34 1`**; `JumpIf W2116 >= 2400 → label68`; **`JumpIfFlag 0 (1241) → loop`**; `ResetFlag 1241`; **`UselessJump 0 label47 label47`**; `Jump loop` | wait for SF_TITLEEND; idle counter SW_TITLEMOVIECT (attract mode after 2400 frames); then label47: system SE 0, fade `W2119` to 64, continue |
| Main menu init, label77/78 | ...; `SetFlag 1240`; `ResetFlag 1241`; **`10 34 2`**; `W4411 = 0`; `W2115 = 4`, `W2119` 32→0; **`W2115 = 3`**, `W2119 = 32` | menu init, SW_TITLEMODE 4 (transition) then 3 (menu) |
| Main menu, label87 | `Sleep 1`; `JumpIfFlag 1 (1805) → label104`; **`10 34 1`**; `KeyOnJump 1 (8192 = PAD1B) → label59`; **`JumpIfFlag 0 (1241) → loop`**; `ResetFlag 1241`; **`JumpIf W2139 == 0 / 10 / 11 / 20 / 21 / 22 / 23 / 24 / 30 / 40`** | choice in SW_TITLECUR; Back handled by the script |
| label52 | ...; SystemMes fade-out; **`10 34 3`**; `Jump label74` | after a save-data message (W3333); meaning unknown |
| System menu, label118/120 | `W2143 = 0`; `00 44 0`; `10 3F 17`; SE 5; `WaitForFlag 1820`; `W2113 |= 4`; `W2143 = 256`; `W2142` 0→32; loop: `00 44 1`; `KeyOnJump 3` with 10/6/5 → close/close/`JumpTable W3338` | in-game system menu: engine keeps the cursor in SW_SYSMENUCNO, the script reads keys (out of scope) |

### Proven

- `10 34` types used: 0, 1, 2, 3 (one byte, Thread 07b).
- The Steam scripts use impacto's **common** variable layout: W2113
  SW_GAMESTATE, W2115 SW_TITLEMODE, W2116 SW_TITLEMOVIECT, W2119
  SW_TITLEDISPCT, W2139 SW_TITLECUR, W2142/W2143 SW_SYSMENUCT/ALPHA, W3338
  SW_SYSMENUCNO, W4300 SW_TITLE (`== 65535` test), flags 1240 SF_TITLEMODE,
  1241 SF_TITLEEND, 1805 SF_RETURNTITLE. The `sghd` profile overrode three of
  these with PS3 values (SW_TITLEDISPCT 1014, SW_SYSMENUCT 1042, SW_TITLE
  2300); removed.
- Both title loops end only when flag 1241 is set by someone other than the
  title thread; the main-menu branch then depends only on W2139.
- `UselessJump 0 label47 label47` followed by `Jump loop`: not jumping makes
  the decision path (label47) unreachable from the loop and the loop
  endless, and both labels are equal, so the jump is taken whatever the
  condition. impacto treated it as never taken: **after press start the
  script would have looped forever even with input.**

### Strongly supported (structure), not proven

- Flag 1241 and W2139 are written by the engine's title menu during
  `10 34 1` (nothing in the visible script writes them; same names and
  roles as impacto's common SF_TITLEEND / SW_TITLECUR).
- Choice ids are item × 10 + sub-item: 0 START, 10/11 LOAD sub-items, 20-24
  EXTRA sub-items, 30 CONFIG, 40 HELP (five items of the original title).
- The phase is told apart by SW_TITLEMODE: 3 = main menu.

### Hypotheses / unknown

- Type 0 vs 2 differ only in what they initialise; type 3 unknown.
- Whether the engine increments W2116 (idle → label68 attract mode) —
  not implemented, so the attract mode never starts.
- What LOAD/EXTRA sub-items 10/11 and 20-24 are; what CONFIG/HELP need.
- Comparison with impacto RNE: RNE's `TitleMenu` instruction has the same
  byte layout and SF_TITLEMODE show/hide, but RNE's handler only sets
  TITLECUR as a "New Game" hack; SGHD reports decisions through
  SF_TITLEEND, like impacto's CC/MO8 `TitleMenuNew` press-start handling.
- Why `MAIN00.SCX` was not reached: the missing SF_TITLEEND (no title menu)
  plus the never-taken `UselessJump` fully explain it; the path after START
  (label107) is not in the context window.

## Implementation

| Change | Files |
|---|---|
| `TitleMenuType.SGHD`, `UI::SGHD::TitleMenu`: SF_TITLEMODE show/hide; input read every frame while the script polls (latched, because the script polls every other frame); press-start phase: Enter/Space/click → decision; main menu: Up/Down skip disabled items, mouse hover/click on item boxes, Enter/click → item ChoiceId | `src/games/sghd/titlemenu.*`, `src/profile/games/sghd/titlemenu.*`, `src/profile/ui/titlemenu.cpp`, `src/ui/ui.h`, `CMakeLists.txt` |
| `10 34`: type 0/2 reset the cursor and drop stale decisions; type 1 polls the menu and on a decision writes SW_TITLECUR (main menu only) and sets SF_TITLEEND, logging `TitleMenu: press start` / `main menu choice (SW_TITLECUR = N)`; never waits, yields the frame | `src/vm/inst_sghd.cpp` |
| `00 50` UselessJump taken when all labels are equal | `src/vm/inst_sghd.cpp` |
| Title/system-menu scriptvars = Steam/common values | `profiles/sghd/scriptvars.lua` |
| Menu profile: choice ids 0/10/20/30/40, only START enabled, hit boxes measured on the owner's screenshot of the original title (1080p, ±3 px), no sprites until TITLE_CHIP regions are named | `profiles/sghd/hud/titlemenu.lua` |

No artwork is drawn yet: the TITLE_CHIP.DDS regions are not identified
(the Thread 07 region list has two 179×47 chips and a 10×47 bar matching
the screenshot's chip/cursor sizes, but which region is which item is not
determinable from numbers). The profile accepts `ItemSprites`,
`ItemSelectedSprites`, `CursorSprite`, `CursorOffset` once named.

## Tests

| Test | Checks |
|---|---|
| `SghdTitleMenuProbe` (5) | synthetic copy of the Steam title flow with real X input (XTEST through libX11/libXtst): Enter, Enter → START → next script loaded (exit 77); mouse click on START box (77); all items enabled + Down + Enter → SW_TITLECUR 10 (exit 10); committed profile skips disabled items (77); no input → keeps polling without freezing (timeout, >100 polls) |
| `SghdTitleProtocolEvidence` (3) | effective scriptvars equal the fixture's Steam indices; menu profile ids/mode/enabled; `10 34` handler never waits |
| `sghd_reference_trace` | UselessJump with equal labels is taken |

Orb, `impacto-desktop:ubuntu24`, rebuilt binary: `python3 -m unittest
discover -s tests/compat` with `IMPACTO_BIN` → 133/133 OK (96 unit + 37
probes); `SghdTitleMenuProbe` repeated four times without a failure. CI:
[handoff.md](../handoff.md) "CI".

## Remaining unknowns

Title artwork (region naming), title movie 37 (Bink 2), LOAD/EXTRA/CONFIG/
HELP, `10 34 3`, idle attract mode, the path after START on real data,
intermittent segfaults.
