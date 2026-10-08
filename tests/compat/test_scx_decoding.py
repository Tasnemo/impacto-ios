"""SC3/SCX container and SGHD instruction-stream decoding checks.

Two decoders are run over the same synthetic script:

* `decode_sghd`  - the Steam STEINS;GATE (SGHD) argument layouts, as
  documented by the sc3ntist SGHD disassembler.
* `decode_impacto_sgps3` - the number of bytes impacto's *current* sgps3
  handlers consume (src/vm/inst_controlflow.cpp, inst_system.cpp,
  opcodetables_sgps3.h), parameterised by Profile::Vm::UseReturnIds.

Where they disagree, the Steam script stream desyncs inside impacto.  The
tests pin down both the correct layout and the concrete failure so Thread 04
can verify the fix (flip UseReturnIds, replace InstDummy slots) by making
the "impacto" decoder agree with the reference.
"""

import pathlib
import struct
import unittest

from sc3fixtures import (SGHD_LAYOUTS, ScxBuilder, decode_immediate,
                         decode_sghd, encode_immediate,
                         sghd_reference_trace, sghd_task2_fixture,
                         eval_single_immediate, expr, scx_label_address,
                         scx_return_address, scx_string_address, sghd_assign,
                         sghd_call, sghd_call_far, sghd_call_if_flag,
                         sghd_end_of_script, sghd_group_checkpoint, sghd_jump,
                         sghd_jump_if, sghd_nop, sghd_return,
                         sghd_return_if_flag, sghd_set_flag, skip_expression)

REPO = pathlib.Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------
# Reference (SGHD) decoder
# --------------------------------------------------------------------------

# decode_sghd lives in sc3fixtures (shared with the runtime probe).


# --------------------------------------------------------------------------
# Emulation of impacto's sgps3 handlers (byte consumption only)
# --------------------------------------------------------------------------

HANG = "InstDummy(hang)"


def decode_impacto_sgps3(blob: bytes, pos: int, use_return_ids: bool):
    """Return (handler, next_pos). next_pos == pos means InstDummy (no
    StartInstruction, so the thread never advances: see
    src/vm/inst_system.cpp InstDummy and src/vm/vm.cpp RunThread)."""
    grp = blob[pos]
    if grp == 0xFE:
        return "ExpressionEval", skip_expression(blob, pos + 1)
    op = blob[pos + 1]
    p = pos + 2
    key = (grp, op)
    if key == (0x00, 0x00):
        return "InstEnd", p
    if key == (0x00, 0x07):
        return "InstJump", p + 2
    if key == (0x00, 0x0A):
        # InstIf: PopUint8, PopExpression, PopUint16
        p = skip_expression(blob, p + 1)
        return "InstIf", p + 2
    if key == (0x00, 0x0B):
        # InstCall: PopLocalLabel; PopUint16(retNum) only if UseReturnIds
        return "InstCall", p + 2 + (2 if use_return_ids else 0)
    if key == (0x00, 0x0D):
        p = skip_expression(blob, p)
        return "InstCallFar", p + 2 + (2 if use_return_ids else 0)
    if key == (0x00, 0x0E):
        return "InstReturn", p
    if key == (0x00, 0x12):
        return "InstSetFlag", skip_expression(blob, p)
    if key == (0x00, 0x54):
        # opcodetables_sgps3.h 00 54 -> InstUnk0054: PopExpression x2
        p = skip_expression(blob, p)
        return "InstUnk0054", skip_expression(blob, p)
    if key in ((0x00, 0x57), (0x00, 0x5F), (0x01, 0x09)):
        return HANG, pos
    if grp not in (0x00, 0x01, 0x02, 0x10):
        # vm.cpp RunThread: "Thread CRASH! Unknown opcode. Attempting
        # recovery" (pops the call stack or skips to the next 0xFE byte)
        return f"ThreadCrash({grp:02X} {op:02X})", pos
    raise AssertionError(f"fixture uses unhandled opcode {grp:02X} {op:02X}")


def run_decoder(decoder, blob, start, end, **kw):
    out = []
    pos = start
    while pos < end:
        result = decoder(blob, pos, **kw)
        name, nxt = result[0], result[-1]
        out.append(name)
        if nxt == pos:
            break
        pos = nxt
    return out


# --------------------------------------------------------------------------
# Fixture
# --------------------------------------------------------------------------

