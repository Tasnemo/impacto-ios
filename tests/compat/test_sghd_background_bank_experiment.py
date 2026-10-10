"""Static guards for Round 11's *experimental* Steam background-bank A/B test.

The Steam game archives are not checked into CI. Real behavior must be tested
by the owner before this branch is considered production-ready.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "profiles/common/scriptvars.lua"
SGHD = ROOT / "profiles/sghd/scriptvars.lua"
GAME = ROOT / "src/game.cpp"

BG_NAMES = (
    "SW_BG1POSX", "SW_BG1POSY", "SW_BG1NO", "SW_BG1PRI",
    "SW_BG1DISPMODE", "SW_BG1FADECT", "SW_BG1FADETYPE",
    "SW_BG1ALPHA", "SW_BG1MASKNO", "SW_BG1MASKFADERANGE",
    "SW_BG1POSX_OFS", "SW_BG1POSY_OFS", "SW_BG1ALPHA_OFS",
    "SW_BG1SURF", "SW_BGLINK", "SW_BGLINK2"
)

class SteamBackgroundBankExperiment(unittest.TestCase):
    def test_sghd_uses_shared_background_addresses(self):
        common = COMMON.read_text(encoding="utf-8")
        sghd = SGHD.read_text(encoding="utf-8")
        for name in BG_NAMES:
            self.assertRegex(common, rf"\b{name}\s*=\s*\d+")
            self.assertNotRegex(sghd, rf"(?m)^sv\.{name}\s*=")
        self.assertRegex(common, r"SW_BG1FADETYPE=4511")
        self.assertRegex(common, r"SW_BG1SURF=3400")
        self.assertRegex(common, r"SW_BG1POSX_OFS=2500")

    def test_side_by_side_diagnostics_are_rate_limited(self):
        game = GAME.read_text(encoding="utf-8")
        self.assertIn("SGHD BG bank sample", game)
        self.assertIn("nextBgBankLogMs = nowMs + 2000", game)
        for index in (2407, 2411, 1800, 4507, 4511, 3400):
            self.assertIn(f"ScrWork[{index}]", game)

if __name__ == "__main__":
    unittest.main()
