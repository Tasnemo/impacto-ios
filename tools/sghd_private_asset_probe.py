#!/usr/bin/env python3
"""Private, asset-free-to-repo STEINS;GATE Steam file validation.

Uses the existing SGHD instruction decoder on the owner's local Steam assets.
No assets, extracted bytes, dialogue, raw text or screenshots are copied,
uploaded, or written anywhere. Prints only aggregate numerical evidence.

Example (run on the owner's PC, from a checkout of this repository):
  python tools/sghd_private_asset_probe.py --root "C:\\Steam\\steamapps\\common\\STEINS;GATE"

Or with files supplied separately:
  python tools/sghd_private_asset_probe.py --script path/to/script.mpk \\
      --system path/to/system.mpk --exe path/to/Game.exe \\
      --title path/to/title.bk2
"""

import argparse
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

# Existing stdlib-only project decoder (not third-party).
from sghd_census import MOVIE, mpk_entries, mpk_read, walk_script


def movie_table(exe: Path):
    """Movie filenames in original Game.exe table order. Return names only."""
    data = exe.read_bytes()
    found = re.findall(rb"(?<![A-Za-z0-9_])([A-Za-z0-9_]+\.bk2)\x00",
                       data, flags=re.IGNORECASE)
    # Table entries are unique in the original Steam executable.
    return [name.decode("ascii").lower() for name in found]


def probe_script(path: Path):
    entries = mpk_entries(path)
    by_id = {entry[0]: entry[1] for entry in entries}
    if len(entries) != 190 or by_id.get(2) != "_STARTUP_WIN.SCX" or by_id.get(12) != "SG00_01.SCX":
        raise ValueError("Steam script MPK does not match the expected 190-script release")

    words = Counter()
    script_count = 0
    decoded_count = 0
    decode_errors = 0
    movie_ops = Counter()
    for entry in entries:
        if not entry[1].upper().endswith(".SCX"):
            continue
        script_count += 1
        instructions, errors, _, _ = walk_script(mpk_read(path, entry))
        decoded_count += len(instructions)
        decode_errors += len(errors)
        for _, _, slot, _, args in instructions:
            if slot in MOVIE:
                # No script text, filenames, or per-scene plot content emitted.
                movie_ops[entry[1]] += 1
            for kind, value in args:
                if kind != "E":
                    continue
                for idx, token in enumerate(value[:-1]):
                    if token == "W" and isinstance(value[idx + 1], int):
                        words[value[idx + 1]] += 1

    return {
        "script_count": script_count,
        "decoded_instruction_count": decoded_count,
        "decode_errors": decode_errors,
        "background_word_refs": {
            str(index): words[index] for index in
            [1800, 2400, 2407, 2410, 2411, 2412, 2413, 2414, 2500,
             3400, 4500, 4507, 4511, 4513]
        },
        "opening_script_movie_opcode_count": movie_ops["SG00_01.SCX"],
    }


def probe_system(path: Path):
    entries = mpk_entries(path)
    by_name = {entry[1].upper(): entry[0] for entry in entries}
    return {
        "entry_count": len(entries),
        "title_atlas_id": by_name.get("TITLE_CHIP.DDS"),
        "default_font_id": by_name.get("FONT.PNG"),
        "secondary_font_id": by_name.get("FONT2.PNG"),
    }


def probe_title(path: Path):
    with path.open("rb") as handle:
        header = handle.read(32)
    if len(header) < 28 or header[:4] not in (b"KB2j", b"KB2i", b"KB2h"):
        raise ValueError("Not a supported Bink 2 header signature")
    width, height = struct.unpack_from("<II", header, 20)
    return {"bink2_signature": header[:4].decode("ascii"),
            "width": width, "height": height}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, help="Steam STEINS;GATE installation root")
    p.add_argument("--script", type=Path, help="path to script.mpk")
    p.add_argument("--system", type=Path, help="path to system.mpk")
    p.add_argument("--exe", type=Path, help="path to Game.exe")
    p.add_argument("--title", type=Path, help="path to title.bk2")
    a = p.parse_args(argv)
    if a.root is None and not any((a.script, a.system, a.exe, a.title)):
        p.error("Specify --root or at least one of --script/--system/--exe/--title")
    root = a.root
    paths = {
        "scripts": a.script or (root / "USRDIR/script.mpk" if root else None),
        "system": a.system or (root / "USRDIR/system.mpk" if root else None),
        "exe": a.exe or (root / "Game.exe" if root else None),
        "title_video": a.title or (root / "USRDIR/movie/1920x1080/title.bk2" if root else None),
    }
    out = {"probe_version": 1, "files_present": {}}
    for kind, path in paths.items():
        if path is None:
            continue
        if not path.is_file():
            raise FileNotFoundError("Required local file missing: " + kind)
        out["files_present"][kind] = True
        if kind == "scripts":
            out["scripts"] = probe_script(path)
        elif kind == "system":
            out["system"] = probe_system(path)
        elif kind == "exe":
            table = movie_table(path)
            out["exe_movie_table"] = {
                "movie_count": len(table),
                "title_movie_id": table.index("title.bk2") if "title.bk2" in table else None,
            }
        elif kind == "title_video":
            out["title_video"] = probe_title(path)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