def build_fixture():
    """Label 0: main; label 1: subroutine; label 2: flag-guarded sub."""
    b = ScxBuilder()
    s_hello = b.add_string(b"\x00Hello\x00")  # arbitrary string payload

    main = bytearray()
    main += sghd_assign(1234)
    main += sghd_set_flag(1770)
    call_at = len(main)
    main += sghd_call(1, 0)          # return id 0
    after_call = len(main)
    main += sghd_jump_if(1, 0, 0)    # never taken (cond 0, expects true)
    main += sghd_call_if_flag(1, 1770, 2, 1)   # return id 1
    after_call_if_flag = len(main)
    main += sghd_call_far(0, 1, 2)   # return id 2
    after_call_far = len(main)
    main += sghd_group_checkpoint(0, 42)
    main += sghd_nop()
    main += sghd_jump(0)
    main += sghd_end_of_script()

    sub = sghd_assign(-5) + sghd_return()
    guarded = sghd_return_if_flag(1, 1770) + sghd_assign(7) + sghd_return()

    b.add_label(bytes(main))
    b.add_label(sub)
    b.add_label(guarded)
    b.add_return(0, after_call)
    b.add_return(0, after_call_if_flag)
    b.add_return(0, after_call_far)
    blob = b.build()
    marks = dict(call_at=call_at, after_call=after_call,
                 after_call_if_flag=after_call_if_flag,
                 after_call_far=after_call_far, string=s_hello)
    return blob, marks


class ExpressionImmediates(unittest.TestCase):
    CASES = [0, 1, 15, -1, -16, 16, -17, 0xFFF, -0x1000, 0x1000, -0x1001,
             0xFFFFF, -0x100000, 0x100000, -0x100001, 0x7FFFFFFF,
             -0x80000000]

    def test_round_trip_all_length_classes(self):
        for value in self.CASES:
            with self.subTest(value=value):
                token = encode_immediate(value) + b"\x0A"
                decoded, pos = decode_immediate(token, 0)
                self.assertEqual(decoded, value)
                self.assertEqual(pos, len(token))

    def test_length_class_boundaries(self):
        # bits 5-6 of the first byte select the size impacto switches on
        self.assertEqual(len(encode_immediate(15)), 1)
        self.assertEqual(len(encode_immediate(16)), 2)
        self.assertEqual(len(encode_immediate(-16)), 1)
        self.assertEqual(len(encode_immediate(-17)), 2)
        self.assertEqual(len(encode_immediate(0xFFF)), 2)
        self.assertEqual(len(encode_immediate(0x1000)), 3)
        self.assertEqual(len(encode_immediate(0xFFFFF)), 3)
        self.assertEqual(len(encode_immediate(0x100000)), 5)
        self.assertEqual(encode_immediate(-1)[0] & 0x10, 0x10)
        self.assertEqual(encode_immediate(1)[0] & 0x10, 0)

    def test_impacto_source_decodes_the_same_four_classes(self):
        text = (REPO / "src" / "vm" / "expression.cpp").read_text()
        for needle in ("case 0x20:", "case 0x40:", "case 0x60:",
                       "0xFFFFFFE0", "0xFFFFE000", "0xFFE00000"):
            self.assertIn(needle, text)


class ScxContainer(unittest.TestCase):
    def setUp(self):
        self.blob, self.marks = build_fixture()

    def test_header_pointers(self):
        self.assertEqual(self.blob[:4], b"SC3\0")
        string_table = struct.unpack_from("<I", self.blob, 4)[0]
        return_table = struct.unpack_from("<I", self.blob, 8)[0]
        self.assertLess(string_table, return_table)
        self.assertEqual(scx_label_address(self.blob, 0), 12 + 4 * 3)

    def test_string_and_return_tables_resolve(self):
        s = scx_string_address(self.blob, self.marks["string"])
        self.assertEqual(self.blob[s:s + 7], b"\x00Hello\x00")
        base = scx_label_address(self.blob, 0)
        self.assertEqual(scx_return_address(self.blob, 0),
                         base + self.marks["after_call"])
        self.assertEqual(scx_return_address(self.blob, 2),
                         base + self.marks["after_call_far"])


