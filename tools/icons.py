#!/usr/bin/env python3
"""Erzeugt die App-Icons (PNG) für die installierbare Web-App. Nur Standardbibliothek.

Einmalig ausführen, wenn sich das Icon ändern soll:  python tools/icons.py
"""
import struct
import zlib
from pathlib import Path

ZIEL = Path(__file__).resolve().parent.parent / "assets"
HINTERGRUND = (0x00, 0x6C, 0x4C)
BLITZ = (0xFF, 0xC9, 0x4A)
# Blitz im 24er-Raster (gleiche Form wie assets/icon.svg)
BLITZ_PUNKTE = [(13, 2), (4, 14), (11, 14), (10, 22), (19, 10), (12, 10)]
UNTERPROBEN = 3


def im_polygon(x, y, pts):
    drin = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            drin = not drin
        j = i
    return drin


def im_abgerundeten_quadrat(x, y, groesse, radius):
    if radius <= 0:
        return 0 <= x < groesse and 0 <= y < groesse
    cx = min(max(x, radius), groesse - radius)
    cy = min(max(y, radius), groesse - radius)
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2


def male(groesse, blitz_anteil, radius_anteil):
    """RGBA-Pixel: Hintergrund (abgerundet oder vollflächig) mit zentriertem Blitz."""
    skala = groesse * blitz_anteil / 20  # Blitz ist 20 Einheiten hoch (2..22)
    versatz_x = groesse / 2 - 11.5 * skala
    versatz_y = groesse / 2 - 12 * skala
    pts = [(versatz_x + px * skala, versatz_y + py * skala) for px, py in BLITZ_PUNKTE]
    min_x, max_x = min(p[0] for p in pts), max(p[0] for p in pts)
    min_y, max_y = min(p[1] for p in pts), max(p[1] for p in pts)
    radius = groesse * radius_anteil
    n = UNTERPROBEN
    zeilen = []
    for py in range(groesse):
        zeile = bytearray([0])
        for px in range(groesse):
            bg = bz = 0
            for sy in range(n):
                y = py + (sy + 0.5) / n
                for sx in range(n):
                    x = px + (sx + 0.5) / n
                    if im_abgerundeten_quadrat(x, y, groesse, radius):
                        bg += 1
                        if min_x <= x <= max_x and min_y <= y <= max_y and im_polygon(x, y, pts):
                            bz += 1
            gesamt = n * n
            if bg == 0:
                zeile += b"\x00\x00\x00\x00"
                continue
            anteil = bz / bg
            farbe = [round(HINTERGRUND[k] * (1 - anteil) + BLITZ[k] * anteil) for k in range(3)]
            zeile += bytes(farbe + [round(255 * bg / gesamt)])
        zeilen.append(bytes(zeile))
    return b"".join(zeilen)


def png(pfad, groesse, daten):
    def block(typ, inhalt):
        return struct.pack(">I", len(inhalt)) + typ + inhalt + struct.pack(">I", zlib.crc32(typ + inhalt) & 0xFFFFFFFF)
    kopf = struct.pack(">IIBBBBB", groesse, groesse, 8, 6, 0, 0, 0)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n" + block(b"IHDR", kopf) + block(b"IDAT", zlib.compress(daten, 9)) + block(b"IEND", b""))


def main():
    auftraege = [
        ("icon-192.png", 192, 0.62, 0.22),
        ("icon-512.png", 512, 0.62, 0.22),
        ("icon-maskable-512.png", 512, 0.46, 0),   # vollflächig, Blitz in der sicheren Zone
        ("apple-touch-icon.png", 180, 0.6, 0),
    ]
    for name, groesse, blitz, radius in auftraege:
        png(ZIEL / name, groesse, male(groesse, blitz, radius))
        print("geschrieben:", name)


if __name__ == "__main__":
    main()
