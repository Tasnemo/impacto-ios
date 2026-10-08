"""tools/sghd_evidence.py against a synthetic install tree (no game data)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc3fixtures as fx  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "sghd_evidence.py"


class EvidenceTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        usr = root / "USRDIR"
        usr.mkdir()
        secret = b"SECRET-SCRIPT-TEXT" * 4
        (usr / "system.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(7, "data.png", b"\x89PNG" + secret),
             fx.MpkFile(9, "op.bk2", b"KB2j" + secret)]))
        (usr / "script.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(2, "_startup.scx", b"SC3\0" + secret)]))
        (usr / "old.mpk").write_bytes(fx.build_mpk(
            [fx.MpkFile(0, "x.bin", b"\0")], major=1))
        (root / "movie").mkdir()
        (root / "movie" / "ed.bik").write_bytes(b"BIKi" + secret)
        proc = subprocess.run([sys.executable, str(TOOL), str(root)],
                              capture_output=True, text=True)
        cls.rc, cls.out = proc.returncode, proc.stdout

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_runs(self):
        self.assertEqual(self.rc, 0)

    def test_reports_mpk_versions_and_entries(self):
        self.assertIn("USRDIR/system.mpk: 4d 50 4b 00 00 00 02 00", self.out)
        self.assertIn("MPK version 2.0 (supported), 2 entries", self.out)
        self.assertIn("MPK version 1.0 (NOT supported by impacto)", self.out)
        self.assertRegex(self.out, r"id\s+7\s+data\.png")
        self.assertRegex(self.out, r"id\s+2\s+_startup\.scx")

    def test_reports_movie_signatures(self):
        self.assertIn("op.bk2", self.out)
        self.assertIn("movie: Bink 2", self.out)
        self.assertIn("movie/ed.bik: 42 49 4b 69  Bink 1", self.out)

    def test_never_prints_file_contents(self):
        self.assertNotIn("SECRET", self.out)


if __name__ == "__main__":
    unittest.main()
