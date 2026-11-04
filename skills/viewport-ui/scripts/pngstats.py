"""Stdlib PNG stats (no PIL): dimensions + RGB mean/std.

Parses IHDR for (w, h), decompresses IDAT, reverses scanline filters,
computes mean/std over RGB bytes (alpha skipped). Supports 8-bit
truecolor / truecolor+alpha only (what Kit screenshots write).
"""
import struct
import zlib


def png_stats(path):
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, w, h, ctype, blobs = 8, 0, 0, 0, []
    while pos < len(raw):
        (ln,) = struct.unpack(">I", raw[pos:pos + 4])
        typ = raw[pos + 4:pos + 8]
        dat = raw[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bd, ctype, _, _, _ = struct.unpack(">IIBBBBB", dat)
            assert bd == 8 and ctype in (2, 6), (bd, ctype)
        elif typ == b"IDAT":
            blobs.append(dat)
        elif typ == b"IEND":
            break
        pos += 12 + ln
    ch = 3 if ctype == 2 else 4
    stride = w * ch
    px = zlib.decompress(b"".join(blobs))
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = px[p]
        p += 1
        line = bytearray(px[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (
                    b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    n = h * w
    tot, tot2, k = 0, 0, 0
    for i in range(0, len(out), ch):
        for j in range(3):
            v = out[i + j]
            tot += v
            tot2 += v * v
            k += 1
    mean = tot / k
    var = tot2 / k - mean * mean
    return {"w": w, "h": h, "mean": mean, "std": var ** 0.5,
            "bytes": len(raw), "raw": bytes(out), "ch": ch}


def mean_abs_diff(a_path, b_path):
    """Mean absolute RGB pixel difference between two same-size PNGs."""
    pa, pb = png_stats(a_path), png_stats(b_path)
    assert (pa["w"], pa["h"]) == (pb["w"], pb["h"]), "size mismatch"
    ra, rb, ch = pa["raw"], pb["raw"], pa["ch"]
    tot, k = 0, 0
    for i in range(0, len(ra), ch):
        for j in range(3):
            tot += abs(ra[i + j] - rb[i + j])
            k += 1
    return tot / k
