#!/usr/bin/env python3
"""Baut die statische Website "Stromfresser-Check" nach dist/.

Material-You-Design, als App installierbar (PWA, offline nutzbar).
Nur Python-Standardbibliothek, keine API, kein Server. Aufruf:
    python build.py            # lokale Vorschau (Platzhalter erlaubt)
    python build.py --strict   # Veröffentlichung: bricht ab, wenn das Impressum fehlt
"""
import argparse
import datetime
import hashlib
import html
import json
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus

from wissen import ARTIKEL, LEXIKON

ROOT = Path(__file__).resolve().parent
PLATZHALTER = "BITTE_AUSFUELLEN"
STUNDEN_JAHR = 8760
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]
KATEGORIEN = ["Küche", "Haushalt", "Heizen & Kühlen", "Unterhaltung", "Büro & Technik", "Licht", "Sonstiges"]
KATEGORIE_EMOJI = {"Küche": "🍳", "Haushalt": "🧺", "Heizen & Kühlen": "🌡️", "Unterhaltung": "🎮",
                   "Büro & Technik": "💻", "Licht": "💡", "Sonstiges": "✨"}
# Grobe Richtwerte Jahresverbrauch nach Personen (ohne Warmwasser über Strom), auch in assets/app.js genutzt
HAUSHALT_SCHNITT = {1: 1500, 2: 2500, 3: 3200, 4: 3800, 5: 4500}
REFERENZ_KWH = HAUSHALT_SCHNITT[2]
HAUSHALT_VORLAGE = [("kuehlschrank", 1), ("waschmaschine", 1), ("geschirrspueler", 1), ("elektroherd", 1),
                    ("backofen", 1), ("wasserkocher", 1), ("fernseher", 1), ("wlan-router", 1),
                    ("laptop", 1), ("smartphone", 2), ("led-lampe", 8)]
# Typische Verteilung des Solarertrags über das Jahr in Deutschland (Prozent, Summe 100)
SOLAR_MONATE = [3, 4.5, 8, 11, 13, 13.5, 13.5, 12, 9, 6.5, 3.5, 2.5]
FAVORITEN = ["kuehlschrank", "heizluefter", "spielkonsole", "durchlauferhitzer", "fernseher", "waschmaschine"]


# ---------------------------------------------------------------- Rechnen

def nutzungsstunden(g):
    return min(g["stunden"] * g["nutzungen_woche"] * g.get("wochen_jahr", 52), STUNDEN_JAHR)


def jahresverbrauch_kwh(g):
    """Gleiche Formel wie in assets/app.js (kwhJahr)."""
    h = nutzungsstunden(g)
    standby = g.get("standby_w", 0) or 0
    return (g["leistung_w"] * h + standby * (STUNDEN_JAHR - h)) / 1000


def standby_kwh(g):
    standby = g.get("standby_w", 0) or 0
    return standby * (STUNDEN_JAHR - nutzungsstunden(g)) / 1000


def zahl(x, stellen=0):
    """Deutsche Zahlenformatierung: 1.234,5"""
    s = f"{x:,.{stellen}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def euro(x):
    return zahl(x, 2) + " €" if x < 100 else zahl(x, 0) + " €"


def dauer(stunden):
    if stunden < 1:
        return f"{round(stunden * 60)} min"
    return zahl(stunden, 1 if stunden % 1 else 0) + " h"


def bkw_rechnung(modul=900, wr=800, region=950, ausrichtung=1.0, montage=1.0, eigen=40, preis=0.35, kosten=400):
    """Gleiche Formel wie in assets/app.js (rechneBkw)."""
    kwp = min(modul, wr * 1.15) / 1000
    ertrag = kwp * region * ausrichtung * montage
    ersparnis = ertrag * min(eigen, 100) / 100 * preis
    return ertrag, ersparnis, (kosten / ersparnis if ersparnis > 0 else 0)


# ---------------------------------------------------------------- Konfiguration

def basis_url(cfg):
    url = (cfg.get("base_url") or "auto").strip()
    if url != "auto":
        return url.rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        owner = owner.lower()
        if name.lower() == f"{owner}.github.io":
            return f"https://{owner}.github.io"
        return f"https://{owner}.github.io/{name}"
    return "http://localhost:8000"


def fehlende_pflichtangaben(cfg):
    imp = cfg.get("impressum", {})
    return [k for k in ("name", "strasse", "plz_ort", "email") if not imp.get(k) or PLATZHALTER in imp.get(k, "")]


# ---------------------------------------------------------------- Icons (eigene Strich-Icons, 24er-Raster)

ICONS = {
    "home": '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',
    "grid": '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/>'
            '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    "pie": '<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
    "quiz": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .8-1 1.5v.6"/><path d="M12 17h.01"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    "tune": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "share": '<circle cx="17.5" cy="5.5" r="2.5"/><circle cx="6.5" cy="12" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/><path d="m8.7 10.7 6.6-3.9M8.7 13.3l6.6 3.9"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.5 1.1 1.3 1.1 2.2h5c0-.9.4-1.7 1.1-2.2A6 6 0 0 0 12 3z"/>',
    "cart": '<path d="M3 4h2.2l2.3 11h10.3L20 8H6.4"/><circle cx="9" cy="19.5" r="1.4"/><circle cx="17" cy="19.5" r="1.4"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
    "bolt": '<path fill="currentColor" stroke="none" d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>',
    "book": '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v14H6.5A1.5 1.5 0 0 0 5 18.5zM5 18.5A1.5 1.5 0 0 0 6.5 20H19v-3"/><path d="M9 7h6"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.1-.4-.4-2.1z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
          + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
          + "</defs></svg>")


def icon(name, cls="ic"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


NAV = [("start", "", "Start", "home"), ("geraete", "geraete/", "Geräte", "grid"),
       ("haushalt", "haushalt/", "Haushalt", "pie"), ("wissen", "wissen/", "Wissen", "book"),
       ("werkzeuge", "werkzeuge/", "Tools", "wrench")]

# Typische Standby-Werte (Watt) und Startanzahl für den Standby-Rechner
STANDBY_GERAETE = [
    ("tv", "📺", "Fernseher", 0.5, 1), ("receiver", "📡", "Receiver / Set-Top-Box", 3, 1),
    ("soundbar", "🔊", "Soundbar", 2, 0), ("konsole", "🎮", "Spielkonsole (Ruhemodus)", 3, 0),
    ("speaker", "🗣️", "Smart Speaker", 2, 1), ("repeater", "📶", "WLAN-Repeater", 3, 0),
    ("drucker", "🖨️", "Drucker", 3, 1), ("mikrowelle", "🍲", "Mikrowelle mit Uhr", 1.5, 1),
    ("kaffee", "☕", "Kaffeemaschine", 1, 1), ("pc", "🖥️", "PC (ausgeschaltet)", 1, 1),
    ("monitor", "🖱️", "Monitor", 0.3, 1), ("ladegeraet", "🔌", "Ladegerät ohne Gerät", 0.3, 3),
    ("zahnbuerste", "🪥", "Zahnbürsten-Ladestation", 1, 1), ("boiler", "🚰", "Untertischboiler", 12, 0),
]
# Vorlagen für den Austausch-Rechner: alt kWh/Jahr, neu kWh/Jahr, Anschaffung €
AUSTAUSCH_VORLAGEN = [
    ("kuehlschrank", "🧊", "Kühlschrank", 300, 150, 500), ("gefrierschrank", "❄️", "Gefrierschrank", 400, 200, 500),
    ("trockner", "🌀", "Trockner", 610, 234, 650), ("licht", "💡", "10 Lampen → LED", 874, 117, 40),
    ("fernseher", "📺", "Fernseher", 438, 131, 600), ("waschmaschine", "🫧", "Waschmaschine", 260, 160, 550),
]


# ---------------------------------------------------------------- HTML-Bausteine

e = html.escape


def gross(s):
    return s[:1].upper() + s[1:]


class Seite:
    def __init__(self, ctx, pfad):
        """pfad: Unterordner relativ zur Website-Wurzel, z. B. '' oder 'geraet/kuehlschrank/'."""
        self.ctx = ctx
        self.pfad = pfad
        tiefe = pfad.count("/")
        self.wurzel = "../" * tiefe if tiefe else "./"

    def link(self, ziel):
        return self.wurzel + ziel

    @property
    def kanonisch(self):
        return f"{self.ctx['base']}/{self.pfad}"


def amazon_link(ctx, query):
    url = "https://www.amazon.de/s?k=" + quote_plus(query)
    if ctx["tag"]:
        url += "&tag=" + quote_plus(ctx["tag"])
    return url


def produkt_karte(ctx, label, text, query, emoji="🛒"):
    stern = "*" if ctx["tag"] else ""
    rel = "sponsored nofollow noopener" if ctx["tag"] else "nofollow noopener"
    return f"""
<aside class="produkt karte-outline">
  <span class="produkt-emoji" aria-hidden="true">{emoji}</span>
  <div class="produkt-text">
    <h3>{e(label)}</h3>
    <p>{e(text)}</p>
  </div>
  <a class="knopf knopf-tonal ripple" href="{e(amazon_link(ctx, query))}" rel="{rel}" target="_blank">{icon('cart')}Bei Amazon ansehen{stern}</a>
</aside>"""


def messgeraet_karte(ctx):
    return produkt_karte(ctx, "Echten Verbrauch messen statt schätzen",
                         "Ein Strommessgerät für die Steckdose zeigt Watt und kWh deines Geräts direkt an – "
                         "einfache Modelle kosten oft unter 20 €.",
                         "Strommessgerät Steckdose", "🔌")


def faq_html(fragen):
    teile = "".join(f'<details class="faq-eintrag"><summary>{e(f)}{icon("chevron", "ic faq-pfeil")}</summary><p>{e(a)}</p></details>'
                    for f, a in fragen)
    return f'<section class="abschnitt"><h2>Häufige Fragen</h2><div class="faq">{teile}</div></section>'


def faq_jsonld(fragen):
    daten = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for f, a in fragen],
    }
    return '<script type="application/ld+json">' + json.dumps(daten, ensure_ascii=False) + "</script>"


def euro_kwh(kwh, teiler=1, cls=""):
    """Betrag, den app.js mit dem eigenen Strompreis des Besuchers neu berechnet."""
    t = f' data-teiler="{teiler}"' if teiler != 1 else ""
    c = f' class="{cls}"' if cls else ""
    return f'<span{c} data-euro-kwh="{kwh:.3f}"{t}>{euro(kwh * PREIS_STANDARD[0] / teiler)}</span>'


PREIS_STANDARD = [0.35]  # wird in baue() aus config.json gesetzt


def geraet_karte(s, g):
    kwh = jahresverbrauch_kwh(g)
    return f"""<a class="geraet-karte ripple" href="{s.link('geraet/' + g['slug'] + '/')}" data-name="{e(g['name'].lower())}" data-kat="{e(g['kategorie'])}" data-kwh="{kwh:.3f}">
  <span class="emoji-kreis" aria-hidden="true">{g['emoji']}</span>
  <span class="gk-text"><strong>{e(gross(g['name']))}</strong><small>{zahl(kwh)} kWh / Jahr</small></span>
  <span class="gk-preis">{euro_kwh(kwh)}<small>/ Jahr</small></span>
</a>"""


def rangliste(s, geraete, markiert=None, anzahl=None):
    """Balkenliste nach Jahreskosten; markiert = slug, der hervorgehoben wird."""
    sortiert = sorted(geraete, key=jahresverbrauch_kwh, reverse=True)[:anzahl]
    hoechst = jahresverbrauch_kwh(sortiert[0]) if sortiert else 1
    zeilen = []
    for i, g in enumerate(sortiert, 1):
        kwh = jahresverbrauch_kwh(g)
        breite = max(2, round(kwh / hoechst * 100))
        klasse = " aktiv" if g["slug"] == markiert else ""
        zeilen.append(f"""<li style="--i:{i}"><a class="rang-zeile ripple{klasse}" href="{s.link('geraet/' + g['slug'] + '/')}">
  <span class="rang-nr">{i}</span><span class="rang-emoji" aria-hidden="true">{g['emoji']}</span>
  <span class="rang-mitte"><span class="rang-name">{e(gross(g['name']))}</span><span class="rang-balken"><span style="width:{breite}%"></span></span></span>
  <span class="rang-preis">{euro_kwh(kwh)}</span></a></li>""")
    return f'<ol class="rangliste">{"".join(zeilen)}</ol>'


def layout(seite, titel, beschreibung, inhalt, aktiv="", extra_head="", index=True, fab="", kopf_aktion=""):
    ctx = seite.ctx
    w = seite.wurzel
    v = ctx["version"]
    meta = []
    if ctx["verification"]:
        meta.append(f'<meta name="google-site-verification" content="{e(ctx["verification"])}">')
    if ctx["umami_id"]:
        domain = ctx["base"].split("://", 1)[-1].split("/", 1)[0]
        meta.append(f'<script defer src="{e(ctx["umami_script"])}" data-website-id="{e(ctx["umami_id"])}" data-domains="{e(domain)}"></script>')
    if ctx["adsense"]:
        meta.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={e(ctx["adsense"])}" crossorigin="anonymous"></script>')
    if not index:
        meta.append('<meta name="robots" content="noindex">')
    entwurf = ""
    if ctx["fehlend"]:
        entwurf = '<div class="entwurf">ENTWURF – Impressum in config.json noch nicht ausgefüllt. Nicht veröffentlichen.</div>'
    partner = ""
    if ctx["tag"]:
        partner = "<p>* Affiliate-Link: Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Für dich ändert sich der Preis nicht.</p>"
    aktuell = ' aria-current="page"'
    nav = "".join(
        f'<a class="nav-item" href="{w}{href}"{aktuell if key == aktiv else ""}>'
        f'<span class="nav-pille">{icon(ic)}</span><span class="nav-label">{label}</span></a>'
        for key, href, label, ic in NAV)
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titel)}</title>
<meta name="description" content="{e(beschreibung)}">
<link rel="canonical" href="{e(seite.kanonisch)}">
<meta property="og:title" content="{e(titel)}">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(seite.kanonisch)}">
<meta property="og:image" content="{e(ctx['base'])}/assets/icon-512.png">
<meta name="theme-color" content="#F5FBF5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1512" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="{w}manifest.webmanifest">
<link rel="icon" href="{w}assets/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{w}assets/apple-touch-icon.png">
<script>document.documentElement.classList.add("js")</script>
<link rel="stylesheet" href="{w}assets/style.css?v={v}">
{chr(10).join(meta)}
{extra_head}
</head>
<body data-root="{w}" data-preis="{ctx['preis']}">
{SPRITE}
{entwurf}
<header class="appbar">
  <a class="appbar-titel" href="{w}"><span class="logo">{icon('bolt')}</span><span>Stromfresser<span class="dimm">-Check</span></span></a>
  <div class="appbar-aktionen">
    {kopf_aktion}
    <button class="icon-knopf ripple" type="button" data-installieren hidden aria-label="Als App installieren" title="Als App installieren">{icon('download')}</button>
    <a class="icon-knopf ripple" href="{w}geraete/#suche" data-spotlight-oeffnen aria-label="Suchen" title="Suchen (Strg + K)">{icon('search')}</a>
    <button class="icon-knopf ripple" type="button" data-preis-oeffnen aria-label="Strompreis einstellen" title="Strompreis einstellen">{icon('tune')}</button>
  </div>
