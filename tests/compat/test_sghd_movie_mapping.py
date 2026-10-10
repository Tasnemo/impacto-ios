"""Steam STEINS;GATE movie ID mapping without copyrighted video fixtures.

References only movie filenames (metadata), never the owner's private MPKs,
Game.exe, BK2s, converted footage or extracted frames.
"""
import re
import unittest
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INST_MOVIE = ROOT / "src" / "vm" / "inst_movie.cpp"
VFS = ROOT / "profiles" / "sghd" / "vfs.lua"
RUNTIME = ROOT / "tests" / "compat" / "test_runtime_probe.py"


class SghdMovieMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cxx = INST_MOVIE.read_text(encoding="utf-8")
        cls.vfs = VFS.read_text(encoding="utf-8")
        block = cls.cxx.split("static constexpr std::array<std::string_view, 38> SghdMovieStems", 1)[1]
        block = block.split("};", 1)[0]
        cls.stems = re.findall(r'"([a-z0-9_]+)"', block)

    def test_original_steam_movie_id_order(self):
        self.assertEqual(len(self.stems), 38)
        self.assertEqual(len(set(self.stems)), 38)
        for index, name in (
            (0, "ar"), (1, "ending_c"), (6, "imv001"),
            (20, "imv034b"), (32, "op"), (33, "op2"),
            (34, "prologue01"), (35, "prologue02"),
            (36, "timeleapbg"), (37, "title"),
        ):
            self.assertEqual(self.stems[index], name)

    def test_movies_resolve_by_name_in_steam_only(self):
        self.assertIn('GameInstructionSet != InstructionSet::SGHD', self.cxx)
        self.assertIn('Io::VfsOpen("movie", movieId, stream)', self.cxx)
        self.assertIn('Io::VfsOpen("movie", stem + ".mp4", stream)', self.cxx)
        self.assertIn('Io::VfsOpen("movie", stem + ".bk2", stream)', self.cxx)
        self.assertEqual(self.cxx.count('OpenMovieStream(playNo, &stream)'), 2)

    def test_optional_private_conversion_folder_only(self):
        self.assertIn('"/sghd/movie-converted"', self.vfs)
        self.assertNotIn('"/sghd/movie/1920x1080"', self.vfs)
        self.assertIn('ar.bk2', RUNTIME.read_text(encoding="utf-8"))

    def test_runtime_synthetic_bink_movie_is_actually_created(self):
        # Runtime probe must exercise an undecodable Bink movie, not an absent
        # file; otherwise its 'safe skip' test can produce misleading results.
        sys.path.insert(0, str(ROOT / "tests" / "compat"))
        from test_runtime_probe import write_gamedata
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_gamedata(root, game="sghd-harness-media")
            movie = root / "gamedata" / "sghd" / "movie" / "ar.bk2"
            self.assertTrue(movie.is_file())
            self.assertEqual(movie.read_bytes()[:4], b"KB2j")

if __name__ == "__main__":
    unittest.main()
