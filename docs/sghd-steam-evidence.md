# STEINS;GATE Steam install: evidence and decisions (Thread 05)

Input: the owner's `tools/sghd_evidence.py` report from a legitimate Steam
install (private, **not committed**). Only the constants the `sghd` profile
needs are recorded, in
[`tests/compat/fixtures/sghd_steam_evidence.json`](../tests/compat/fixtures/sghd_steam_evidence.json);
`tests/compat/test_sghd_profile_evidence.py` pins the profile to them.

## What the evidence settles

| Question (handoff) | Answer | Profile change |
|---|---|---|
| Archive names/version | 11 lowercase `USRDIR/*.mpk`, all MPK v2.0, uncompressed entries. impacto uses 8: script, system, bgm, se, voice, bg, chara, mask. `manual`, `shader`, `mgsshader` are unused. | `vfs.lua` comment only (names were already right) |
| Start script | `script.mpk` id 2 = `_STARTUP_WIN.SCX` (ids 0–4 are `_ATCH`, `_MAIL`, `_STARTUP_WIN`, `_SYSTEM`, `_TIPS`) | `StartScript = 2` confirmed |
| `system.mpk` sheets | 32 entries: 29 DDS, `FONT.PNG` (9), `FONT2.PNG` (10), `WAVTABLE.DAT` (31) | `sprites.lua`: Backlog → 2 `BACKLOG.DDS`, Data → 6 `DATA01.DDS`, Font → 9 `FONT.PNG`, Title → 30 `TITLE_CHIP.DDS`; Menu/TitleBg1/TitleBg2 have no counterpart → `ScriptHandled` |
| Movies | 38 loose `.bk2` files each in `USRDIR/movie/1280x720` and `1920x1080`; signature `KB2j` = **Bink 2** | not mounted (see below) |
| Audio | `bgm.mpk` `.ogg`, `se.mpk`/`voice.mpk` `.OGG` entries | none needed if Vorbis (synthetic probe passes) |
| Character layers | `chara.mpk` pairs `CRS_*.png` + `CRS_*_.lay` | open: LAY byte order (profile still says big-endian, from PS3) |

The sheet mapping is by entry name only. Sheet dimensions and every sprite
rectangle are still the PS3 values, so the HUD will not line up yet.

## Movie decision (M2)

The Steam movies cannot be played by impacto: FFmpeg has no Bink 2 decoder
(its demuxer opens the file and reports codec `none`), and the movie
id → file mapping is inside `Game.exe`, not in an archive. So:

1. `movie` is not mounted. `PlayMovie` then fails to open the file, logs
   it, and the script continues (`SghdMovieSkipProbe.test_unmounted_movie_is_skipped`).
2. If a Bink 2 file is mounted anyway, impacto used to start playback with
   no video stream and the reader thread dereferenced it. Now
   `FFmpegPlayer::Play` refuses a stream without a decodable video track,
   and `PlayMovie` skips a movie that did not start, instead of waiting
   forever on `SF_MOVIEPLAY` (`test_bink2_movie_is_skipped_without_crash`,
   synthetic `KB2j` file). Both fixes also apply to other games; before,
   that case crashed.
3. Later option, not implemented: the owner transcodes the movies locally
   to a format FFmpeg reads (needs RAD's Bink 2 tools; FFmpeg cannot read
   Bink 2) and mounts a folder whose sorted names match the movie ids from
   the census (`--exe`, `Movie instructions`).

## Still open: second-round owner evidence

`tools/sghd_census.py` (stdlib only, tested on synthetic data by
`tests/compat/test_sghd_census.py`) collects the rest without printing
script text, images or audio:

```powershell
cd <checkout of this repository, branch phase-03-sghd-implementation>
python tools\sghd_census.py "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE" > sghd-census.txt
```

It takes a few minutes (pure-Python PNG decoding of the two fonts). Share
`sghd-census.txt` privately, as you did `sghd-evidence.txt`.

| Census section | Unblocks |
|---|---|
| Scripts: decode errors | Confirms every SGHD layout on all 190 real scripts (a desync means a wrong layout) |
| Scripts: opcode counts, stub uses | Which stubbed opcodes real scripts use, with their sub-types (Task 6/8 priorities) |
| Scripts: phone/mail with context | Task 7a phone protocol catalogue (`10 37`/`10 38` sub-types, the flags/ScrWork around them) |
| Scripts: movie instructions | Movie ids actually used; with `--exe` the id → file mapping |
| Scripts: ScrWork/FlagWork ranges | Save ranges (Task 4 currently uses CHLCC defaults) |
| Assets: DDS/PNG headers | Sheet `DesignWidth`/`DesignHeight`, DDS formats impacto can decode (DXT1–5/RGB only, not DX10/BC7) |
| Assets: font ink extents | Font grid and advance widths for `font.lua` (FONT vs FONT2 role) |
| Assets: LAY check | `LayFileBigEndian` and texture multipliers for characters |
| Assets: audio codecs | Vorbis vs Opus for every bgm/se/voice entry |

Sprite rectangles (dialogue box, name plate, title chips, phone) cannot be
derived from numbers alone; they need a person to look at the sheets on the
owner's machine, or a first-boot screenshot.

## First boot on Windows (Task 5 exit criterion)

The `Desktop Windows` workflow (`.github/workflows/desktop-windows.yml`)
uploads an `impacto-windows-x64-<sha>` artifact with no game data. Unzip it,
then:

```powershell
$STEAM = "C:\Program Files (x86)\Steam\steamapps\common\STEINS;GATE"
mkdir gamedata\sghd
foreach ($a in "script","system","bgm","se","voice","bg","chara","mask") {
  Copy-Item "$STEAM\USRDIR\$a.mpk" gamedata\sghd\   # or New-Item -ItemType HardLink
}
.\impacto.exe -g sghd -ll Debug -lf sghd.log
```

Expect a broken HUD (PS3 rectangles). Share `sghd.log` privately (it may
contain dialogue at Debug level; `-ll Info` avoids most of it) plus a
screenshot if anything renders.
