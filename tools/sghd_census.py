#!/usr/bin/env python3
"""Second-round STEINS;GATE (Steam) evidence: script, asset and executable census.

Run on the machine with the legally owned Steam installation (Windows,
Python 3.9+, no third-party packages), from a checkout of this repository:

    python tools\\sghd_census.py "C:\\Program Files (x86)\\Steam\\steamapps\\common\\STEINS;GATE" > sghd-census.txt

Sections (each can be selected with --scripts / --assets / --exe):

* scripts: decodes every SCX in USRDIR/script.mpk with the complete SGHD
  instruction layout table below and reports decode integrity (any desync
  means a layout in this table, and probably in impacto, is wrong), opcode
  counts, every use of the opcodes impacto only stubs, every phone/mail
  instruction (10 37 / 10 38) with its numeric arguments and the
  surrounding instructions, movie instructions (playNo arguments), and the
  ScrWork/FlagWork index ranges the scripts touch (save ranges).
  Since Thread 06 (v2): padding/data after an unconditional end of flow and
  undecodable label entries are reported separately from real decode errors,
  real errors come with the preceding instructions and a hex window, and
  text-style data (01 0E) is dumped.
* assets: image headers (PNG size/colour type, DDS size/format/mipmaps) of
  every system.mpk entry and the first chara.mpk images; per-glyph ink
  extents of FONT*.PNG; LAY header plausibility (byte order) of the first
  chara.mpk .lay entry.
* exe: offsets of the movie base names inside Game.exe, in file order (the
  movie id -> file mapping lives in the executable).
* context (Thread 08, only when asked for): every use of the given opcodes
  with the 6 preceding and 16 following decoded instructions, e.g. the title
  menu protocol around 10 34:

    python tools\\sghd_census.py "<STEINS;GATE folder>" --context=10:34,00:44 > sghd-context.txt

  "--context" alone means 10:34,00:44,00:53.

Only opcode names, numbers, sizes and offsets are printed. Dialogue text is
never decoded: string arguments are printed as string-table indices only.
Review the report before sharing it privately; do not publish it.

The layout table is hand-derived from the SGHD decoder tables of
CommitteeOfZero/sc3ntist (opcode names as in tests/compat/fixtures/
sghd_opcodes.json); no sc3ntist code is included.
"""

from __future__ import annotations

import re
import struct
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

# --------------------------------------------------------------------------
# SGHD instruction layouts
#
# Tokens: B byte, H u16, E expression, L local label (u16), R return-address
# id (u16), S string-table index (u16). Typed entries are
# (name, tokens before the type byte, {type: tokens, "*": default}); a type
# missing from the dict (and no "*") is an unrecognized instruction.
# --------------------------------------------------------------------------

