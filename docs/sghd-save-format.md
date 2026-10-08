# sghd fork-native save format (version 1)

Thread 04 Task 4. Implemented by `src/games/sghd/savesystem.cpp`
(`SaveDataType.SGHD`), selected in `profiles/sghd/savedata.lua`.

**This is not the Steam `SAVEDATA.DAT` format.** Steam's layout is
undocumented and is neither read nor written. The file only round-trips
impacto's own VM state so that the SGHD VM can save and resume. A Steam save
importer would be a separate, evidence-based task.

Default path: `<RootSavesDir>/sghd/impacto-sghd.sav`. All integers are
little-endian.

| Field | Type | Notes |
|---|---|---|
| magic | 8 bytes | `IMPSGHD\0` |
| version | u32 | `1`; other versions are rejected |
| full slot count | u32 | `80` (Steam UI count, unverified) |
| quick slot count | u32 | `48` |
| FlagWork ranges | u32 n, n × u32 | flattened (start byte, length) pairs from the profile |
| ScrWork ranges | u32 n, n × u32 | flattened (start index, length) pairs from the profile |
| read lines | u32 count, then per script: u32 script id, u32 byte count, bitmap | bit `line % 8` of byte `line / 8` |
| quick-save order | 48 × u8 | `QuickSaveRecentSortedId` |
| entries | 80 full, then 48 quick | see below |

A file whose ranges differ from the active profile is refused (the stored
variable blocks would land in the wrong places).

Entry: `u8 status`; if 0 nothing follows. Otherwise:

| Field | Type |
|---|---|
| play time, SW_TITLE | 2 × u32 |
| flags (bit 0 = write protect) | u8 |
| quick-save type | u32 |
| save date: tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec | 6 × i32 |
| checkpoint id (last `SetCheckpointId`, e.g. `10 22` type `0A`) | u32 |
| main thread: exec priority, group, wait counter, script param, script buffer, IP, loop counter, loop label, call-stack depth | 9 × u32 |
| return addresses / return ids (thread union, verbatim) | 8 × u32 |
| return script buffers | 8 × u32 |
| thread variables | 16 × i32 |
| dialogue page | u32 |
| FlagWork bytes | u32 n, n bytes |
| ScrWork values | u32 n, n × i32 |

The "main thread" is `ThreadPool[ScrWork[SW_MAINTHDP]]`; thread 0 (the
startup thread) is never saved or restored. The raw IP is restored, so a save
is only valid with the same script files loaded in the same buffers (the
script's own load routine is responsible for that, as in the other MAGES
titles).

VM entry points (existing handlers in the sghd table): `10 22` type 0
(AutoSave → `SaveMemory`), `00 2A` (`InstSaveOld`) 16 = flush working entry
to full slot `ScrWork[SW_SAVEFILENO]`, 30/31 = write file / wait, 32/33 = read
file / wait; `10 24` (`InstLoadData`) type 0 = load slot variables, type 1 =
restore the main thread. These sub-type meanings come from impacto's
existing CHLCC-era handlers and are unverified for the Steam scripts.

Not persisted yet: tips, CG/EV and BGM unlocks, thumbnails, configuration.
`FlagWorkRanges = {50, 50, 300, 100}` and `ScrWorkRanges = {300, 300, 2300,
1300}` copy the CHLCC/sgps3 layout and must be checked against real Steam
scripts.

Test: `tests/compat/test_runtime_probe.py` `SghdSaveRoundTripProbe` (save
run → parse the file in Python → second process loads slot 79 and resumes the
main thread at the saved address with the saved call stack).
