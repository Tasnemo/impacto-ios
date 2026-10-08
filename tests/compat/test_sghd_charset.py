"""profiles/sghd/charset.lua vs the sc3tools SGHD charset (Thread 04 Task 6).

tools/data/sghd_charset.utf8 is CommitteeOfZero/sc3tools'
resources/sghd/charset.utf8 (MIT): character N is glyph id N, encoded in
scripts as the big-endian token 0x8000 + N.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import gen_sghd_charset as gen  # noqa: E402

CHARSET = (REPO / "tools" / "data" / "sghd_charset.utf8").read_text(encoding="utf-8")


def sc3_token(glyph_id: int) -> int:
    """profiles/common/charset.lua UpdateCharset: 0x80 + id / 256, id % 256."""
    return ((0x80 + glyph_id // 256) << 8) | (glyph_id % 256)


def character_to_sc3(char: str) -> int:
    return sc3_token(CHARSET.index(char))  # first occurrence wins


def sgps3_index_list(name: str) -> list[int]:
    text = (REPO / "profiles" / "sgps3" / "charset.lua").read_text(encoding="utf-8")
    body = re.search(r"local %s = \{(.*?)\};" % name, text, re.S).group(1)
    return [int(x, 0) for x in re.findall(r"0x[0-9A-Fa-f]+|\d+",
                                          body.replace("[0]=", ""))]


class SghdCharset(unittest.TestCase):
    def test_profile_is_generated_from_data(self):
        proc = subprocess.run([sys.executable, str(REPO / "tools" / "gen_sghd_charset.py"),
                               "--check"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_glyph_count_and_layout(self):
        self.assertEqual(len(CHARSET), 2895)
        self.assertEqual(CHARSET[0], " ")
        self.assertEqual(CHARSET[1:11], "0123456789")
        self.assertEqual(CHARSET[11:37], "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.assertEqual(CHARSET[63], "\u3000")

    def test_tokens(self):
        self.assertEqual(character_to_sc3(" "), 0x8000)
        self.assertEqual(character_to_sc3("A"), 0x800B)
        self.assertEqual(character_to_sc3("\u3000"), 0x803F)
        self.assertEqual(sc3_token(2894), 0x8B4E)
        # duplicated glyphs map to their first id
        self.assertEqual(CHARSET.count("♪"), 2)
        self.assertEqual(character_to_sc3("♪"), sc3_token(230))

    def test_flags_match_the_hand_written_ps3_index_lists(self):
        # The PS3 profile lists glyphs by id; decoding those ids with the
        # sc3tools Steam charset yields exactly the generator's character
        # sets, i.e. both releases share this part of the glyph layout.
        for name, chars in (("spaces", gen.SPACES),
                            ("wordEndingPuncts", gen.WORD_ENDING),
                            ("wordStartingPuncts", gen.WORD_STARTING)):
            with self.subTest(name=name):
                decoded = {CHARSET[i] for i in sgps3_index_list(name)}
                self.assertEqual(decoded, set(chars))
                ids = {CHARSET.index(c) for c in chars}
                self.assertEqual(ids, set(sgps3_index_list(name)))

    def test_ps3_glyph_grid_is_smaller_than_the_steam_charset(self):
        # Documented gap (M1): font.lua still describes the PS3 font sheet
        # (64 x 14 cells), far fewer than the 2895 Steam glyph ids. Needs the
        # Steam font sheet (Task 5) before it can change.
        font = (REPO / "profiles" / "sghd" / "font.lua").read_text(encoding="utf-8")
        cols, rows = map(int, re.search(
            r"GridSize = \{ X = (\d+), Y = (\d+) \}", font).groups())
        self.assertEqual((cols, rows), (64, 14))
        self.assertLess(cols * rows, len(CHARSET))


if __name__ == "__main__":
    unittest.main()
