#!/usr/bin/env python3
"""Collect shareable STEINS;GATE (Steam) layout evidence for Thread 04 Task 5.

Run on the machine with the legally owned Steam installation (Windows,
Python 3.9+, no third-party packages):

    python tools/sghd_evidence.py "C:\\Program Files (x86)\\Steam\\steamapps\\common\\STEINS;GATE" > sghd-evidence.txt

The report contains only metadata: file names and sizes, the first 16 bytes
of each archive/movie file, MPK versions, and MPK table-of-contents entries
(id, name, sizes). It never reads or prints file contents beyond those
headers, so it contains no script text, images or audio. Check it before
sharing anyway.

It answers the open questions in docs/handoff.md: MPK version (impacto reads
only 2.0), archive names for profiles/sghd/vfs.lua, system.mpk sheet ids for
sprites.lua, script.mpk ids for StartScript, and movie signatures (BIK = Bink
1, KB2 = Bink 2) for the movie decision (M2).
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

MOVIE_EXTS = {".bik", ".bk2", ".usm", ".wmv", ".mp4", ".webm", ".ogv"}
ARCHIVE_EXTS = {".mpk", ".cpk", ".afs"}
MPK_ENTRY = 0x100


def hex16(path: Path) -> str:
    with path.open("rb") as f:
        return f.read(16).hex(" ")


def movie_kind(head: bytes) -> str:
    if head[:3] == b"BIK":
        return "Bink 1 (ffmpeg can decode)"
    if head[:3] == b"KB2":
        return "Bink 2 (impacto/ffmpeg cannot decode)"
    if head[:4] == b"CRID":
        return "CRI USM"
    return "unknown"


def mpk_report(path: Path, max_entries: int | None) -> list[str]:
    out = []
    with path.open("rb") as f:
        header = f.read(0x40)
        if header[:4] != b"MPK\0":
            return ["  not an MPK archive"]
        minor, major, count = struct.unpack_from("<HHI", header, 4)
        supported = "supported" if (major, minor) == (2, 0) else "NOT supported by impacto"
        out.append(f"  MPK version {major}.{minor} ({supported}), {count} entries")
        shown = count if max_entries is None else min(count, max_entries)
        for _ in range(shown):
            raw = f.read(MPK_ENTRY)
            if len(raw) < MPK_ENTRY:
                out.append("  (truncated table of contents)")
                break
            comp, file_id, offset, csize, size = struct.unpack_from("<IIQQQ", raw)
            name = raw[32:].split(b"\0", 1)[0].decode("ascii", "replace")
            kind = ""
            if Path(name).suffix.lower() in MOVIE_EXTS:
                here = f.tell()
                f.seek(offset)
                kind = "  movie: " + movie_kind(f.read(4))
                f.seek(here)
            out.append(f"  id {file_id:5d}  {name:40s} size {size:10d}"
                       f"  stored {csize:10d}  compression {comp}{kind}")
        if shown < count:
            out.append(f"  ... {count - shown} more entries (use --all)")
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(args[0])
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    show_all = "--all" in argv

    files = sorted(p for p in root.rglob("*") if p.is_file())
    print(f"# sghd evidence report ({len(files)} files under the install root)")
    print("\n## Files (relative path, size)")
    for p in files:
        print(f"{p.relative_to(root).as_posix()}  {p.stat().st_size}")

    print("\n## Archives (first 16 bytes, MPK table of contents)")
    for p in files:
        if p.suffix.lower() not in ARCHIVE_EXTS:
            continue
        print(f"{p.relative_to(root).as_posix()}: {hex16(p)}")
        limit = None if show_all or p.stem.lower() in ("system", "script") else 40
        for line in mpk_report(p, limit):
            print(line)

    print("\n## Loose movie files (signature)")
    for p in files:
        if p.suffix.lower() in MOVIE_EXTS:
            with p.open("rb") as f:
                head = f.read(4)
            print(f"{p.relative_to(root).as_posix()}: {head.hex(' ')}  {movie_kind(head)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
