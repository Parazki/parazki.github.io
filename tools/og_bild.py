#!/usr/bin/env python3
"""Erzeugt assets/og-bild.png (1200 x 630): das Vorschaubild für Google, WhatsApp, Facebook & Co.

Baut eine HTML-Seite aus den eigenen Illustrationen (bilder.py) und lässt sie von Microsoft Edge
im Headless-Modus fotografieren. Nur bei Design-Änderungen nötig – das PNG liegt fertig in assets/.
Aufruf: python tools/og_bild.py
"""
import base64
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import bilder  # noqa: E402

EDGE = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")]


def daten_url(key):
    return "data:image/svg+xml;base64," + base64.b64encode(bilder.BILDER[key]().encode("utf-8")).decode("ascii")


def html():
    logo = (ROOT / "assets" / "icon.svg").read_text(encoding="utf-8")
    logo_url = "data:image/svg+xml;base64," + base64.b64encode(logo.encode("utf-8")).decode("ascii")
    geraete = "".join(f'<img src="{daten_url(k)}" style="--i:{i}">' for i, k in
                      enumerate(["kuehlschrank", "fernseher", "heizluefter", "waschmaschine", "led"]))
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{ font-family: "Segoe UI Variable Display", "Segoe UI", system-ui, sans-serif; letter-spacing: -.02em; color: #1d1d1f;
       background: radial-gradient(900px 420px at 50% 120%, #e3f5e8, transparent 70%), #f5f5f7; position: relative; }}
.kopf {{ position: absolute; top: 58px; left: 0; right: 0; display: flex; justify-content: center; align-items: center; gap: 16px; font-size: 34px; font-weight: 600; }}
.kopf img {{ width: 58px; height: 58px; border-radius: 15px; }}
.kopf b {{ font-weight: 600; }}
.kopf span {{ color: #6e6e73; font-weight: 500; }}
h1 {{ position: absolute; top: 150px; left: 0; right: 0; margin: 0; text-align: center; font-size: 76px; line-height: 1.04; font-weight: 700; letter-spacing: -.045em; }}
h1 b {{ font-weight: 700; background: linear-gradient(90deg, #248a3d, #30c158 45%, #ff9f0a); -webkit-background-clip: text; background-clip: text; color: transparent; }}
p {{ position: absolute; top: 330px; left: 0; right: 0; margin: 0; text-align: center; font-size: 30px; color: #6e6e73; }}
.reihe {{ position: absolute; left: 0; right: 0; bottom: -24px; display: flex; justify-content: center; align-items: flex-end; gap: 6px; }}
.reihe img {{ width: 196px; height: 196px; filter: drop-shadow(0 18px 18px rgba(0,0,0,.12)); }}
.reihe img:nth-child(3) {{ width: 230px; height: 230px; }}
</style></head><body>
<div class="kopf"><img src="{logo_url}"><b>Stromfresser<span>-Check</span></b></div>
<h1>Finde die Stromfresser<br><b>in deinem Zuhause.</b></h1>
<p>Stromkosten für 52 Geräte berechnen – kostenlos und ohne Anmeldung.</p>
<div class="reihe">{geraete}</div>
</body></html>"""


def main():
    edge = next((p for p in EDGE if p.exists()), None)
    if not edge:
        raise SystemExit("Microsoft Edge nicht gefunden.")
    ziel = ROOT / "assets" / "og-bild.png"
    with tempfile.TemporaryDirectory() as tmp:
        seite = Path(tmp) / "og.html"
        seite.write_text(html(), encoding="utf-8")
        subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=1200,630", f"--user-data-dir={Path(tmp) / 'profil'}", f"--screenshot={ziel}",
                        seite.as_uri()], check=True, capture_output=True, timeout=120)
    breite, hoehe = struct.unpack(">II", ziel.read_bytes()[16:24])
    print(f"geschrieben: {ziel.name} ({breite} x {hoehe}, {ziel.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
