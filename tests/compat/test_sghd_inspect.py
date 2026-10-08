"""tools/sghd_inspect.py (owner-side sheet/sprite/width inspection) on
synthetic data. No game data: the DDS, PNG, MPK and executable are built
here."""

import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc3fixtures as fx  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "sghd_inspect.py"
sys.path.insert(0, str(REPO / "tools"))
import sghd_inspect as inspect_tool  # noqa: E402


def dxt5(width: int, height: int, opaque_blocks: set[tuple[int, int]],
         rgb565: int = 0xF800) -> bytes:
    """DXT5 texture; listed 4x4 blocks are opaque `rgb565`, others clear."""
    header = bytearray(128)
    header[:4] = b"DDS "
    struct.pack_into("<7I", header, 4, 124, 0x1007, height, width, width * height, 0, 1)
    struct.pack_into("<II4s", header, 76, 32, 0x4, b"DXT5")
    body = bytearray()
    for by in range(height // 4):
        for bx in range(width // 4):
            a = 255 if (bx, by) in opaque_blocks else 0
            body += bytes([a, a]) + bytes(6) + struct.pack("<HHI", rgb565, rgb565, 0)
    return bytes(header) + bytes(body)


class InspectDecoding(unittest.TestCase):
    def test_dxt5_decode_and_boxes(self):
        # 32x16: a 3x2-block region at blocks (1..3, 1..2) and one block at (7, 0)
        blocks = {(x, y) for x in (1, 2, 3) for y in (1, 2)} | {(7, 0)}
        w, h, px = inspect_tool.dds_decode(dxt5(32, 16, blocks))
        self.assertEqual((w, h), (32, 16))
        o = (5 * 32 + 5) * 4
        self.assertEqual(tuple(px[o:o + 4]), (255, 0, 0, 255))
        self.assertEqual(px[3], 0)
        _, _, alpha = inspect_tool.dds_decode(dxt5(32, 16, blocks), alpha_only=True)
        boxes = inspect_tool.opaque_boxes(w, h, alpha)
        self.assertEqual(boxes, [(4, 4, 12, 8), (28, 0, 4, 4)])

    def test_split_box_separates_sprites_one_pixel_apart(self):
        # two opaque 5x3 rectangles separated by a 1-px transparent column:
        # one region at 4x4-block level, two at pixel level
        w, h = 16, 4
        alpha = bytearray(w * h)
        for y in range(3):
            for x in list(range(0, 5)) + list(range(6, 11)):
                alpha[y * w + x] = 255
        boxes = inspect_tool.opaque_boxes(w, h, alpha)
        self.assertEqual(boxes, [(0, 0, 11, 3)])
        self.assertEqual(inspect_tool.split_box(w, alpha, boxes[0]),
                         [(0, 0, 5, 3), (6, 0, 5, 3)])

    def test_png_roundtrip(self):
        rgba = bytes([10, 20, 30, 40, 50, 60, 70, 80])
        w, h, px = inspect_tool.png_decode(inspect_tool.png_encode(2, 1, rgba))
        self.assertEqual((w, h, bytes(px)), (2, 1, rgba))

    def test_profile_sprites_parse_real_profile(self):
        sprites = {s[0]: s for s in inspect_tool.profile_sprites(REPO / "profiles" / "sghd")}
        self.assertIn("ADVBox", sprites)
        self.assertEqual(sprites["ADVBox"][1], "Data")
        sheets = inspect_tool.profile_sheets(REPO / "profiles" / "sghd")
        self.assertEqual(sheets["Data"], (6, False))
        self.assertEqual(sheets["Menu"][1], True)

    def test_width_table_search(self):
        ink = [None] * 2944
        widths = [12, 30, 48, 20, 26, 38, 16, 44] * 32
        for i in range(256):
            if i % 3:
                ink[i] = widths[i] + (i % 2)  # noisy measurement
        table = bytes(widths) + bytes(2944 - 256)
        exe = bytes(range(256)) * 40 + table + bytes(1000)
        cands = inspect_tool.find_width_table(exe, ink)
        self.assertTrue(cands)
        self.assertEqual(cands[0][1:], (256 * 40, 1))
        self.assertGreater(cands[0][0], 0.95)


class InspectTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        usr = cls.root / "USRDIR"
        usr.mkdir()
        # DATA01.DDS (id 6) stands in for the Steam sheet: 64x32 with one
        # opaque region; profile sprites outside it are skipped, not fatal
        blocks = {(x, y) for x in range(0, 4) for y in range(0, 2)}
        (usr / "system.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(6, "DATA01.DDS", dxt5(64, 32, blocks))]))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args],
                              capture_output=True, text=True)

    def test_sheets(self):
        proc = self.run_tool("sheets", str(self.root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("## id 6 DATA01.DDS 64x32: 1 regions", proc.stdout)
        self.assertIn("  0 0 16 8", proc.stdout)

    def test_crops(self):
        out = self.root / "crops"
        proc = self.run_tool("crops", str(self.root), str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((out / "index.html").exists())
        # DialogueWaitIcon (Data 1.5,145.5) lies outside the 64x32 stand-in
        self.assertIn("skip DialogueWaitIcon: rectangle outside Data", proc.stdout)

    def test_regions(self):
        out = self.root / "regions"
        proc = self.run_tool("regions", str(self.root), str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DATA01.DDS: 1 crops", proc.stdout)
        self.assertTrue((out / "6_0_0_16_8.png").exists())
        self.assertIn("6_0_0_16_8.png", (out / "index.html").read_text())

    def test_usage(self):
        self.assertEqual(self.run_tool().returncode, 2)


if __name__ == "__main__":
    unittest.main()
