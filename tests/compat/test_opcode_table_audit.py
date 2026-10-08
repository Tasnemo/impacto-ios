"""Audit impacto's sgps3 opcode tables against the SGHD instruction set.

`fixtures/sghd_opcodes.json` lists every opcode slot the Steam
STEINS;GATE compiler emits (derived from the sc3ntist SGHD disassembler).
`fixtures/sgps3_known_gaps.json` is the documented gap list used by
docs/steins-gate-blockers.md.  The tests assert that the documented list
is exactly what the source shows, so docs and code cannot silently drift.
"""

import json
import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parents[2]
VM_DIR = REPO / "src" / "vm"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

TABLES = (("System", "00"), ("Graph", "01"), ("User1", "10"))


def load_sgps3_table() -> dict[str, str]:
    text = (VM_DIR / "opcodetables_sgps3.h").read_text()
    table = {}
    for array, group in TABLES:
        m = re.search(
            r"OpcodeTable%s_SGPS3\[256\] = \{(.*?)\n\};" % array, text, re.S)
        entries = re.findall(
            r"\s*(Inst\w+),?\s*//\s*%s ([0-9A-F]{2})" % group, m.group(1))
        if len(entries) != 256:
            raise AssertionError(f"{array}: parsed {len(entries)} slots")
        for handler, opcode in entries:
            table[f"{group} {opcode}"] = handler
    return table


def load_handler_bodies() -> dict[str, str]:
    bodies = {}
    for path in sorted(VM_DIR.glob("inst_*.cpp")):
        text = path.read_text()
        for m in re.finditer(r"^VmInstruction\((\w+)\)\s*\{", text, re.M):
            i, depth = m.end(), 1
            while depth and i < len(text):
                depth += (text[i] == "{") - (text[i] == "}")
                i += 1
            bodies[m.group(1)] = text[m.start():i]
    return bodies


class OpcodeTableAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sgps3 = load_sgps3_table()
        cls.sghd = json.loads((FIXTURES / "sghd_opcodes.json").read_text())["opcodes"]
        cls.gaps = json.loads((FIXTURES / "sgps3_known_gaps.json").read_text())
        cls.bodies = load_handler_bodies()

    def test_sghd_reference_covers_three_groups(self):
        groups = {k[:2] for k in self.sghd}
        self.assertEqual(groups, {"00", "01", "10"})
        self.assertEqual(len(self.sghd), 154)

    def test_every_sgps3_handler_has_a_body(self):
        missing = {h for h in self.sgps3.values() if h not in self.bodies}
        self.assertEqual(missing, set())

    def test_dummy_slots_used_by_sghd_match_documented_list(self):
        actual = {k: self.sghd[k] for k in self.sghd
                  if self.sgps3[k] == "InstDummy"}
        self.assertEqual(actual, self.gaps["dummy_slots_used_by_sghd"])

    def test_handlers_without_start_instruction(self):
        # Handlers that never advance IpOffset hang the VM (RunThread loops
        # until the thread blocks).  Only InstDummy and the unused
        # InstSysVoicePlay (00 4D, not emitted by SGHD) lack it today.
        used = set(self.sgps3.values())
        stuck = sorted(h for h in used
                       if "StartInstruction" not in self.bodies[h])
        self.assertEqual(stuck, ["InstDummy", "InstSysVoicePlay"])
        self.assertNotIn("00 4D", self.sghd)

    def test_return_if_flag_slot_differs(self):
        # impacto places InstReturnIfFlag at 00 55 but SGHD emits it at 00 57
        self.assertEqual(self.sgps3["00 55"], "InstReturnIfFlag")
        self.assertEqual(self.sghd["00 57"], "ReturnIfFlag")
        self.assertNotIn("00 55", self.sghd)

    def test_group_calc_slot_differs(self):
        self.assertEqual(self.sgps3["01 0A"], "InstCalc")
        self.assertEqual(self.sghd["01 05"], "GroupCalc")
        self.assertEqual(self.sgps3["01 05"], "InstDummy")

    def test_documented_layout_mismatches_point_at_live_slots(self):
        for slot in self.gaps["argument_layout_mismatches"]:
            with self.subTest(slot=slot):
                self.assertIn(slot, self.sghd)
                self.assertNotEqual(self.sgps3[slot], "InstDummy")

    def test_sgps3_profile_disables_return_ids(self):
        profile = (REPO / "profiles" / "sgps3" / "game.lua").read_text()
        self.assertRegex(profile, r"UseReturnIds\s*=\s*false")

    def test_sgps3_is_not_a_launchable_game_definition(self):
        defs = (REPO / "gamedefinitions.lua").read_text()
        self.assertNotRegex(defs, r"(?m)^\s*sgps3\s*=")
        # Thread 04 Task 1 registered the Steam release as its own game id
        self.assertRegex(defs, r"(?m)^\s*sghd\s*=")

    def test_sghd_profile_selects_sghd_table_with_return_ids(self):
        profile = (REPO / "profiles" / "sghd" / "game.lua").read_text()
        self.assertIn("GameInstructionSet = InstructionSet.SGHD", profile)
        self.assertRegex(profile, r"UseReturnIds\s*=\s*true")


if __name__ == "__main__":
    unittest.main()