LAYOUTS = {
    (0x00, 0x00): ("EndOfScript", ""),
    (0x00, 0x01): ("CreateThread", "E E L"),
    (0x00, 0x02): ("TerminateThread", "E"),
    (0x00, 0x03): ("ExitThread", ""),
    (0x00, 0x04): ("LoadScript", "E E"),
    (0x00, 0x05): ("Sleep", "E"),
    (0x00, 0x06): ("Halt", ""),
    (0x00, 0x07): ("Jump", "L"),
    (0x00, 0x08): ("JumpTable", "E L"),
    (0x00, 0x0A): ("JumpIf", "B E L"),
    (0x00, 0x0B): ("Call", "L R"),
    (0x00, 0x0C): ("JumpFar", "E L"),
    (0x00, 0x0D): ("CallFar", "E L R"),
    (0x00, 0x0E): ("Return", ""),
    (0x00, 0x0F): ("LoopTimes", "L E"),
    (0x00, 0x10): ("JumpIfFlag", "B E L"),
    (0x00, 0x11): ("WaitForFlag", "B E"),
    (0x00, 0x12): ("SetFlag", "E"),
    (0x00, 0x13): ("ResetFlag", "E"),
    (0x00, 0x14): ("CopyFlag", "E E"),
    (0x00, 0x15): ("UnkJump0015", "B E E L"),
    (0x00, 0x18): ("SetThreadVar", "E E"),
    (0x00, 0x19): ("Unk0019", "E E"),
    (0x00, 0x1A): ("Thread001A", ""),
    (0x00, 0x1B): ("Unk001B", "E H"),
    (0x00, 0x1D): ("LongAssign", "E"),
    (0x00, 0x1F): ("SetSwitch", "E"),
    (0x00, 0x20): ("JumpSwitchCase", "E L"),
    (0x00, 0x21): ("PlayBgm", "", {2: "E E", "*": "E"}),
    (0x00, 0x22): ("StopBgm", "B"),
    (0x00, 0x23): ("PlaySoundEffect", "B", {2: "", "*": "E E"}),
    (0x00, 0x24): ("StopSoundEffect", "B"),
    (0x00, 0x25): ("SetVibration", "E E E"),
    (0x00, 0x26): ("Unk0026", "E"),
    (0x00, 0x28): ("Unk0028", "E E E E"),
    (0x00, 0x29): ("Useless_0029", "B"),
    (0x00, 0x2A): ("Unk002A", "B"),
    (0x00, 0x2B): ("LongAssign", "E"),
    (0x00, 0x2C): ("Unk002C", "E"),
    (0x00, 0x2D): ("Nop3", "B"),
    (0x00, 0x2E): ("SetRichPresence", "B E"),
    (0x00, 0x2F): ("Unk002F", "", {1: "E", "*": ""}),
    (0x00, 0x30): ("Unk0030", "B"),
    (0x00, 0x31): ("Unk0031", "E"),
    (0x00, 0x32): ("ResetSomething0032", ""),
    (0x00, 0x33): ("Wait", "E E"),
    (0x00, 0x34): ("Unk0034", ""),
    (0x00, 0x35): ("Unk0035", "B"),
    (0x00, 0x36): ("Nop3", "B"),
    (0x00, 0x37): ("PlayVoice", "B E E"),
    (0x00, 0x38): ("StopVoice", "B E"),
    (0x00, 0x3A): ("Group003A", "", {0: "E E", 1: "", 2: "E", 3: "E"}),
    (0x00, 0x3B): ("Audio003B", "B"),
    (0x00, 0x3D): ("EvalTwo", "E E"),
    (0x00, 0x3E): ("ResetAudioState", ""),
    (0x00, 0x3F): ("Unk003F", ""),
    (0x00, 0x40): ("Nop", ""),
    (0x00, 0x41): ("Nop3", "B"),
    (0x00, 0x42): ("Unk0042", "E"),
    (0x00, 0x43): ("Unk0043", "", {0x0A: "", 0x0B: "", 0x0F: "", 0x10: "",
                                   0x11: "", 0x0C: "E", 0x0D: "S", 0x0E: "S",
                                   0: "", 1: "", 5: "", 6: "", 7: "",
                                   3: "H", 4: "H", 2: "E"}),
    (0x00, 0x44): ("Unk0044", "B"),
    (0x00, 0x46): ("Unk0046", "E"),
    (0x00, 0x49): ("Nop3", "B"),
    (0x00, 0x4A): ("DebugCtrl", "B"),
    (0x00, 0x4B): ("WaitForSomething004B", ""),
    (0x00, 0x4C): ("Unk004C", "", {0: "E", "*": ""}),
    (0x00, 0x4F): ("LongAssign", "E"),
    (0x00, 0x50): ("UselessJump", "", {0: "L L", 2: "L L", 3: "L L L",
                                       "*": ""}),
    (0x00, 0x51): ("Group0051", "", {0: "E", 1: "", 2: "", 3: ""}),
    (0x00, 0x52): ("Nop", ""),
    (0x00, 0x53): ("Useless0053", "B E L"),
    (0x00, 0x54): ("CallIfFlag", "B E L R"),
    (0x00, 0x56): ("CallFarIfFlag", "B E E L R"),
    (0x00, 0x57): ("ReturnIfFlag", "B E"),
    (0x00, 0x58): ("Unk0058", "", {2: "E E E E L", 3: "E E E E L",
                                   "*": "E L"}),
    (0x00, 0x59): ("Unk0059", "B E E L"),
    (0x00, 0x5F): ("Nop", ""),
    (0x01, 0x00): ("CreateSurface", "B E E E"),
    (0x01, 0x01): ("ReleaseSurface", "E"),
    (0x01, 0x02): ("LoadTexture", "E E E"),
    (0x01, 0x03): ("ReleaseSurface", "E"),
    (0x01, 0x04): ("Unk0104", "E E E E E"),
    (0x01, 0x05): ("GroupCalc", "", {0: "E E", 1: "E E", 2: "E E E",
                                     3: "E E E E", 4: "E E E E",
                                     5: "E E E E", 6: "E E E E"}),
    (0x01, 0x06): ("Unk0106", "", {0: "E E", 1: "E E E"}),
    (0x01, 0x07): ("Unk0107", "E E E"),
    (0x01, 0x08): ("Unk0108", "B"),
    (0x01, 0x09): ("GroupCheckpoint", "", {0: "H", 1: "H E", 2: "E",
                                           "*": ""}),
    (0x01, 0x0A): ("Unk010A", "B"),
    (0x01, 0x0B): ("ClearDialogueBox", ""),
    (0x01, 0x0C): ("GroupLoadDialogue", "", {0: "E S", 1: "E E S",
                                             3: "E E E S", 0x0B: "E E E S"}),
    (0x01, 0x0D): ("GroupDisplayDialogue", "", {0: ""}),
    (0x01, 0x0E): ("InstantiateTextStyle", "E L"),
    (0x01, 0x0F): ("SetNGmoji", "S S"),
    (0x01, 0x10): ("Unk0110", "B"),
    (0x01, 0x11): ("GroupDialogueBox", "", {5: "E", 6: "E", 7: "E", "*": ""}),
    (0x01, 0x12): ("Unk0112", "", {0: "S E", 2: "S E", "*": "S"}),
    (0x01, 0x13): ("Unk0113", "", {2: "E", "*": ""}),
    (0x01, 0x14): ("Unk0114", "", {0: "", 1: "", "*": "S"}),
    (0x01, 0x20): ("Unk0120", "E"),
    (0x01, 0x21): ("InstantiateStringArray", "E L"),
    (0x01, 0x22): ("ActualLoadCutscene", "", {99: "E E E E", "*": "B E E"}),
    (0x01, 0x23): ("GroupCutscene", "", {"*": ""}),
    (0x01, 0x24): ("LoadCutscene", "E"),
    (0x01, 0x25): ("Group0125", "", {0: "S", 1: "E E S", 2: "S",
                                     3: "S E E E", "*": ""}),
    (0x01, 0x26): ("PlayCutscene", "", {99: "E E E", "*": "B E"}),
    (0x01, 0x27): ("ActualLoadCutscene", "", {99: "E E E E", "*": "B E E"}),
    (0x01, 0x28): ("GroupCutscene", "", {"*": ""}),
    (0x01, 0x29): ("LoadCutscene", "E"),
    (0x01, 0x2A): ("PlayCutscene", "", {99: "E E E", "*": "B E"}),
    (0x01, 0x2B): ("SetCutscenePaused", "B"),
    (0x10, 0x00): ("InitSubsystem", "E"),
    (0x10, 0x01): ("LoadBackground", "E E"),
    (0x10, 0x02): ("SwapBackgrounds", "E E"),
    (0x10, 0x04): ("UnkBglink1004", "", {0: "E E E", 1: "E E E", 2: "E E E",
                                         3: "E E E", "*": "E E E E"}),
    (0x10, 0x05): ("LoadCharacter", "", {0: "E E H", "*": "E E"}),
    (0x10, 0x06): ("Unk1006", "E E"),
    (0x10, 0x07): ("CopyBackground", "E E"),
    (0x10, 0x09): ("EvalTwo", "E E"),
    (0x10, 0x0A): ("Nop", ""),
    (0x10, 0x0B): ("Nop", ""),
    (0x10, 0x0C): ("Nop3", "B"),
    (0x10, 0x0E): ("EvalTwo", "E E"),
    (0x10, 0x10): ("HideBackgroundMaybe", "E"),
    (0x10, 0x11): ("HideCharacterMaybe", "E"),
    (0x10, 0x12): ("Nop", ""),
    (0x10, 0x13): ("Unk1013", "B"),
    (0x10, 0x14): ("SaveResetRelated1014", "B"),
    (0x10, 0x15): ("Nop3", "B"),
    (0x10, 0x1A): ("Unk101A", "B"),
    (0x10, 0x1B): ("Nop3", "B"),
    (0x10, 0x1C): ("Nop3", "B"),
    (0x10, 0x1D): ("Unk101D", "B"),
    (0x10, 0x1E): ("Unk101E", ""),
    (0x10, 0x1F): ("Unk101F", "B"),
    (0x10, 0x20): ("Unk1020", "B"),
    (0x10, 0x21): ("Unk1021", "B"),
    (0x10, 0x22): ("Group1022", "", {0: "", 1: "", 2: "", 3: "", 5: "",
                                     0x0A: "H", 0x14: "", 0x15: "",
                                     0xFF: ""}),
    (0x10, 0x23): ("Unk1023", "", {0: "B", 0x0A: "B", "*": ""}),
    (0x10, 0x24): ("Unk1024", "", {0: "E E", "*": ""}),
    (0x10, 0x27): ("Unk1027", "", {1: "E E", "*": "E"}),
    (0x10, 0x28): ("Unk1028", "E"),
    (0x10, 0x29): ("SetEnvFlag", "E"),
    (0x10, 0x2A): ("Unk102A", "B E E E"),
    (0x10, 0x2D): ("Nop", ""),
    (0x10, 0x2F): ("Nop", ""),
    (0x10, 0x30): ("Group1030", "", {0: "", 1: "E E E E E", 2: "",
                                     3: "E E E E E", 4: "E E E E E E",
                                     5: "E E E E E E", 0x0A: "",
                                     0x0B: "E E E E E", 0x0C: "E E E E E E"}),
    (0x10, 0x33): ("GroupTips", "", {0: "L L", 1: "", 2: "", 3: "", 4: ""}),
    (0x10, 0x34): ("Unk1034", "B"),
    (0x10, 0x36): ("Nop3", "B"),
    (0x10, 0x37): ("Group1037", "", {0: "B E", 1: "B E", 2: "B E L",
                                     3: "B E L", 4: "L L L L L L", 5: "",
                                     6: "", 7: "", 8: "", 9: "", 0x0A: "",
                                     0x0F: "E", 0x10: "E", 0x11: "",
                                     0x12: "E E", 0x13: "", 0x14: "E E E E",
                                     0x15: "E E E E", 0x16: "", 0x17: "",
                                     0x18: "", 0x19: "", 0x1A: "E", 0x1E: ""}),
    (0x10, 0x38): ("Group1038", "", {0: "L", "*": ""}),
    (0x10, 0x3F): ("Unk103F", "B"),
    (0x10, 0x40): ("Win32_SetResolution", ""),
    (0x10, 0x41): ("Win32_DestroyWindow", ""),
}