</header>
<nav class="navbar" aria-label="Hauptnavigation">{nav}</nav>
<main class="inhalt">
{inhalt}
</main>
{fab}
<footer class="fuss">
  <div class="fuss-marke"><span class="logo">{icon('bolt')}</span><div><strong>{e(ctx['name'])}</strong><small>Stromkosten verstehen. Geld sparen.</small></div></div>
  <nav class="fuss-links" aria-label="Weitere Seiten">
    <a href="{w}geraete/">Alle Geräte</a><a href="{w}haushalt/">Mein Haushalt</a><a href="{w}quiz/">Quiz</a>
    <a href="{w}balkonkraftwerk/">Balkonkraftwerk</a><a href="{w}impressum/">Impressum</a><a href="{w}datenschutz/">Datenschutz</a>
  </nav>
  <div class="fuss-recht">
    {partner}
    <p>Alle Werte sind typische Durchschnittswerte und ersetzen keine Messung. Stand: {e(ctx['stand'])}.</p>
  </div>
</footer>
<dialog class="dialog" id="preis-dialog">
  <form method="dialog">
    <h2>{icon('tune')} Dein Strompreis</h2>
    <p>Alle Kosten auf dieser Seite werden mit deinem Preis berechnet. Den Arbeitspreis findest du auf deiner Stromrechnung (Cent pro kWh).</p>
    <label class="feld"><span class="feld-label">Strompreis</span>
      <span class="feld-rahmen"><input type="number" name="preis" min="0.05" max="2" step="0.01" inputmode="decimal" value="{ctx['preis']}"><em>€/kWh</em></span></label>
    <div class="dialog-aktionen">
      <button class="knopf knopf-text" value="standard" type="submit">Standard</button>
      <button class="knopf knopf-text" value="abbrechen" type="submit">Abbrechen</button>
      <button class="knopf knopf-gefuellt" value="ok" type="submit">Speichern</button>
    </div>
  </form>
</dialog>
<div class="spotlight" data-spotlight hidden>
  <div class="spotlight-panel" role="dialog" aria-modal="true" aria-label="Suche">
    <label class="spotlight-feld">{icon('search')}<input type="search" placeholder="Geräte, Rechner, Ratgeber, Begriffe …" aria-label="Suchen" data-spotlight-eingabe autocomplete="off" enterkeyhint="go"><button class="icon-knopf" type="button" data-spotlight-zu aria-label="Suche schließen">{icon('close')}</button></label>
    <div class="spotlight-ergebnisse" data-spotlight-ergebnisse role="listbox"></div>
    <p class="spotlight-tipp"><kbd>↑</kbd><kbd>↓</kbd> auswählen · <kbd>Enter</kbd> öffnen · <kbd>Esc</kbd> schließen</p>
  </div>
</div>
<div class="snackbar" role="status" aria-live="polite"><span class="snackbar-text"></span><a class="snackbar-aktion" hidden></a></div>
<script src="{w}assets/daten.js?v={v}" defer></script>
<script src="{w}assets/app.js?v={v}" defer></script>
</body>
</html>
"""


def schieber(name, label, wert, minimum, maximum, schritt, einheit, anzeige=None):
    """Zahlenfeld + Schieberegler, von app.js synchron gehalten."""
    anzeige = anzeige or f"{zahl(wert, 0 if float(wert).is_integer() else 2)} {einheit}"
    return f"""<div class="regler">
  <div class="regler-kopf"><label for="f-{name}">{label}</label><output data-anzeige="{name}">{e(anzeige)}</output></div>
  <input class="schieber" type="range" min="{minimum:g}" max="{maximum:g}" step="{schritt:g}" value="{wert:g}" data-fuer="{name}" aria-label="{label}">
  <input class="versteckt-zahl" id="f-{name}" type="number" name="{name}" value="{wert:g}" min="0" step="any" inputmode="decimal">
</div>"""


def zahlenfeld(name, label, wert, einheit):
    return f"""<label class="feld"><span class="feld-label">{label}</span>
  <span class="feld-rahmen"><input type="number" name="{name}" value="{wert:g}" min="0" step="any" inputmode="decimal"><em>{einheit}</em></span></label>"""


def rechner_form(ctx, g=None):
    """Rechner-Karte. Ohne g: freier Rechner mit neutralen Startwerten."""
    frei = g is None
    g = g or {"slug": "", "emoji": "⚡", "name": "Gerät", "leistung_w": 100, "stunden": 3, "nutzungen_woche": 7,
              "wochen_jahr": 52, "standby_w": 0}
    preis = ctx["preis"]
    kwh = jahresverbrauch_kwh(g)
    sb = standby_kwh(g)
    w = g["leistung_w"]
    w_max = 2500 if frei else max(50, w * 3)
    h = g["stunden"]
    h_max = 24 if h >= 1 or frei else 3
    h_schritt = 0.25 if h_max == 24 else 0.05
    anteil = min(100, kwh / REFERENZ_KWH * 100)
    leistung_feld = zahlenfeld("leistung", "Leistung im Betrieb", w, "Watt")
    return f"""
<form class="rechner" data-rechner="geraet" data-slug="{e(g['slug'])}" onsubmit="return false">
  <div class="ergebnis-held">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">{g['emoji']}</span><span class="eh-label">Kosten pro Jahr</span></div>
    <div class="eh-wert" data-aus="euro_jahr">{euro(kwh * preis)}</div>
    <div class="eh-chips">
      <span class="eh-chip"><b data-aus="euro_monat">{euro(kwh * preis / 12)}</b> pro Monat</span>
      <span class="eh-chip"><b data-aus="kwh_jahr">{zahl(kwh)} kWh</b> pro Jahr</span>
      <span class="eh-chip" data-standby-chip{'' if sb else ' hidden'}>Standby <b data-aus="euro_standby">{euro(sb * preis)}</b></span>
    </div>
    <div class="eh-vergleich">
      <div class="balken"><span data-aus-balken style="width:{anteil:.1f}%"></span></div>
      <small><span data-aus="anteil">{zahl(anteil, 1)} %</span> des Jahresverbrauchs eines 2-Personen-Haushalts (ca. {zahl(REFERENZ_KWH)} kWh)</small>
    </div>
  </div>
  <div class="rechner-felder">
    {leistung_feld}
    <input class="schieber schieber-voll" type="range" min="0" max="{w_max:g}" step="{1 if w_max <= 200 else 10}" value="{w:g}" data-fuer="leistung" aria-label="Leistung in Watt">
    {schieber("stunden", "Laufzeit pro Nutzung", h, 0, h_max, h_schritt, "h", dauer(h))}
    {schieber("nutzungen", "Nutzungen pro Woche", g["nutzungen_woche"], 0, 14, 1, "×", f'{zahl(g["nutzungen_woche"])} × pro Woche')}
    <details class="mehr">
      <summary>{icon('tune')} Weitere Einstellungen{icon('chevron', 'ic mehr-pfeil')}</summary>
      <div class="mehr-inhalt">
        {schieber("wochen", "Wochen pro Jahr", g.get("wochen_jahr", 52), 1, 52, 1, "Wochen")}
        {zahlenfeld("standby", "Standby-Leistung", g.get("standby_w", 0) or 0, "Watt")}
        {zahlenfeld("preis", "Strompreis (gilt für die ganze Seite)", preis, "€/kWh")}
      </div>
    </details>
  </div>
  <div class="rechner-aktionen">
    <button class="knopf knopf-tonal ripple" type="button" data-teilen>{icon('share')}Ergebnis teilen</button>
    <button class="knopf knopf-text ripple" type="button" data-zuruecksetzen>{icon('refresh')}Zurücksetzen</button>
  </div>
</form>"""


def haushalt_fab(g):
    return f"""<button class="fab ripple" type="button" data-zum-haushalt="{e(g['slug'])}">{icon('plus')}<span>Zu meinem Haushalt</span></button>"""


# ---------------------------------------------------------------- Seiten

def startseite(ctx, geraete):
    s = Seite(ctx, "")
    preis_txt = zahl(ctx["preis"], 2)
    nach_slug = {g["slug"]: g for g in geraete}
    favoriten = "".join(
        f'<a class="chip ripple" href="{s.link("geraet/" + slug + "/")}"><span aria-hidden="true">{nach_slug[slug]["emoji"]}</span>{e(gross(nach_slug[slug]["name"]))}</a>'
        for slug in FAVORITEN if slug in nach_slug)
    kategorien = "".join(
        f'<a class="kategorie-karte ripple" href="{s.link("geraete/")}?kat={quote_plus(k)}"><span class="kk-emoji" aria-hidden="true">{KATEGORIE_EMOJI[k]}</span>'
        f'<span>{e(k)}</span><small>{sum(1 for g in geraete if g["kategorie"] == k)} Geräte</small></a>'
        for k in KATEGORIEN if any(g["kategorie"] == k for g in geraete))
    gb = nach_slug.get("gluehbirne")
    led = nach_slug.get("led-lampe")
    fakten = [
        ("🔌", "1 Watt Dauer-Standby", f"kostet rund {euro_kwh(8.76)} im Jahr. Zehn Geräte mit je 2 W sind schnell über 50 €."),
        ("🚿", "Oft unterschätzt", "Der Durchlauferhitzer ist in vielen Haushalten der größte Verbraucher – ein Sparduschkopf halbiert ihn."),
    ]
    if gb and led:
        fakten.append(("💡", "Glühbirne gegen LED", f"Eine LED spart gegenüber einer 60-W-Birne rund {euro_kwh(jahresverbrauch_kwh(gb) - jahresverbrauch_kwh(led))} pro Jahr und Lampe."))
    if "smartphone" in nach_slug:
        fakten.append(("📱", "Handy laden", f"kostet im Jahr nur etwa {euro_kwh(jahresverbrauch_kwh(nach_slug['smartphone']))} – weniger als ein Kaffee."))
    top = sorted(geraete, key=jahresverbrauch_kwh, reverse=True)[0]
    ticker_start = f"{top['emoji']} {gross(top['name'])} · {euro(jahresverbrauch_kwh(top) * ctx['preis'])} im Jahr"
    fakten_html = "".join(f'<div class="fakt-karte"><span class="fakt-emoji" aria-hidden="true">{em}</span><strong>{e(t)}</strong><p>{txt}</p></div>'
                          for em, t, txt in fakten)
    fragen = [
        ("Wie berechne ich die Stromkosten eines Geräts?",
         "Leistung in Watt × Betriebsstunden ÷ 1000 ergibt die Kilowattstunden (kWh). Multipliziert mit deinem Strompreis pro kWh erhältst du die Kosten. "
         "Beispiel: 100 W × 3 Stunden täglich × 365 Tage ÷ 1000 = 109,5 kWh im Jahr."),
        ("Welcher Strompreis ist voreingestellt?",
         f"Als Annahme {preis_txt} €/kWh. Über das Regler-Symbol oben rechts stellst du deinen eigenen Preis ein – er gilt dann für alle Rechner."),
        ("Was kostet Standby im Jahr?",
         f"Jedes Watt Dauer-Standby sind 8,76 kWh im Jahr – bei {preis_txt} €/kWh rund {euro(8.76 * ctx['preis'])}."),
        ("Kann ich den Stromfresser-Check als App nutzen?",
         "Ja. Im Browser auf dem Handy „Zum Startbildschirm hinzufügen“ bzw. „App installieren“ wählen – dann startet er wie eine App und funktioniert auch offline."),
    ]
    inhalt = f"""
<section class="held">
  <div class="held-text">
    <span class="held-marke">{icon('bolt')} Kostenlos · ohne Anmeldung · {len(geraete)} Geräte</span>
    <h1>Was kostet dein Gerät wirklich?</h1>
    <p class="lead">Finde die Stromfresser in deinem Zuhause – mit Rechnern, Spartipps und deinem persönlichen Haushalts-Check.</p>
    <div class="ticker" aria-hidden="true"><span class="ticker-punkt"></span><span class="ticker-fenster"><span class="ticker-text" data-ticker>{ticker_start}</span></span></div>
  </div>
  <form class="suchleiste" action="{s.link('geraete/')}" method="get" role="search">
    {icon('search')}<input type="search" name="q" placeholder="Gerät suchen …" aria-label="Gerät suchen" autocomplete="off">
    <button class="knopf knopf-gefuellt ripple" type="submit">Suchen</button>
  </form>
  <div class="chip-reihe chip-scroll">{favoriten}</div>
</section>

<section class="kennzahlen" aria-label="Kennzahlen">
  <div><b data-hochzaehlen="{len(geraete)}">{len(geraete)}</b><small>Geräte</small></div>
  <div><b data-hochzaehlen="{len(KATEGORIEN)}">{len(KATEGORIEN)}</b><small>Bereiche</small></div>
  <div><b>0 €</b><small>kostenlos</small></div>
  <div><b>{icon('bolt')}</b><small>als App</small></div>
</section>

<aside class="install-karte" data-install-karte hidden>
  <span class="ik-icon">{icon('bolt')}</span>
  <div><strong>Als App installieren</strong><p>Direkt vom Startbildschirm öffnen – auch offline.</p></div>
  <button class="knopf knopf-gefuellt ripple" type="button" data-installieren-karte>Installieren</button>
</aside>

<a class="sparcheck-promo ripple" href="{s.link('werkzeuge/spar-check/')}">
  <span class="sp-emoji" aria-hidden="true">🎯</span>
  <span class="sp-text"><span class="overline">Neu · 60 Sekunden</span><strong>Wie viel kannst du sparen?</strong><small>8 kurze Fragen – dein persönlicher Sparplan mit Euro-Beträgen.</small></span>
  <span class="sp-knopf">Starten{icon('chevron')}</span>
</a>

<section class="werkzeuge">
  {werkzeug_karten(s, ["haushalt", "zaehler", "tarif", "eauto", "standby", "quiz"])}
</section>
<p class="mehr-link"><a class="knopf knopf-text" href="{s.link('werkzeuge/')}">Alle {len(WERKZEUGE) - 1} Werkzeuge ansehen{icon('chevron')}</a></p>

{haus_story(s, ctx)}

