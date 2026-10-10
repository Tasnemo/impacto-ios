"""Asset-free tests for the optional Steam binary probe.

These use tiny synthetic headers/table names, never proprietary game data.
"""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import sghd_private_asset_probe as probe


class PrivateAssetProbeTests(unittest.TestCase):
    def test_title_movie_index_from_original_style_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Game.exe"
            paths = [b"ar.bk2", b"op.bk2", b"title.bk2"]
            path.write_bytes(b"header\x00" + b"\x00".join(paths) + b"\x00")
            self.assertEqual(probe.movie_table(path), ["ar.bk2", "op.bk2", "title.bk2"])

    def test_bink2_header_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "title.bk2"
            header = bytearray(32)
            header[:4] = b"KB2j"
            struct.pack_into("<II", header, 20, 1920, 1080)
            path.write_bytes(header)
            self.assertEqual(probe.probe_title(path)["width"], 1920)
            self.assertEqual(probe.probe_title(path)["height"], 1080)

    def test_probe_exe_summary_does_not_reveal_movie_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Game.exe"
            path.write_bytes(b"some_movie_name.bk2\x00title.bk2\x00")
            output = StringIO()
            with redirect_stdout(output):
                rc = probe.main(["--exe", str(path)])
            self.assertEqual(rc, 0)
            result = json.loads(output.getvalue())
            self.assertEqual(result["exe_movie_table"]["title_movie_id"], 1)
            self.assertNotIn("some_movie_name", output.getvalue())
            self.assertNotIn(str(path), output.getvalue())


if __name__ == "__main__":
    unittest.main()
