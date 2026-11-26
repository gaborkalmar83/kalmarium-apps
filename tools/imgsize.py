"""Tiny image header reader (WebP, PNG, JPEG, GIF). Python stdlib only."""
import struct
from pathlib import Path


def _webp(b):
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return None
    kind = b[12:16]
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", b[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        bits = struct.unpack("<I", b[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8X":
        return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
    return None


def _png(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", b[16:24])


def _gif(b):
    if b[:3] != b"GIF":
        return None
    return struct.unpack("<HH", b[6:10])


def _jpeg(b):
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    n = len(b)
    while i + 9 < n:
        if b[i] != 0xFF:
            i += 1
            continue
        marker = b[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seglen = struct.unpack(">H", b[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h
        i += 2 + seglen
    return None


def dims(path):
    """Return (width, height) or None if unreadable or missing."""
    try:
        b = Path(path).read_bytes()[:400000]
    except OSError:
        return None
    for fn in (_webp, _png, _jpeg, _gif):
        try:
            r = fn(b)
        except (struct.error, IndexError):
            r = None
        if r:
            return r
    return None
