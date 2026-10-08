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


def load_table(name: str = "sgps3", suffix: str = "SGPS3") -> dict[str, str]:
    text = (VM_DIR / f"opcodetables_{name}.h").read_text()
    table = {}
    for array, group in TABLES:
        m = re.search(
            r"OpcodeTable%s_%s\[256\] = \{(.*?)\n\};" % (array, suffix), text, re.S)
        entries = re.findall(
            r"\s*(Inst\w+),?\s*//\s*%s ([0-9A-F]{2})" % group, m.group(1))
        if len(entries) != 256:
            raise AssertionError(f"{array}: parsed {len(entries)} slots")
        for handler, opcode in entries:
            table[f"{group} {opcode}"] = handler
    return table


def load_sgps3_table() -> dict[str, str]:
    return load_table("sgps3", "SGPS3")


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
        profile = (REPO / "profiles" / "sghd" / "vm.lua").read_text()
        self.assertIn("sghd/vm.lua", (REPO / "profiles" / "sghd" / "game.lua").read_text())
        self.assertIn("GameInstructionSet = InstructionSet.SGHD", profile)
        self.assertRegex(profile, r"UseReturnIds\s*=\s*true")


# Thread 04 Task 2: the SGHD table.  Every slot Thread 03 documented as broken
# is wired either to an SGHD-layout handler or to a shared handler that has
# an InstructionSet::SGHD branch for the differing sub-type.
SGHD_WIRING = {
    "00 23": "InstSEplay", "00 35": "InstByteArgStubSGHD",
    "00 37": "InstVoicePlay", "00 38": "InstVoiceStopNew",
    "00 41": "InstByteArgStubSGHD", "00 43": "InstSystemMesSGHD",
    "00 4B": "InstStubSGHD", "00 4C": "InstUnk004CSGHD",
    "00 50": "InstUselessJumpSGHD", "00 52": "InstNopSGHD",
    "00 53": "InstUseless0053SGHD", "00 54": "InstCallIfFlag",
    "00 56": "InstCallFarIfFlag", "00 57": "InstReturnIfFlag",
    "00 58": "InstUnk0058SGHD", "00 59": "InstUnk0059SGHD",
    "00 5F": "InstNopSGHD",
    "01 05": "InstCalc", "01 06": "InstUnk0106SGHD", "01 07": "InstUnk0107SGHD",
    "01 08": "InstByteArgStubSGHD", "01 09": "InstCheckpointSGHD",
    "01 0A": "InstByteArgStubSGHD", "01 12": "InstSel",
    "01 25": "InstSetRevMes",
    "10 05": "InstCHAload", "10 12": "InstNopSGHD",
    "10 1A": "InstByteArgStubSGHD", "10 22": "InstAutoSave",
    "10 23": "InstSaveMenu", "10 24": "InstLoadData",
    "10 27": "InstEncyclopediaSGHD", "10 33": "InstTips",
    "10 37": "InstPhoneSGHD", "10 3F": "InstByteArgStubSGHD",
    "10 40": "InstNopSGHD", "10 41": "InstNopSGHD",
}
# Thread 06: slots the first owner census proved wrong (not in the Thread 03
# gap list; evidence in docs/sghd-decode-integrity.md and
# fixtures/sghd_steam_evidence.json "census_layouts").
CENSUS_WIRING = {"10 3A": "InstUnk103ASGHD",
                 # Thread 08 (first real boot): fixed one-byte slots that
                 # SghdFixedLayoutAudit found the sgps3 handlers misread
                 "10 34": "InstTitleMenuSGHD", "10 36": "InstByteArgStubSGHD"}
# shared handlers kept in place; the SGHD layout lives in a guarded branch
SGHD_BRANCHED = {"InstSel", "InstSetRevMes", "InstCHAload", "InstSaveMenu",
                 "InstLoadData", "InstTips"}


class SghdOpcodeTableAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sgps3 = load_sgps3_table()
        cls.table = load_table("sghd", "SGHD")
        cls.sghd = json.loads((FIXTURES / "sghd_opcodes.json").read_text())["opcodes"]
        cls.gaps = json.loads((FIXTURES / "sgps3_known_gaps.json").read_text())
        cls.bodies = load_handler_bodies()

    def test_wiring_covers_exactly_the_documented_gaps(self):
        documented = (set(self.gaps["dummy_slots_used_by_sghd"])
                      | set(self.gaps["argument_layout_mismatches"]))
        self.assertEqual(len(documented), 37)
        self.assertEqual(set(SGHD_WIRING), documented)

    def test_documented_slots_are_wired(self):
        actual = {k: self.table[k] for k in SGHD_WIRING}
        self.assertEqual(actual, SGHD_WIRING)

    def test_no_dummy_slot_remains(self):
        # expected gap list for sghd: empty
        self.assertEqual(
            {k: self.sghd[k] for k in self.sghd if self.table[k] == "InstDummy"}, {})
        self.assertNotIn("InstDummy", set(self.table.values()))

    def test_every_handler_advances_the_instruction_pointer(self):
        stuck = sorted(h for h in set(self.table.values())
                       if "StartInstruction" not in self.bodies[h])
        self.assertEqual(stuck, [])

    def test_branched_shared_handlers_have_sghd_branch(self):
        for handler in SGHD_BRANCHED:
            with self.subTest(handler=handler):
                self.assertIn("InstructionSet::SGHD", self.bodies[handler])

    def test_other_slots_unchanged_from_sgps3(self):
        changed = {k for k in self.table if self.table[k] != self.sgps3[k]}
        replaced_dummies = {k for k in changed
                            if self.sgps3[k] in ("InstDummy", "InstSysVoicePlay")
                            and self.table[k] == "InstUnknownSGHD"}
        self.assertEqual(
            changed - replaced_dummies - set(SGHD_WIRING) - set(CENSUS_WIRING), set())

    def test_census_wiring(self):
        actual = {k: self.table[k] for k in CENSUS_WIRING}
        self.assertEqual(actual, CENSUS_WIRING)
        evidence = json.loads((FIXTURES / "sghd_steam_evidence.json").read_text())
        self.assertEqual(evidence["census_layouts"]["10 3A"]["layout"],
                         "E E E E E E")


# Byte width of each census layout token / impacto Pop macro. Labels, return
# ids, string indices and raw u16 all take two bytes; E is an expression.
CENSUS_TOKEN = {"B": "B", "E": "E", "H": "H", "L": "H", "R": "H", "S": "H"}
POP_TOKEN = {"PopUint8": "B", "PopExpression": "E", "ExpressionEval": "E",
             "PopUint16": "H", "PopLocalLabel": "H", "PopFarLabel": "H",
             "PopString": "H"}
# Fixed-layout slots whose handler pops differ only inside a branch that is
# not taken for SGHD (reviewed in Thread 08); value = why it is safe.
FIXED_LAYOUT_EXCEPTIONS = {
    "00 18": "InstMemberWrite: PopUint8 only when noExpressions (not SGHD)",
    "00 26": "InstSSEplay: channel byte only for CHN",
    "10 13": "InstOption: extra expression only for CHLCC type 4",
    "10 29": "InstSetEVflag: leading byte only for MO8/CHN",
}


class SghdFixedLayoutAudit(unittest.TestCase):
    """Thread 08: every SGHD slot with a fixed (untyped) census layout must
    be read by a handler that pops the same byte classes in the same order.

    The census layout table (tools/sghd_census.py) decoded every reachable
    instruction of the 190 Steam scripts without error (Thread 07), so it is
    the reference. Thread 04 only audited the 37 slots documented in Thread
    03 and missed 10 34 (CHAOS;HEAD TitleMenuOld: no byte, blocks on a title
    menu) and 10 36 (BGeffect: up to four expressions after the byte)."""

    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(REPO / "tools"))
        import sghd_census
        cls.layouts = sghd_census.ALL_LAYOUTS
        cls.table = load_table("sghd", "SGHD")
        cls.bodies = load_handler_bodies()

    def handler_tokens(self, handler: str) -> str:
        calls = re.findall(r"\b(Pop\w+|ExpressionEval)\(", self.bodies[handler])
        return " ".join(POP_TOKEN[c] for c in calls if c in POP_TOKEN)

    def test_fixed_layout_slots_consume_census_bytes(self):
        mismatched = {}
        for (group, opcode), entry in self.layouts.items():
            if len(entry) != 2:  # typed layouts are covered by probes
                continue
            slot = f"{group:02X} {opcode:02X}"
            want = " ".join(CENSUS_TOKEN[t] for t in entry[1].split())
            got = self.handler_tokens(self.table[slot])
            if got != want and slot not in FIXED_LAYOUT_EXCEPTIONS:
                mismatched[slot] = (entry[0], want, self.table[slot], got)
        self.assertEqual(mismatched, {})

    def test_exceptions_are_still_branch_only(self):
        for slot, why in FIXED_LAYOUT_EXCEPTIONS.items():
            with self.subTest(slot=slot):
                body = self.bodies[self.table[slot]]
                self.assertRegex(body, r"if \(|switch \(", why)

    def test_title_menu_slot_never_waits(self):
        # yields the frame (BlockThread) but never re-executes itself
        body = self.bodies[self.table["10 34"]]
        self.assertNotIn("ResetInstruction", body)
        self.assertIn("PopUint8(type)", body)


if __name__ == "__main__":
    unittest.main()