# Slots the Steam scripts use that the sc3ntist table above lacks (Thread 06,
# first census: labels starting with these opcodes were undecodable).
# Layouts follow impacto's handlers for the same slots (CHAmove, SetSceneView
# Flag); 10 3A takes six expressions: census v2 showed its only use followed
# by TV[63]..TV[67] and the immediate 128, then a valid Sleep (impacto's
# sgps3-era handler read a type byte instead).
EXTRA_LAYOUTS = {
    (0x10, 0x0D): ("CHAmove", "", {0: "", 1: "E L", 2: "E", 3: "", 4: "E E",
                                   5: "E E E E E E E"}),
    (0x10, 0x2E): ("SetSceneViewFlag", "E"),
    (0x10, 0x3A): ("Unk103A", "E E E E E E"),
}
ALL_LAYOUTS = {**LAYOUTS, **EXTRA_LAYOUTS}
# unconditional end of control flow: bytes after one of these and before the
# next label are unreachable (alignment padding or data), not code
TERMINATORS = {(0x00, 0x00), (0x00, 0x07), (0x00, 0x08), (0x00, 0x0C),
               (0x00, 0x0E)}

# opcodes impacto parses but only stubs for SGHD (docs/handoff.md)
IMPACTO_STUBS = {
    (0x00, 0x35), (0x00, 0x41), (0x00, 0x43), (0x00, 0x4B), (0x00, 0x4C),
    (0x00, 0x50), (0x00, 0x53), (0x00, 0x58), (0x00, 0x59), (0x01, 0x06),
    (0x01, 0x07), (0x01, 0x08), (0x01, 0x09), (0x01, 0x0A), (0x10, 0x1A),
    (0x10, 0x27), (0x10, 0x37), (0x10, 0x3F),
}
PHONE = {(0x10, 0x37), (0x10, 0x38)}
MOVIE = {(0x01, 0x22), (0x01, 0x23), (0x01, 0x24), (0x01, 0x26),
         (0x01, 0x27), (0x01, 0x28), (0x01, 0x29), (0x01, 0x2A),
         (0x01, 0x2B)}
