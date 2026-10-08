"""tools/sghd_census.py (owner-side second-round evidence) on synthetic data.

No game data: every archive, script, image and executable below is built
here. Checks that the census decodes SGHD scripts with the same layouts as
the reference decoder, reports phone/movie/stub instructions and decode
errors, measures font glyph ink, reads DDS/LAY headers, and never prints
string contents."""

import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc3fixtures as fx  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "sghd_census.py"
sys.path.insert(0, str(REPO / "tools"))
import sghd_census as census  # noqa: E402

SECRET = b"SECRET-DIALOGUE"


def png_rgba(width: int, height: int, alpha_rows: list[list[int]]) -> bytes:
    """RGBA PNG whose rows use filter types 0..4 in turn (exercises unfilter)."""
    bpp, stride = 4, width * 4
    raw_rows = [bytes(b for a in row for b in (255, 255, 255, a)) for row in alpha_rows]
    out, prev = bytearray(), bytes(stride)
    for y, line in enumerate(raw_rows):
        ftype = y % 5
        enc = bytearray()
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 0:
                pred = 0
            elif ftype == 1:
                pred = a
            elif ftype == 2:
                pred = b
            elif ftype == 3:
                pred = (a + b) >> 1
            else:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            enc.append((line[i] - pred) & 0xFF)
        out += bytes([ftype]) + enc
        prev = line

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(out)))
            + chunk(b"IEND", b""))


def dds_dxt5(width: int, height: int) -> bytes:
    header = bytearray(128)
    header[:4] = b"DDS "
    struct.pack_into("<7I", header, 4, 124, 0x1007, height, width, width * height, 0, 1)
    struct.pack_into("<II4s", header, 76, 32, 0x4, b"DXT5")
    struct.pack_into("<I", header, 108, 0x1000)  # DDSCAPS_TEXTURE (required by the loader)
    return bytes(header) + bytes(width * height)


def lay_le() -> bytes:
    # 1 state (id 7, start 0, 2 vertices); screen xy + normalized tex uv
    return (struct.pack("<ii", 1, 0) + struct.pack("<iii", 7, 0, 2)
            + struct.pack("<4f", 10.0, 20.0, 0.25, 0.5)
            + struct.pack("<4f", 30.0, 40.0, 0.75, 1.0))


def census_script() -> bytes:
    E = fx.expr
    b = fx.ScxBuilder()
    s = b.add_string(SECRET)
    main = (fx.sghd_assign(1)
            + fx.ins(0x10, 0x37, fx.u8(0x14), E(1), E(2), E(3), E(4))
            + fx.sghd_set_flag(1770)
            + fx.ins(0x01, 0x22, fx.u8(0), fx.u8(1), E(12), E(1))     # PlayMovie
            + fx.ins(0x00, 0x35, fx.u8(9))                          # stub
            + fx.ins(0x01, 0x0C, fx.u8(0), E(0), fx.u16(s))           # LoadDialogue
            + fx.ins(0x00, 0x08, E(0), fx.u16(1))                    # JumpTable -> data label 1
            + fx.ins(0x10, 0x38, fx.u8(0), fx.u16(1))             # u16 table -> data label 1
            + fx.ins(0x01, 0x0E, E(0), fx.u16(3))                    # text style -> label 3
            + fx.sghd_assign_scrwork(2123, 5)
            + fx.sghd_end_of_script())
    b.add_label(main)
    b.add_label(b"\xff\xff\xff\xff")                                # data, not code
    b.add_label(bytes([0x20, 0x00]) + fx.sghd_end_of_script())     # unknown opcode
    b.add_label(struct.pack("<24h", *range(24)))                    # text style data
    return b.build()


