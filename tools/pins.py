#!/usr/bin/env python3
"""Erzeugt Pinterest-Pins (1000 x 1500) nach werbung/pins/: je ein Spartipp mit echten Zahlen der Seite und Link dorthin.

Gleiches Verfahren wie tools/og_bild.py: HTML aus den eigenen Illustrationen (bilder.py), fotografiert von
Microsoft Edge im Headless-Modus. Titel, Beschreibung und Ziel-Link jedes Pins stehen in werbung/pins/pins.txt.
Aufruf: python tools/pins.py
"""
import base64
import json
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import bilder  # noqa: E402
import build  # noqa: E402
from og_bild import EDGE  # noqa: E402

ADRESSE = "https://parazki.github.io"
PREIS = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["strompreis_eur_kwh"]


def bild(key):
    return "data:image/svg+xml;base64," + base64.b64encode(bilder.BILDER[key]().encode("utf-8")).decode("ascii")


def ct(x):
    return f"{x:.1f}".replace(".", ",").removesuffix(",0")


def geraete():
    return {g["slug"]: g for g in json.loads((ROOT / "data" / "geraete.json").read_text(encoding="utf-8"))}


def euro_jahr(g):
    return round(build.jahresverbrauch_kwh(g) * PREIS)


STIL = """
html, body { margin: 0; width: 1000px; height: 1500px; overflow: hidden; }
body { font-family: "Segoe UI Variable Display", "Segoe UI", system-ui, sans-serif; letter-spacing: -.02em; color: #1d1d1f;
       background: radial-gradient(1100px 700px at 50% 108%, var(--hauch), transparent 70%), #f5f5f7; position: relative; }
.kopf { position: absolute; top: 64px; left: 0; right: 0; display: flex; justify-content: center; align-items: center; gap: 16px; font-size: 36px; font-weight: 600; }
.kopf img { width: 60px; height: 60px; border-radius: 16px; }
.kopf span { color: #6e6e73; font-weight: 500; }
h1 { position: absolute; top: 170px; left: 70px; right: 70px; margin: 0; text-align: center; font-size: 92px; line-height: 1.03; font-weight: 700; letter-spacing: -.045em; }
h1 b { font-weight: 700; background: linear-gradient(90deg, var(--a), var(--b)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.unter { position: absolute; left: 90px; right: 90px; margin: 0; text-align: center; font-size: 36px; line-height: 1.3; color: #6e6e73; }
.fuss { position: absolute; left: 0; right: 0; bottom: 70px; display: flex; flex-direction: column; align-items: center; gap: 18px; }
.knopf { background: #0071e3; color: #fff; font-size: 34px; font-weight: 600; padding: 22px 46px; border-radius: 999px; }
.url { font-size: 28px; color: #6e6e73; font-weight: 500; }
.notiz { position: absolute; left: 0; right: 0; bottom: 250px; text-align: center; font-size: 22px; color: #86868b; }
.karte { background: #fff; border-radius: 40px; box-shadow: 0 24px 60px rgba(0,0,0,.08); }
"""


def seite(inhalt, knopf, hauch="#e3f5e8", a="#248a3d", b="#ff9f0a"):
    logo = (ROOT / "assets" / "icon.svg").read_text(encoding="utf-8")
    logo_url = "data:image/svg+xml;base64," + base64.b64encode(logo.encode("utf-8")).decode("ascii")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{STIL}
body {{ --hauch: {hauch}; --a: {a}; --b: {b}; }}</style></head><body>
<div class="kopf"><img src="{logo_url}"><b>Stromfresser<span>-Check</span></b></div>
{inhalt}
<div class="fuss"><div class="knopf">{knopf} →</div><div class="url">parazki.github.io</div></div>
</body></html>"""


def pin_heizen(g):
    lufter, decke = g["heizluefter"], g["heizdecke"]
    pro_h = [w["leistung_w"] / 1000 * PREIS * 100 for w in (lufter, decke)]
    faktor = round(pro_h[0] / pro_h[1])
    karte = lambda key, name, watt, preis, farbe: f"""<div class="karte" style="width:390px;padding:44px 0 50px;text-align:center">
<img src="{bild(key)}" style="width:250px;height:250px"><div style="font-size:38px;font-weight:600;margin-top:8px">{name}</div>
<div style="font-size:26px;color:#86868b;margin-top:4px">{watt} Watt</div>
<div style="font-size:120px;font-weight:700;letter-spacing:-.05em;line-height:1;margin-top:34px;color:{farbe}">{preis}<span style="font-size:52px"> ct</span></div>
<div style="font-size:30px;color:#6e6e73;margin-top:8px">pro Stunde</div></div>"""
    inhalt = f"""<h1>Heizlüfter oder<br><b>Heizdecke?</b></h1>