class SghdLayoutVersusImpacto(unittest.TestCase):
    def setUp(self):
        self.blob, self.marks = build_fixture()
        self.main = scx_label_address(self.blob, 0)
        self.main_end = scx_label_address(self.blob, 1)

    def test_reference_decoder_reads_main_label(self):
        names = run_decoder(decode_sghd, self.blob, self.main, self.main_end)
        self.assertEqual(names, [
            "Assign", "SetFlag", "Call", "JumpIf", "CallIfFlag", "CallFar",
            "GroupCheckpoint", "Nop", "Jump", "EndOfScript"])

    def test_call_return_id_resolves_to_next_instruction(self):
        name, (label, ret), nxt = decode_sghd(
            self.blob, self.main + self.marks["call_at"])
        self.assertEqual((name, label), ("Call", 1))
        self.assertEqual(scx_return_address(self.blob, ret), nxt)

    def test_impacto_without_return_ids_desyncs_after_call(self):
        # Current profiles/sgps3/game.lua sets UseReturnIds = false, so
        # InstCall leaves the u16 return id in the stream.  The next
        # "instruction" impacto decodes is the return id bytes (00 00 ->
        # InstEnd), i.e. the main thread terminates right after the first
        # Call.
        pos = self.main + self.marks["call_at"]
        handler, nxt = decode_impacto_sgps3(self.blob, pos, False)
        self.assertEqual(handler, "InstCall")
        self.assertEqual(nxt, pos + 4)
        self.assertEqual(self.blob[nxt:nxt + 2], b"\x00\x00")
        self.assertNotEqual(nxt, self.main + self.marks["after_call"])
        self.assertEqual(decode_impacto_sgps3(self.blob, nxt, False)[0],
                         "InstEnd")

    def test_impacto_with_return_ids_matches_reference_until_first_gap(self):
        names = run_decoder(decode_impacto_sgps3, self.blob, self.main,
                            self.main_end, use_return_ids=True)
        # Aligned through Call and JumpIf; 00 54 is decoded by InstUnk0054
        # (two expressions) instead of CallIfFlag (byte, expr, label, ret):
        # byte 0x01 (condition) and the flag immediate are read as the first
        # expression, then the label/return-id bytes become the "second
        # expression" and the stream is lost.
        self.assertEqual(names[:4], ["ExpressionEval", "InstSetFlag",
                                     "InstCall", "InstIf"])
        self.assertEqual(names[4], "InstUnk0054")
        # The byte after the mis-decoded CallIfFlag is not an instruction
        # boundary: impacto reports an unknown opcode group and "recovers".
        self.assertTrue(names[5].startswith("ThreadCrash("), names)

    def test_dummy_slots_never_advance(self):
        guarded = scx_label_address(self.blob, 2)
        handler, nxt = decode_impacto_sgps3(self.blob, guarded, True)
        self.assertEqual(handler, HANG)
        self.assertEqual(nxt, guarded)
        # and the real reference instruction there is ReturnIfFlag
        self.assertEqual(decode_sghd(self.blob, guarded)[0], "ReturnIfFlag")


class SghdAllAffectedOpcodesFixture(unittest.TestCase):
    """Thread 04 Task 2: one script exercising all 37 opcodes Thread 03
    found broken.  The same blob is run through the real VM by
    test_runtime_probe.SghdTask2RuntimeProbe, which compares impacto's
    executed addresses with sghd_reference_trace()."""

    def setUp(self):
        self.blob = sghd_task2_fixture()
        self.gaps = __import__("json").loads(
            (REPO / "tests" / "compat" / "fixtures" /
             "sgps3_known_gaps.json").read_text())

    def decoded_main(self):
        pos = scx_label_address(self.blob, 0)
        end = scx_label_address(self.blob, 1)
        out = []
        while pos < end:
            name, args, nxt = decode_sghd(self.blob, pos)
            out.append((pos, name, args))
            pos = nxt
        self.assertEqual(pos, end, "decoder must land exactly on label 1")
        return out

    def test_reference_decoder_walks_main_label_to_end(self):
        decoded = self.decoded_main()
        self.assertEqual(decoded[-1][1], "EndOfScript")

    def test_fixture_contains_all_37_affected_opcodes(self):
        documented = (set(self.gaps["dummy_slots_used_by_sghd"])
                      | set(self.gaps["argument_layout_mismatches"]))
        seen = set()
        for label in range(3):
            pos = scx_label_address(self.blob, label)
            end = scx_label_address(self.blob, label + 1)
            while pos < end:
                if self.blob[pos] != 0xFE:
                    seen.add(f"{self.blob[pos]:02X} {self.blob[pos + 1]:02X}")
                pos = decode_sghd(self.blob, pos)[2]
        self.assertEqual(documented - seen, set())

    def test_every_affected_opcode_has_a_reference_layout(self):
        documented = (set(self.gaps["dummy_slots_used_by_sghd"])
                      | set(self.gaps["argument_layout_mismatches"]))
        have = {f"{g:02X} {o:02X}" for g, o in SGHD_LAYOUTS}
        self.assertEqual(documented - have, set())

    def test_reference_trace_takes_both_conditional_calls_and_returns(self):
        trace = sghd_reference_trace(self.blob)
        ops = [op for _, op in trace]
        self.assertEqual(ops[-1], "00:00")
        # CallIfFlag taken -> Return; CallFarIfFlag taken -> ReturnIfFlag
        self.assertEqual(ops[1:3], ["00:54", "00:0e"])
        self.assertEqual(ops[4:6], ["00:56", "00:57"])
        main_end = scx_label_address(self.blob, 1)
        self.assertLess(trace[-1][0], main_end, "ends in the main label")


class ImpactoDummyHandlerAudit(unittest.TestCase):
    """Source-level evidence for the hang described in the blockers doc."""

    def test_inst_dummy_has_no_start_instruction(self):
        text = (REPO / "src" / "vm" / "inst_system.cpp").read_text()
        start = text.index("VmInstruction(InstDummy)")
        body = text[start:text.index("}", start)]
        self.assertNotIn("StartInstruction", body)
        self.assertNotIn("IpOffset", body)

    def test_run_thread_loops_until_blocked(self):
        text = (REPO / "src" / "vm" / "vm.cpp").read_text()
        self.assertIn("} while (!BlockCurrentScriptThread);", text)


if __name__ == "__main__":
    unittest.main()
