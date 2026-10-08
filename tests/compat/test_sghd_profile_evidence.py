"""profiles/sghd values that come from the owner's Steam install evidence.

Pins each Task 5 configuration value to tests/compat/fixtures/
sghd_steam_evidence.json (minimal constants extracted from the private
tools/sghd_evidence.py report), so the profile cannot drift from the real
install layout. Synthetic: no game data is read."""

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parents[2]
SGHD = REPO / "profiles" / "sghd"
EVIDENCE = json.loads((REPO / "tests/compat/fixtures/sghd_steam_evidence.json").read_text())


def lua_sheets() -> dict:
    text = (SGHD / "sprites.lua").read_text()
    sheets = {}
    for name, body in re.findall(r'\["(\w+)"\] = \{(.*?)\n    \}', text, re.S):
        sheet_id = re.search(r'Path = \{\s*Mount = "system", Id = (\d+)', body)
        sheets[name] = {"id": int(sheet_id.group(1)) if sheet_id else None,
                        "script_handled": "ScriptHandled = true" in body}
    return sheets


class SghdSteamEvidence(unittest.TestCase):
    def test_vfs_mounts_existing_steam_archives(self):
        text = (SGHD / "vfs.lua").read_text()
        mounts = dict(re.findall(r'\["(\w+)"\] = \{root\.BasePaths\.RootGamedataDir \.\. "/sghd/([^"]+)"\}', text))
        self.assertEqual(set(mounts), {"script", "system", "bgm", "se", "voice", "bg", "chara", "mask"})
        for mount, archive in mounts.items():
            self.assertEqual(archive, f"{mount}.mpk")
            self.assertIn(archive, EVIDENCE["archives"], archive)
        self.assertEqual(EVIDENCE["mpk_version"], [2, 0])  # the only version MpkArchive reads

    def test_movies_not_mounted_because_bink2(self):
        self.assertEqual(EVIDENCE["movies"]["signature"], "4b42326a")  # 'KB2j'
        self.assertNotIn('["movie"]', (SGHD / "vfs.lua").read_text())

    def test_start_script_is_startup_win(self):
        start = int(re.search(r"StartScript = (\d+)", (SGHD / "vm.lua").read_text()).group(1))
        self.assertEqual(EVIDENCE["script_mpk"][str(start)], "_STARTUP_WIN.SCX")

    def test_sprite_sheets_follow_evidence(self):
        sheets = lua_sheets()
        expected = {k: v for k, v in EVIDENCE["sprite_sheets"].items() if not k.startswith("_")}
        self.assertEqual(set(sheets), set(expected))
        system = EVIDENCE["system_mpk"]
        for name, entry in expected.items():
            with self.subTest(sheet=name):
                if entry is None:
                    self.assertTrue(sheets[name]["script_handled"],
                                    "no Steam counterpart: must not load an unrelated texture")
                else:
                    self.assertFalse(sheets[name]["script_handled"])
                    self.assertEqual(system[str(sheets[name]["id"])], entry)

    def test_runtime_probe_fixture_uses_the_same_ids(self):
        import test_runtime_probe as probe
        loaded = {str(i): n for i, n in probe.SGHD_SYSTEM_SHEETS.items()}
        expected = {str(s["id"]) for s in lua_sheets().values() if not s["script_handled"]}
        self.assertEqual(set(loaded), expected)
        for sheet_id, name in loaded.items():
            self.assertEqual(EVIDENCE["system_mpk"][sheet_id], name)


if __name__ == "__main__":
    unittest.main()