# instructions whose label argument points at data, not code
DATA_LABEL_OPS = {(0x00, 0x08), (0x00, 0x20), (0x01, 0x0E), (0x01, 0x21),
                  (0x10, 0x0D),   # CHAmove type 1: sequence data
                  (0x10, 0x38)}   # type 0: u16 table (_ATCH.SCX)


def data_label_refs(slot, args) -> list[int]:
    """Labels an instruction names as data rather than as a jump target."""
    if slot in DATA_LABEL_OPS:
        return [v for k, v in args if k == "L"]
    if slot == (0x10, 0x37) and ("T", 4) in args:  # six table labels (_MAIL.SCX)
        return [v for k, v in args if k == "L"]
    return []

EXPR_OPS = {
    0x01: "*", 0x02: "/", 0x03: "+", 0x04: "-", 0x05: "%", 0x06: "<<",
    0x07: ">>", 0x08: "&", 0x09: "^", 0x0A: "|", 0x0B: "neg", 0x0C: "==",
    0x0D: "!=", 0x0E: "<=", 0x0F: ">=", 0x10: "<", 0x11: ">", 0x14: "=",
    0x15: "*=", 0x16: "/=", 0x17: "+=", 0x18: "-=", 0x19: "%=", 0x1A: "<<=",
    0x1B: ">>=", 0x1C: "&=", 0x1D: "|=", 0x1E: "^=", 0x20: "++", 0x21: "--",
    0x28: "W", 0x29: "F", 0x2A: "D", 0x2B: "LT", 0x2C: "FLT", 0x2D: "TV",
    0x2E: "DMA", 0x2F: "f2F", 0x30: "f30", 0x31: "f31", 0x32: "f32",
    0x33: "rand",
}


class DecodeError(Exception):
    pass


def read_immediate(code: bytes, pos: int) -> tuple[int, int]:
    """Immediate token incl. its precedence byte (impacto ExpressionParser)."""
    b0 = code[pos]
    cls = b0 & 0x60
    if cls == 0x00:
        value = b0 & 0x1F
        if b0 & 0x10:
            value |= ~0x1F
        pos += 1
    elif cls == 0x20:
        value = ((b0 & 0x1F) << 8) | code[pos + 1]
        if b0 & 0x10:
            value |= ~0x1FFF
        pos += 2
    elif cls == 0x40:
        value = ((b0 & 0x1F) << 16) | (code[pos + 2] << 8) | code[pos + 1]
        if b0 & 0x10:
            value |= ~0x1FFFFF
        pos += 3
    else:
        value = struct.unpack_from("<i", code, pos + 1)[0]
        pos += 5
    return value, pos + 1


def read_expression(code: bytes, pos: int) -> tuple[list, int]:
    """Token list (ints for immediates, op names otherwise) and new pos."""
    toks: list = []
    while True:
        if pos >= len(code):
            raise DecodeError("expression runs past the end")
        b = code[pos]
        if b == 0x00:
            return toks, pos + 1
        if b & 0x80:
            value, pos = read_immediate(code, pos)
            toks.append(value)
        else:
            if b not in EXPR_OPS:
                raise DecodeError(f"unknown expression token {b:#04x}")
            toks.append(EXPR_OPS[b])
            pos += 2
        if len(toks) > 64:
            raise DecodeError("expression too long")


def fmt_expr(toks: list) -> str:
    return "(" + " ".join(str(t) for t in toks) + ")"


def decode(code: bytes, pos: int):
    """Return (slot, name, args, next_pos); args are (kind, value) pairs."""
    if pos + 2 > len(code):
        raise DecodeError("truncated instruction")
    if code[pos] == 0xFE:
        toks, p = read_expression(code, pos + 1)
        return (0xFE, 0), "Assign", [("E", toks)], p
    slot = (code[pos], code[pos + 1])
    entry = ALL_LAYOUTS.get(slot)
    if entry is None:
        raise DecodeError(f"unrecognized opcode {slot[0]:02X} {slot[1]:02X}")
    p = pos + 2
    name, pre = entry[0], entry[1]
    layout = pre
    args = []

    def take(tokens: str):
        nonlocal p
        for t in tokens.split():
            if t == "B":
                args.append(("B", code[p]))
                p += 1
            elif t == "E":
                toks, p = read_expression(code, p)
                args.append(("E", toks))
            else:
                args.append((t, struct.unpack_from("<H", code, p)[0]))
                p += 2

    take(layout)
    if len(entry) == 3:
        kind = code[p]
        p += 1
        args.append(("T", kind))
        cases = entry[2]
        if kind in cases:
            take(cases[kind])
        elif "*" in cases:
            take(cases["*"])
        else:
            raise DecodeError(f"{name}: unrecognized type {kind:#04x}")
    return slot, name, args, p