class CensusLayoutTable(unittest.TestCase):
    def test_slots_and_names_match_opcode_fixture(self):
        names = json.loads((REPO / "tests/compat/fixtures/sghd_opcodes.json")
                           .read_text())["opcodes"]
        table = {f"{g:02X} {o:02X}": e[0] for (g, o), e in census.LAYOUTS.items()}
        self.assertEqual(table, names)

    def test_agrees_with_reference_decoder_on_task2_fixture(self):
        blob = fx.sghd_task2_fixture()
        insts, errors, _, notes = census.walk_script(blob)
        self.assertEqual(errors, [])
        self.assertEqual(notes, [])
        # every instruction the reference decoder sees in label 0, at the same
        # addresses (census additionally decodes the other labels)
        pos = fx.scx_label_address(blob, 0)
        end = fx.scx_label_address(blob, 1)
        ref = []
        while pos < end:
            name, _, nxt = fx.decode_sghd(blob, pos)
            ref.append(pos)
            pos = nxt
        got = [p for label, p, *_ in insts if label == 0]
        self.assertEqual(got, ref)

    def test_dds_loader_sanity_check_reported(self):
        good = census.dds_info(dds_dxt5(8, 8))
        self.assertIn("flags 0x1007 caps 0x1000", good)
        self.assertNotIn("rejected", good)
        bad = bytearray(dds_dxt5(8, 8))
        struct.pack_into("<I", bad, 108, 0)  # no DDSCAPS_TEXTURE
        self.assertIn("(impacto: rejected, missing DDSCAPS_TEXTURE)", census.dds_info(bytes(bad)))

    def test_full_expressions_decode(self):
        # ScrWork[2123] = 5  ->  W 2123 = 5
        blob = fx.sghd_assign_scrwork(2123, 5)
        slot, name, args, nxt = census.decode(blob, 0)
        self.assertEqual((name, args, nxt), ("Assign", [("E", ["W", 2123, "=", 5])], len(blob)))


class CensusClassification(unittest.TestCase):
    """Thread 06: separate layout evidence from padding and data."""

    @staticmethod
    def script() -> bytes:
        E = fx.expr
        b = fx.ScxBuilder()
        # 0: code, Return, then one stray byte before label 1 (after-end)
        b.add_label(fx.sghd_assign(1) + fx.sghd_return() + b"\x10")
        # 1: real mid-code failure: Assign then an unknown opcode
        b.add_label(fx.sghd_assign(2) + bytes([0x00, 0x60]) + fx.sghd_return())
        # 2: slots missing from sc3ntist decode with impacto's layouts
        b.add_label(fx.ins(0x10, 0x0D, fx.u8(1), E(63), fx.u16(4))
                    + fx.ins(0x10, 0x3A, E(63)) + fx.ins(0x10, 0x2E, E(4300))
                    + fx.sghd_return())
        # 3: unreferenced u32 table; 4: CHAmove sequence data
        b.add_label(struct.pack("<3i", 297, 301, -1))
        b.add_label(struct.pack("<4H", 1, 0, 360, 60))
        # 5: last label, EndOfScript and one alignment byte before strings
        b.add_label(fx.sghd_end_of_script() + b"\x00")
        return b.build()

    def test_classification(self):
        blob = self.script()
        insts, errors, data_labels, notes = census.walk_script(blob)
        self.assertEqual([(e[0], e[2]) for e in errors],
                         [(1, "unrecognized opcode 00 60")])
        self.assertTrue(any("bytes" in line for line in errors[0][4]))
        self.assertIn(("after-end", 0), [(n[0], n[1]) for n in notes])
        self.assertIn(("after-end", 5), [(n[0], n[1]) for n in notes])
        names = [i[3] for i in insts if i[0] == 2]
        self.assertEqual(names, ["CHAmove", "Unk103A", "SetSceneViewFlag", "Return"])
        # label 3 is unreferenced data: an entry note, never an error;
        # label 4 is CHAmove sequence data and is skipped
        self.assertIn(("entry", 3), [(n[0], n[1]) for n in notes])
        self.assertEqual(data_labels, {4})

    def test_lt_reference_marks_data_label(self):
        b = fx.ScxBuilder()
        # TV 64 = LT(1, TV 63): expression tokens as impacto encodes them
        def imm(v):
            return fx.encode_immediate(v) + b"\x0a"
        b.add_label(b"\xfe\x2d\x0a" + imm(64) + b"\x14\x01\x2b\x0a" + imm(1)
                    + b"\x2d\x0a" + imm(63) + b"\x00" + fx.sghd_return())
        b.add_label(struct.pack("<2i", 5, -1))
        _, errors, data_labels, notes = census.walk_script(b.build())
        self.assertEqual(errors, [])
        self.assertEqual(data_labels, {1})
        self.assertEqual(notes, [])


class CensusTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        usr = root / "USRDIR"
        (usr / "movie" / "1920x1080").mkdir(parents=True)
        (usr / "script.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(2, "_STARTUP_WIN.SCX", census_script())]))
        # 64 columns x 1 row of 2-px cells: glyph 0 inks column 1 only,
        # glyph 1 both columns, glyph 2 empty, rest empty
        row = [0] * 128
        row[1] = 255
        row[2] = row[3] = 200
        font = png_rgba(128, 2, [row, [0] * 128])
        (usr / "system.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(2, "BACKLOG.DDS", dds_dxt5(64, 32)),
             fx.MpkFile(9, "FONT.PNG", font)]))
        (usr / "chara.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(0, "CRS_X.png", png_rgba(4, 1, [[0, 0, 0, 0]])),
             fx.MpkFile(1, "CRS_X_.lay", lay_le())]))
        ogg = (REPO / "tests/compat/fixtures/synthetic_tone.ogg").read_bytes()
        (usr / "voice.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(0, "A.OGG", ogg), fx.MpkFile(1, "B.OGG", ogg),
             fx.MpkFile(2, "C.OGG", b"RIFF" + bytes(60))]))
        for stem in ("title", "op"):
            (usr / "movie" / "1920x1080" / f"{stem}.bk2").write_bytes(b"KB2j")
        (root / "Game.exe").write_bytes(b"MZ\0\0" + b"\0title\0zzz\0op.bk2\0shop\0")
        proc = subprocess.run([sys.executable, str(TOOL), str(root)],
                              capture_output=True, text=True)
        cls.rc, cls.out = proc.returncode, proc.stdout

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_exit_status(self):
        self.assertEqual(self.rc, 0, self.out)

    def test_never_prints_strings(self):
        self.assertNotIn("SECRET", self.out)
        self.assertIn("LoadDialogue type=0x00 (0) str#0", self.out)

    def test_data_label_skipped_unknown_opcode_reported(self):
        entry = self.out.split("### Labels whose first instruction")[1].split("###")[0]
        self.assertIn("_STARTUP_WIN.SCX label2 @", entry)
        self.assertIn("unrecognized opcode 20 00", entry)
        self.assertNotIn("label1 @", self.out.split("### Decode errors")[1].split("###")[0])

    def test_text_style_dump(self):
        section = self.out.split("### Text styles")[1].split("###")[0]
        self.assertIn("id (0) 0 1 2 3 4 5", section)
        self.assertIn(" 21 22 23", section)
        self.assertIn("data-labels   2", self.out)

    def test_phone_instruction_with_context(self):
        self.assertIn("10 37 Group1037 type=0x14 (1) (2) (3) (4)", self.out)
        self.assertIn("10 37 type=0x14: 1", self.out)
        self.assertIn("10 38 Group1038 type=0x00 label1", self.out)
        self.assertIn("> @", self.out)  # following instructions listed

    def test_movie_and_stub_and_ranges(self):
        self.assertIn("01 22 ActualLoadCutscene type=0x00 1 (12) (1)", self.out)
        self.assertIn("00 35 Unk0035: 1  [(9,)x1]", self.out)
        self.assertIn("2100:1", self.out)       # ScrWork 2123 bucket
        self.assertIn("1700:1", self.out)       # flag 1770 bucket

    def test_assets(self):
        self.assertIn("id   2 BACKLOG.DDS          DDS 64x32 mips 1 pfflags 0x4 fourcc DXT5", self.out)
        self.assertIn("id   9 FONT.PNG             PNG 128x2 depth 8 colortype 6", self.out)
        self.assertIn("cell 2x2 px", self.out)
        self.assertIn("row   0: 1-1 0-1 . .", self.out)
        self.assertIn("little-endian: states 1 second-int 0 vertices 2 needs 52 of 52 bytes", self.out)
        self.assertIn("max tex of first 64 (0.7500, 1.0000)", self.out)

    def test_audio_codecs(self):
        self.assertIn("voice.mpk: not-ogg:52494646 x1, ogg-vorbis x2", self.out)

    def test_exe_movie_order(self):
        section = self.out.split("## Game.exe")[1]
        names = [line.split()[1] for line in section.strip().splitlines()[1:]]
        self.assertEqual(names, ["title", "op.bk2"])  # 'shop' is not 'op'


if __name__ == "__main__":
    unittest.main()
