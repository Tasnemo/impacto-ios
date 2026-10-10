"""Static checks for the SGHD Steam background controls.

The owner's original, private Steam script.mpk demonstrates:
  SG00_01.SCX 0x028E: 10 01 LoadBackground(buffer 1, id 59)
  SG00_01.SCX 0x0297: W4508 = 11   (render priority)
  SG00_01.SCX 0x3016: W4511 = 1    (render type)
  SG00_01.SCX 0x62C3: W4511 = 15   (render type)
  SG00_01.SCX 0x0E9A: W4504 = 1000 (transform scale)
Those numeric observations are recorded here; no script/game bytes are stored.

The unrelated W2400 region occurs frequently, but raw frequency counts cannot
identify a particular field's semantics. We now inherit the common W4500 bank.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SGHD = ROOT / "profiles/sghd/scriptvars.lua"
COMMON = ROOT / "profiles/common/scriptvars.lua"
GAME = ROOT / "src/game.cpp"

BG_NAMES = (
    "SW_BG1POSX", "SW_BG1POSY", "SW_BG1SX", "SW_BG1SY",
    "SW_BG1SIZE", "SW_BG1LX", "SW_BG1LY", "SW_BG1NO", "SW_BG1PRI",
    "SW_BG1DISPMODE", "SW_BG1FADECT", "SW_BG1FADETYPE",
    "SW_BG1ALPHA", "SW_BG1MASKNO", "SW_BG1MASKFADERANGE",
    "SW_BG1POSX_OFS", "SW_BG1POSY_OFS", "SW_BG1SX_OFS",
    "SW_BG1SY_OFS", "SW_BG1SIZE_OFS", "SW_BG1LX_OFS",
    "SW_BG1LY_OFS", "SW_BG1ALPHA_OFS", "SW_BG1SURF",
    "SW_BGLINK", "SW_BGLINK2",
)


class SteamBackgroundBankDiagnostics(unittest.TestCase):
    def test_steam_bg_controls_inherit_common_bank(self):
        sghd = SGHD.read_text(encoding="utf-8")
        common = COMMON.read_text(encoding="utf-8")
        for name in BG_NAMES:
            self.assertNotRegex(sghd, rf"(?m)^sv\.{name}\s*=")
            self.assertRegex(common, rf"\b{name}\s*=\s*\d+")
        for name, value in (
            ("SW_BG1POSX", 4500), ("SW_BG1SIZE", 4504),
            ("SW_BG1NO", 4507), ("SW_BG1PRI", 4508),
            ("SW_BG1FADETYPE", 4511),
            ("SW_BG1POSX_OFS", 2500),
            ("SW_BG1SURF", 3400),
            ("SW_BGLINK", 4490),
        ):
            self.assertRegex(common, rf"\b{name}\s*=\s*{value}\b")

    def test_other_ps3_overrides_intentionally_not_changed(self):
        sghd = SGHD.read_text(encoding="utf-8")
        self.assertIn("sv.SW_CHA1POSX = 2600;", sghd)
        self.assertIn("sv.SW_CHA1SURF = 1850;", sghd)

    def test_old_and_new_registers_remain_sampled_in_runtime(self):
        game = GAME.read_text(encoding="utf-8")
        self.assertIn("SGHD BG bank sample", game)
        self.assertIn("nextBgBankLogMs = nowMs + 2000", game)
        for index in (2407, 2411, 1800, 4507, 4511, 3400):
            self.assertIn(f"ScrWork[{index}]", game)


if __name__ == "__main__":
    unittest.main()
