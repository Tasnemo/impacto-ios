"""Synthetic fixture builders for STEINS;GATE (SGHD) compatibility tests.

Everything here is generated from documented format facts; no commercial
game data is embedded.  Byte layouts are cross-referenced to the impacto
sources that consume them so the tests fail when either side changes:

* MPK v2.0 archive ........ src/io/mpkarchive.cpp (MpkArchive::Create)
* SC3/SCX script header ... src/vm/vm.cpp (ScriptGetLabelAddress,
                             ScriptGetStrAddress, ScriptGetRetAddress)
* Expression immediates ... src/vm/expression.cpp (ExpressionParser::GetTokens)

The SGHD argument layouts come from the CommitteeOfZero/sc3ntist
SGHDDisassembler (reference only; no sc3ntist code is copied).
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# MPK archives
# --------------------------------------------------------------------------

MPK_MAGIC = b"MPK\0"
MPK_TOC_OFFSET = 0x40
MPK_ENTRY_SIZE = 0x100
MPK_NAME_SIZE = MPK_ENTRY_SIZE - 4 - 4 - 8 - 8 - 8  # 224 bytes


@dataclass
class MpkFile:
    file_id: int
    name: str
    data: bytes
    compressed: bool = False


def build_mpk(files: list[MpkFile], major: int = 2, minor: int = 0) -> bytes:
    """Build an MPK archive the way MAGES. tools do for the Steam release.

    Header (impacto reads big-endian magic, then LE u16 minor, LE u16 major,
    LE u32 file count):
        0x00  "MPK\\0"
        0x04  u16 minor version
        0x06  u16 major version
        0x08  u32 file count (upper 4 bytes of the u64 are zero)
        0x0C  padding to 0x40
    Table of contents at 0x40, 256 bytes per entry:
        u32 compression (0 = stored, 1 = zlib)
        u32 file id
        u64 data offset
        u64 compressed size
        u64 uncompressed size
        224-byte NUL-padded file name
    File payloads follow, aligned to 0x800 like the retail archives.
    """
    header = bytearray(MPK_TOC_OFFSET)
    header[0:4] = MPK_MAGIC
    struct.pack_into("<HHI", header, 4, minor, major, len(files))

    toc = bytearray()
    payload = bytearray()
    data_start = MPK_TOC_OFFSET + MPK_ENTRY_SIZE * len(files)
    data_start = (data_start + 0x7FF) & ~0x7FF

    for f in files:
        blob = zlib.compress(f.data) if f.compressed else f.data
        offset = data_start + len(payload)
        name = f.name.encode("ascii")
        if len(name) >= MPK_NAME_SIZE:
            raise ValueError("file name too long for MPK TOC")
        toc += struct.pack("<IIQQQ", int(f.compressed), f.file_id, offset,
                           len(blob), len(f.data))
        toc += name.ljust(MPK_NAME_SIZE, b"\0")
        payload += blob
        pad = (-len(payload)) % 0x800
        payload += b"\0" * pad

    body = bytes(header) + bytes(toc)
    body += b"\0" * (data_start - len(body))
    return body + bytes(payload)


@dataclass
class MpkEntry:
    compressed: int
    file_id: int
    offset: int
    compressed_size: int
    size: int
    name: str


class MpkUnsupported(Exception):
    pass


def parse_mpk(blob: bytes) -> list[MpkEntry]:
    """Parse an MPK exactly the way src/io/mpkarchive.cpp does.

    Mirrors MpkArchive::Create: rejects anything but version 2.0 (the
    "TODO support v1" branch), reads the TOC at 0x40, stops at the first
    entry with offset 0 and skips unknown compression values.
    """
    if blob[0:4] != MPK_MAGIC:
        raise MpkUnsupported("Not an MPK")
    minor, major, count = struct.unpack_from("<HHI", blob, 4)
    if minor != 0 or major != 2:
        raise MpkUnsupported(f"Unsupported MPK version {major}.{minor}")
    entries = []
    pos = MPK_TOC_OFFSET
    seen = set()
    for _ in range(count):
        compression, file_id, offset, csize, size = struct.unpack_from(
            "<IIQQQ", blob, pos)
        name = blob[pos + 32:pos + MPK_ENTRY_SIZE].split(b"\0", 1)[0]
        pos += MPK_ENTRY_SIZE
        if compression not in (0, 1):
            continue
        if file_id in seen:
            continue
        if offset == 0:
            break
        seen.add(file_id)
        entries.append(MpkEntry(compression, file_id, offset, csize, size,
                                name.decode("ascii")))
    return entries


def read_mpk_file(blob: bytes, entry: MpkEntry) -> bytes:
    raw = blob[entry.offset:entry.offset + entry.compressed_size]
    return zlib.decompress(raw) if entry.compressed else raw


# --------------------------------------------------------------------------
# SC3 expressions
# --------------------------------------------------------------------------

EXPR_PRECEDENCE_IMM = 0x0A  # any byte; immediates carry a precedence slot too


def encode_immediate(value: int) -> bytes:
    """Encode an immediate token the way the MAGES. compiler does.

    First byte has bit 7 set; bits 5-6 give the length class; bit 4 is the
    sign for the short forms.  impacto decodes the same four classes in
    ExpressionParser::GetTokens (0x00/0x20/0x40/0x60).
    """
    if -16 <= value < 16:
        return bytes([0x80 | (value & 0x1F)])
    if -0x1000 <= value < 0x1000:
        return bytes([0x80 | 0x20 | ((value >> 8) & 0x1F), value & 0xFF])
    if -0x100000 <= value < 0x100000:
        return bytes([0x80 | 0x40 | ((value >> 16) & 0x1F), value & 0xFF,
                      (value >> 8) & 0xFF])
    return bytes([0x80 | 0x60]) + struct.pack("<i", value)


def expr(value: int) -> bytes:
    """A complete expression consisting of one immediate: tokens + 0x00."""
    return encode_immediate(value) + bytes([EXPR_PRECEDENCE_IMM, 0x00])


def decode_immediate(data: bytes, pos: int) -> tuple[int, int]:
    """Return (value, new_pos) for an immediate token at pos (incl. precedence)."""
    b0 = data[pos]
    cls = b0 & 0x60
    if cls == 0x00:
        value = b0 & 0x1F
        if b0 & 0x10:
            value |= ~0x1F
        pos += 1
    elif cls == 0x20:
        value = ((b0 & 0x1F) << 8) | data[pos + 1]
        if b0 & 0x10:
            value |= ~0x1FFF
        pos += 2
    elif cls == 0x40:
        value = ((b0 & 0x1F) << 16) | (data[pos + 2] << 8) | data[pos + 1]
        if b0 & 0x10:
            value |= ~0x1FFFFF
        pos += 3
    else:
        value = struct.unpack_from("<i", data, pos + 1)[0]
        pos += 5
    pos += 1  # precedence byte
    return value, pos


def skip_expression(data: bytes, pos: int) -> int:
    """Advance past a full expression (tokens until the 0x00 terminator)."""
    while data[pos] != 0x00:
        if data[pos] & 0x80:
            _, pos = decode_immediate(data, pos)
        else:
            pos += 2  # operator byte + precedence byte
    return pos + 1


def eval_single_immediate(data: bytes, pos: int) -> tuple[int, int]:
    value, pos = decode_immediate(data, pos)
    assert data[pos] == 0x00, "fixture expressions are single immediates"
    return value, pos + 1


# --------------------------------------------------------------------------
# SCX script container
# --------------------------------------------------------------------------

SCX_MAGIC = b"SC3\0"
SCX_STRING_TABLE_PTR = 4
SCX_RETURN_TABLE_PTR = 8
SCX_LABEL_TABLE = 12


@dataclass
class ScxBuilder:
    """Assemble a script with the SC3/SCX layout impacto and sc3ntist read.

    Layout: [12-byte header][label table][code][string table][return address
    table][string data].  impacto reads the string-table pointer at +4, the
    return-address-table pointer at +8 and label entries from +12
    (src/vm/vm.cpp ScriptGetStrAddress / ScriptGetRetAddress /
    ScriptGetLabelAddress), all little-endian u32.
    """

    labels: list[bytes] = field(default_factory=list)
    strings: list[bytes] = field(default_factory=list)
    # return addresses as (label index, byte offset within that label)
    returns: list[tuple[int, int]] = field(default_factory=list)

    def add_label(self, code: bytes) -> int:
        self.labels.append(code)
        return len(self.labels) - 1

    def add_string(self, data: bytes) -> int:
        self.strings.append(data)
        return len(self.strings) - 1

    def add_return(self, label: int, offset: int) -> int:
        self.returns.append((label, offset))
        return len(self.returns) - 1

    def build(self) -> bytes:
        label_table_size = 4 * len(self.labels)
        code_start = SCX_LABEL_TABLE + label_table_size
        label_offsets = []
        pos = code_start
        for code in self.labels:
            label_offsets.append(pos)
            pos += len(code)
        string_table = pos
        return_table = string_table + 4 * len(self.strings)
        string_data = return_table + 4 * len(self.returns)

        string_offsets = []
        pos = string_data
        for s in self.strings:
            string_offsets.append(pos)
            pos += len(s)

        out = bytearray()
        out += SCX_MAGIC
        out += struct.pack("<II", string_table, return_table)
        for off in label_offsets:
            out += struct.pack("<I", off)
        for code in self.labels:
            out += code
        for off in string_offsets:
            out += struct.pack("<I", off)
        for label, off in self.returns:
            out += struct.pack("<I", label_offsets[label] + off)
        for s in self.strings:
            out += s
        assert len(out) == pos
        return bytes(out)


def scx_label_address(blob: bytes, label: int) -> int:
    return struct.unpack_from("<I", blob, SCX_LABEL_TABLE + 4 * label)[0]


def scx_string_address(blob: bytes, index: int) -> int:
    table = struct.unpack_from("<I", blob, SCX_STRING_TABLE_PTR)[0]
    return struct.unpack_from("<I", blob, table + 4 * index)[0]


def scx_return_address(blob: bytes, index: int) -> int:
    table = struct.unpack_from("<I", blob, SCX_RETURN_TABLE_PTR)[0]
    return struct.unpack_from("<I", blob, table + 4 * index)[0]


# --------------------------------------------------------------------------
# SGHD instruction encoders (Steam STEINS;GATE layouts)
# --------------------------------------------------------------------------

def sghd_assign(value: int) -> bytes:
    # 0xFE prefix, then an expression (sc3ntist InstAssign; impacto vm.cpp
    # RunThread handles opcodeGrp 0xFE by calling ExpressionEval).
    return bytes([0xFE]) + expr(value)


def sghd_assign_scrwork(index: int, value: int) -> bytes:
    """FE  ScrWork[index] = value  (tokens 0x28 FuncGlobalVars, 0x14 Assign;
    src/vm/expression.cpp ExprTokenType)."""
    return (bytes([0xFE, 0x28, 0x0A]) + encode_immediate(index)
            + bytes([EXPR_PRECEDENCE_IMM, 0x14, 0x01]) + encode_immediate(value)
            + bytes([EXPR_PRECEDENCE_IMM, 0x00]))


def sghd_end_of_script() -> bytes:
    return bytes([0x00, 0x00])


def sghd_jump(label: int) -> bytes:
    return bytes([0x00, 0x07]) + struct.pack("<H", label)


def sghd_jump_if(expect_true: int, condition: int, label: int) -> bytes:
    return (bytes([0x00, 0x0A, expect_true]) + expr(condition)
            + struct.pack("<H", label))


def sghd_call(label: int, return_id: int) -> bytes:
    """00 0B: local label (u16) + return-address id (u16)."""
    return bytes([0x00, 0x0B]) + struct.pack("<HH", label, return_id)


def sghd_call_far(script_buffer: int, label: int, return_id: int) -> bytes:
    """00 0D: far label (expr buffer + u16 label) + return-address id (u16)."""
    return (bytes([0x00, 0x0D]) + expr(script_buffer)
            + struct.pack("<HH", label, return_id))


def sghd_return() -> bytes:
    return bytes([0x00, 0x0E])


def sghd_set_flag(flag: int) -> bytes:
    return bytes([0x00, 0x12]) + expr(flag)


def sghd_call_if_flag(condition: int, flag: int, label: int,
                      return_id: int) -> bytes:
    """00 54: byte condition, flag expr, local label, return-address id."""
    return (bytes([0x00, 0x54, condition]) + expr(flag)
            + struct.pack("<HH", label, return_id))


def sghd_return_if_flag(condition: int, flag: int) -> bytes:
    """00 57 in SGHD (impacto's sgps3 table has InstReturnIfFlag at 00 55)."""
    return bytes([0x00, 0x57, condition]) + expr(flag)


def sghd_nop() -> bytes:
    return bytes([0x00, 0x5F])


def sghd_group_checkpoint(kind: int, checkpoint_id: int) -> bytes:
    """01 09 type 00: u16 checkpoint id (sc3ntist GroupCheckpoint)."""
    assert kind == 0
    return bytes([0x01, 0x09, kind]) + struct.pack("<H", checkpoint_id)


# --------------------------------------------------------------------------
# Generic SGHD encoding and the reference decoder for every opcode that
# differs from impacto's sgps3 table (Thread 04 Task 2).  Layouts follow
# the sc3ntist SGHD disassembler; tokens: B = u8, H = u16 (label, string
# or return id), E = expression.
# --------------------------------------------------------------------------

def u8(value: int) -> bytes:
    return bytes([value & 0xFF])


def u16(value: int) -> bytes:
    return struct.pack("<H", value)


def ins(group: int, opcode: int, *parts: bytes) -> bytes:
    """Encode an instruction from already-encoded argument parts."""
    return bytes([group, opcode]) + b"".join(parts)


def _layout_00_23(t):   # PlaySoundEffect: channel, type, [effect, loop]
    return "E E" if t[1] != 2 else ""


def _sub(table, default=None):
    def pick(t):
        if t[0] in table:
            return table[t[0]]
        if default is None:
            raise AssertionError(f"unknown subtype {t[0]:#x}")
        return default
    return pick


# slot -> (name, fixed leading bytes, rest layout (str or callable(prefix)))
SGHD_LAYOUTS = {
    (0x00, 0x00): ("EndOfScript", 0, ""),
    (0x00, 0x07): ("Jump", 0, "H"),
    (0x00, 0x0A): ("JumpIf", 0, "B E H"),
    (0x00, 0x0B): ("Call", 0, "H H"),
    (0x00, 0x0D): ("CallFar", 0, "E H H"),
    (0x00, 0x0E): ("Return", 0, ""),
    (0x00, 0x12): ("SetFlag", 0, "E"),
    (0x00, 0x13): ("ResetFlag", 0, "E"),
    (0x00, 0x23): ("PlaySoundEffect", 2, _layout_00_23),
    (0x00, 0x35): ("Unk0035", 0, "B"),
    (0x00, 0x37): ("PlayVoice", 0, "B E E"),
    (0x00, 0x38): ("StopVoice", 0, "B E"),
    (0x00, 0x41): ("Nop3", 0, "B"),
    (0x00, 0x43): ("SystemMessage", 1, _sub({
        0x0A: "", 0x0B: "", 0x0C: "E", 0x0D: "H", 0x0E: "H", 0x0F: "",
        0x10: "", 0x11: "", 0x00: "", 0x01: "", 0x02: "E", 0x03: "H",
        0x04: "H", 0x05: "", 0x06: "", 0x07: ""})),
    (0x00, 0x4B): ("WaitForSomething004B", 0, ""),
    (0x00, 0x4C): ("Unk004C", 1, lambda t: "E" if t[0] == 0 else ""),
    (0x00, 0x50): ("UselessJump", 1, lambda t: {0: "H H", 2: "H H",
                                                3: "H H H"}.get(t[0], "")),
    (0x00, 0x52): ("Nop", 0, ""),
    (0x00, 0x53): ("Useless0053", 0, "B E H"),
    (0x00, 0x54): ("CallIfFlag", 0, "B E H H"),
    (0x00, 0x56): ("CallFarIfFlag", 0, "B E E H H"),
    (0x00, 0x57): ("ReturnIfFlag", 0, "B E"),
    (0x00, 0x58): ("Unk0058", 1, lambda t: ("E E E E" if t[0] in (2, 3)
                                            else "E") + " H"),
    (0x00, 0x59): ("Unk0059", 0, "B E E H"),
    (0x00, 0x5F): ("Nop", 0, ""),
    (0x01, 0x05): ("GroupCalc", 1, _sub({0: "E E", 1: "E E", 2: "E E E",
                                         3: "E E E E", 4: "E E E E",
                                         5: "E E E E", 6: "E E E E"})),
    (0x01, 0x06): ("Unk0106", 1, _sub({0: "E E", 1: "E E E"})),
    (0x01, 0x07): ("Unk0107", 0, "E E E"),
    (0x01, 0x08): ("Unk0108", 0, "B"),
    (0x01, 0x09): ("GroupCheckpoint", 1, _sub({0: "H", 1: "H E", 2: "E"},
                                               default="")),
    (0x01, 0x0A): ("Unk010A", 0, "B"),
    (0x01, 0x12): ("Unk0112", 1, lambda t: "H E" if t[0] in (0, 2) else "H"),
    (0x01, 0x25): ("Group0125", 1, _sub({0: "H", 1: "E E H", 2: "H",
                                         3: "H E E E"})),
    (0x10, 0x05): ("LoadCharacter", 1, lambda t: "E E H" if t[0] == 0
                   else "E E"),
    (0x10, 0x12): ("Nop", 0, ""),
    (0x10, 0x1A): ("Unk101A", 0, "B"),
    (0x10, 0x22): ("Group1022", 1, lambda t: "H" if t[0] == 0x0A else ""),
    (0x10, 0x23): ("Unk1023", 1, lambda t: "B" if t[0] in (0, 0x0A) else ""),
    (0x10, 0x24): ("Unk1024", 1, lambda t: "E E" if t[0] == 0 else ""),
    (0x10, 0x27): ("Unk1027", 1, lambda t: "E E" if t[0] == 1 else "E"),
    (0x10, 0x33): ("GroupTips", 1, lambda t: "H H" if t[0] == 0 else ""),
    (0x10, 0x37): ("Group1037", 1, _sub({
        0x00: "B E", 0x01: "B E", 0x02: "B E H", 0x03: "B E H",
        0x04: "H H H H H H", 0x0F: "E", 0x10: "E", 0x12: "E E",
        0x14: "E E E E", 0x15: "E E E E", 0x1A: "E"}, default="")),
    (0x10, 0x38): ("Group1038", 1, lambda t: "H" if t[0] == 0 else ""),
    (0x10, 0x3F): ("Unk103F", 0, "B"),
    (0x10, 0x40): ("Win32_SetResolution", 0, ""),
    (0x10, 0x41): ("Win32_DestroyWindow", 0, ""),
}


def decode_sghd(blob: bytes, pos: int):
    """Return (name, args, next_pos) for the SGHD instruction at pos.

    Expressions in fixtures are single immediates, so their values are
    returned as arguments."""
    if blob[pos] == 0xFE:
        if blob[pos + 1] & 0x80:
            value, p = eval_single_immediate(blob, pos + 1)
            return "Assign", (value,), p
        return "Assign", (), skip_expression(blob, pos + 1)
    key = (blob[pos], blob[pos + 1])
    if key not in SGHD_LAYOUTS:
        raise AssertionError(f"fixture uses unhandled opcode {key[0]:02X} {key[1]:02X}")
    name, fixed, rest = SGHD_LAYOUTS[key]
    p = pos + 2
    prefix = tuple(blob[p:p + fixed])
    p += fixed
    layout = rest(prefix) if callable(rest) else rest
    args = list(prefix)
    for tok in layout.split():
        if tok == "B":
            args.append(blob[p])
            p += 1
        elif tok == "H":
            args.append(struct.unpack_from("<H", blob, p)[0])
            p += 2
        else:
            value, p = eval_single_immediate(blob, p)
            args.append(value)
    return name, tuple(args), p


def sghd_reference_trace(blob: bytes, start_label: int = 0,
                         max_steps: int = 10000) -> list[tuple[int, str]]:
    """Execute control flow of a fixture script the way the SGHD engine is
    documented to: flags, Call/CallFar/CallIfFlag/CallFarIfFlag with return
    ids, Return/ReturnIfFlag, Jump.  Everything else falls through.

    Returns (address, 'gg:oo') for every non-Assign instruction, the same
    shape impacto logs at Trace level, ending with EndOfScript."""
    flags: set[int] = set()
    stack: list[int] = []
    pos = scx_label_address(blob, start_label)
    trace = []
    for _ in range(max_steps):
        name, args, nxt = decode_sghd(blob, pos)
        if name != "Assign":
            trace.append((pos, f"{blob[pos]:02x}:{blob[pos + 1]:02x}"))
        if name == "EndOfScript":
            return trace
        if name == "SetFlag":
            flags.add(args[0])
        elif name == "ResetFlag":
            flags.discard(args[0])
        elif name == "Jump":
            nxt = scx_label_address(blob, args[0])
        elif name in ("Call", "CallFar", "CallIfFlag", "CallFarIfFlag"):
            if name == "Call":
                label, ret = args
            elif name == "CallFar":
                _, label, ret = args
            elif name == "CallIfFlag":
                cond, flag, label, ret = args
                if (flag in flags) != bool(cond):
                    pos = nxt
                    continue
            else:
                cond, flag, _, label, ret = args
                if (flag in flags) != bool(cond):
                    pos = nxt
                    continue
            stack.append(scx_return_address(blob, ret))
            nxt = scx_label_address(blob, label)
        elif name == "Return":
            nxt = stack.pop()
        elif name == "ReturnIfFlag":
            cond, flag = args
            if (flag in flags) == bool(cond):
                nxt = stack.pop()
        pos = nxt
    raise AssertionError("reference trace did not reach EndOfScript")


def sghd_task2_fixture() -> bytes:
    """One script that encodes all 37 opcodes Thread 03 found broken in
    impacto (16 Dummy slots + 21 layout mismatches), with every taken branch
    returning to the main label, ending in EndOfScript.

    Uses only arguments that are safe without game data: audio ids that do
    not exist (the engine logs and continues), character id 0 (already
    "loaded"), sub-types that do not open UI."""
    E = expr
    b = ScxBuilder()
    s_empty = b.add_string(b"\xFF")        # empty SC3 string
    F = 1770                                # flag used for conditional calls
    main = bytearray()
    returns = []                            # byte offsets of return points

    def call_like(code: bytes):
        main.extend(code)
        returns.append(len(main))

    main += sghd_set_flag(F)
    # control flow (00 54 / 00 56 / 00 57); return ids 0..2
    call_like(sghd_call_if_flag(1, F, 1, 0))            # taken -> label 1
    call_like(ins(0x00, 0x54, u8(0), E(F), u16(1), u16(1)))   # not taken
    call_like(ins(0x00, 0x56, u8(1), E(F), E(0), u16(2), u16(2)))  # taken
    main += ins(0x00, 0x5F)                              # Nop
    main += ins(0x00, 0x52)                              # Nop (SGHD)
    main += ins(0x10, 0x12)                              # Nop (SGHD)
    # sound
    main += ins(0x00, 0x23, u8(0), u8(0), E(77), E(0))   # SEplay, missing id
    main += ins(0x00, 0x23, u8(0), u8(2))                # SEplay resume
    main += ins(0x00, 0x37, u8(0), E(77), E(0))          # PlayVoice
    main += ins(0x00, 0x38, u8(0), E(0))                 # StopVoice
    # system
    main += ins(0x00, 0x35, u8(1))
    main += ins(0x00, 0x41, u8(1))
    main += ins(0x00, 0x43, u8(0x0C), E(5))              # SystemMes expr
    main += ins(0x00, 0x43, u8(0x0D), u16(s_empty))      # SystemMes string
    main += ins(0x00, 0x43, u8(0x0A))
    main += ins(0x00, 0x4B)
    main += ins(0x00, 0x4C, u8(0), E(3))
    main += ins(0x00, 0x4C, u8(1))
    main += ins(0x00, 0x50, u8(3), u16(0), u16(0), u16(0))
    main += ins(0x00, 0x50, u8(1))
    main += ins(0x00, 0x53, u8(1), E(2), u16(0))
    main += ins(0x00, 0x58, u8(2), E(1), E(2), E(3), E(4), u16(0))
    main += ins(0x00, 0x58, u8(0), E(1), u16(0))
    main += ins(0x00, 0x59, u8(1), E(2), E(3), u16(0))
    # graph group
    main += ins(0x01, 0x05, u8(0), E(100), E(0x4000))    # CalcSin -> ScrWork
    main += ins(0x01, 0x06, u8(0), E(1), E(2))
    main += ins(0x01, 0x06, u8(1), E(101), E(1), E(2))
    main += ins(0x01, 0x07, E(1), E(2), E(3))
    main += ins(0x01, 0x08, u8(1))
    main += ins(0x01, 0x09, u8(0), u16(42))              # checkpoint
    main += ins(0x01, 0x09, u8(1), u16(43), E(1))
    main += ins(0x01, 0x0A, u8(1))
    main += ins(0x01, 0x12, u8(0), u16(s_empty), E(0))   # Sel init
    main += ins(0x01, 0x25, u8(3), u16(s_empty), E(77), E(0), E(0))
    # user1 group
    main += ins(0x10, 0x05, u8(0), E(1), E(0), u16(0))   # CHAload buf 1 (bitmask), id 0
    main += ins(0x10, 0x1A, u8(1))
    main += ins(0x10, 0x22, u8(0x0A), u16(42))           # AutoSave checkpoint
    main += ins(0x10, 0x23, u8(0x0A), u8(1))
    main += ins(0x10, 0x24, u8(0x0A))
    main += ins(0x10, 0x27, u8(1), E(3), E(F))
    main += ins(0x10, 0x27, u8(0), E(3))
    main += ins(0x10, 0x33, u8(0), u16(3), u16(3))       # Tips data init
    for sub, parts in ((0x10, (E(1),)), (0x14, (E(1), E(2), E(3), E(4))),
                       (0x15, (E(1), E(2), E(3), E(4))), (0x1A, (E(1),)),
                       (0x03, (u8(1), E(2), u16(0))), (0x05, ())):
        main += ins(0x10, 0x37, u8(sub), *parts)
    main += ins(0x10, 0x3F, u8(1))
    main += ins(0x10, 0x40)
    main += ins(0x10, 0x41)
    main += sghd_end_of_script()

    sub1 = sghd_assign(1) + sghd_return()                 # label 1
    sub2 = (sghd_return_if_flag(1, F)                     # label 2: returns
            + ins(0x00, 0x00))                            # never reached
    tips = b"\x00\x00"                                    # label 3: tips data
    b.add_label(bytes(main))
    b.add_label(sub1)
    b.add_label(sub2)
    b.add_label(tips)
    for off in returns:
        b.add_return(0, off)
    return b.build()
