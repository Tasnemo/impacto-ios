#!/usr/bin/env python3
"""Windows-local inspection helpers for the STEINS;GATE (Steam) port.

Run on the machine with the legally owned Steam install (Python 3.9+, no
third-party packages), from a checkout of this repository:

    python tools\\sghd_inspect.py sheets "C:\\...\\STEINS;GATE" > sghd-sheets.txt
    python tools\\sghd_inspect.py crops  "C:\\...\\STEINS;GATE" crops-out
    python tools\\sghd_inspect.py regions "C:\\...\\STEINS;GATE" regions-out
    python tools\\sghd_inspect.py widths "C:\\...\\STEINS;GATE" > sghd-widths.txt

sheets  For every system.mpk image: bounding boxes (x y w h) of the opaque
        regions (alpha > 32, 4x4-block connectivity), largest first. Numbers
        only -- safe to share privately; lets the next thread match sprite
        rectangles (dialogue box, nameplate, buttons) to the Steam sheets.
sprites Same boxes, but only for the sheets the profile uses.
crops   Crops every sprite rectangle defined in profiles/sghd/**/*.lua out of
        the Steam sheets into <out>/*.png plus <out>/index.html, for looking
        at locally. The PNGs are game artwork: do NOT share or commit them.
regions Crops every opaque region (large ones also split per pixel) of the
        Data/Title/Backlog sheets into <out>/*.png + index.html, named by box,
        so the owner can name UI elements. Local only, like crops.
widths  Searches Game.exe for the glyph advance-width table by correlating
        byte runs with the ink widths of FONT.PNG; prints the best candidates
        and, for the best one, the 2944 values (numbers only).

All decoding (MPK, DDS DXT1/DXT3/DXT5, PNG) is pure Python and slow
(about half a minute per large sheet).
"""

from __future__ import annotations

import html
import re
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import sghd_census as census  # noqa: E402

ALPHA_THRESHOLD = 32
SPLIT_AREA = 256 * 256  # block regions at least this large are split per pixel


# --------------------------------------------------------------------------
# image decoding
# --------------------------------------------------------------------------