def fmt_args(args) -> str:
    out = []
    for kind, value in args:
        if kind == "E":
            out.append(fmt_expr(value))
        elif kind == "T":
            out.append(f"type={value:#04x}")
        elif kind == "S":
            out.append(f"str#{value}")
        elif kind == "L":
            out.append(f"label{value}")
        elif kind == "R":
            out.append(f"ret{value}")
        else:
            out.append(str(value))
    return " ".join(out)


def slot_text(slot) -> str:
    return "FE" if slot[0] == 0xFE else f"{slot[0]:02X} {slot[1]:02X}"


# --------------------------------------------------------------------------
# containers
# --------------------------------------------------------------------------

def mpk_entries(path: Path):
    """[(id, name, offset, size)] of an uncompressed-or-not MPK v2 archive."""
    with path.open("rb") as f:
        header = f.read(0x40)
        if header[:4] != b"MPK\0":
            raise ValueError(f"{path} is not an MPK archive")
        count = struct.unpack_from("<I", header, 8)[0]
        out = []
        for _ in range(count):
            raw = f.read(0x100)
            comp, file_id, offset, csize, size = struct.unpack_from("<IIQQQ", raw)
            name = raw[32:].split(b"\0", 1)[0].decode("ascii", "replace")
            out.append((file_id, name, offset, csize, size, comp))
    return out


def mpk_read(path: Path, entry) -> bytes:
    file_id, name, offset, csize, size, comp = entry
    with path.open("rb") as f:
        f.seek(offset)
        data = f.read(csize)
    if comp:
        data = zlib.decompress(data)
    return data


def scx_labels(blob: bytes) -> tuple[list[int], int]:
    if blob[:4] != b"SC3\0":
        raise DecodeError("not an SC3 script")
    string_table = struct.unpack_from("<I", blob, 4)[0]
    first = struct.unpack_from("<I", blob, 12)[0]
    count = (first - 12) // 4
    labels = list(struct.unpack_from(f"<{count}I", blob, 12))
    return labels, string_table


# --------------------------------------------------------------------------
# scripts
# --------------------------------------------------------------------------

def hex_context(blob: bytes, pos: int, before: int = 16, after: int = 32) -> str:
    start = max(0, pos - before)
    return (f"{start:#x}: {blob[start:pos].hex(' ')} | "
            f"{blob[pos:pos + after].hex(' ')}")


def walk_script(blob: bytes):
    """Decode every code label; returns (instructions, errors, data labels,
    notes).

    instructions: [(label, addr, slot, name, args)] in address order.
    errors: [(label, addr, message, first bytes, context lines)] -- decode
    failures inside reachable code, i.e. evidence of a wrong layout.
    notes: [(kind, label, addr, message, first bytes)] -- failures that are
    not layout evidence: "after-end" (bytes after an unconditional end of
    flow: padding or data), "padding" (zero bytes before the string table),
    "entry" (the label's first instruction is undecodable: a data label or an
    opcode missing from the table).
    Labels referenced as data (jump tables, text styles, string arrays,
    LT label-table expressions) are skipped in a second pass."""
    labels, code_end = scx_labels(blob)

    def run(skip: set[int]):
        insts, errors, notes, data_labels = [], [], [], set()
        starts = {}  # address -> first label id (labels may share addresses)
        for label_id, addr in enumerate(labels):
            if label_id not in skip and addr < code_end:
                starts.setdefault(addr, label_id)
        bounds = sorted(set(labels) | {code_end})
        for addr, label_id in sorted(starts.items()):
            end = min(b for b in bounds if b > addr)
            pos, trail = addr, []

            def fail(at: int, msg: str):
                head = blob[at:at + 8].hex(" ")
                if trail and trail[-1][2] in TERMINATORS:
                    notes.append(("after-end", label_id, at, msg, head))
                elif end == code_end and end - at < 4 and not any(blob[at:end]):
                    notes.append(("padding", label_id, at, msg, head))
                elif at == addr:
                    notes.append(("entry", label_id, at, msg, head))
                else:
                    ctx = [f"      < @{p:#x} {slot_text(s)} {n} {fmt_args(a)}"
                           for _, p, s, n, a in trail[-4:]]
                    ctx.append("      bytes " + hex_context(blob, at))
                    errors.append((label_id, at, msg, head, ctx))

            while pos < end:
                try:
                    slot, name, args, nxt = decode(blob, pos)
                except (DecodeError, IndexError, struct.error) as e:
                    fail(pos, str(e))
                    break
                if nxt > end:
                    fail(pos, f"{slot_text(slot)} {name} overran next label "
                              f"(@{end:#x}) by {nxt - end} bytes")
                    break
                inst = (label_id, pos, slot, name, args)
                insts.append(inst)
                trail.append(inst)
                data_labels.update(data_label_refs(slot, args))
                for kind, value in args:
                    if kind == "E":
                        data_labels.update(
                            value[i + 1] for i, tok in enumerate(value[:-1])
                            if tok == "LT" and isinstance(value[i + 1], int))
                pos = nxt
        return insts, errors, notes, data_labels

    insts, errors, notes, data_labels = run(set())
    if data_labels:
        insts, errors, notes, _ = run(data_labels)
    return insts, errors, data_labels, notes


# expression arguments that name a flag directly (sc3ntist ExprFlagRef), by
# position among the instruction's expression arguments
FLAG_ARGS = {(0x00, 0x10): (0,), (0x00, 0x11): (0,), (0x00, 0x12): (0,),
             (0x00, 0x13): (0,), (0x00, 0x14): (0, 1), (0x00, 0x54): (0,),
             (0x00, 0x56): (0,), (0x00, 0x57): (0,)}


