"""Asset-free regression for the Steam SGHD render-mode 40 crash.

A WinDbg stack traced the access violation (impacto+0x361c9) to
Background2D::Render -> BackgroundRenderTable[40] at background2d.cpp:553.
The fixed array has only 40 slots (0 through 39), so that index dispatches
a pointer made out of the following static data ("bgeffect").
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "src/background2d.h"
IMPL = ROOT / "src/background2d.cpp"


class BackgroundRenderModeBounds(unittest.TestCase):
    def test_original_crash_mode_is_one_past_render_table(self):
        header = HEADER.read_text(encoding="utf-8")
        entries = header.split("BackgroundRenderTable =", 1)[1].split("};", 1)[0]
        self.assertEqual(
            len(re.findall(r"&Background2D::", entries)), 40,
            "The source-level regression test should be updated if the table grows.",
        )

    def test_all_dispatchers_use_one_checked_helper(self):
        cpp = IMPL.read_text(encoding="utf-8")
        self.assertEqual(cpp.count("  RenderUsingFadeType();"), 3)
        self.assertNotIn("BackgroundRenderTable[RenderType]", cpp)
        self.assertIn("if (RenderType < 0 ||", cpp)
        self.assertIn(
            "static_cast<size_t>(RenderType) >= BackgroundRenderTable.size()",
            cpp,
        )
        self.assertIn(
            "std::invoke(BackgroundRenderTable[static_cast<size_t>(RenderType)], this);",
            cpp,
        )
        self.assertIn("    RenderRegular();\n    return;", cpp)

    def test_unmapped_mode_is_logged_once_and_falls_back(self):
        cpp = IMPL.read_text(encoding="utf-8")
        self.assertIn("static std::unordered_set<int> warnedModes;", cpp)
        self.assertIn("warnedModes.insert(RenderType).second", cpp)
        self.assertIn("Unknown background fade/render mode {}", cpp)


if __name__ == "__main__":
    unittest.main()