<div style="position:absolute;top:440px;left:0;right:0;display:flex;justify-content:center;gap:40px">
{karte("heizluefter", "Heizlüfter", "2.000", ct(round(pro_h[0])), "#d70015")}{karte("heizdecke", "Heizdecke", "60", ct(round(pro_h[1], 1)), "#248a3d")}</div>
<p class="unter" style="top:1105px">Die Heizdecke wärmt dich – nicht den ganzen Raum. Rund {faktor}-mal günstiger.</p>
<div class="notiz">Bei {ct(PREIS * 100)} ct/kWh</div>"""
    return dict(datei="heizluefter-oder-heizdecke", html=seite(inhalt, "Eigene Kosten berechnen", "#fde8d8", "#ff6a00", "#d70015"),
                link=f"{ADRESSE}/geraet/heizluefter/",
                titel=f"Heizlüfter oder Heizdecke? {ct(round(pro_h[0]))} ct gegen {ct(round(pro_h[1], 1))} ct pro Stunde",
                text=(f"Ein Heizlüfter zieht rund 2.000 Watt und kostet bei {ct(PREIS * 100)} ct/kWh etwa {ct(round(pro_h[0]))} Cent pro Stunde. "
                      f"Eine Heizdecke mit 60 Watt kostet nur rund {ct(round(pro_h[1], 1))} Cent – sie wärmt dich direkt statt den ganzen Raum. "
                      "Mit dem kostenlosen Rechner siehst du die Kosten für deine eigene Nutzung. #stromsparen #heizkosten #energiesparen"))


def pin_standby(g):
    jahr_watt = 8.76 * PREIS
    reihe = "".join(f'<img src="{bild(k)}" style="width:170px;height:170px">' for k in ["fernseher", "receiver", "spielkonsole", "drucker", "soundbar"])
    inhalt = f"""<h1>Standby kostet<br><b>mehr, als du denkst.</b></h1>
<div class="karte" style="position:absolute;top:450px;left:110px;right:110px;padding:56px 0 50px;text-align:center">
<div style="font-size:34px;color:#6e6e73">1 Watt rund um die Uhr</div>
<div style="font-size:200px;font-weight:700;letter-spacing:-.06em;line-height:1;margin-top:18px;color:#bf4800">{f"{jahr_watt:.2f}".replace(".", ",")} €</div>
<div style="font-size:34px;color:#6e6e73;margin-top:12px">im Jahr – für nichts</div></div>
<div style="position:absolute;top:900px;left:0;right:0;display:flex;justify-content:center;gap:4px">{reihe}</div>
<p class="unter" style="top:1095px">10 Geräte mit je 2 Watt Standby kosten so über {round(20 * jahr_watt / 10) * 10} € im Jahr.</p>
<div class="notiz">Bei {ct(PREIS * 100)} ct/kWh · 8,76 kWh je Watt und Jahr</div>"""
    return dict(datei="standby-kosten", html=seite(inhalt, "Standby-Rechner öffnen", "#fdebd3", "#ff9f0a", "#bf4800"),
                link=f"{ADRESSE}/werkzeuge/standby/",
                titel=f"Standby kostet mehr, als du denkst: 1 Watt = {f'{jahr_watt:.2f}'.replace('.', ',')} € im Jahr",
                text=(f"Jedes Watt Dauerverbrauch sind 8,76 kWh im Jahr – bei {ct(PREIS * 100)} ct/kWh rund {f'{jahr_watt:.2f}'.replace('.', ',')} €. "
                      "Fernseher, Receiver, Konsole, Drucker und Soundbar ziehen oft rund um die Uhr Strom. "
                      "Der kostenlose Standby-Rechner zeigt, was deine Geräte im Jahr kosten. #stromsparen #standby #haushaltstipps"))


def pin_top5(g):
    top = sorted((x for x in g.values() if x["slug"] != "elektroauto"), key=lambda x: -build.jahresverbrauch_kwh(x))[:5]
    hoechst = euro_jahr(top[0])
    zeilen = "".join(f"""<div style="display:flex;align-items:center;gap:26px;padding:14px 40px">
<img src="{bild(x['slug'])}" style="width:100px;height:100px;flex:none">
<div style="flex:1"><div style="display:flex;justify-content:space-between;align-items:baseline">
<span style="font-size:38px;font-weight:600">{x['name']}</span><span style="font-size:42px;font-weight:700;color:#d70015">{euro_jahr(x)} €</span></div>
<div style="height:14px;border-radius:7px;background:#f2f2f4;margin-top:14px"><div style="height:14px;border-radius:7px;width:{euro_jahr(x) / hoechst * 100:.0f}%;background:linear-gradient(90deg,#ff9f0a,#d70015)"></div></div></div></div>"""
                     for x in top)
    inhalt = f"""<h1>Die 5 größten<br><b>Stromfresser</b></h1>
