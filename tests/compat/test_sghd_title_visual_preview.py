"""Asset-free guards for the SGHD Windows title preview.

The actual Steam graphics remain on the owner's disk. These tests only check
the profile's coordinate-based sprite declarations and the rendering hooks.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
TITLE = ROOT / "profiles/sghd/hud/titlemenu.lua"
RENDERER = ROOT / "src/games/sghd/titlemenu.cpp"
GAME = ROOT / "src/game.cpp"


class SghdTitleVisualPreview(unittest.TestCase):
    def test_steam_title_sheet_is_used_without_bundling_pixels(self):
        text = TITLE.read_text(encoding="utf-8")
        self.assertIn('Sheet = "Title"', text)
        self.assertIn('PreviewBackgroundSprite = "SghdPreviewTitleBg"', text)
        self.assertIn('ItemSprites = {', text)
        self.assertIn('ItemSelectedSprites = {', text)
        self.assertEqual(
            set(re.findall(r'"SghdTitleCandidate([1-5])Normal"', text)),
            set("12345"),
        )
        self.assertEqual(
            set(re.findall(r'"SghdTitleCandidate([1-5])Selected"', text)),
            set("12345"),
        )

    def test_candidate_pairs_fit_the_declared_title_sheet(self):
        text = TITLE.read_text(encoding="utf-8")
        rows = re.findall(
            r"\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\}",
            text,
        )
        self.assertEqual(len(rows), 5)
        for raw in rows:
            left, top, right, selected_top, width, height = map(int, raw)
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            self.assertLessEqual(left + width, 3072)
            self.assertLessEqual(right + width, 3072)
            self.assertLessEqual(top + height, 1536)
            self.assertLessEqual(selected_top + height, 1536)

    def test_title_overlay_drawn_independently_of_script_draw_order(self):
        game = GAME.read_text(encoding="utf-8")
        renderer = RENDERER.read_text(encoding="utf-8")
        self.assertIn('menu == UI::TitleMenuPtr', game)
        self.assertIn('UI::TitleMenuPtr->Render();', game)
        self.assertIn('if (State != Shown) return;', renderer)
        self.assertIn('DrawFallbackText("Press Enter"', renderer)
        self.assertIn('START", "LOAD", "EXTRA", "CONFIG", "HELP', renderer)
        self.assertIn('if (sprite)', renderer)
        self.assertIn('item.SelectedSprite ? item.SelectedSprite : item.NormalSprite', renderer)
        self.assertIn('RectF(bounds.X + 4.0f, bounds.Y + 4.0f, 8.0f, 46.0f)', renderer)
        self.assertNotIn('WINDOWS COMPATIBILITY PREVIEW', renderer)
        self.assertNotIn('PRESS ENTER OR CLICK TO START', renderer)
        self.assertNotIn('DrawFallbackText(labels[i],\n                         {bounds.X - 130.0f', renderer)


if __name__ == "__main__":
    unittest.main()