def _rgb565(c: int) -> tuple[int, int, int]:
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def _color_block(block: bytes, dxt1: bool) -> list[tuple[int, int, int, int]]:
    c0, c1, idx = struct.unpack_from("<HHI", block)
    p0, p1 = _rgb565(c0), _rgb565(c1)
    if c0 > c1 or not dxt1:
        p2 = tuple((2 * a + b) // 3 for a, b in zip(p0, p1))
        p3 = tuple((a + 2 * b) // 3 for a, b in zip(p0, p1))
        pal = [p0 + (255,), p1 + (255,), p2 + (255,), p3 + (255,)]
    else:
        p2 = tuple((a + b) // 2 for a, b in zip(p0, p1))
        pal = [p0 + (255,), p1 + (255,), p2 + (255,), (0, 0, 0, 0)]
    return [pal[(idx >> (2 * i)) & 3] for i in range(16)]


def _alpha_block_dxt5(block: bytes) -> list[int]:
    a0, a1 = block[0], block[1]
    bits = int.from_bytes(block[2:8], "little")
    if a0 > a1:
        pal = [a0, a1] + [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
    else:
        pal = [a0, a1] + [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]
    return [pal[(bits >> (3 * i)) & 7] for i in range(16)]


def dds_decode(data: bytes, alpha_only: bool = False):
    """(width, height, pixels): pixels is a bytearray of RGBA, or of alpha
    only when alpha_only. Top mip level only."""
    if data[:4] != b"DDS ":
        raise ValueError("not a DDS file")
    h, w = struct.unpack_from("<II", data, 12)
    fourcc = data[84:88]
    if fourcc not in (b"DXT1", b"DXT3", b"DXT5"):
        raise ValueError(f"unsupported DDS format {fourcc!r}")
    bsize = 8 if fourcc == b"DXT1" else 16
    bw, bh = (w + 3) // 4, (h + 3) // 4
    chan = 1 if alpha_only else 4
    out = bytearray(w * h * chan)
    pos = 128
    for by in range(bh):
        for bx in range(bw):
            block = data[pos:pos + bsize]
            pos += bsize
            if fourcc == b"DXT5":
                alpha = _alpha_block_dxt5(block)
            elif fourcc == b"DXT3":
                bits = int.from_bytes(block[:8], "little")
                alpha = [((bits >> (4 * i)) & 15) * 17 for i in range(16)]
            else:
                alpha = None
            colors = None
            if not alpha_only or alpha is None:
                colors = _color_block(block[bsize - 8:], fourcc == b"DXT1")
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x >= w or y >= h:
                    continue
                a = alpha[i] if alpha is not None else colors[i][3]
                o = (y * w + x) * chan
                if alpha_only:
                    out[o] = a
                else:
                    r, g, b, _ = colors[i]
                    out[o:o + 4] = bytes((r, g, b, a))
    return w, h, out


def png_decode(data: bytes, alpha_only: bool = False):
    """(width, height, pixels) for 8-bit non-interlaced PNGs."""
    w, h, depth, ctype = census.png_info(data)
    if depth != 8 or data[28] != 0 or ctype not in (0, 2, 4, 6):
        raise ValueError(f"unsupported PNG (depth {depth}, type {ctype})")
    pos, idat = 8, bytearray()
    while pos < len(data):
        length, tag = struct.unpack_from(">I4s", data, pos)
        if tag == b"IDAT":
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length
    raw = zlib.decompress(bytes(idat))
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    stride = w * bpp
    prev = bytearray(stride)
    chan = 1 if alpha_only else 4
    out = bytearray(w * h * chan)
    for y in range(h):
        ftype = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif ftype == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else
                                      (b if pb <= pc else c))) & 0xFF
        prev = line
        for x in range(w):
            px = line[x * bpp:(x + 1) * bpp]
            if ctype == 6:
                rgba = px
            elif ctype == 2:
                rgba = px + b"\xff"
            elif ctype == 4:
                rgba = bytes((px[0], px[0], px[0], px[1]))
            else:
                rgba = bytes((px[0], px[0], px[0], 255))
            o = (y * w + x) * chan
            if alpha_only:
                out[o] = rgba[3]
            else:
                out[o:o + 4] = rgba
    return w, h, out


def image_decode(data: bytes, alpha_only: bool = False):
    if data[:4] == b"DDS ":
        return dds_decode(data, alpha_only)
    return png_decode(data, alpha_only)


def png_encode(w: int, h: int, rgba: bytes) -> bytes:
    raw = b"".join(b"\0" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------
# opaque regions
# --------------------------------------------------------------------------

def opaque_boxes(w: int, h: int, alpha: bytes, threshold: int = ALPHA_THRESHOLD):
    """Bounding boxes (x, y, w, h) of 4x4-block-connected opaque regions,
    refined to pixel extents, largest area first."""
    bw, bh = (w + 3) // 4, (h + 3) // 4
    solid = bytearray(bw * bh)
    for y in range(h):
        row = alpha[y * w:(y + 1) * w]
        for x in range(w):
            if row[x] > threshold:
                solid[(y >> 2) * bw + (x >> 2)] = 1
    seen = bytearray(bw * bh)
    boxes = []
    for start in range(bw * bh):
        if not solid[start] or seen[start]:
            continue
        stack, seen[start] = [start], 1
        x0 = y0 = 1 << 30
        x1 = y1 = -1
        while stack:
            i = stack.pop()
            bx, by = i % bw, i // bw
            x0, x1, y0, y1 = min(x0, bx), max(x1, bx), min(y0, by), max(y1, by)
            for nx, ny in ((bx - 1, by), (bx + 1, by), (bx, by - 1), (bx, by + 1)):
                if 0 <= nx < bw and 0 <= ny < bh:
                    j = ny * bw + nx
                    if solid[j] and not seen[j]:
                        seen[j] = 1
                        stack.append(j)
        # refine to pixels inside the block box
        px0, py0 = x0 * 4, y0 * 4
        px1, py1 = min(w, x1 * 4 + 4), min(h, y1 * 4 + 4)
        xs = [x for x in range(px0, px1)
              if any(alpha[y * w + x] > threshold for y in range(py0, py1))]
        ys = [y for y in range(py0, py1)
              if any(alpha[y * w + x] > threshold for x in range(px0, px1))]
        boxes.append((xs[0], ys[0], xs[-1] - xs[0] + 1, ys[-1] - ys[0] + 1))
    boxes.sort(key=lambda b: (-b[2] * b[3], b[1], b[0]))
    return boxes


def split_box(w: int, alpha: bytes, box, threshold: int = ALPHA_THRESHOLD):
    """Pixel-level (4-connected) opaque components inside one block-level
    box; packed atlases often keep sprites only 1-3 px apart, which the 4x4
    block pass merges. Largest first."""
    bx, by, bw, bh = box
    seen = bytearray(bw * bh)
    out = []
    for sy in range(bh):
        row = (by + sy) * w + bx
        for sx in range(bw):
            if seen[sy * bw + sx] or alpha[row + sx] <= threshold:
                continue
            stack, seen[sy * bw + sx] = [(sx, sy)], 1
            x0, y0, x1, y1 = sx, sy, sx, sy
            while stack:
                cx, cy = stack.pop()
                x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < bw and 0 <= ny < bh and not seen[ny * bw + nx] \
                            and alpha[(by + ny) * w + bx + nx] > threshold:
                        seen[ny * bw + nx] = 1
                        stack.append((nx, ny))
            out.append((bx + x0, by + y0, x1 - x0 + 1, y1 - y0 + 1))
    out.sort(key=lambda b: (-b[2] * b[3], b[1], b[0]))
    return out


# --------------------------------------------------------------------------
# profile sprites
# --------------------------------------------------------------------------

SPRITE_RE = re.compile(
    r'root\.Sprites\[\s*([^\]]+?)\s*\]\s*=\s*\{\s*Sheet\s*=\s*"(\w+)"\s*,\s*'
    r'Bounds\s*=\s*\{\s*X\s*=\s*(-?[\d.]+)\s*,\s*Y\s*=\s*(-?[\d.]+)\s*,\s*'
    r'Width\s*=\s*(-?[\d.]+)\s*,\s*Height\s*=\s*(-?[\d.]+)', re.S)
SHEET_RE = re.compile(r'\["(\w+)"\]\s*=\s*\{(?:\s*--[^\n]*)*\s*Path\s*=\s*\{\s*Mount\s*=\s*"system"\s*,'
                      r'\s*Id\s*=\s*(\d+)\s*\}(.*?)\}', re.S)


def profile_sprites(profile_dir: Path):
    """[(name, sheet, x, y, w, h)] for literal sprite definitions; computed
    names (loops) are reported with their Lua expression."""
    out = []
    for path in sorted(profile_dir.rglob("*.lua")):
        for m in SPRITE_RE.finditer(path.read_text(encoding="utf-8")):
            name = m.group(1).strip('"')
            out.append((name, m.group(2)) + tuple(float(v) for v in m.groups()[2:]))
    return out


def profile_sheets(profile_dir: Path) -> dict[str, tuple[int, bool]]:
    text = (profile_dir / "sprites.lua").read_text(encoding="utf-8")
    return {m.group(1): (int(m.group(2)), "ScriptHandled" in m.group(3))
            for m in SHEET_RE.finditer(text)}


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def system_images(root: Path):
    path = root / "USRDIR" / "system.mpk"
    for entry in census.mpk_entries(path):
        if entry[1].upper().endswith((".DDS", ".PNG")):
            yield entry[0], entry[1], census.mpk_read(path, entry)


def cmd_sheets(root: Path, only: set[int] | None = None, limit: int = 120) -> list[str]:
    out = ["# sghd sheet regions (numbers only; private)",
           f"# opaque = alpha > {ALPHA_THRESHOLD}; boxes x y w h, largest first"]
    for file_id, name, data in system_images(root):
        if only is not None and file_id not in only:
            continue
        try:
            w, h, alpha = image_decode(data, alpha_only=True)
        except ValueError as e:
            out.append(f"## id {file_id} {name}: {e}")
            continue
        boxes = opaque_boxes(w, h, alpha)
        out.append(f"## id {file_id} {name} {w}x{h}: {len(boxes)} regions")
        for box in boxes[:limit]:
            out.append("  %d %d %d %d" % box)
            if box[2] * box[3] >= SPLIT_AREA:
                parts = split_box(w, alpha, box)
                if len(parts) > 1:
                    out.append(f"    split into {len(parts)} pixel-connected parts:")
                    out += ["    - %d %d %d %d" % p for p in parts[:limit] if p[2] * p[3] >= 16]
    return out


def cmd_region_crops(root: Path, dest: Path, only: set[int] | None = None) -> list[str]:
    """Crop every region (and split part) of the profile sheets to PNG with
    its box in the file name, for naming UI elements locally."""
    dest.mkdir(parents=True, exist_ok=True)
    rows, log = [], []
    for file_id, name, data in system_images(root):
        if only is not None and file_id not in only:
            continue
        w, h, px = image_decode(data)
        alpha = px[3::4]
        boxes = opaque_boxes(w, h, alpha)
        for box in list(boxes):
            if box[2] * box[3] >= SPLIT_AREA:
                boxes += [p for p in split_box(w, alpha, box) if p[2] * p[3] >= 16]
        for x, y, bw, bh in boxes:
            crop = b"".join(bytes(px[(yy * w + x) * 4:(yy * w + x + bw) * 4])
                            for yy in range(y, y + bh))
            fname = f"{file_id}_{x}_{y}_{bw}_{bh}.png"
            (dest / fname).write_bytes(png_encode(bw, bh, crop))
            rows.append(f"<tr><td>{name}</td><td>{x} {y} {bw} {bh}</td>"
                        f"<td style='background:#808080'><img src='{fname}' "
                        f"style='max-width:600px'></td></tr>")
        log.append(f"{name}: {len(boxes)} crops")
    (dest / "index.html").write_text(
        "<html><body><p>Opaque regions of the Steam sheets. Local only: game "
        "artwork, do not share. Reply with lines 'sprite name: sheet x y w h'.</p>"
        "<table border=1><tr><th>sheet</th><th>x y w h</th><th>crop</th></tr>"
        + "".join(rows) + "</table></body></html>", encoding="utf-8")
    return log


def cmd_crops(root: Path, dest: Path) -> list[str]:
    profile = REPO / "profiles" / "sghd"
    sheets = profile_sheets(profile)
    sprites = profile_sprites(profile)
    images = {i: d for i, _, d in system_images(root)}
    decoded = {}
    dest.mkdir(parents=True, exist_ok=True)
    rows, log = [], []
    for name, sheet, x, y, w, h in sprites:
        if sheet not in sheets or sheets[sheet][1]:
            log.append(f"skip {name}: sheet {sheet} not loaded from system.mpk")
            continue
        sid = sheets[sheet][0]
        if sid not in images:
            log.append(f"skip {name}: system.mpk has no id {sid}")
            continue
        if sid not in decoded:
            decoded[sid] = image_decode(images[sid])
        sw, sh, px = decoded[sid]
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(sw, int(x + w + 0.999)), min(sh, int(y + h + 0.999))
        if x1 <= x0 or y1 <= y0:
            log.append(f"skip {name}: rectangle outside {sheet} ({sw}x{sh})")
            continue
        crop = b"".join(bytes(px[(yy * sw + x0) * 4:(yy * sw + x1) * 4]) for yy in range(y0, y1))
        fname = re.sub(r"[^\w.-]", "_", name) + ".png"
        (dest / fname).write_bytes(png_encode(x1 - x0, y1 - y0, crop))
        rows.append(f"<tr><td>{html.escape(name)}</td><td>{sheet}</td>"
                    f"<td>{x:g} {y:g} {w:g} {h:g}</td>"
                    f"<td style='background:#808080'><img src='{fname}'></td></tr>")
        log.append(f"wrote {fname} ({sheet} {x:g},{y:g} {w:g}x{h:g})")
    (dest / "index.html").write_text(
        "<html><body><p>Profile sprite rectangles cropped from the Steam sheets. "
        "Local only: game artwork, do not share.</p><table border=1>"
        "<tr><th>sprite</th><th>sheet</th><th>x y w h</th><th>crop</th></tr>"
        + "".join(rows) + "</table></body></html>", encoding="utf-8")
    return log


def ink_widths(root: Path) -> list[int | None]:
    """Ink-derived advance per glyph (None for empty cells)."""
    import gen_sghd_font_widths as gen
    rows = gen.rows_from_install(root)
    widths = gen.widths_from_rows(rows)
    flat = [cell for row in rows for cell in row]
    return [None if cell == "." else w for cell, w in zip(flat, widths)]


def data_ranges(exe: bytes) -> list[tuple[int, int]]:
    """File ranges of the PE's non-code sections (whole file if unparsable)."""
    try:
        pe = struct.unpack_from("<I", exe, 0x3C)[0]
        if exe[pe:pe + 4] != b"PE\0\0":
            raise ValueError
        count, opt = struct.unpack_from("<H", exe, pe + 6)[0], struct.unpack_from("<H", exe, pe + 20)[0]
        out = []
        for i in range(count):
            sec = pe + 24 + opt + 40 * i
            size, ptr = struct.unpack_from("<II", exe, sec + 16)
            flags = struct.unpack_from("<I", exe, sec + 36)[0]
            if not flags & 0x20 and size:
                out.append((ptr, min(len(exe), ptr + size)))
        return out or [(0, len(exe))]
    except (ValueError, struct.error):
        return [(0, len(exe))]


def correlation(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0


def find_width_table(exe: bytes, ink: list[int | None], probe: int = 256, top: int = 5):
    """Best (correlation, offset, element size) candidates for a width table
    whose first `probe` entries track the measured ink widths."""
    idx = [i for i in range(probe) if ink[i] is not None]
    ref = [float(ink[i]) for i in idx]
    narrow = min(idx, key=lambda i: ink[i])
    wide = max(idx, key=lambda i: ink[i])
    best = []
    for size in (1, 2):
        def val(off, i):
            return exe[off + i] if size == 1 else exe[off + 2 * i] | exe[off + 2 * i + 1] << 8
        for lo, hi in data_ranges(exe):
            for off in range(lo, hi - probe * size, size):
                a, b = val(off, narrow), val(off, wide)
                if not 0 < a < b <= 96:
                    continue  # cheap pre-filter: narrowest < widest glyph
                vals = [val(off, i) for i in idx]
                if max(vals) > 96:
                    continue
                r = correlation(ref, [float(v) for v in vals])
                if r > 0.6:
                    best.append((r, off, size))
    best.sort(reverse=True)
    return best[:top]


def cmd_widths(root: Path) -> list[str]:
    exe = (root / "Game.exe").read_bytes()
    ink = ink_widths(root)
    out = ["# sghd Game.exe glyph width table candidates (numbers only; private)",
           "# correlation offset element-size : first 64 values"]
    cands = find_width_table(exe, ink)
    if not cands:
        return out + ["  no candidate with correlation > 0.6"]
    for r, off, size in cands:
        vals = [exe[off + i * size] if size == 1 else
                exe[off + i * 2] | exe[off + i * 2 + 1] << 8 for i in range(64)]
        out.append(f"  {r:.3f} {off:#x} {size} : " + " ".join(map(str, vals)))
    r, off, size = cands[0]
    count = 64 * 46
    vals = [exe[off + i * size] if size == 1 else
            exe[off + i * 2] | exe[off + i * 2 + 1] << 8 for i in range(count)]
    out.append(f"## best candidate {off:#x}, {count} values")
    out += ["  " + " ".join(map(str, vals[i:i + 64])) for i in range(0, count, 64)]
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in ("sheets", "sprites", "crops", "regions", "widths"):
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(argv[1])
    if not (root / "USRDIR").is_dir():
        print(f"no USRDIR under {root}", file=sys.stderr)
        return 2
    if argv[0] == "sheets":
        lines = cmd_sheets(root)
    elif argv[0] == "sprites":
        used = {sid for sid, handled in profile_sheets(REPO / "profiles" / "sghd").values()
                if not handled}
        lines = cmd_sheets(root, used)
    elif argv[0] == "regions":
        if len(argv) != 3:
            print(__doc__, file=sys.stderr)
            return 2
        used = {sid for sid, handled in profile_sheets(REPO / "profiles" / "sghd").values()
                if not handled and sid != 9}  # not the font
        lines = cmd_region_crops(root, Path(argv[2]), used)
    elif argv[0] == "crops":
        if len(argv) != 3:
            print(__doc__, file=sys.stderr)
            return 2
        lines = cmd_crops(root, Path(argv[2]))
    else:
        lines = cmd_widths(root)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
