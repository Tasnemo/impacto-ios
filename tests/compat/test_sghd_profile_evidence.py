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



def lua_sheet_sizes() -> dict:
    text = (SGHD / "sprites.lua").read_text()
    out = {}
    for name, body in re.findall(r'\["(\w+)"\] = \{(.*?)\n    \}', text, re.S):
        w = re.search(r"DesignWidth = (\d+)", body)
        h = re.search(r"DesignHeight = (\d+)", body)
        out[name] = [int(w.group(1)), int(h.group(1))]
    return out


class SghdCensusEvidence(unittest.TestCase):
    """Thread 06: constants from the second-round census."""

    def test_design_resolution(self):
        game = (SGHD / "game.lua").read_text()
        w = int(re.search(r"root\.DesignWidth = (\d+)", game).group(1))
        h = int(re.search(r"root\.DesignHeight = (\d+)", game).group(1))
        self.assertEqual([w, h], EVIDENCE["design_resolution"]["value"])
        self.assertEqual(EVIDENCE["system_images"]["BLOGMASK.DDS"][:2], [w, h])

    def test_loaded_sheet_sizes_are_steam_texture_sizes(self):
        sizes = lua_sheet_sizes()
        for name, entry in EVIDENCE["sprite_sheets"].items():
            if name.startswith("_") or entry is None:
                continue
            with self.subTest(sheet=name):
                self.assertEqual(sizes[name], EVIDENCE["system_images"][entry][:2])

    def test_font_grid_and_widths(self):
        text = (SGHD / "font.lua").read_text()
        grid = re.search(r"GridSize = \{ X = (\d+), Y = (\d+) \}", text)
        self.assertEqual([int(grid.group(1)), int(grid.group(2))], EVIDENCE["font"]["grid"])
        size = EVIDENCE["font"]["size"]
        self.assertEqual(size[0] // EVIDENCE["font"]["grid"][0], EVIDENCE["font"]["cell"])
        self.assertEqual(size[1] // EVIDENCE["font"]["grid"][1], EVIDENCE["font"]["cell"])
        widths = [int(v) for v in re.findall(
            r"\d+", text.split("AdvanceWidthsTable = {", 1)[1].split("}", 1)[0])]
        self.assertEqual(len(widths), 64 * 46)
        self.assertTrue(all(1 <= v <= EVIDENCE["font"]["cell"] for v in widths))
        charset = (REPO / "tools/data/sghd_charset.utf8").read_text(encoding="utf-8")
        self.assertEqual(len(charset), EVIDENCE["font"]["charset_glyphs"])
        self.assertEqual(45 * 64 + EVIDENCE["font"]["last_row_inked_cells"], len(charset))

    def test_lay_settings(self):
        game = (SGHD / "game.lua").read_text()
        self.assertEqual(EVIDENCE["lay"]["byte_order"], "little")
        self.assertRegex(game, r"LayFileBigEndian = false")
        self.assertEqual(EVIDENCE["lay"]["tex_coords"], "pixels")
        self.assertRegex(game, r"LayFileTexXMultiplier = 1;")
        self.assertRegex(game, r"LayFileTexYMultiplier = 1;")
        for sample in EVIDENCE["lay"]["samples"]:
            # 8-byte header, 12-byte states, 16-byte vertices, 1 trailing byte each
            self.assertEqual(8 + 12 * sample["states"] + 17 * sample["vertices"], sample["bytes"])

    def test_every_phone_subtype_is_parsed(self):
        body = (REPO / "src/vm/inst_sghd.cpp").read_text().split("VmInstruction(InstPhoneSGHD)")[1]
        body = body.split("VmInstruction(", 1)[0]
        handled = {int(v, 16) for v in re.findall(r"case (0x[0-9A-Fa-f]+):", body)}
        used = {int(k.split()[2], 16) for k in EVIDENCE["phone_subtypes"]
                if k.startswith("10 37")}
        self.assertEqual(used - handled, set())


if __name__ == "__main__":
    unittest.main()