<p class="unter" style="top:385px">Was sie typisch im Jahr kosten</p>
<div class="karte" style="position:absolute;top:470px;left:70px;right:70px;padding:18px 0">{zeilen}</div>
<div class="notiz">Typische Nutzung · {ct(PREIS * 100)} ct/kWh · ohne E-Auto</div>"""
    liste = ", ".join(f"{x['name']} ({euro_jahr(x)} €)" for x in top)
    return dict(datei="groesste-stromfresser", html=seite(inhalt, "Alle 52 Geräte ansehen", "#fde2e2", "#ff6a00", "#d70015"),
                link=f"{ADRESSE}/geraete/",
                titel="Die 5 größten Stromfresser im Haushalt – und was sie im Jahr kosten",
                text=(f"Bei typischer Nutzung und {ct(PREIS * 100)} ct/kWh: {liste}. "
                      "Für 52 Haushaltsgeräte kannst du die Kosten mit deinen eigenen Werten kostenlos nachrechnen. #stromsparen #stromkosten #haushalt"))


def pin_tipps(g):
    tipps = [("waschmaschine", "Mit 30 °C statt 60 °C waschen"), ("topf", "Beim Kochen immer mit Deckel"),
             ("kuehlschrank", "Kühlschrank auf 7 °C stellen"), ("wasserkocher", "Nur so viel Wasser kochen wie nötig"),
             ("leiste", "TV & Konsole ganz ausschalten"), ("led-lampe", "Glühbirnen durch LEDs ersetzen"),
             ("heizdecke", "Heizdecke statt Heizlüfter")]
    zeilen = "".join(f"""<div style="display:flex;align-items:center;gap:26px;padding:8px 40px">
<img src="{bild(k)}" style="width:82px;height:82px;flex:none"><span style="font-size:36px;font-weight:600;line-height:1.2">{t}</span></div>"""
                     for k, t in tipps)
    inhalt = f"""<h1>7 Spartipps,<br><b>die sofort wirken.</b></h1>
<div class="karte" style="position:absolute;top:420px;left:80px;right:80px;padding:20px 0">{zeilen}</div>
<div class="notiz">Ohne Kauf, ohne Umbau – und 23 weitere Tipps auf der Seite</div>"""
    return dict(datei="7-spartipps", html=seite(inhalt, "Alle 30 Tipps lesen"),
                link=f"{ADRESSE}/wissen/strom-sparen/",
                titel="7 Strom-Spartipps, die sofort wirken (ohne Kauf, ohne Umbau)",
                text=("Mit 30 °C statt 60 °C waschen spart mehr als die Hälfte der Energie. Dazu: Deckel auf den Topf, Kühlschrank auf 7 °C, "
                      "nur so viel Wasser kochen wie nötig, Standby ganz aus, LEDs statt Glühbirnen und Heizdecke statt Heizlüfter. "
                      "Alle 30 Tipps für Küche, Wäsche, Technik, Licht und Heizen. #stromsparen #spartipps #haushaltstipps"))


def pin_balkon(g):
    ertrag, ersparnis, jahre = build.bkw_rechnung()
    wert = lambda zahl, text: f"""<div class="karte" style="flex:1;padding:28px 0;text-align:center">
<div style="font-size:64px;font-weight:700;letter-spacing:-.04em">{zahl}</div><div style="font-size:28px;color:#6e6e73;margin-top:4px">{text}</div></div>"""
    inhalt = f"""<h1>Lohnt sich ein<br><b>Balkonkraftwerk?</b></h1>
