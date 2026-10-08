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
        widths = [float(v) for v in re.findall(
            r"[\d.]+", text.split("AdvanceWidthsTable = {", 1)[1].split("}", 1)[0])]
        self.assertEqual(len(widths), 64 * 46)
        self.assertTrue(all(1 <= v <= EVIDENCE["font"]["cell"] for v in widths))
        # Thread 07: generated from the Game.exe table (32-unit em -> 48 px cell)
        fw = EVIDENCE["font"]["widths"]
        scale = EVIDENCE["font"]["cell"] / fw["em"]
        self.assertIn(fw["offset"], text)
        self.assertEqual(widths[0], fw["glyph0"] * scale)
        self.assertEqual(widths[1], fw["glyph1"] * scale)
        self.assertTrue(all((v / scale).is_integer() for v in widths[:fw["count"]]))
        self.assertEqual(set(widths[fw["count"]:]), {float(EVIDENCE["font"]["cell"])})

    def test_exe_width_report_parser(self):
        sys.path.insert(0, str(REPO / "tools"))
        import gen_sghd_font_widths as gen
        rows = ["32 " + " ".join(["17"] * 63)] + [" ".join(["20"] * 64)] * 5
        report = ("# header\n  0.950 0x1000 1 : 32 17 17\n  0.700 0x1001 1 : 17\n"
                  "## best candidate 0x1000, 2944 values\n"
                  + "\n".join("  " + r for r in rows) + "\n  0 0 252 255\n")
        widths, info = gen.widths_from_exe_report(report)
        self.assertEqual(info, {"offset": "0x1000", "correlation": 0.95, "count": 384})
        self.assertEqual(widths[:2], [48.0, 25.5])
        self.assertEqual(widths[64], 30.0)
        self.assertEqual(widths[384:], [48.0] * (2944 - 384))
        with self.assertRaises(ValueError):
            gen.widths_from_exe_report(report.replace("0.950", "0.850"))
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

    def test_text_styles_are_720p(self):
        ts = EVIDENCE["text_styles"]
        self.assertLessEqual(ts["mode0"]["MaxLineWidth"], ts["max_line_width"])
        self.assertLessEqual(ts["max_line_width"], 1280)
        self.assertTrue(all(c < l for c, l in zip(ts["mode0"]["WaitIconPos"], (1280, 720))))
        # impacto scales script text styles by DesignWidth/1280 unless the
        # profile overrides them; the Steam profile must not override
        self.assertNotIn("TextModesInfo", (SGHD / "dialogue.lua").read_text())
        self.assertEqual(ts["mode0"]["TextGlyph"][1] * 1920 // 1280, 48)

    def test_sprites_lie_inside_their_sheets(self):
        sys.path.insert(0, str(REPO / "tools"))
        import sghd_inspect as si
        sizes = lua_sheet_sizes()
        for name, sheet, x, y, w, h in si.profile_sprites(SGHD):
            with self.subTest(sprite=name):
                sw, sh = sizes[sheet]
                self.assertTrue(0 <= x and 0 <= y and x + w <= sw and y + h <= sh,
                                f"{name} outside {sheet} {sw}x{sh}")

    def test_checked_sprites_match_steam_regions(self):
        sys.path.insert(0, str(REPO / "tools"))
        import sghd_inspect as si
        sprites = {s[0]: s[2:] for s in si.profile_sprites(SGHD)}
        regions = EVIDENCE["sheet_regions"]["DATA01.DDS_checked"]
        x, y, w, h = sprites["ADVBox"]
        rx, ry, rw, rh = regions["adv_box"]
        self.assertLessEqual(abs(x - rx), 1)
        self.assertLessEqual(abs((x + w) - (rx + rw)), 1)
        self.assertLessEqual(abs(y - ry), 3)
        x, y, w, h = sprites["NametagLeftSprite"]
        rx, ry, rw, rh = regions["nametag_left"]
        self.assertTrue(x <= rx and y <= ry and rx + rw <= x + w + 1 and ry + rh <= y + h)
        x, y, w, h = sprites["DialogueWaitIcon"]
        rx, ry, rw, rh = regions["wait_icon_column"]
        self.assertTrue(rx <= x and ry <= y and x + w <= rx + rw and y + h <= ry + rh)

    def test_no_inherited_chaos_head_title_or_backlog_sprites(self):
        text = "".join(p.read_text() for p in SGHD.rglob("*.lua"))
        for name in ("Seira", "CHLogo", "LCCLogo", "DelusionADV", "ChuLeftLogo",
                     "ScrollbarTrack", "BacklogBackground"):
            self.assertFalse(name in text, name)
        self.assertFalse((SGHD / "hud" / "systemmenu.lua").exists())

    def test_voice_table_is_little_endian(self):
        vt = EVIDENCE["voice_table"]
        self.assertEqual(EVIDENCE["system_mpk"][str(vt["id"])], vt["entry"])
        self.assertEqual(int.from_bytes(bytes.fromhex(vt["first_bytes"])[:2], "little"),
                         EVIDENCE["audio"]["voice.mpk"]["ogg-vorbis"])
        self.assertRegex((SGHD / "game.lua").read_text(), r"VoiceTableLittleEndian = true")

    def test_every_phone_subtype_is_parsed(self):
        body = (REPO / "src/vm/inst_sghd.cpp").read_text().split("VmInstruction(InstPhoneSGHD)")[1]
        body = body.split("VmInstruction(", 1)[0]
        handled = {int(v, 16) for v in re.findall(r"case (0x[0-9A-Fa-f]+):", body)}
        used = {int(k.split()[2], 16) for k in EVIDENCE["phone_subtypes"]
                if k.startswith("10 37")}
        self.assertEqual(used - handled, set())


if __name__ == "__main__":
    unittest.main()
