"""MPK archive format checks for the Steam STEINS;GATE release.

The Steam release ships its data as `USRDIR/*.mpk` (MAGES. Package) files
with the 2.0 header (64-bit offsets).  impacto's reader
(src/io/mpkarchive.cpp) only understands that version.  These tests build
synthetic archives and check them against the exact byte layout impacto
consumes, and also check that the source still carries the limitation the
compatibility docs describe.
"""

import pathlib
import re
import unittest

from sc3fixtures import (MpkFile, MpkUnsupported, build_mpk, parse_mpk,
                         read_mpk_file)

REPO = pathlib.Path(__file__).resolve().parents[2]
MPK_SOURCE = REPO / "src" / "io" / "mpkarchive.cpp"


class MpkV2Layout(unittest.TestCase):
    def setUp(self):
        self.files = [
            MpkFile(0, "script_startup.scx", b"SC3\0" + bytes(60)),
            MpkFile(1, "bgm01.ogg", b"OggS" + bytes(1000), compressed=True),
            MpkFile(7, "sg_data.png", b"\x89PNG\r\n\x1a\n" + bytes(300)),
        ]
        self.blob = build_mpk(self.files)

    def test_header_matches_impacto_reader(self):
        # MpkArchive::Create: magic as big-endian u32 0x4D504B00, then
        # LE u16 minor == 0 and LE u16 major == 2, then LE u32 file count.
        self.assertEqual(self.blob[0:4], b"MPK\0")
        self.assertEqual(self.blob[4:6], b"\x00\x00")  # minor
        self.assertEqual(self.blob[6:8], b"\x02\x00")  # major
        self.assertEqual(int.from_bytes(self.blob[8:12], "little"), 3)

    def test_toc_entries_round_trip(self):
        entries = parse_mpk(self.blob)
        self.assertEqual([e.file_id for e in entries], [0, 1, 7])
        self.assertEqual([e.name for e in entries],
                         [f.name for f in self.files])
        for entry, src in zip(entries, self.files):
            self.assertEqual(entry.size, len(src.data))
            self.assertEqual(entry.compressed, int(src.compressed))
            self.assertEqual(read_mpk_file(self.blob, entry), src.data)

    def test_compressed_entry_is_zlib(self):
        entry = parse_mpk(self.blob)[1]
        self.assertEqual(entry.compressed, 1)
        self.assertLess(entry.compressed_size, entry.size)
        # zlib stream header (impacto uses ZlibStream for compression == 1)
        self.assertEqual(self.blob[entry.offset] & 0x0F, 8)

    def test_sparse_ids_are_preserved(self):
        # Steam archives address files by id (VfsSlurp("script", id)); ids
        # are not required to be dense.
        ids = {e.file_id for e in parse_mpk(self.blob)}
        self.assertEqual(ids, {0, 1, 7})


class MpkV1Rejected(unittest.TestCase):
    def test_v1_header_is_rejected_like_impacto(self):
        blob = build_mpk([MpkFile(0, "a.bin", b"x")], major=1, minor=0)
        with self.assertRaisesRegex(MpkUnsupported, "version 1.0"):
            parse_mpk(blob)

    def test_impacto_source_still_only_accepts_2_0(self):
        # Keep docs/steins-gate-compatibility.md honest: if upstream adds
        # v1 support, this assertion fails and the docs must be updated.
        text = MPK_SOURCE.read_text()
        self.assertRegex(text, r"MinorVersion != 0 \|\| MajorVersion != 2")
        self.assertIn("TODO support v1", text)


if __name__ == "__main__":
    unittest.main()
