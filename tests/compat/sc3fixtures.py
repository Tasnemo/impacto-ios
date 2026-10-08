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