<section class="statement" aria-label="Standby in Zahlen">
  <p class="statement-zeile">1 Watt.</p>
  <p class="statement-zeile">Rund um die Uhr.</p>
  <p class="statement-zeile statement-verlauf">{euro(8.76 * ctx['preis'])} im Jahr.</p>
  <p class="statement-unter">So viel kostet jedes Watt Standby. <a href="{s.link('werkzeuge/standby/')}">Was kostet dein Standby?</a></p>
</section>

<section class="abschnitt">
  <div class="abschnitt-kopf"><div><span class="overline">Ranking</span><h2>Die größten Stromfresser</h2></div><a class="knopf knopf-text" href="{s.link('geraete/')}">Alle {len(geraete)}{icon('chevron')}</a></div>
  <p class="unterzeile">Typische Jahreskosten bei <span data-preis-anzeige>{preis_txt} €/kWh</span></p>
  {rangliste(s, geraete, anzahl=10)}
</section>

<section class="abschnitt">
  <span class="overline">Fakten</span>
  <h2>Wusstest du?</h2>
  <div class="karussell">{fakten_html}</div>
</section>

<section class="abschnitt" id="rechner">
  <span class="overline">Selbst rechnen</span>
  <h2>Freier Stromkosten-Rechner</h2>
  <p class="unterzeile">Leistung steht auf dem Typenschild oder in der Anleitung.</p>
  {rechner_form(ctx)}
</section>

<section class="abschnitt">
  <div class="abschnitt-kopf"><div><span class="overline">Wissen</span><h2>Strom verstehen</h2></div><a class="knopf knopf-text" href="{s.link('wissen/')}">Alle Ratgeber{icon('chevron')}</a></div>
  <div class="karussell">{''.join(artikel_karte(s, a) for a in ARTIKEL)}</div>
</section>

<section class="abschnitt">
  <span class="overline">Entdecken</span>
  <h2>Nach Bereich stöbern</h2>
  <div class="kategorie-raster">{kategorien}</div>
</section>

{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    titel = f"Stromrechner {ctx['jahr']}: Stromkosten & Verbrauch jedes Geräts berechnen"
    beschr = (f"Kostenloser Stromrechner für {len(geraete)} Geräte: Stromkosten pro Jahr und Monat, Haushalts-Check, "
              "Zählerstand- und Standby-Rechner, Ratgeber und Spartipps. Auch als App nutzbar.")
    jsonld = faq_jsonld(fragen) + '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "WebApplication", "name": ctx["name"], "url": s.kanonisch,
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "Android, iOS, Windows, macOS",
        "inLanguage": "de", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}}, ensure_ascii=False) + "</script>"
    return s, layout(s, titel, beschr, inhalt, "start", jsonld)


def geraete_uebersicht(ctx, geraete):
    s = Seite(ctx, "geraete/")
    chips = '<button class="chip filter-chip ripple" type="button" data-kat-filter="" aria-pressed="true">' + icon("check", "ic chip-haken") + "Alle</button>"
    chips += "".join(f'<button class="chip filter-chip ripple" type="button" data-kat-filter="{e(k)}" aria-pressed="false">'
                     f'{icon("check", "ic chip-haken")}<span aria-hidden="true">{KATEGORIE_EMOJI[k]}</span>{e(k)}</button>'
                     for k in KATEGORIEN if any(g["kategorie"] == k for g in geraete))
    karten = "".join(geraet_karte(s, g) for g in sorted(geraete, key=jahresverbrauch_kwh, reverse=True))
    inhalt = f"""
<section class="seitenkopf">
  <h1>Alle Geräte im Stromkosten-Check</h1>
  <p class="lead">{len(geraete)} Haushaltsgeräte mit typischem Verbrauch und Kosten pro Jahr. Tippe ein Gerät an für Rechner und Spartipps.</p>
</section>
<div class="filter-leiste" id="suche">
  <label class="suchleiste suchleiste-klein">{icon('search')}<input type="search" placeholder="Gerät suchen" aria-label="Gerät suchen" data-geraete-suche autocomplete="off"></label>
  <div class="segmente segmente-klein" role="radiogroup" aria-label="Sortierung">
    <label><input type="radio" name="sortierung" value="kosten" checked><span>{icon('check', 'ic seg-haken')}Kosten</span></label>
    <label><input type="radio" name="sortierung" value="name"><span>{icon('check', 'ic seg-haken')}A–Z</span></label>
  </div>
</div>
<div class="chip-reihe chip-scroll" role="group" aria-label="Bereich filtern">{chips}</div>
<p class="unterzeile" data-treffer>{len(geraete)} Geräte</p>
<div class="geraete-raster" data-geraete-liste>{karten}</div>
<div class="leer" data-leer hidden><span aria-hidden="true">🔍</span><p>Kein Gerät gefunden. Probier den <a href="{s.link('')}#rechner">freien Rechner</a> mit eigenen Werten.</p></div>
"""
    titel = f"Stromverbrauch von {len(geraete)} Haushaltsgeräten im Vergleich ({ctx['jahr']})"
    beschr = "Alle Haushaltsgeräte im Vergleich: typischer Stromverbrauch und Kosten pro Jahr – mit Suche, Filter und Rechner für jedes Gerät."
    return s, layout(s, titel, beschr, inhalt, "geraete")


def geraeteseite(ctx, g, geraete):
    s = Seite(ctx, f"geraet/{g['slug']}/")
    preis = ctx["preis"]
    kwh = jahresverbrauch_kwh(g)
    kosten = kwh * preis
    name, artikel = g["name"], g["artikel"]
    voll = f"{artikel} {name}"
    preis_txt = zahl(preis, 2)
    standby_satz = ""
    if g.get("standby_w"):
        sb = standby_kwh(g)
        standby_satz = f" Davon entfallen etwa {zahl(sb, 1)} kWh ({euro(sb * preis)}) auf den Standby."
    kategorie = [x for x in geraete if x["kategorie"] == g["kategorie"]]
    weitere = [x for x in geraete if x["kategorie"] != g["kategorie"]]
    weitere = sorted(weitere, key=lambda x: abs(jahresverbrauch_kwh(x) - kwh))[:6]
    fragen = [
        (f"Wie viel Strom verbraucht {voll} im Jahr?",
         f"Bei typischer Nutzung etwa {zahl(kwh)} kWh im Jahr. Annahme: {g['hinweis']}"),
        (f"Was kostet {voll} im Monat?",
         f"Bei einem Strompreis von {preis_txt} €/kWh rund {euro(kosten / 12)} pro Monat bzw. {euro(kosten)} pro Jahr.{standby_satz}"),
        (f"Wie viel Strom verbraucht {voll} pro Stunde?",
         f"Im Betrieb etwa {zahl(g['leistung_w'], 0 if float(g['leistung_w']).is_integer() else 1)} Watt, also {zahl(g['leistung_w'] / 1000, 3)} kWh pro Stunde – "
         f"das kostet bei {preis_txt} €/kWh rund {zahl(g['leistung_w'] / 1000 * preis * 100, 1)} Cent pro Betriebsstunde."),
        (f"Was kostet {voll} pro Tag?",
         f"Im Jahresdurchschnitt rund {zahl(kosten / 365 * 100, 1)} Cent pro Tag bei typischer Nutzung ({zahl(kwh / 365, 2)} kWh)."),
        (f"{gross(name)}: Wie kann ich Strom sparen?", g["tipp"]),
    ]
    p = g["produkt"]
    standby_html = ""
    if g.get("standby_w"):
        sb = standby_kwh(g)
        standby_html = f" Davon entfallen etwa {zahl(sb, 1)} kWh ({euro_kwh(sb)}) auf den Standby."
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('geraete/')}?kat={quote_plus(g['kategorie'])}">{e(g['kategorie'])}</a>{icon('chevron')}<span>{e(gross(name))}</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">{g['emoji']}</div>
  <h1>Wie viel Strom verbraucht {e(voll)}?</h1>
  <p class="lead">{e(gross(voll))} verbraucht bei typischer Nutzung etwa <strong>{zahl(kwh)} kWh pro Jahr</strong>.
  Bei <span data-preis-anzeige>{preis_txt} €/kWh</span> sind das rund <strong>{euro_kwh(kwh)} im Jahr</strong> bzw. <strong>{euro_kwh(kwh, 12)} im Monat</strong>.{standby_html}</p>
</section>
{rechner_form(ctx, g)}
<div class="hinweis-karte">{icon('info')}<p><strong>Annahme:</strong> {e(g['hinweis'])} Passe die Regler an dein Gerät an.</p></div>
<div class="knopf-reihe"><a class="knopf knopf-tonal ripple" href="{s.link('werkzeuge/vergleich/')}?a={g['slug']}">⚖️ Mit anderem Gerät vergleichen</a></div>
<section class="abschnitt">
  <div class="tipp-karte">
    <div class="tipp-kopf">{icon('bulb')}<h2>So sparst du Strom</h2></div>
    <p>{e(g['tipp'])}</p>
  </div>
</section>
{produkt_karte(ctx, p['label'], p['text'], p['query'], g['emoji'])}
<section class="abschnitt">
  <span class="overline">Vergleich</span>
  <h2>{e(g['kategorie'])} im Vergleich</h2>
  <p class="unterzeile">Typische Jahreskosten aller Geräte dieses Bereichs</p>
  {rangliste(s, kategorie, markiert=g['slug'])}
</section>
<section class="abschnitt">
  <span class="overline">Weiterstöbern</span>
  <h2>Ähnlich teuer</h2>
  <div class="karussell">{''.join(geraet_karte(s, x) for x in weitere)}</div>
