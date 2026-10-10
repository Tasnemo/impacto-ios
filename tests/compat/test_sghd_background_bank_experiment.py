"""Static checks for Round 11's non-invasive background-bank diagnostics.

Real Steam SGHD script.mpk (190 SCX files) has 1734 byte-pattern hits for the
W2400 constant and zero hits for W4511. This is not enough to prove each
background field's meaning, but it refutes a wholesale 2400->4500 migration.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SGHD = ROOT / "profiles/sghd/scriptvars.lua"
GAME = ROOT / "src/game.cpp"

class SteamBackgroundBankDiagnostics(unittest.TestCase):
    def test_original_ps3_named_bank_preserved_until_confirmed(self):
        sghd = SGHD.read_text(encoding="utf-8")
        for name, addr in (
            ("SW_BG1POSX", 2400),
            ("SW_BG1NO", 2407),
            ("SW_BG1FADETYPE", 2411),
            ("SW_BG1SURF", 1800),
        ):
            self.assertIn(f"sv.{name} = {addr};", sghd)

    def test_side_by_side_diagnostics_are_rate_limited(self):
        game = GAME.read_text(encoding="utf-8")
        self.assertIn("SGHD BG bank sample", game)
        self.assertIn("nextBgBankLogMs = nowMs + 2000", game)
        for index in (2407, 2411, 1800, 4507, 4511, 3400):
            self.assertIn(f"ScrWork[{index}]", game)

if __name__ == "__main__":
    unittest.main()