<img src="{bild("balkonkraftwerk")}" style="position:absolute;top:385px;left:305px;width:390px;height:390px;filter:drop-shadow(0 24px 30px rgba(0,0,0,.12))">
<div style="position:absolute;top:790px;left:90px;right:90px;text-align:center">
<div style="font-size:34px;color:#6e6e73">bezahlt nach etwa</div>
<div style="font-size:150px;font-weight:700;letter-spacing:-.05em;line-height:1.05;color:#248a3d">{ct(round(jahre, 1))} Jahren</div></div>
<div style="position:absolute;top:1015px;left:90px;right:90px;display:flex;gap:28px">{wert(f"{round(ertrag)} kWh", "Ertrag pro Jahr")}{wert(f"{round(ersparnis)} €", "gespart pro Jahr")}</div>
<div class="notiz">Beispiel: 900 W Module, Süd, 40 % Eigenverbrauch, 400 € Kaufpreis</div>"""
    return dict(datei="balkonkraftwerk-lohnt-sich", html=seite(inhalt, "Mit eigenen Werten rechnen", "#fff4c2", "#248a3d", "#ffb800"),
                link=f"{ADRESSE}/balkonkraftwerk/",
                titel=f"Lohnt sich ein Balkonkraftwerk? Im Beispiel nach {ct(round(jahre, 1))} Jahren bezahlt",
                text=(f"900 W Module nach Süden erzeugen rund {round(ertrag)} kWh im Jahr. Bei 40 % Eigenverbrauch und {ct(PREIS * 100)} ct/kWh "
                      f"sparst du etwa {round(ersparnis)} € pro Jahr – ein Gerät für 400 € ist nach rund {ct(round(jahre, 1))} Jahren bezahlt. "
                      "Mit dem kostenlosen Rechner trägst du Ausrichtung, Region und Eigenverbrauch selbst ein. #balkonkraftwerk #solar #stromsparen"))


def pin_spar_check(g):
    schritte = [("1", "8 kurze Fragen", "zu Haushalt, Geräten und Gewohnheiten"),
                ("2", "Dein Sparplan", "mit Euro-Betrag für jede Maßnahme"),
                ("3", "Sofort loslegen", "die größten Hebel stehen ganz oben")]
    zeilen = "".join(f"""<div style="display:flex;align-items:center;gap:30px;padding:26px 46px">
<div style="width:92px;height:92px;flex:none;border-radius:50%;background:linear-gradient(135deg,#30c158,#248a3d);color:#fff;font-size:48px;font-weight:700;display:flex;align-items:center;justify-content:center">{n}</div>
<div><div style="font-size:42px;font-weight:700">{t}</div><div style="font-size:30px;color:#6e6e73;margin-top:2px">{u}</div></div></div>"""
                     for n, t, u in schritte)
    reihe = "".join(f'<img src="{bild(k)}" style="width:150px;height:150px">' for k in ["kuehlschrank", "waschmaschine", "fernseher", "wasserkocher", "led-lampe"])
    inhalt = f"""<h1>Dein Strom-Sparplan<br><b>in 60 Sekunden.</b></h1>
<div class="karte" style="position:absolute;top:440px;left:80px;right:80px;padding:22px 0">{zeilen}</div>
<div style="position:absolute;top:1010px;left:0;right:0;display:flex;justify-content:center;gap:10px">{reihe}</div>
<div class="notiz">Kostenlos · ohne Anmeldung · ohne E-Mail</div>"""
    return dict(datei="spar-check", html=seite(inhalt, "Spar-Check starten"),
                link=f"{ADRESSE}/werkzeuge/spar-check/",
                titel="Dein persönlicher Strom-Sparplan in 60 Sekunden – kostenlos",
                text=("Beantworte 8 kurze Fragen zu deinem Haushalt und erhalte einen Sparplan mit Euro-Beträgen für jede Maßnahme – "
                      "die größten Hebel stehen ganz oben. Kostenlos und ohne Anmeldung. #stromsparen #stromkosten #energiesparen"))


PINS = [pin_heizen, pin_standby, pin_top5, pin_tipps, pin_balkon, pin_spar_check]


def main():
    edge = next((p for p in EDGE if p.exists()), None)
    if not edge:
        raise SystemExit("Microsoft Edge nicht gefunden.")
    ziel = ROOT / "werbung" / "pins"
    ziel.mkdir(parents=True, exist_ok=True)
    g = geraete()
    texte = []
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for i, baue in enumerate(PINS, 1):
            pin = baue(g)
            seite_html = Path(tmp) / f"{pin['datei']}.html"
            seite_html.write_text(pin["html"], encoding="utf-8")
            png = ziel / f"{i}-{pin['datei']}.png"
            subprocess.run([str(edge), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            "--window-size=1000,1500", f"--user-data-dir={Path(tmp) / 'profil'}", f"--screenshot={png}",
                            seite_html.as_uri()], check=True, capture_output=True, timeout=120)
            # Edge kehrt teils zurück, bevor das Bild geschrieben ist
            for _ in range(60):
                if png.exists() and png.stat().st_size > 0:
                    break
                time.sleep(.5)
            else:
                raise SystemExit(f"Kein Bild von Edge: {png.name}")
            time.sleep(.5)
            breite, hoehe = struct.unpack(">II", png.read_bytes()[16:24])
            print(f"geschrieben: {png.name} ({breite} x {hoehe}, {png.stat().st_size // 1024} KB)")
            texte.append(f"{png.name}\nTitel: {pin['titel']}\nLink: {pin['link']}\nBeschreibung: {pin['text']}\n")
    (ziel / "pins.txt").write_text("\n".join(texte), encoding="utf-8")


if __name__ == "__main__":
    main()