</section>
{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    titel = f"{gross(name)}: Stromverbrauch & Kosten pro Jahr berechnen ({ctx['jahr']})"
    beschr = (f"{gross(voll)} verbraucht ca. {zahl(kwh)} kWh im Jahr – rund {euro(kosten)}. "
              f"Mit Rechner für deine eigenen Werte und Spartipps.")
    return s, layout(s, titel, beschr, inhalt, "geraete", faq_jsonld(fragen), fab=haushalt_fab(g))


def haushalt_seite(ctx, geraete):
    s = Seite(ctx, "haushalt/")
    personen = "".join(f'<label><input type="radio" name="personen" value="{n}"{" checked" if n == 2 else ""}><span>{icon("check", "ic seg-haken")}{n}{"+" if n == 5 else ""}</span></label>'
                       for n in HAUSHALT_SCHNITT)
    fragen = [
        ("Wie viel Strom verbraucht ein Haushalt im Jahr?",
         "Als grobe Richtwerte ohne Warmwasser über Strom: 1 Person ca. 1.500 kWh, 2 Personen ca. 2.500 kWh, 3 Personen ca. 3.200 kWh, "
         "4 Personen ca. 3.800 kWh. Mit Durchlauferhitzer oder Elektroheizung liegt der Verbrauch deutlich höher."),
        ("Werden meine Eingaben gespeichert?",
         "Nur auf deinem Gerät im Browser. Es wird nichts an einen Server übertragen. Wenn du die Browserdaten löschst, ist die Liste weg."),
        ("Warum ist mein echter Verbrauch höher als die Summe?",
         "Die Liste enthält nur die Geräte, die du eingetragen hast. Kleingeräte, Heizungspumpe, Beleuchtung und Standby vieler Geräte kommen oft noch dazu."),
    ]
    inhalt = f"""
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🏠</div>
  <h1>Mein Haushalt: Stromkosten aller Geräte</h1>
  <p class="lead">Stell deine Geräte zusammen und sieh, was dein Haushalt im Jahr an Strom kostet – und wo sich Sparen am meisten lohnt.</p>
</section>
<noscript><p class="hinweis-karte">Für den Haushalts-Check muss JavaScript aktiviert sein.</p></noscript>
<div class="haushalt" data-haushalt>
  <div class="ergebnis-held">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🏠</span><span class="eh-label">Dein Haushalt pro Jahr</span></div>
    <div class="eh-wert" data-hh="euro_jahr">0,00 €</div>
    <div class="eh-chips">
      <span class="eh-chip"><b data-hh="euro_monat">0,00 €</b> pro Monat</span>
      <span class="eh-chip"><b data-hh="kwh_jahr">0 kWh</b> pro Jahr</span>
      <span class="eh-chip"><b data-hh="anzahl">0</b> Geräte</span>
    </div>
    <div class="eh-vergleich">
      <div class="personen-zeile"><span>Personen im Haushalt</span>
        <div class="segmente segmente-klein" role="radiogroup" aria-label="Personen im Haushalt">{personen}</div></div>
      <div class="balken"><span data-hh-balken style="width:0%"></span></div>
      <small data-hh="vergleich">Füge Geräte hinzu, um dich mit einem Durchschnittshaushalt zu vergleichen.</small>
    </div>
  </div>

  <div class="haushalt-hinzufuegen karte-flach">
    <label class="suchleiste suchleiste-klein">{icon('plus')}<input type="search" placeholder="Gerät hinzufügen …" aria-label="Gerät hinzufügen" data-hh-suche autocomplete="off"></label>
    <div class="vorschlaege" data-hh-vorschlaege></div>
    <div class="knopf-reihe">
      <button class="knopf knopf-tonal ripple" type="button" data-hh-vorlage>{icon('home')}Typischen Haushalt laden</button>
      <button class="knopf knopf-text ripple" type="button" data-hh-leeren hidden>{icon('trash')}Alles entfernen</button>
    </div>
  </div>

  <div class="leer" data-hh-leer><span aria-hidden="true">🔌</span><p>Noch keine Geräte. Such oben nach einem Gerät oder lade einen typischen Haushalt als Startpunkt.</p></div>

  <section class="abschnitt" data-hh-diagramm hidden>
    <h2>Wohin dein Geld geht</h2>
    <div class="diagramm-karte"><svg class="donut" viewBox="0 0 120 120" data-hh-donut aria-hidden="true"></svg><ul class="legende" data-hh-legende></ul></div>
  </section>

  <section class="abschnitt" data-hh-listen-abschnitt hidden>
    <h2>Deine Geräte</h2>
    <ul class="hh-liste" data-hh-liste></ul>
  </section>

  <section class="abschnitt" data-hh-tipps-abschnitt hidden>
    <h2>Hier lohnt sich Sparen am meisten</h2>
    <div class="tipp-stapel" data-hh-tipps></div>
  </section>
</div>
{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    titel = "Haushalts-Stromrechner: Was kostet mein Haushalt im Jahr?"
    beschr = "Stell deine Geräte zusammen und berechne die Stromkosten deines ganzen Haushalts – mit Vergleich zum Durchschnitt und Spartipps."
    return s, layout(s, titel, beschr, inhalt, "haushalt", faq_jsonld(fragen))


def quiz_seite(ctx, geraete):
    s = Seite(ctx, "quiz/")
    inhalt = f"""
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🧠</div>
  <h1>Stromfresser-Quiz: Was kostet mehr?</h1>
  <p class="lead">10 Runden, zwei Geräte – tippe auf das, was im Jahr mehr Strom kostet. Die Auflösung zeigt dir sofort die echten Zahlen.</p>
</section>
<noscript><p class="hinweis-karte">Für das Quiz muss JavaScript aktiviert sein.</p></noscript>
<div class="quiz" data-quiz>
  <div class="quiz-kopf">
    <span data-quiz="runde">Runde 1 von 10</span><span class="quiz-punkte">{icon('check')}<b data-quiz="punkte">0</b></span>
  </div>
  <div class="fortschritt"><span data-quiz-fortschritt style="width:0%"></span></div>
  <p class="quiz-frage">Was kostet im Jahr mehr Strom?</p>
  <div class="quiz-optionen" data-quiz-optionen></div>
  <div class="quiz-aufloesung" data-quiz-aufloesung hidden>
    <p data-quiz="aufloesung"></p>
    <button class="knopf knopf-gefuellt ripple" type="button" data-quiz-weiter>Weiter{icon('chevron')}</button>
  </div>
  <div class="quiz-ende" data-quiz-ende hidden>
    <span class="quiz-pokal" data-quiz="emoji">🏆</span>
    <h2 data-quiz="ergebnis">10 von 10</h2>
    <p data-quiz="spruch"></p>
    <p class="unterzeile" data-quiz="rekord"></p>
    <div class="knopf-reihe knopf-reihe-mitte">
      <button class="knopf knopf-gefuellt ripple" type="button" data-quiz-neu>{icon('refresh')}Nochmal spielen</button>
      <button class="knopf knopf-tonal ripple" type="button" data-quiz-teilen>{icon('share')}Ergebnis teilen</button>
    </div>
    <a class="knopf knopf-text" href="{s.link('haushalt/')}">Jetzt den eigenen Haushalt checken{icon('chevron')}</a>
  </div>
</div>
"""
    titel = "Stromfresser-Quiz: Welches Gerät kostet mehr Strom?"
    beschr = "Teste dein Gefühl für Stromkosten: 10 Runden, zwei Haushaltsgeräte – welches kostet im Jahr mehr? Mit echten Zahlen zur Auflösung."
    return s, layout(s, titel, beschr, inhalt, "werkzeuge")


def balkonkraftwerk_seite(ctx):
    s = Seite(ctx, "balkonkraftwerk/")
    preis = ctx["preis"]
    ertrag, ersparnis, amort = bkw_rechnung(preis=preis)
    maxanteil = max(SOLAR_MONATE)
    monate = "".join(
        f'<div class="monat"><span class="monat-wert" data-bkw-monat="{i}">{zahl(ertrag * a / 100)}</span>'
        f'<span class="monat-saeule"><span data-bkw-saeule="{i}" style="height:{a / maxanteil * 100:.0f}%"></span></span>'
        f'<span class="monat-name">{MONATE[i][:3]}</span></div>'
        for i, a in enumerate(SOLAR_MONATE))

    def segmente(name, optionen):
        return '<div class="segmente" role="radiogroup">' + "".join(
            f'<label><input type="radio" name="{name}" value="{wert}"{" checked" if an else ""}><span>{icon("check", "ic seg-haken")}{e(text)}</span></label>'
            for wert, text, an in optionen) + "</div>"

    fragen = [
        ("Wie viel Strom erzeugt ein Balkonkraftwerk?",
         "In Deutschland grob 850 bis 1.050 kWh pro Jahr und Kilowatt Modulleistung bei Südausrichtung und guter Neigung. "
         "Ost/West-Ausrichtung oder senkrechte Montage am Balkongeländer liefern deutlich weniger."),
        ("Wie viel Prozent des Solarstroms nutze ich selbst?",
         "Ohne Speicher meist 30 bis 50 %. Der Rest fließt ins Netz und wird in der Regel nicht vergütet. "
         "Wer tagsüber zu Hause ist oder Geräte gezielt mittags laufen lässt, kommt höher."),
        ("Wie viel Watt darf ein Balkonkraftwerk haben?",
         "In Deutschland ist für vereinfacht angemeldete Steckersolargeräte eine Wechselrichterleistung von bis zu 800 W vorgesehen; "
         "die Modulleistung darf höher sein. Die Anmeldung erfolgt im Marktstammdatenregister. Prüfe die aktuellen Regeln vor dem Kauf."),
        ("Nach wie vielen Jahren rechnet sich ein Balkonkraftwerk?",
         f"Mit den Startwerten dieses Rechners nach etwa {zahl(amort, 1)} Jahren. Entscheidend sind Ausrichtung, Eigenverbrauch und Anschaffungspreis."),
    ]
    inhalt = f"""
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">☀️</div>
  <h1>Balkonkraftwerk-Rechner: Lohnt es sich für dich?</h1>
  <p class="lead">Berechne Ertrag, jährliche Ersparnis und Amortisationszeit deines Balkonkraftwerks – mit Ausrichtung, Region und Eigenverbrauch.</p>
</section>
<form class="rechner" data-rechner="bkw" onsubmit="return false">
  <div class="ergebnis-held ergebnis-solar">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">☀️</span><span class="eh-label">Ersparnis pro Jahr</span></div>
    <div class="eh-wert" data-aus="ersparnis">{euro(ersparnis)}</div>
    <div class="eh-chips">
      <span class="eh-chip"><b data-aus="ertrag">{zahl(ertrag)} kWh</b> Ertrag</span>
      <span class="eh-chip"><b data-aus="eigen_kwh">{zahl(ertrag * 0.4)} kWh</b> selbst genutzt</span>
      <span class="eh-chip">bezahlt nach <b data-aus="amort">{zahl(amort, 1)} Jahren</b></span>
    </div>
  </div>
  <div class="rechner-felder">
    {schieber("modul", "Modulleistung gesamt", 900, 200, 2400, 10, "Wp")}
    <div class="regler"><div class="regler-kopf"><span>Wechselrichter</span></div>
      {segmente("wr", [(600, "600 W", False), (800, "800 W", True)])}</div>
    <div class="regler"><div class="regler-kopf"><span>Region</span></div>
      {segmente("region", [(900, "Nord", False), (950, "Mitte", True), (1050, "Süd", False)])}</div>
    <div class="regler"><div class="regler-kopf"><span>Ausrichtung</span></div>
      {segmente("ausrichtung", [(1, "Süd", True), (0.95, "SO/SW", False), (0.8, "Ost/West", False), (0.6, "Nord", False)])}</div>
    <div class="regler"><div class="regler-kopf"><span>Montage</span></div>
      {segmente("montage", [(1, "Schräg 30°", True), (0.9, "Flach", False), (0.7, "Senkrecht", False)])}</div>
    {schieber("eigen", "Eigenverbrauch", 40, 10, 90, 1, "%")}
    {schieber("kosten", "Anschaffungskosten", 400, 100, 1500, 10, "€")}
    {zahlenfeld("preis", "Strompreis (gilt für die ganze Seite)", preis, "€/kWh")}
  </div>
  <div class="rechner-aktionen">
    <button class="knopf knopf-tonal ripple" type="button" data-teilen>{icon('share')}Ergebnis teilen</button>
  </div>
</form>
{solar_story(s, ertrag, ersparnis)}
<section class="abschnitt">
  <h2>Ertrag über das Jahr</h2>
  <p class="unterzeile">Typische Verteilung in Deutschland, in kWh pro Monat</p>
  <div class="monate karte-flach">{monate}</div>
</section>
<div class="hinweis-karte">{icon('info')}<p>Grobe Schätzung mit Durchschnittswerten für Deutschland. Verschattung, Wetter und dein Verbrauchsprofil können das Ergebnis stark verändern. Liegt die Modulleistung deutlich über der Wechselrichterleistung, rechnet der Rechner mit einer Begrenzung.</p></div>
<section class="abschnitt">
  <div class="tipp-karte">
    <div class="tipp-kopf">{icon('bulb')}<h2>So holst du mehr heraus</h2></div>
    <p>Lass Waschmaschine, Geschirrspüler und Ladegeräte mittags laufen, wenn die Sonne scheint – so steigt dein Eigenverbrauch und damit die Ersparnis. Eine schattenfreie Südausrichtung mit etwa 30° Neigung bringt den höchsten Ertrag.</p>
  </div>
</section>
{produkt_karte(ctx, "Balkonkraftwerk-Komplettsets", "Sets mit Modulen, Wechselrichter und Kabel – achte auf 800-W-Wechselrichter und passende Halterung für deinen Balkon.", "Balkonkraftwerk 800W Komplettset", "☀️")}
{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    titel = f"Balkonkraftwerk-Rechner {ctx['jahr']}: Ertrag, Ersparnis & Amortisation"
    beschr = "Lohnt sich ein Balkonkraftwerk? Berechne kostenlos Ertrag, jährliche Ersparnis und Amortisationszeit – mit Ausrichtung, Region und Eigenverbrauch."
    return s, layout(s, titel, beschr, inhalt, "werkzeuge", faq_jsonld(fragen))


def impressum_seite(ctx):
    s = Seite(ctx, "impressum/")
    imp = ctx["impressum"]
    inhalt = f"""
<section class="seitenkopf"><h1>Impressum</h1></section>
<div class="text-karte">
<p>Angaben gemäß § 5 DDG</p>
<p>{e(imp.get('name', ''))}<br>{e(imp.get('strasse', ''))}<br>{e(imp.get('plz_ort', ''))}</p>
<h2>Kontakt</h2>
<p>E-Mail: {e(imp.get('email', ''))}</p>
<h2>Verantwortlich für den Inhalt</h2>
<p>{e(imp.get('name', ''))}, Anschrift wie oben.</p>
<h2>Haftung für Inhalte</h2>
<p>Die Inhalte dieser Seite wurden mit Sorgfalt erstellt. Alle Verbrauchs- und Kostenangaben sind jedoch Durchschnittswerte und Schätzungen; für Richtigkeit, Vollständigkeit und Aktualität wird keine Gewähr übernommen.</p>
</div>
"""
    return s, layout(s, "Impressum", "Impressum", inhalt, index=False)


def datenschutz_seite(ctx):
    s = Seite(ctx, "datenschutz/")
    imp = ctx["impressum"]
    statistik = ""
    if ctx["umami_id"]:
        statistik = """<h2>Besucherstatistik (Umami)</h2>
<p>Um zu verstehen, welche Seiten und Funktionen hilfreich sind, nutzt diese Website den Statistikdienst Umami Cloud (umami.is). Umami setzt keine Cookies, speichert nichts auf deinem Gerät und erstellt keine Nutzerprofile. Erfasst werden zusammengefasst und ohne Personenbezug: aufgerufene Seite, Verweildauer, verweisende Website, Gerätetyp, Browser, Betriebssystem, Land sowie Aktionen wie „Quiz beendet“ oder „Amazon-Link angeklickt“. Deine IP-Adresse wird nicht gespeichert. Rechtsgrundlage ist unser berechtigtes Interesse an einer nutzerfreundlichen Website (Art. 6 Abs. 1 lit. f DSGVO).</p>"""
    werbung = ""
    if ctx["adsense"]:
        werbung = """<h2>Google AdSense</h2>
<p>Diese Website nutzt Google AdSense (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland) zur Einblendung von Werbung. Dabei können Cookies und ähnliche Technologien eingesetzt werden. Dies geschieht nur mit deiner Einwilligung (Art. 6 Abs. 1 lit. a DSGVO), die du über das Einwilligungsbanner erteilen und jederzeit widerrufen kannst.</p>"""
    inhalt = f"""
<section class="seitenkopf"><h1>Datenschutzerklärung</h1></section>
<div class="text-karte">
<h2>Verantwortlicher</h2>
<p>{e(imp.get('name', ''))}, {e(imp.get('strasse', ''))}, {e(imp.get('plz_ort', ''))}, E-Mail: {e(imp.get('email', ''))}</p>
<h2>Hosting</h2>
<p>Diese Website wird bei GitHub Pages gehostet (GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). Beim Aufruf der Seiten verarbeitet GitHub technisch notwendige Daten wie deine IP-Adresse, um die Seite auszuliefern und die Sicherheit zu gewährleisten (berechtigtes Interesse, Art. 6 Abs. 1 lit. f DSGVO). Details: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement" rel="nofollow noopener">Datenschutzerklärung von GitHub</a>.</p>
<h2>Rechner, Haushalts-Check und Quiz</h2>
<p>Alle Berechnungen laufen ausschließlich in deinem Browser. Deinen Strompreis, deine Haushaltsliste und deinen Quiz-Rekord speichert die Seite nur lokal in deinem Browser (Local Storage), damit sie beim nächsten Besuch noch da sind. Diese Daten werden nicht übertragen und du kannst sie jederzeit über die Browsereinstellungen löschen. Diese Website setzt selbst keine Cookies.</p>
{statistik}
<h2>Offline-Nutzung</h2>
<p>Damit die Seite als App installiert und offline genutzt werden kann, speichert ein sogenannter Service Worker Seiten und Dateien dieser Website im Zwischenspeicher deines Browsers. Dabei werden keine personenbezogenen Daten erhoben.</p>
<h2>Amazon-Partnerprogramm</h2>
<p>Diese Website enthält Links zu Amazon.de. Als Teilnehmer des Amazon-Partnerprogramms (Amazon Europe Core S.à r.l. und weitere Amazon-Gesellschaften) erhalten wir für qualifizierte Käufe eine Provision. Erst wenn du einen solchen Link anklickst, gelangst du zu Amazon; Amazon kann dann Cookies setzen, um die Herkunft der Bestellung nachzuvollziehen. Es gelten die Datenschutzbestimmungen von Amazon.</p>
{werbung}
<h2>Deine Rechte</h2>
<p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht auf Beschwerde bei einer Datenschutz-Aufsichtsbehörde.</p>
</div>
"""
    return s, layout(s, "Datenschutzerklärung", "Datenschutzerklärung", inhalt, index=False)


def fehlerseite(ctx):
    # GitHub Pages liefert 404.html für alle Pfade aus – deshalb absolute Links.
    s = Seite(ctx, "")
    s.wurzel = ctx["base"] + "/"
    inhalt = f"""<section class="seitenkopf leer"><span aria-hidden="true">🔌</span><h1>Seite nicht gefunden</h1>
<p class="lead">Diese Seite gibt es nicht (mehr).</p>
<a class="knopf knopf-gefuellt" href="{s.wurzel}">Zum Stromkosten-Rechner</a></section>"""
    return layout(s, "Seite nicht gefunden", "Seite nicht gefunden", inhalt, index=False)


# ---------------------------------------------------------------- Werkzeuge, Wissen, Scroll-Geschichten

WERKZEUGE = {
    "haushalt": ("haushalt/", "🏠", "Mein Haushalt", "Alle Geräte sammeln, Gesamtkosten und Sparpotenzial sehen", "wk-primaer"),
    "zaehler": ("werkzeuge/zaehlerstand/", "🔢", "Zählerstand-Rechner", "Droht eine Nachzahlung? Verbrauch hochrechnen", "wk-sekundaer"),
    "quiz": ("quiz/", "🧠", "Stromfresser-Quiz", "Was kostet mehr? Teste dein Gefühl", "wk-tertiaer"),
    "solar": ("balkonkraftwerk/", "☀️", "Balkonkraftwerk", "Ertrag, Ersparnis und Amortisation", "wk-tertiaer"),
    "standby": ("werkzeuge/standby/", "🔌", "Standby-Rechner", "Was kosten Geräte, die nie ganz aus sind?", "wk-sekundaer"),
    "austausch": ("werkzeuge/austausch/", "🔁", "Austausch-Rechner", "Lohnt sich ein neues, sparsames Gerät?", "wk-primaer"),
    "frei": ("#rechner", "🧮", "Freier Rechner", "Eigene Watt und Stunden eingeben", ""),
    "sparcheck": ("werkzeuge/spar-check/", "🎯", "Spar-Check", "8 Fragen – dein persönlicher Sparplan in Euro", "wk-primaer"),
    "tarif": ("werkzeuge/tarifvergleich/", "🔄", "Tarif-Vergleich", "Lohnt sich ein Anbieterwechsel?", "wk-tertiaer"),
    "eauto": ("werkzeuge/e-auto/", "🚗", "E-Auto-Ladekosten", "Zu Hause, Ladesäule oder Verbrenner?", "wk-sekundaer"),
    "vergleich": ("werkzeuge/vergleich/", "⚖️", "Geräte-Vergleich", "Zwei Geräte direkt nebeneinander", ""),
}


def werkzeug_karten(s, schluessel):
    karten = []
    for k in schluessel:
        ziel, emoji, titel, text, klasse = WERKZEUGE[k]
        href = ziel if ziel.startswith("#") else s.link(ziel)
        karten.append(f'<a class="werkzeug-karte {klasse} ripple" href="{href}"><span class="wk-emoji" aria-hidden="true">{emoji}</span>'
                      f'<strong>{e(titel)}</strong><small>{e(text)}</small>{icon("chevron", "ic wk-pfeil")}</a>')
    return "".join(karten)


def artikel_karte(s, a):
    return (f'<a class="artikel-karte ripple" href="{s.link("wissen/" + a["slug"] + "/")}"><span class="ak-emoji" aria-hidden="true">{a["emoji"]}</span>'
            f'<strong>{e(a["titel"])}</strong><small>{e(a["kurz"])}</small><span class="ak-mehr">Lesen{icon("chevron")}</span></a>')


def story(schritte, bild, name):
    """Scroll-Geschichte im Apple-Stil: Bühne bleibt stehen, Texte und Bild wechseln beim Scrollen."""
    texte = "".join(
        f'<div class="story-schritt" data-schritt="{i}"><span class="overline">{e(over)}</span><h2>{titel}</h2><p>{text}</p></div>'
        for i, (over, titel, text) in enumerate(schritte))
    return f'''<section class="story" data-story style="--schritte:{len(schritte)}" aria-label="{e(name)}">
  <div class="story-buehne">
    <div class="story-bild" aria-hidden="true">{bild}</div>
    <div class="story-texte">{texte}</div>
    <div class="story-punkte" aria-hidden="true">{"".join("<i></i>" for _ in schritte)}</div>
  </div>
</section>'''


def haus_story(s, ctx):
    gesamt = HAUSHALT_SCHNITT[2]
    bild = f'''<svg class="haus-svg" viewBox="0 0 360 270">
  <line class="boden" x1="0" y1="250" x2="360" y2="250"/>
  <path class="leitung" d="M300 250 V205 H272"/>
  <polygon class="dach" points="18,112 150,28 282,112"/>
  <rect class="hauswand" x="30" y="104" width="240" height="146" rx="8"/>
  <rect class="raum r1" x="42" y="116" width="104" height="58" rx="6"/><text class="raum-emoji" x="94" y="154">🧊</text>
  <rect class="raum r2" x="154" y="116" width="104" height="58" rx="6"/><text class="raum-emoji" x="206" y="154">📺</text>
  <rect class="raum r3" x="42" y="182" width="104" height="58" rx="6"/><text class="raum-emoji" x="94" y="220">🫧</text>
  <rect class="raum r4" x="154" y="182" width="104" height="58" rx="6"/><text class="raum-emoji" x="206" y="220">💻</text>
  <text class="raum-emoji klein r1-zusatz" x="244" y="232">📶</text>
  <g class="zaehler-box"><rect x="284" y="150" width="62" height="56" rx="10"/><text class="zaehler-zahl" x="315" y="181" data-story-zahl="{gesamt}">{zahl(gesamt)}</text><text class="zaehler-einheit" x="315" y="197">kWh</text></g>
</svg>'''
    schritte = [
        ("Dein Zuhause", "Strom fließt rund um die Uhr.", "Auch wenn gerade niemand etwas einschaltet – irgendetwas läuft immer."),
        ("Immer an", "Manche Geräte schlafen nie.", "Kühlschrank, Router und Standby laufen 8.760 Stunden im Jahr. Kleine Leistung, großer Effekt."),
        ("Volle Kraft", "Andere laufen nur kurz – aber heftig.", "Waschmaschine, Herd und Fernseher brauchen viel Leistung, wenn sie laufen."),
        ("Unterm Strich", f"Rund {zahl(gesamt)} kWh im Jahr.",
         f'Das sind etwa {euro(gesamt * ctx["preis"])} für einen 2-Personen-Haushalt. <a href="{s.link("haushalt/")}">Wie ist es bei dir?</a>'),
    ]
    return story(schritte, bild, "Wohin fließt dein Strom?")


def solar_story(s, ertrag, ersparnis):
    bild = f'''<svg class="solar-svg" viewBox="0 0 360 270">
  <defs><linearGradient id="himmel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="himmel-oben"/><stop offset="1" class="himmel-unten"/></linearGradient></defs>
  <rect class="himmel" x="0" y="0" width="360" height="250" rx="18" fill="url(#himmel)"/>
  <g class="sonne"><circle cx="180" cy="62" r="20"/><g class="strahlen"><path d="M180 30v-10M180 104v10M148 62h-10M212 62h10M157 39l-7-7M203 85l7 7M157 85l-7 7M203 39l7-7"/></g></g>
  <line class="boden" x1="0" y1="250" x2="360" y2="250"/>
  <g class="modul"><polygon points="40,206 128,186 140,232 52,252"/>
    <path class="zellen" d="M62 201l12 46M84 196l12 46M106 191l12 46M46 222l88-20"/></g>
  <path class="kabel" d="M136 228 H178 M206 228 H246"/>
  <g class="wechselrichter"><rect x="178" y="212" width="28" height="32" rx="6"/><text x="192" y="233">~</text></g>
  <polygon class="dach" points="236,150 288,112 340,150"/>
  <rect class="hauswand" x="246" y="146" width="84" height="104" rx="6"/>
  <rect class="fenster" x="262" y="166" width="52" height="40" rx="5"/><text class="raum-emoji" x="288" y="194">🧊</text>
  <text class="solar-zahl" x="288" y="236" data-story-zahl="{round(ertrag)}">{zahl(ertrag)} kWh</text>
</svg>'''
    schritte = [
        ("Schritt 1", "Die Sonne liefert Energie.", "Kostenlos und jeden Tag – auch bei Wolken kommt noch ein Teil an."),
        ("Schritt 2", "Solarmodule machen daraus Strom.", "Die Zellen wandeln Licht direkt in Gleichstrom um. Am meisten mittags und im Sommer."),
        ("Schritt 3", "Der Wechselrichter macht ihn haushaltstauglich.", "Aus Gleichstrom wird Wechselstrom – und der fließt über die Steckdose in dein Hausnetz."),
        ("Ergebnis", f"Rund {zahl(ertrag)} kWh im Jahr.",
         f"Deine Geräte nutzen den Solarstrom sofort. Mit den Startwerten oben sparst du etwa {euro(ersparnis)} pro Jahr."),
    ]
    return story(schritte, bild, "So funktioniert ein Balkonkraftwerk")


def werkzeuge_uebersicht(ctx):
    s = Seite(ctx, "werkzeuge/")
    inhalt = f"""
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🧰</div>
  <h1>Alle Werkzeuge rund um Stromkosten</h1>
  <p class="lead">Rechnen, vergleichen, spielen – kostenlos, ohne Anmeldung und direkt im Browser. Deine Eingaben bleiben auf deinem Gerät.</p>
</section>
<section class="werkzeuge werkzeuge-gross">
  {werkzeug_karten(s, ["sparcheck", "haushalt", "zaehler", "tarif", "eauto", "standby", "austausch", "vergleich", "solar", "quiz"])}
  <a class="werkzeug-karte ripple" href="{s.link('')}#rechner"><span class="wk-emoji" aria-hidden="true">🧮</span><strong>Freier Rechner</strong><small>Eigene Watt und Stunden eingeben</small>{icon('chevron', 'ic wk-pfeil')}</a>
  <a class="werkzeug-karte ripple" href="{s.link('geraete/')}"><span class="wk-emoji" aria-hidden="true">📋</span><strong>Geräte-Rechner</strong><small>52 Geräte mit typischen Werten</small>{icon('chevron', 'ic wk-pfeil')}</a>
</section>
{messgeraet_karte(ctx)}
"""
    return s, layout(s, "Stromkosten-Werkzeuge: Rechner für Haushalt, Zähler, Standby & Solar",
                     "Kostenlose Strom-Rechner: Haushalts-Check, Zählerstand und Nachzahlung, Standby-Kosten, Geräte-Austausch, Balkonkraftwerk und Quiz.",
                     inhalt, "werkzeuge")


def standby_seite(ctx):
    s = Seite(ctx, "werkzeuge/standby/")
    preis = ctx["preis"]
    watt = sum(w * n for _, _, _, w, n in STANDBY_GERAETE)
    kwh = watt * 20 * 365 / 1000
    zeilen = "".join(f"""<li class="standby-zeile"><span class="emoji-kreis" aria-hidden="true">{em}</span>
  <span class="hh-name"><b>{e(name)}</b><small>ca. {zahl(w, 1 if w % 1 else 0)} W Standby</small></span>
  <span class="stepper"><button type="button" data-schritt="-1" aria-label="{e(name)} weniger">{icon('minus')}</button>
  <output>{n}</output><button type="button" data-schritt="1" aria-label="{e(name)} mehr">{icon('plus')}</button></span>
  <input type="hidden" name="sb-{key}" value="{n}" data-watt="{w}"></li>""" for key, em, name, w, n in STANDBY_GERAETE)
    fragen = [
        ("Wie viel Standby ist normal?", "Neue Geräte dürfen im reinen Bereitschaftsmodus meist nur noch wenig verbrauchen, oft höchstens 0,5 Watt. Vernetzte und ältere Geräte liegen oft deutlich darüber."),
        ("Wie messe ich den Standby-Verbrauch?", "Mit einem Strommessgerät für die Steckdose: Gerät einstecken, ausschalten und den angezeigten Wert in Watt ablesen."),
        ("Lohnt sich eine schaltbare Steckdosenleiste?", f"Ja, wenn mehrere Geräte dranhängen. Schon 5 Watt weniger Dauerverbrauch sparen bei {zahl(preis, 2)} €/kWh rund {euro(5 * 8.76 * preis)} im Jahr."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Standby</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🔌</div>
  <h1>Standby-Rechner: Was kosten Geräte, die nie ganz aus sind?</h1>
  <p class="lead">Tippe an, welche Geräte bei dir im Bereitschaftsmodus warten. Die Werte sind typische Durchschnittswerte – nachmessen lohnt sich.</p>
</section>
<form class="rechner" data-rechner="standby" onsubmit="return false">
  <div class="ergebnis-held">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🔌</span><span class="eh-label">Standby-Kosten pro Jahr</span></div>
    <div class="eh-wert" data-aus="euro_jahr">{euro(kwh * preis)}</div>
    <div class="eh-chips">
      <span class="eh-chip"><b data-aus="watt">{zahl(watt, 1)} W</b> zusammen</span>
      <span class="eh-chip"><b data-aus="kwh_jahr">{zahl(kwh)} kWh</b> pro Jahr</span>
      <span class="eh-chip"><b data-aus="euro_10">{euro(kwh * preis * 10)}</b> in 10 Jahren</span>
    </div>
  </div>
  <div class="rechner-felder">
    {schieber("stunden", "Standby-Stunden pro Tag", 20, 1, 24, 1, "h", "20 h")}
    <ul class="hh-liste">{zeilen}</ul>
  </div>
</form>
<div class="hinweis-karte">{icon('info')}<p>Gerechnet wird: Standby-Leistung × Stunden pro Tag × 365. Mit einer schaltbaren Steckdosenleiste lässt sich der Großteil davon vermeiden.</p></div>
{produkt_karte(ctx, "Schaltbare Steckdosenleiste", "Ein Klick – und alle angeschlossenen Geräte ziehen keinen Standby-Strom mehr.", "Steckdosenleiste schaltbar", "🔌")}
{messgeraet_karte(ctx)}
<section class="abschnitt"><a class="knopf knopf-tonal ripple" href="{s.link('wissen/standby/')}">{icon('book')}Ratgeber: Alles über Standby</a></section>
{faq_html(fragen)}
"""
    return s, layout(s, "Standby-Rechner: Was kostet Standby im Jahr?",
                     "Berechne kostenlos, was deine Geräte im Standby pro Jahr kosten – Fernseher, Receiver, Konsole, Drucker und mehr.",
                     inhalt, "werkzeuge", faq_jsonld(fragen))


def austausch_seite(ctx):
    s = Seite(ctx, "werkzeuge/austausch/")
    preis = ctx["preis"]
    _, _, _, alt, neu, kosten = AUSTAUSCH_VORLAGEN[0]
    ersparnis = (alt - neu) * preis
    amort = kosten / ersparnis if ersparnis > 0 else 0
    vorlagen = "".join(
        f'<label><input type="radio" name="vorlage" value="{k}" data-alt="{a}" data-neu="{n}" data-kosten="{c}"{" checked" if i == 0 else ""}>'
        f'<span>{icon("check", "ic chip-haken")}<i aria-hidden="true">{em}</i>{e(name)}</span></label>'
        for i, (k, em, name, a, n, c) in enumerate(AUSTAUSCH_VORLAGEN))
    fragen = [
        ("Wann lohnt sich ein neuer Kühlschrank?", "Vor allem bei Geräten, die älter als etwa 15 Jahre sind. Alte Kühlgeräte verbrauchen oft doppelt so viel wie moderne. Wie schnell sich der Tausch rechnet, zeigt der Rechner."),
        ("Woher weiß ich, wie viel mein altes Gerät verbraucht?", "Am genauesten mit einem Strommessgerät: eine Woche messen und mal 52 nehmen. Für Kühlgeräte steht der Verbrauch auch auf dem Energielabel bzw. im Datenblatt."),
        ("Was ist die Amortisationszeit?", "Die Zeit, bis die Stromersparnis die Anschaffungskosten wieder eingespielt hat. Danach spart das neue Gerät jedes Jahr echtes Geld."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Austausch</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🔁</div>
  <h1>Austausch-Rechner: Lohnt sich ein neues Gerät?</h1>
  <p class="lead">Vergleiche dein altes Gerät mit einem sparsamen neuen – und sieh, nach wie vielen Jahren sich der Kauf bezahlt macht.</p>
</section>
<form class="rechner" data-rechner="austausch" onsubmit="return false">
  <div class="ergebnis-held">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🔁</span><span class="eh-label">Ersparnis pro Jahr</span></div>
    <div class="eh-wert" data-aus="ersparnis">{euro(ersparnis)}</div>
    <div class="eh-chips">
      <span class="eh-chip">bezahlt nach <b data-aus="amort">{zahl(amort, 1)} Jahren</b></span>
      <span class="eh-chip">nach 10 Jahren <b data-aus="bilanz">{euro(ersparnis * 10 - kosten)}</b></span>
    </div>
  </div>
  <div class="rechner-felder">
    <div class="regler"><div class="regler-kopf"><span>Gerät</span></div><div class="vorlagen-chips">{vorlagen}</div></div>
    {zahlenfeld("alt", "Verbrauch altes Gerät", alt, "kWh / Jahr")}
    {zahlenfeld("neu", "Verbrauch neues Gerät", neu, "kWh / Jahr")}
    {schieber("kosten", "Anschaffungskosten", kosten, 0, 2000, 10, "€")}
    {zahlenfeld("preis", "Strompreis (gilt für die ganze Seite)", preis, "€/kWh")}
  </div>
</form>
<section class="abschnitt">
  <span class="overline">Bilanz</span>
  <h2>Deine Ersparnis über 10 Jahre</h2>
  <p class="unterzeile">Ersparnis minus Anschaffung, aufsummiert – ab dem grünen Balken bist du im Plus.</p>
  <div class="bilanz-diagramm karte-flach" data-bilanz></div>
</section>
<div class="hinweis-karte">{icon('info')}<p>Die Vorlagen sind typische Werte. Den echten Verbrauch deines alten Geräts misst du am besten eine Woche lang mit einem Strommessgerät.</p></div>
{messgeraet_karte(ctx)}
<section class="abschnitt"><a class="knopf knopf-tonal ripple" href="{s.link('wissen/energielabel/')}">{icon('book')}Ratgeber: Das Energielabel verstehen</a></section>
{faq_html(fragen)}
"""
    return s, layout(s, "Austausch-Rechner: Lohnt sich ein neuer Kühlschrank, Trockner oder LED?",
                     "Rechne aus, ob sich ein neues, sparsames Gerät lohnt: Ersparnis pro Jahr, Amortisation und 10-Jahres-Bilanz.",
                     inhalt, "werkzeuge", faq_jsonld(fragen))


def zaehler_seite(ctx):
    s = Seite(ctx, "werkzeuge/zaehlerstand/")
    preis = ctx["preis"]
    heute = ctx["heute"]
    vorher = heute - datetime.timedelta(days=90)
    alt, neu, grund, abschlag = 12000, 12600, 12, 80
    proTag = (neu - alt) / 90
    jahr = proTag * 365
    kosten = jahr * preis + grund * 12
    diff = kosten - abschlag * 12
    fragen = [
        ("Wie berechne ich meine Nachzahlung?", "Hochgerechneter Jahresverbrauch × Arbeitspreis + 12 × Grundpreis ergibt die Jahreskosten. Davon ziehst du die Summe deiner Abschläge ab. Ist das Ergebnis positiv, droht eine Nachzahlung."),
        ("Wie genau ist die Hochrechnung?", "Je länger der Zeitraum zwischen den Ablesungen, desto genauer. Im Winter ist der Verbrauch meist etwas höher als im Sommer – eine Hochrechnung aus Wintermonaten fällt deshalb eher zu hoch aus."),
        ("Wo finde ich Grundpreis und Arbeitspreis?", "Auf deiner letzten Stromrechnung oder in deinem Vertrag. Der Arbeitspreis steht in Cent pro kWh, der Grundpreis meist in Euro pro Monat oder Jahr."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Zählerstand</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🔢</div>
  <h1>Zählerstand-Rechner: Droht eine Nachzahlung?</h1>
  <p class="lead">Trag zwei Zählerstände ein – der Rechner zeigt deinen Verbrauch, rechnet ihn aufs Jahr hoch und vergleicht ihn mit deinem Abschlag.</p>
</section>
<form class="rechner" data-rechner="zaehler" onsubmit="return false">
  <div class="ergebnis-held" data-zaehler-ergebnis>
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🔢</span><span class="eh-label" data-aus="label">{"Voraussichtliche Nachzahlung" if diff > 0 else "Voraussichtliches Guthaben"}</span></div>
    <div class="eh-wert" data-aus="differenz">{euro(abs(diff))}</div>
    <div class="eh-chips">
      <span class="eh-chip"><b data-aus="verbrauch">{zahl(neu - alt)} kWh</b> in <b data-aus="tage">90</b> Tagen</span>
      <span class="eh-chip"><b data-aus="pro_tag">{zahl(proTag, 1)} kWh</b> pro Tag</span>
      <span class="eh-chip">Hochrechnung <b data-aus="jahr">{zahl(jahr)} kWh</b></span>
      <span class="eh-chip">Kosten <b data-aus="kosten">{euro(kosten)}</b> / Jahr</span>
    </div>
    <p class="eh-meldung" data-aus="meldung" hidden></p>
  </div>
  <div class="rechner-felder">
    <div class="feld-paar">
      {zahlenfeld("alt", "Erster Zählerstand", alt, "kWh")}
      <label class="feld"><span class="feld-label">am</span><span class="feld-rahmen"><input type="date" name="datum_alt" value="{vorher.isoformat()}"></span></label>
    </div>
    <div class="feld-paar">
      {zahlenfeld("neu", "Aktueller Zählerstand", neu, "kWh")}
      <label class="feld"><span class="feld-label">am</span><span class="feld-rahmen"><input type="date" name="datum_neu" value="{heute.isoformat()}"></span></label>
    </div>
    {zahlenfeld("preis", "Arbeitspreis (gilt für die ganze Seite)", preis, "€/kWh")}
    {zahlenfeld("grund", "Grundpreis", grund, "€ / Monat")}
    {zahlenfeld("abschlag", "Monatlicher Abschlag", abschlag, "€ / Monat")}
  </div>
</form>
<div class="hinweis-karte">{icon('info')}<p>Die Hochrechnung ist eine Schätzung. Saisonale Schwankungen, Preisänderungen und Bonusse deines Anbieters sind nicht berücksichtigt.</p></div>
<section class="abschnitt"><a class="knopf knopf-tonal ripple" href="{s.link('wissen/stromzaehler-ablesen/')}">{icon('book')}Ratgeber: Stromzähler richtig ablesen</a></section>
{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    return s, layout(s, "Zählerstand-Rechner: Stromverbrauch hochrechnen & Nachzahlung prüfen",
                     "Zwei Zählerstände eintragen: Verbrauch pro Tag, Hochrechnung aufs Jahr und ob eine Nachzahlung oder ein Guthaben droht.",
                     inhalt, "werkzeuge", faq_jsonld(fragen))


def platzhalter(s, ctx):
    return {"root": s.wurzel, "preis": zahl(ctx["preis"], 2), "euro_1w": euro(8.76 * ctx["preis"]),
            "euro_kwh": f"{zahl(ctx['preis'] * 100, 0)} Cent"}


def wissen_uebersicht(ctx):
    s = Seite(ctx, "wissen/")
    inhalt = f"""
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">📚</div>
  <h1>Strom-Wissen: einfach erklärt</h1>
  <p class="lead">Kurze, verständliche Ratgeber rund um Stromverbrauch, Kosten und Sparen – mit Beispielen und Rechnern zum Ausprobieren.</p>
</section>
<a class="cta-karte ripple" href="{s.link('wissen/lexikon/')}"><span class="cta-icon">🔤</span><span><small>Nachschlagen</small><strong>Strom-Lexikon: {len(LEXIKON)} Begriffe von A bis Z</strong></span>{icon('chevron')}</a>
<section class="artikel-raster">{''.join(artikel_karte(s, a) for a in ARTIKEL)}</section>
{messgeraet_karte(ctx)}
"""
    return s, layout(s, "Strom-Wissen: Ratgeber zu Verbrauch, Kosten und Strom sparen",
                     "Einfach erklärt: Watt und kWh, Standby, Stromzähler ablesen, Energielabel, 30 Spartipps und normaler Stromverbrauch.",
                     inhalt, "wissen")


def wissen_artikel(ctx, a):
    s = Seite(ctx, f"wissen/{a['slug']}/")
    werte = platzhalter(s, ctx)
    abschnitte = a["abschnitte"]
    toc = "".join(f'<a class="chip ripple" href="#abschnitt-{i}">{e(h)}</a>' for i, (h, _) in enumerate(abschnitte))
    text = "".join(f'<section class="artikel-abschnitt" id="abschnitt-{i}"><h2>{e(h)}</h2>{html.format(**werte)}</section>'
                   for i, (h, html) in enumerate(abschnitte))
    fragen = [(f, antwort.format(**werte)) for f, antwort in a["fragen"]]
    woerter = sum(len(h.split()) + len(x.split()) for h, x in abschnitte)
    minuten = max(1, round(woerter / 200))
    cta_text, cta_ziel = a["werkzeug"]
    weitere = [x for x in ARTIKEL if x["slug"] != a["slug"]]
    inhalt = f"""
<div class="lesefortschritt" aria-hidden="true"><span data-lesefortschritt></span></div>
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('wissen/')}">Wissen</a>{icon('chevron')}<span>{e(a['titel'])}</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">{a['emoji']}</div>
  <h1>{e(a['titel'])}</h1>
  <p class="lead">{e(a['kurz'])}</p>
  <p class="lesezeit">{icon('clock')}{minuten} Min. Lesezeit · Stand {e(ctx['stand'])}</p>
</section>
<nav class="chip-reihe chip-scroll inhaltsverzeichnis" aria-label="Inhalt">{toc}</nav>
<article class="artikel-text">{text}</article>
<a class="cta-karte ripple" href="{s.link(cta_ziel)}"><span class="cta-icon">{icon('wrench')}</span><span><small>Jetzt ausprobieren</small><strong>{e(cta_text)}</strong></span>{icon('chevron')}</a>
{messgeraet_karte(ctx)}
{faq_html(fragen)}
<section class="abschnitt">
  <span class="overline">Weiterlesen</span>
  <h2>Mehr Strom-Wissen</h2>
  <div class="karussell">{''.join(artikel_karte(s, x) for x in weitere)}</div>
</section>
"""
    jsonld = faq_jsonld(fragen) + '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "Article", "headline": a["titel"], "description": a["beschreibung"],
        "inLanguage": "de", "dateModified": ctx["heute"].isoformat(), "mainEntityOfPage": s.kanonisch,
        "author": {"@type": "Organization", "name": ctx["name"]}}, ensure_ascii=False) + "</script>"
    return s, layout(s, f"{a['titel']} ({ctx['jahr']})", a["beschreibung"], inhalt, "wissen", jsonld)


# ---------------------------------------------------------------- Spar-Check, Tarife, E-Auto, Vergleich, Lexikon

SPAR_FRAGEN = [
    ("personen", "👨‍👩‍👧", "Wie viele Personen leben bei dir?", "Damit schätzen wir Warmwasser und Wäsche realistisch ein.",
     [("1", "🧍", "1"), ("2", "🧑‍🤝‍🧑", "2"), ("3", "👨‍👩‍👦", "3"), ("4", "👨‍👩‍👧‍👦", "4"), ("5", "🏡", "5+")]),
    ("wasser", "🚿", "Wie wird bei dir Warmwasser erzeugt?", "Steht ein kleiner Kasten unter dem Waschbecken oder an der Dusche, ist es meist ein Durchlauferhitzer.",
     [("strom", "⚡", "Mit Strom (Durchlauferhitzer, Boiler)"), ("anders", "🔥", "Über die Heizung (Gas, Fernwärme, Wärmepumpe)"), ("unklar", "🤷", "Weiß ich nicht")]),
    ("kuehl", "🧊", "Wie alt ist dein Kühlschrank?", "Alte Geräte brauchen oft doppelt so viel Strom wie neue.",
     [("neu", "✨", "Jünger als 5 Jahre"), ("mittel", "🙂", "5 bis 15 Jahre"), ("alt", "🦖", "Älter als 15 Jahre")]),
    ("trockner", "🌀", "Hast du einen Wäschetrockner?", "Kondens- und Ablufttrockner brauchen deutlich mehr als Wärmepumpentrockner.",
     [("nein", "🧺", "Nein, Wäscheständer"), ("wp", "🌀", "Ja, Wärmepumpentrockner"), ("kondens", "♨️", "Ja, Kondens- oder Ablufttrockner")]),
    ("licht", "💡", "Welche Lampen nutzt du?", "Eine LED braucht rund 85 % weniger Strom als eine Glühbirne.",
     [("led", "🔆", "Fast nur LED"), ("gemischt", "🌗", "Gemischt"), ("alt", "💡", "Noch viele Glüh- oder Halogenlampen")]),
    ("standby", "🔌", "Wie viele Geräte sind nie ganz aus?", "Fernseher, Konsole, Receiver, Drucker, Lautsprecher, Ladegeräte …",
     [("wenig", "🙂", "Kaum welche"), ("einige", "📺", "Einige"), ("viel", "🔌", "Sehr viele")]),
    ("heizen", "🌬️", "Heizt du manchmal mit Strom?", "Zum Beispiel mit Heizlüfter, Radiator oder Infrarotheizung.",
     [("nie", "🙅", "Nie"), ("manchmal", "🌤️", "Manchmal"), ("oft", "❄️", "Regelmäßig im Winter")]),
    ("waschen", "🫧", "Mit wie viel Grad wäschst du meistens?", "Das Aufheizen des Wassers macht den Großteil des Verbrauchs aus.",
     [("30", "🧊", "20–30 °C"), ("40", "🌡️", "40 °C"), ("60", "🔥", "60 °C und mehr")]),
]


def lexikon_slug(begriff):
    s = begriff.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return "".join(c if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


def sc_frage(i, key, em, frage, hilfe, optionen):
    knoepfe = "".join('<button type="button" class="sc-option ripple" data-wert="%s"><span aria-hidden="true">%s</span><b>%s</b></button>'
                      % (w, oe, e(label)) for w, oe, label in optionen)
    versteckt = "" if i == 0 else " hidden"
    return ('<fieldset class="sc-frage" data-frage="%s" data-index="%d"%s>'
            '<legend><span class="sc-emoji" aria-hidden="true">%s</span>%s</legend>'
            '<p class="sc-hilfe">%s</p><div class="sc-optionen">%s</div></fieldset>'
            % (key, i, versteckt, em, e(frage), e(hilfe), knoepfe))


def spar_check_seite(ctx):
    s = Seite(ctx, "werkzeuge/spar-check/")
    fragen = "".join(sc_frage(i, *f) for i, f in enumerate(SPAR_FRAGEN))
    faq = [
        ("Wie genau ist der Spar-Check?", "Er rechnet mit typischen Durchschnittswerten und zeigt, wo sich Sparen am wahrscheinlichsten lohnt. Für genaue Zahlen nutze die Geräte-Rechner oder ein Strommessgerät."),
        ("Werden meine Antworten gespeichert?", "Nur auf deinem Gerät, damit dein Ergebnis beim nächsten Besuch noch da ist. Es wird nichts übertragen."),
        ("Was bringt am meisten?", "Meist die großen Wärmeverbraucher: Warmwasser über Strom, elektrisches Heizen und alte Trockner. Danach folgen Licht und Standby."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Spar-Check</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🎯</div>
  <h1>Spar-Check: dein persönlicher Sparplan in 60 Sekunden</h1>
  <p class="lead">Beantworte {len(SPAR_FRAGEN)} kurze Fragen – und sieh sofort, welche Maßnahmen bei dir am meisten bringen, in Euro pro Jahr.</p>
</section>
<noscript><p class="hinweis-karte">Für den Spar-Check muss JavaScript aktiviert sein.</p></noscript>
<div class="spar-check" data-spar-check>
  <div class="sc-spiel">
    <div class="quiz-kopf"><span data-sc-schritt>Frage 1 von {len(SPAR_FRAGEN)}</span>
      <button class="knopf knopf-text" type="button" data-sc-zurueck hidden>{icon('chevron', 'ic zurueck-pfeil')}Zurück</button></div>
    <div class="fortschritt"><span data-sc-fortschritt style="width:0%"></span></div>
    {fragen}
  </div>
  <div class="sc-ergebnis" data-sc-ergebnis hidden>
    <div class="ergebnis-held">
      <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🎯</span><span class="eh-label">Dein Sparpotenzial pro Jahr</span></div>
      <div class="eh-wert" data-sc-summe>0 €</div>
      <div class="eh-chips">
        <span class="eh-chip"><b data-sc-kwh>0 kWh</b> weniger</span>
        <span class="eh-chip"><b data-sc-anzahl>0</b> Maßnahmen</span>
        <span class="eh-chip"><b data-sc-zehn>0 €</b> in 10 Jahren</span>
      </div>
    </div>
    <section class="abschnitt"><span class="overline">Dein Sparplan</span><h2>Das bringt bei dir am meisten</h2>
      <div class="sc-massnahmen" data-sc-massnahmen></div></section>
    <a class="cta-karte ripple" href="{s.link('werkzeuge/tarifvergleich/')}"><span class="cta-icon">{icon('wrench')}</span><span><small>Extra-Tipp</small><strong>Tarif prüfen – oft die schnellste Ersparnis</strong></span>{icon('chevron')}</a>
    <div class="knopf-reihe knopf-reihe-mitte">
      <button class="knopf knopf-tonal ripple" type="button" data-sc-teilen>{icon('share')}Ergebnis teilen</button>
      <button class="knopf knopf-text ripple" type="button" data-sc-neu>{icon('refresh')}Neu starten</button>
    </div>
    <p class="unterzeile">Grobe Schätzung auf Basis typischer Werte – „bis zu“-Beträge.</p>
  </div>
</div>
{faq_html(faq)}
"""
    return s, layout(s, "Spar-Check: Persönlicher Strom-Sparplan in 60 Sekunden",
                     "Beantworte 8 kurze Fragen und erhalte deinen persönlichen Strom-Sparplan mit Euro-Beträgen pro Maßnahme – kostenlos.",
                     inhalt, "werkzeuge", faq_jsonld(faq))


def kosten_balken(name):
    return f'<div class="kosten-balken karte-flach" data-balken="{name}"></div>'


def tarif_seite(ctx):
    s = Seite(ctx, "werkzeuge/tarifvergleich/")
    ap = round(ctx["preis"] * 100, 1)
    faq = [
        ("Wie vergleiche ich Stromtarife richtig?", "Rechne die Gesamtkosten für deinen Verbrauch aus: Arbeitspreis × kWh + 12 × Grundpreis. Ein Bonus gilt meist nur im ersten Jahr – vergleiche deshalb auch das zweite Jahr."),
        ("Wo finde ich meinen Arbeits- und Grundpreis?", "Auf deiner letzten Stromrechnung oder im Vertrag. Der Arbeitspreis steht in Cent pro kWh, der Grundpreis in Euro pro Monat oder Jahr."),
        ("Ist ein Anbieterwechsel kompliziert?", "Nein. Meist kündigt der neue Anbieter für dich, und die Versorgung läuft ohne Unterbrechung weiter."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Tarif-Vergleich</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🔄</div>
  <h1>Tarif-Vergleich: Lohnt sich ein Wechsel?</h1>
  <p class="lead">Vergleiche deinen aktuellen Stromtarif mit einem neuen Angebot – im ersten Jahr mit Bonus und ab dem zweiten Jahr ohne.</p>
</section>
<form class="rechner" data-rechner="tarif" onsubmit="return false">
  <div class="ergebnis-held" data-tarif-ergebnis>
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🔄</span><span class="eh-label" data-aus="label">Ersparnis im ersten Jahr</span></div>
    <div class="eh-wert" data-aus="ersparnis">0 €</div>
    <div class="eh-chips">
      <span class="eh-chip">ab Jahr 2: <b data-aus="ersparnis2">0 €</b></span>
      <span class="eh-chip">bisher <b data-aus="alt">0 €</b> / Jahr</span>
    </div>
  </div>
  <div class="rechner-felder">
    {schieber("verbrauch", "Dein Jahresverbrauch", 2500, 500, 8000, 50, "kWh", "2.500 kWh")}
    <button class="knopf knopf-tonal ripple" type="button" data-aus-haushalt hidden>{icon('pie')}Verbrauch aus „Mein Haushalt“ übernehmen</button>
    <h3 class="feld-gruppe">Dein aktueller Tarif</h3>
    <div class="feld-paar">{zahlenfeld("alt_ap", "Arbeitspreis", ap, "ct/kWh")}{zahlenfeld("alt_gp", "Grundpreis", 12, "€/Monat")}</div>
    <h3 class="feld-gruppe">Neuer Tarif</h3>
    <div class="feld-paar">{zahlenfeld("neu_ap", "Arbeitspreis", round(ap - 4, 1), "ct/kWh")}{zahlenfeld("neu_gp", "Grundpreis", 13, "€/Monat")}</div>
    {zahlenfeld("bonus", "Einmaliger Bonus", 50, "€")}
  </div>
</form>
<section class="abschnitt"><span class="overline">Kosten im Vergleich</span><h2>Was du pro Jahr zahlst</h2>{kosten_balken("tarif")}</section>
<a class="cta-karte ripple" href="{s.link('wissen/stromanbieter-wechseln/')}"><span class="cta-icon">{icon('book')}</span><span><small>Ratgeber</small><strong>Stromanbieter wechseln – so geht's</strong></span>{icon('chevron')}</a>
{faq_html(faq)}
"""
    return s, layout(s, "Stromtarif-Vergleich: Lohnt sich ein Anbieterwechsel? (Rechner)",
                     "Kostenloser Rechner: Vergleiche deinen Stromtarif mit einem neuen Angebot – inklusive Bonus, Grundpreis und Kosten ab dem zweiten Jahr.",
                     inhalt, "werkzeuge", faq_jsonld(faq))


def eauto_seite(ctx):
    s = Seite(ctx, "werkzeuge/e-auto/")
    faq = [
        ("Was kostet ein E-Auto pro 100 km?", "Verbrauch in kWh pro 100 km × Strompreis, plus etwa 10 % Ladeverluste. Bei 17 kWh und 0,35 €/kWh sind das grob 6,50 € zu Hause."),
        ("Warum rechnet der Rechner mit Ladeverlusten?", "Beim Laden geht ein Teil der Energie als Wärme verloren. Bezahlt wird der Strom aus der Steckdose, nicht nur der, der im Akku ankommt."),
        ("Welcher Preis gilt an Ladesäulen?", "Das ist je nach Anbieter, Ladetarif und Ladeleistung sehr unterschiedlich. Trag am besten den Preis ein, den du tatsächlich zahlst."),
    ]
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>E-Auto</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🚗</div>
  <h1>E-Auto-Ladekosten: zu Hause, Ladesäule oder Verbrenner?</h1>
  <p class="lead">Rechne aus, was dein E-Auto pro Jahr und pro 100 km kostet – und wie viel du gegenüber einem Benziner sparst.</p>
</section>
<form class="rechner" data-rechner="eauto" onsubmit="return false">
  <div class="ergebnis-held">
    <div class="eh-kopf"><span class="eh-emoji" aria-hidden="true">🚗</span><span class="eh-label" data-aus="label">Ersparnis gegenüber Verbrenner</span></div>
    <div class="eh-wert" data-aus="ersparnis">0 €</div>
    <div class="eh-chips">
      <span class="eh-chip">E-Auto <b data-aus="e_jahr">0 €</b> / Jahr</span>
      <span class="eh-chip"><b data-aus="e_100">0 €</b> pro 100 km</span>
      <span class="eh-chip"><b data-aus="kwh">0 kWh</b> Strom</span>
    </div>
  </div>
  <div class="rechner-felder">
    {schieber("km", "Kilometer pro Jahr", 12000, 2000, 40000, 500, "km", "12.000 km")}
    {schieber("verbrauch", "Verbrauch E-Auto", 17, 12, 30, 0.5, "kWh/100 km", "17 kWh/100 km")}
    {schieber("anteil", "Davon zu Hause geladen", 80, 0, 100, 5, "%", "80 %")}
    <div class="feld-paar">{zahlenfeld("preis", "Strompreis zu Hause", ctx["preis"], "€/kWh")}{zahlenfeld("saeule", "Ladesäule", 0.59, "€/kWh")}</div>
    <h3 class="feld-gruppe">Vergleich: Verbrenner</h3>
    <div class="feld-paar">{zahlenfeld("liter", "Verbrauch", 6.5, "l/100 km")}{zahlenfeld("sprit", "Spritpreis", 1.75, "€/l")}</div>
  </div>
</form>
<section class="abschnitt"><span class="overline">Kosten pro Jahr</span><h2>E-Auto gegen Verbrenner</h2>{kosten_balken("eauto")}</section>
<div class="hinweis-karte">{icon('info')}<p>Gerechnet mit etwa 10 % Ladeverlusten. Kosten für Wartung, Versicherung, Steuer und Anschaffung sind nicht enthalten. Der Ladesäulenpreis ist eine Annahme – trag deinen eigenen ein.</p></div>
<a class="cta-karte ripple" href="{s.link('wissen/e-auto-laden/')}"><span class="cta-icon">{icon('book')}</span><span><small>Ratgeber</small><strong>E-Auto zu Hause laden – Kosten und Tipps</strong></span>{icon('chevron')}</a>
{produkt_karte(ctx, "Typ-2-Ladekabel", "Für öffentliche Ladesäulen und Wallboxen.", "Typ 2 Ladekabel 11 kW", "🔌")}
{faq_html(faq)}
"""
    return s, layout(s, "E-Auto-Ladekosten-Rechner: Kosten pro 100 km & Vergleich mit Verbrenner",
                     "Berechne die Ladekosten deines E-Autos zu Hause und an der Ladesäule – pro Jahr, pro 100 km und im Vergleich zum Benziner.",
                     inhalt, "werkzeuge", faq_jsonld(faq))


def vergleich_seite(ctx, geraete):
    s = Seite(ctx, "werkzeuge/vergleich/")
    nach_slug = {g["slug"]: g for g in geraete}
    optionen = lambda gewaehlt: "".join(
        f'<option value="{g["slug"]}"{" selected" if g["slug"] == gewaehlt else ""}>{g["emoji"]} {e(gross(g["name"]))}</option>'
        for g in sorted(geraete, key=lambda x: gross(x["name"])))

    def spalte(seite, slug):
        g = nach_slug[slug]
        kwh = jahresverbrauch_kwh(g)
        p = ctx["preis"]
        link = s.link("geraet/" + slug + "/")
        pfeil = icon("chevron")
        return (f'<div class="vg-spalte" data-vg="{seite}">'
                f'<span class="vg-emoji" data-vg-emoji aria-hidden="true">{g["emoji"]}</span>'
                f'<strong class="vg-name" data-vg-name>{e(gross(g["name"]))}</strong>'
                f'<span class="vg-wert" data-vg-euro>{euro(kwh * p)}</span><small>pro Jahr</small>'
                f'<ul class="vg-details"><li><span>pro Monat</span><b data-vg-monat>{euro(kwh * p / 12)}</b></li>'
                f'<li><span>pro Tag</span><b data-vg-tag>{zahl(kwh * p / 365 * 100, 1)} ct</b></li>'
                f'<li><span>Verbrauch</span><b data-vg-kwh>{zahl(kwh)} kWh</b></li></ul>'
                f'<a class="knopf knopf-text" data-vg-link href="{link}">Zum Rechner{pfeil}</a></div>')
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('werkzeuge/')}">Werkzeuge</a>{icon('chevron')}<span>Vergleich</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">⚖️</div>
  <h1>Geräte-Vergleich: Was kostet mehr Strom?</h1>
  <p class="lead">Wähle zwei Geräte und vergleiche ihre typischen Stromkosten direkt nebeneinander.</p>
</section>
<form class="vergleich" data-vergleich onsubmit="return false">
  <div class="feld-paar">
    <label class="feld"><span class="feld-label">Gerät A</span><span class="feld-rahmen"><select name="a">{optionen("kuehlschrank")}</select></span></label>
    <label class="feld"><span class="feld-label">Gerät B</span><span class="feld-rahmen"><select name="b">{optionen("fernseher")}</select></span></label>
  </div>
  <div class="vg-raster">{spalte("a", "kuehlschrank")}<div class="vg-gegen" aria-hidden="true">vs</div>{spalte("b", "fernseher")}</div>
  <p class="vg-fazit" data-vg-fazit></p>
</form>
<div class="hinweis-karte">{icon('info')}<p>Verglichen werden typische Nutzungsannahmen. Auf den Geräteseiten passt du Leistung und Laufzeit an dein Gerät an.</p></div>
"""
    return s, layout(s, "Geräte-Vergleich: Stromkosten zweier Geräte direkt vergleichen",
                     "Vergleiche die Stromkosten von zwei Haushaltsgeräten nebeneinander – pro Jahr, Monat und Tag.",
                     inhalt, "werkzeuge")


def lexikon_seite(ctx):
    s = Seite(ctx, "wissen/lexikon/")
    buchstaben = sorted({b[0].upper() for b, _ in LEXIKON})
    chips = "".join(f'<a class="chip ripple" href="#buchstabe-{b}">{b}</a>' for b in buchstaben)
    gruppen = []
    for b in buchstaben:
        eintraege = "".join(
            f'<div class="lex-eintrag" id="{lexikon_slug(begriff)}" data-lex="{e(begriff.lower())} {e(text.lower())}"><dt>{e(begriff)}</dt><dd>{e(text)}</dd></div>'
            for begriff, text in LEXIKON if begriff[0].upper() == b)
        gruppen.append(f'<section class="lex-gruppe" id="buchstabe-{b}"><h2>{b}</h2><dl>{eintraege}</dl></section>')
    jsonld = '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "DefinedTermSet", "name": "Strom-Lexikon", "inLanguage": "de",
        "hasDefinedTerm": [{"@type": "DefinedTerm", "name": b, "description": t, "url": f"{s.kanonisch}#{lexikon_slug(b)}"} for b, t in LEXIKON],
    }, ensure_ascii=False) + "</script>"
    inhalt = f"""
<nav class="krumen" aria-label="Brotkrümel"><a href="{s.wurzel}">Start</a>{icon('chevron')}<a href="{s.link('wissen/')}">Wissen</a>{icon('chevron')}<span>Lexikon</span></nav>
<section class="seitenkopf">
  <div class="seiten-icon" aria-hidden="true">🔤</div>
  <h1>Strom-Lexikon: {len(LEXIKON)} Begriffe einfach erklärt</h1>
  <p class="lead">Von Abschlag bis Wirkungsgrad – die wichtigsten Begriffe rund um Stromrechnung, Zähler und Solar in einem Satz erklärt.</p>
</section>
<label class="suchleiste suchleiste-klein lex-suche">{icon('search')}<input type="search" placeholder="Begriff suchen" aria-label="Begriff suchen" data-lex-suche autocomplete="off"></label>
<nav class="chip-reihe chip-scroll" aria-label="Buchstaben">{chips}</nav>
<div class="lexikon" data-lexikon>{''.join(gruppen)}</div>
<div class="leer" data-lex-leer hidden><span aria-hidden="true">🔍</span><p>Kein Begriff gefunden.</p></div>
"""
    return s, layout(s, f"Strom-Lexikon: {len(LEXIKON)} Begriffe von Abschlag bis Wirkungsgrad",
                     "Strom-Lexikon: Arbeitspreis, Grundpreis, kWh, kWp, Smart Meter, Wechselrichter und mehr – einfach erklärt.",
                     inhalt, "wissen", jsonld)


def such_index(geraete):
    """Einträge für die globale Suche (Spotlight), relativ zur Website-Wurzel."""
    eintraege = [
        {"t": "Alle Geräte", "u": "geraete/", "e": "📋", "k": "Seite"},
        {"t": "Mein Haushalt", "u": "haushalt/", "e": "🏠", "k": "Werkzeug"},
        {"t": "Alle Werkzeuge", "u": "werkzeuge/", "e": "🧰", "k": "Seite"},
        {"t": "Strom-Wissen", "u": "wissen/", "e": "📚", "k": "Seite"},
        {"t": "Strom-Lexikon", "u": "wissen/lexikon/", "e": "🔤", "k": "Seite"},
    ]
    for key, (ziel, emoji, titel, text, _) in WERKZEUGE.items():
        if not ziel.startswith("#") and key != "haushalt":
            eintraege.append({"t": titel, "u": ziel, "e": emoji, "k": "Werkzeug", "d": text})
    eintraege += [{"t": a["titel"], "u": f"wissen/{a['slug']}/", "e": a["emoji"], "k": "Ratgeber", "d": a["kurz"]} for a in ARTIKEL]
    eintraege += [{"t": b, "u": f"wissen/lexikon/#{lexikon_slug(b)}", "e": "🔤", "k": "Lexikon", "d": t} for b, t in LEXIKON]
    return eintraege


# ---------------------------------------------------------------- App-Dateien (PWA)

def daten_js(ctx, geraete):
    daten = {
        "preis": ctx["preis"],
        "kategorien": KATEGORIEN,
        "schnitt": HAUSHALT_SCHNITT,
        "vorlage": HAUSHALT_VORLAGE,
        "solar": SOLAR_MONATE,
        "austausch": [{"k": k, "alt": a, "neu": n, "kosten": c} for k, _, _, a, n, c in AUSTAUSCH_VORLAGEN],
        "seiten": such_index(geraete),
        "tag": ctx["tag"],
        "geraete": [{"s": g["slug"], "e": g["emoji"], "n": gross(g["name"]), "nm": g["name"], "a": g["artikel"], "k": g["kategorie"],
                     "w": g["leistung_w"], "h": g["stunden"], "nw": g["nutzungen_woche"],
                     "wj": g.get("wochen_jahr", 52), "sb": g.get("standby_w", 0) or 0, "t": g["tipp"]}
                    for g in geraete],
    }
    return "window.SF=" + json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + ";\n"


def manifest(ctx):
    icons = [
        {"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ]
    kurz = [{"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"}]
    return json.dumps({
        "name": f"{ctx['name']} – Stromkosten-Rechner",
        "short_name": "Stromfresser",
        "description": "Stromkosten aller Haushaltsgeräte berechnen, Haushalt checken und sparen.",
        "lang": "de",
        "start_url": "./",
        "scope": "./",
        "id": "./",
        "display": "standalone",
        "background_color": "#F5FBF5",
        "theme_color": "#006C4C",
        "categories": ["utilities", "lifestyle"],
        "icons": icons,
        "shortcuts": [
            {"name": "Spar-Check", "short_name": "Spar-Check", "url": "werkzeuge/spar-check/", "icons": kurz},
            {"name": "Mein Haushalt", "short_name": "Haushalt", "url": "haushalt/", "icons": kurz},
            {"name": "Zählerstand-Rechner", "short_name": "Zähler", "url": "werkzeuge/zaehlerstand/", "icons": kurz},
            {"name": "Stromfresser-Quiz", "short_name": "Quiz", "url": "quiz/", "icons": kurz},
            {"name": "Balkonkraftwerk-Rechner", "short_name": "Solar", "url": "balkonkraftwerk/", "icons": kurz},
        ],
    }, ensure_ascii=False, indent=2)


def service_worker(version):
    vorab = ["./", "geraete/", "haushalt/", "wissen/", "werkzeuge/", "werkzeuge/spar-check/", "quiz/", "balkonkraftwerk/", "manifest.webmanifest",
             f"assets/style.css?v={version}", f"assets/app.js?v={version}", f"assets/daten.js?v={version}",
             "assets/icon.svg", "assets/icon-192.png"]
    return f"""// Service Worker: macht die Seite installierbar und offline nutzbar. Von build.py erzeugt.
const VERSION = "sf-{version}";
const VORAB = {json.dumps(vorab)};
const basis = self.registration.scope;

self.addEventListener("install", (ev) => {{
  ev.waitUntil(caches.open(VERSION).then((c) => c.addAll(VORAB.map((p) => new URL(p, basis)))).then(() => self.skipWaiting()));
}});

self.addEventListener("activate", (ev) => {{
  ev.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k.startsWith("sf-") && k !== VERSION).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
}});

function merken(req, res) {{
  if (res && res.ok && res.type === "basic") {{
    const kopie = res.clone();
    caches.open(VERSION).then((c) => c.put(req, kopie));
  }}
  return res;
}}

self.addEventListener("fetch", (ev) => {{
  const req = ev.request;
  if (req.method !== "GET" || !req.url.startsWith(basis)) return;
  if (req.mode === "navigate") {{
    // Seiten: zuerst Netz (immer aktuell), offline aus dem Zwischenspeicher
    ev.respondWith(fetch(req).then((res) => merken(req, res))
      .catch(() => caches.match(req).then((r) => r || caches.match(new URL("./", basis)))));
    return;
  }}
  // Dateien: sofort aus dem Speicher, im Hintergrund aktualisieren
  ev.respondWith(caches.match(req).then((gespeichert) => {{
    const netz = fetch(req).then((res) => merken(req, res)).catch(() => gespeichert);
    return gespeichert || netz;
  }}));
}});
"""


# ---------------------------------------------------------------- Bauen

def lade_geraete():
    geraete = json.loads((ROOT / "data" / "geraete.json").read_text(encoding="utf-8"))
    slugs = set()
    for g in geraete:
        for feld in ("slug", "emoji", "name", "artikel", "kategorie", "leistung_w", "stunden", "nutzungen_woche", "hinweis", "tipp", "produkt"):
            if feld not in g:
                raise ValueError(f"Gerät {g.get('slug', '?')}: Feld '{feld}' fehlt")
        if g["kategorie"] not in KATEGORIEN:
            raise ValueError(f"Gerät {g['slug']}: unbekannte Kategorie '{g['kategorie']}'")
        if g["slug"] in slugs:
            raise ValueError(f"Gerät {g['slug']}: doppelter slug")
        slugs.add(g["slug"])
    return geraete


def baue(ziel, strict=False, heute=None, cfg=None):
    cfg = cfg if cfg is not None else json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    imp = dict(cfg.get("impressum", {}))
    for feld in ("name", "strasse", "plz_ort", "email"):
        aus_umgebung = os.environ.get("IMPRESSUM_" + feld.upper(), "").strip()
        if aus_umgebung:
            imp[feld] = aus_umgebung
    cfg = dict(cfg, impressum=imp)
    fehlend = fehlende_pflichtangaben(cfg)
    if strict and fehlend:
        raise SystemExit(
            "Abbruch: In config.json fehlen Pflichtangaben fürs Impressum: " + ", ".join(fehlend) +
            ".\nOhne Impressum darf eine Website mit Werbe- oder Partnerlinks in Deutschland nicht online gehen.")
    heute = heute or datetime.date.today()
    geraete = lade_geraete()
    # Version aus allen Eingaben: ändert sich bei jeder inhaltlichen Änderung -> Browser und Service Worker laden neu
    h = hashlib.sha256()
    for datei in sorted([ROOT / "config.json", ROOT / "build.py", ROOT / "wissen.py", ROOT / "data" / "geraete.json", *(ROOT / "assets").iterdir()]):
        if datei.is_file():
            h.update(datei.read_bytes())
    h.update(heute.isoformat().encode())
    preis = float(cfg.get("strompreis_eur_kwh", 0.35))
    PREIS_STANDARD[0] = preis
    ctx = {
        "name": cfg.get("site_name", "Stromfresser-Check"),
        "base": basis_url(cfg),
        "preis": preis,
        "tag": (cfg.get("amazon_partner_tag") or "").strip(),
        "verification": (cfg.get("google_site_verification") or "").strip(),
        "adsense": (cfg.get("adsense_client_id") or "").strip(),
        "umami_id": (cfg.get("umami_website_id") or "").strip(),
        "umami_script": (cfg.get("umami_script") or "https://cloud.umami.is/script.js").strip(),
        "impressum": cfg.get("impressum", {}),
        "fehlend": fehlend,
        "jahr": heute.year,
        "stand": f"{MONATE[heute.month - 1]} {heute.year}",
        "version": h.hexdigest()[:10],
        "heute": heute,
    }

    ziel = Path(ziel)
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", ziel / "assets")

    seiten = [startseite(ctx, geraete), geraete_uebersicht(ctx, geraete), haushalt_seite(ctx, geraete),
              quiz_seite(ctx, geraete), balkonkraftwerk_seite(ctx),
              werkzeuge_uebersicht(ctx), standby_seite(ctx), austausch_seite(ctx), zaehler_seite(ctx),
              spar_check_seite(ctx), tarif_seite(ctx), eauto_seite(ctx), vergleich_seite(ctx, geraete),
              wissen_uebersicht(ctx), lexikon_seite(ctx)]
    seiten += [wissen_artikel(ctx, a) for a in ARTIKEL]
    seiten += [geraeteseite(ctx, g, geraete) for g in geraete]
    seiten += [impressum_seite(ctx), datenschutz_seite(ctx)]
    for seite, inhalt in seiten:
        datei = ziel / seite.pfad / "index.html"
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(inhalt, encoding="utf-8")
    (ziel / "404.html").write_text(fehlerseite(ctx), encoding="utf-8")
    (ziel / "assets" / "daten.js").write_text(daten_js(ctx, geraete), encoding="utf-8")
    (ziel / "manifest.webmanifest").write_text(manifest(ctx), encoding="utf-8")
    (ziel / "sw.js").write_text(service_worker(ctx["version"]), encoding="utf-8")

    indexierbar = [s for s, _ in seiten if s.pfad not in ("impressum/", "datenschutz/")]
    urls = "".join(f"<url><loc>{e(s.kanonisch)}</loc><lastmod>{heute.isoformat()}</lastmod></url>\n" for s in indexierbar)
    (ziel / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "</urlset>\n", encoding="utf-8")
    (ziel / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {ctx['base']}/sitemap.xml\n", encoding="utf-8")
    (ziel / ".nojekyll").write_text("", encoding="utf-8")
    return ctx, len(seiten)


def main():
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8")  # Umlaute in der Windows-Konsole
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="Abbruch, wenn Pflichtangaben fehlen (für die Veröffentlichung)")
    ap.add_argument("--out", default=str(ROOT / "dist"))
    args = ap.parse_args()
    ctx, n = baue(args.out, strict=args.strict)
    print(f"{n} Seiten gebaut nach {args.out} (Basis-URL {ctx['base']}, Version {ctx['version']})")
    if ctx["fehlend"]:
        print("WARNUNG: Impressum unvollständig (" + ", ".join(ctx["fehlend"]) + ") – nur als Vorschau nutzen.", file=sys.stderr)
    if not ctx["tag"]:
        print("HINWEIS: Kein amazon_partner_tag gesetzt – Links bringen noch keine Provision.", file=sys.stderr)


if __name__ == "__main__":
    main()