def var_refs(slot, args, counters):
    exprs = [value for kind, value in args if kind == "E"]
    for i in FLAG_ARGS.get(slot, ()):
        if i < len(exprs) and len(exprs[i]) == 1 and isinstance(exprs[i][0], int):
            counters["F"][exprs[i][0] // 100 * 100] += 1
    for value in exprs:
        for i, tok in enumerate(value[:-1]):
            if tok in ("W", "F") and isinstance(value[i + 1], int):
                counters[tok][value[i + 1] // 100 * 100] += 1


def scripts_report(root: Path) -> list[str]:
    path = root / "USRDIR" / "script.mpk"
    out = ["## Scripts (USRDIR/script.mpk)"]
    if not path.exists():
        return out + ["  script.mpk not found"]
    ops = Counter()
    stubs = defaultdict(Counter)
    phone_kinds = Counter()
    phone_lines, movie_lines, error_lines, style_lines = [], [], [], []
    refs = {"W": Counter(), "F": Counter()}
    per_file, entry_lines = [], []
    note_counts = Counter()
    for entry in mpk_entries(path):
        file_id, name = entry[0], entry[1]
        if not name.upper().endswith(".SCX"):
            continue
        blob = mpk_read(path, entry)
        try:
            insts, errors, data_labels, notes = walk_script(blob)
        except DecodeError as e:
            per_file.append(f"  id {file_id:3d} {name:16s} not decodable: {e}")
            continue
        per_file.append(f"  id {file_id:3d} {name:16s} labels {len(scx_labels(blob)[0]):4d}"
                        f"  data-labels {len(data_labels):3d}  instructions {len(insts):6d}"
                        f"  errors {len(errors)}  notes {len(notes)}")
        for label_id, pos, msg, head, ctx in errors:
            error_lines.append(f"  {name} label{label_id} @{pos:#x}: {msg}  [{head}]")
            error_lines.extend(ctx)
        for kind, label_id, pos, msg, head in notes:
            note_counts[kind] += 1
            if kind == "entry":
                entry_lines.append(f"  {name} label{label_id} @{pos:#x}: {msg}  [{head}]")
        for i, (label_id, pos, slot, iname, args) in enumerate(insts):
            ops[(slot, iname)] += 1
            var_refs(slot, args, refs)
            where = f"{name} label{label_id} @{pos:#x}"
            if slot in IMPACTO_STUBS:
                key = tuple(v for k, v in args if k in ("B", "T"))
                stubs[(slot, iname)][key] += 1
            if slot == (0x01, 0x0E):  # InstantiateTextStyle E L -> 24 x u16
                label = next(v for k, v in args if k == "L")
                addr = scx_labels(blob)[0][label]
                vals = struct.unpack_from("<24h", blob, addr)
                style_lines.append(f"  {where}: id {fmt_args(args[:1])} "
                                   + " ".join(str(v) for v in vals))
            if slot in MOVIE:
                movie_lines.append(f"  {where}: {slot_text(slot)} {iname} {fmt_args(args)}")
            if slot in PHONE:
                kind = next((v for k, v in args if k == "T"), None)
                phone_kinds[(slot, kind)] += 1
                phone_lines.append(f"  {where}: {slot_text(slot)} {iname} {fmt_args(args)}")
                for j in range(max(0, i - 3), min(len(insts), i + 4)):
                    if j == i:
                        continue
                    _, p2, s2, n2, a2 = insts[j]
                    mark = "<" if j < i else ">"
                    phone_lines.append(f"      {mark} @{p2:#x} {slot_text(s2)} {n2} {fmt_args(a2)}")
    out += ["### Per file"] + per_file
    out += ["### Decode errors in reachable code (should be empty; each is layout evidence)"]
    out += error_lines or ["  none"]
    out += ["### Non-code after an unconditional end of flow / string-table padding (count)"]
    out += [f"  {k}: {note_counts[k]}" for k in ("after-end", "padding")]
    out += ["### Labels whose first instruction is undecodable (data or unknown opcode)"]
    out += entry_lines or ["  none"]
    out += ["### Opcode counts"]
    out += [f"  {slot_text(s)} {n:24s} {c}" for (s, n), c in sorted(ops.items())]
    out += ["### Opcodes impacto only stubs (count per byte/type argument tuple)"]
    for (s, n), cnt in sorted(stubs.items()):
        detail = ", ".join(f"{k}x{c}" for k, c in sorted(cnt.items()))
        out.append(f"  {slot_text(s)} {n}: {sum(cnt.values())}  [{detail}]")
    out += ["### Phone/mail subtype counts"]
    out += [f"  {slot_text(s)} type={k:#04x}: {c}" for (s, k), c in sorted(phone_kinds.items())]
    out += ["### Phone/mail instructions with context (< before, > after)"] + phone_lines
    out += ["### Movie instructions"] + (movie_lines or ["  none"])
    out += ["### Text styles (01 0E data: DisplayMode WindowId WindowPosX/Y "
            "NameDispMode MaxNameWidth NamePosX/Y NameGlyphW/H MaxLineWidth "
            "WaitIconDispMode WaitIconPosX/Y TextGlyphW/H RubyGlyphW/H "
            "LineSpacing RubyLineSpacing RubyDispMode LinefeedSpacing "
            "NamePosFlags NameLengthL)"]
    out += style_lines or ["  none"]
    for kind, label in (("W", "ScrWork"), ("F", "FlagWork")):
        out.append(f"### {label} indices referenced by immediates (per 100: count)")
        out.append("  " + " ".join(f"{k}:{v}" for k, v in sorted(refs[kind].items())))
    return out


# --------------------------------------------------------------------------
# assets
# --------------------------------------------------------------------------

def png_info(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    w, h, depth, ctype = struct.unpack_from(">IIBB", data, 16)
    return w, h, depth, ctype


def png_alpha(data: bytes):
    """(width, height, rows of coverage values 0-255); 8-bit PNGs only."""
    w, h, depth, ctype = png_info(data)
    if depth != 8 or data[28] != 0 or ctype not in (0, 2, 3, 4, 6):
        raise ValueError(f"unsupported PNG (depth {depth}, type {ctype}, interlace {data[28]})")
    pos, idat, trns = 8, bytearray(), b""
    while pos < len(data):
        length, tag = struct.unpack_from(">I4s", data, pos)
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IDAT":
            idat += body
        elif tag == b"tRNS":
            trns = body
        pos += 12 + length
    raw = zlib.decompress(bytes(idat))
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    for y in range(h):
        ftype = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        prev = line
        if ctype in (4, 6):
            rows.append(line[bpp - 1::bpp])
        elif ctype == 3 and trns:
            rows.append(bytes(trns[i] if i < len(trns) else 255 for i in line))
        else:
            rows.append(line[0::bpp])  # luminance / red as coverage
    return w, h, rows


def font_ink(data: bytes, columns: int = 64, threshold: int = 0x20) -> list[str]:
    """Per-cell horizontal ink extents, square cells of width/columns px."""
    w, h, rows = png_alpha(data)
    cell = w // columns
    out = [f"    grid {columns} columns x {h // cell} rows, cell {cell}x{cell} px "
           f"(assumed square); per cell 'left-right' ink columns, '.' = empty"]
    for gy in range(h // cell):
        cells = []
        for gx in range(columns):
            x0 = gx * cell
            cols = [any(rows[y][x] > threshold for y in range(gy * cell, (gy + 1) * cell))
                    for x in range(x0, x0 + cell)]
            if any(cols):
                left = cols.index(True)
                right = cell - 1 - cols[::-1].index(True)
                cells.append(f"{left}-{right}")
            else:
                cells.append(".")
        out.append(f"    row {gy:3d}: " + " ".join(cells))
    return out


def dds_info(data: bytes):
    if data[:4] != b"DDS " or len(data) < 128:
        return None
    size, flags, h, w, pitch, depth, mips = struct.unpack_from("<7I", data, 4)
    pf_size, pf_flags, fourcc, bits, rmask, gmask, bmask, amask = struct.unpack_from(
        "<II4s5I", data, 76)
    caps1 = struct.unpack_from("<I", data, 108)[0]
    fourcc_text = fourcc.decode("ascii", "replace") if pf_flags & 0x4 else "-"
    extra = ""
    if fourcc == b"DX10":
        extra = f" dxgi={struct.unpack_from('<I', data, 128)[0]} (impacto: unsupported)"
    elif pf_flags & 0x4 and fourcc not in (b"DXT1", b"DXT2", b"DXT3", b"DXT4", b"DXT5"):
        extra = " (impacto: unsupported fourcc)"
    # header sanity checks of impacto's DDS loader (src/texture/ddsloader.cpp)
    required = {"size": size == 124, "pfsize": pf_size == 32,
                "DDSCAPS_TEXTURE": caps1 & 0x1000, "DDSD_CAPS": flags & 0x1,
                "DDSD_HEIGHT": flags & 0x2, "DDSD_WIDTH": flags & 0x4,
                "DDSD_PIXELFORMAT": flags & 0x1000}
    missing = [k for k, ok in required.items() if not ok]
    if missing:
        extra += " (impacto: rejected, missing " + ",".join(missing) + ")"
    return (f"DDS {w}x{h} mips {mips} pfflags {pf_flags:#x} fourcc {fourcc_text} "
            f"bits {bits} masks {rmask:#x}/{gmask:#x}/{bmask:#x}/{amask:#x} "
            f"flags {flags:#x} caps {caps1:#x}{extra}")


def image_line(name: str, data: bytes) -> str:
    info = png_info(data)
    if info:
        return f"PNG {info[0]}x{info[1]} depth {info[2]} colortype {info[3]}"
    dds = dds_info(data)
    if dds:
        return dds
    return f"other, first bytes {data[:4].hex(' ')}"


def lay_check(data: bytes) -> list[str]:
    out = []
    for order, label in (("<", "little-endian"), (">", "big-endian")):
        try:
            states, unk = struct.unpack_from(order + "ii", data, 0)
            if not 0 < states < 10000:
                out.append(f"    {label}: implausible state count {states}")
                continue
            total = 0
            for i in range(states):
                _, start, count = struct.unpack_from(order + "iii", data, 8 + 12 * i)
                total = max(total, start + count)
            need = 8 + 12 * states + 16 * total
            first = struct.unpack_from(order + "4f", data, 8 + 12 * states)
            texs = [struct.unpack_from(order + "4f", data, 8 + 12 * states + 16 * j)[2:]
                    for j in range(min(total, 64))]
            tmax = (max(t[0] for t in texs), max(t[1] for t in texs)) if texs else (0, 0)
            out.append(f"    {label}: states {states} second-int {unk} vertices {total} "
                       f"needs {need} of {len(data)} bytes; first vertex "
                       f"screen ({first[0]:.1f}, {first[1]:.1f}); max tex of first 64 "
                       f"({tmax[0]:.4f}, {tmax[1]:.4f})")
        except struct.error:
            out.append(f"    {label}: does not fit")
    return out


def audio_kind(head: bytes) -> str:
    if head[:4] != b"OggS":
        return "not-ogg:" + head[:4].hex()
    if head[28:35] == b"\x01vorbis":
        return "ogg-vorbis"
    if head[28:36] == b"OpusHead":
        return "ogg-opus"
    return "ogg-other"


def audio_report(root: Path) -> list[str]:
    out = ["### Audio archives (codec of every entry, by header)"]
    for name in ("bgm.mpk", "se.mpk", "voice.mpk"):
        path = root / "USRDIR" / name
        if not path.exists():
            continue
        kinds = Counter()
        with path.open("rb") as f:
            for entry in mpk_entries(path):
                f.seek(entry[2])
                kinds[audio_kind(f.read(64)) + (" (zlib)" if entry[5] else "")] += 1
        out.append(f"  {name}: " + ", ".join(f"{k} x{c}" for k, c in sorted(kinds.items())))
    return out


def assets_report(root: Path) -> list[str]:
    out = ["## Assets"] + audio_report(root)
    system = root / "USRDIR" / "system.mpk"
    if system.exists():
        out.append("### system.mpk images")
        for entry in mpk_entries(system):
            data = mpk_read(system, entry)
            out.append(f"  id {entry[0]:3d} {entry[1]:20s} {image_line(entry[1], data)}")
            if entry[1].upper().startswith("FONT") and png_info(data):
                try:
                    out += font_ink(data)
                except ValueError as e:
                    out.append(f"    font ink: {e}")
    chara = root / "USRDIR" / "chara.mpk"
    if chara.exists():
        out.append("### chara.mpk (first image/LAY pairs)")
        entries = mpk_entries(chara)
        shown = 0
        for i, entry in enumerate(entries):
            if not entry[1].lower().endswith(".png") or shown >= 3:
                continue
            shown += 1
            out.append(f"  id {entry[0]:3d} {entry[1]:20s} {image_line(entry[1], mpk_read(chara, entry))}")
            if i + 1 < len(entries) and entries[i + 1][1].lower().endswith(".lay"):
                lay = entries[i + 1]
                out.append(f"  id {lay[0]:3d} {lay[1]:20s} LAY {lay[4]} bytes")
                out += lay_check(mpk_read(chara, lay))
    return out


# --------------------------------------------------------------------------
# executable
# --------------------------------------------------------------------------

def exe_report(root: Path) -> list[str]:
    out = ["## Game.exe movie name offsets (file order)"]
    exe = root / "Game.exe"
    movies = sorted({p.stem.lower() for p in (root / "USRDIR").rglob("*.bk2")})
    if not exe.exists() or not movies:
        return out + ["  Game.exe or movies not found"]
    data = exe.read_bytes().lower()
    hits = []
    for stem in movies:
        for m in re.finditer(re.escape(stem.encode()) + rb"(?![0-9a-z_])", data):
            start = m.start()
            if start and (data[start - 1:start].isalnum() or data[start - 1:start] == b"_"):
                continue
            hits.append((start, stem, data[m.end():m.end() + 4]))
    for start, stem, tail in sorted(hits):
        tail_text = tail.split(b"\0", 1)[0].decode("ascii", "replace")
        out.append(f"  {start:#010x} {stem}{tail_text if tail_text.startswith('.') else ''}")
    return out


DEFAULT_CONTEXT = ((0x10, 0x34), (0x00, 0x44), (0x00, 0x53))


def parse_context(argv: list[str]):
    """Opcode slots from --context[=gg:oo,...]; None when not requested."""
    for a in argv:
        if a == "--context":
            return DEFAULT_CONTEXT
        if a.startswith("--context="):
            return tuple(tuple(int(x, 16) for x in s.split(":"))
                         for s in a.split("=", 1)[1].split(",") if s)
    return None


def context_report(root: Path, slots, before: int = 6,
                   after: int = 16) -> list[str]:
    path = root / "USRDIR" / "script.mpk"
    wanted = set(slots)
    out = ["## Context of " + ", ".join(slot_text(s) for s in slots)
           + f" ({before} before, {after} after; numbers only)"]
    if not path.exists():
        return out + ["  script.mpk not found"]
    for entry in mpk_entries(path):
        name = entry[1]
        if not name.upper().endswith(".SCX"):
            continue
        try:
            insts = walk_script(mpk_read(path, entry))[0]
        except DecodeError:
            continue
        for i, (label_id, pos, slot, iname, args) in enumerate(insts):
            if slot not in wanted:
                continue
            out.append(f"### {name} label{label_id} @{pos:#x}: "
                       f"{slot_text(slot)} {iname} {fmt_args(args)}")
            for j in range(max(0, i - before), min(len(insts), i + after + 1)):
                l2, p2, s2, n2, a2 = insts[j]
                mark = "<" if j < i else ">" if j > i else "*"
                out.append(f"  {mark} label{l2} @{p2:#x} {slot_text(s2)} {n2} "
                           f"{fmt_args(a2)}")
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(args[0])
    if not (root / "USRDIR").is_dir():
        print(f"no USRDIR under {root}", file=sys.stderr)
        return 2
    context = parse_context(argv)
    picked = [s for s in ("--scripts", "--assets", "--exe") if s in argv]
    if not picked and context is None:
        picked = ["--scripts", "--assets", "--exe"]
    print("# sghd census (numbers/names only; private, do not publish)")
    if context is not None:
        print()
        print("\n".join(context_report(root, context)))
    for flag, fn in (("--scripts", scripts_report), ("--assets", assets_report),
                     ("--exe", exe_report)):
        if flag in picked:
            print()
            print("\n".join(fn(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
