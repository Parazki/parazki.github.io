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
}
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
          + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
          + "</defs></svg>")


def icon(name, cls="ic"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


NAV = [("start", "", "Start", "home"), ("geraete", "geraete/", "Geräte", "grid"),
       ("haushalt", "haushalt/", "Haushalt", "pie"), ("quiz", "quiz/", "Quiz", "quiz"),
       ("solar", "balkonkraftwerk/", "Solar", "sun")]


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
        zeilen.append(f"""<li><a class="rang-zeile ripple{klasse}" href="{s.link('geraet/' + g['slug'] + '/')}">
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
    <a class="icon-knopf ripple" href="{w}geraete/#suche" aria-label="Gerät suchen" title="Gerät suchen">{icon('search')}</a>
    <button class="icon-knopf ripple" type="button" data-preis-oeffnen aria-label="Strompreis einstellen" title="Strompreis einstellen">{icon('tune')}</button>
  </div>
</header>
<nav class="navbar" aria-label="Hauptnavigation">{nav}</nav>
<main class="inhalt">
{inhalt}
</main>
{fab}
<footer class="fuss">
  {partner}
  <p>Alle Werte sind typische Durchschnittswerte und ersetzen keine Messung. Stand: {e(ctx['stand'])}.</p>
  <p><a href="{w}impressum/">Impressum</a> · <a href="{w}datenschutz/">Datenschutz</a></p>
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
  </div>
  <form class="suchleiste" action="{s.link('geraete/')}" method="get" role="search">
    {icon('search')}<input type="search" name="q" placeholder="Gerät suchen …" aria-label="Gerät suchen" autocomplete="off">
    <button class="knopf knopf-gefuellt ripple" type="submit">Suchen</button>
  </form>
  <div class="chip-reihe chip-scroll">{favoriten}</div>
</section>

<aside class="install-karte" data-install-karte hidden>
  <span class="ik-icon">{icon('bolt')}</span>
  <div><strong>Als App installieren</strong><p>Direkt vom Startbildschirm öffnen – auch offline.</p></div>
  <button class="knopf knopf-gefuellt ripple" type="button" data-installieren-karte>Installieren</button>
</aside>

<section class="werkzeuge">
  <a class="werkzeug-karte wk-primaer ripple" href="{s.link('haushalt/')}"><span class="wk-emoji" aria-hidden="true">🏠</span><strong>Mein Haushalt</strong><small>Alle Geräte sammeln und die Gesamtkosten sehen</small>{icon('chevron', 'ic wk-pfeil')}</a>
  <a class="werkzeug-karte wk-tertiaer ripple" href="{s.link('quiz/')}"><span class="wk-emoji" aria-hidden="true">🧠</span><strong>Stromfresser-Quiz</strong><small>Was kostet mehr? Teste dein Gefühl</small>{icon('chevron', 'ic wk-pfeil')}</a>
  <a class="werkzeug-karte wk-sekundaer ripple" href="{s.link('balkonkraftwerk/')}"><span class="wk-emoji" aria-hidden="true">☀️</span><strong>Balkonkraftwerk</strong><small>Ertrag, Ersparnis und Amortisation</small>{icon('chevron', 'ic wk-pfeil')}</a>
  <a class="werkzeug-karte ripple" href="#rechner"><span class="wk-emoji" aria-hidden="true">🧮</span><strong>Freier Rechner</strong><small>Eigene Watt und Stunden eingeben</small>{icon('chevron', 'ic wk-pfeil')}</a>
</section>

<section class="abschnitt">
  <div class="abschnitt-kopf"><h2>Die größten Stromfresser</h2><a class="knopf knopf-text" href="{s.link('geraete/')}">Alle {len(geraete)}{icon('chevron')}</a></div>
  <p class="unterzeile">Typische Jahreskosten bei <span data-preis-anzeige>{preis_txt} €/kWh</span></p>
  {rangliste(s, geraete, anzahl=10)}
</section>

<section class="abschnitt">
  <h2>Wusstest du?</h2>
  <div class="karussell">{fakten_html}</div>
</section>

<section class="abschnitt" id="rechner">
  <h2>Freier Stromkosten-Rechner</h2>
  <p class="unterzeile">Leistung steht auf dem Typenschild oder in der Anleitung.</p>
  {rechner_form(ctx)}
</section>

<section class="abschnitt">
  <h2>Nach Bereich stöbern</h2>
  <div class="kategorie-raster">{kategorien}</div>
</section>

{messgeraet_karte(ctx)}
{faq_html(fragen)}
"""
    titel = f"Stromkosten-Rechner {ctx['jahr']}: Verbrauch & Kosten jedes Geräts berechnen"
    beschr = (f"Kostenloser Stromkosten-Rechner für {len(geraete)} Geräte: Verbrauch und Kosten pro Jahr und Monat, "
              "Haushalts-Check, Quiz und Spartipps. Auch als App nutzbar.")
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
  <h1><span class="h1-emoji" aria-hidden="true">{g['emoji']}</span>Wie viel Strom verbraucht {e(voll)}?</h1>
  <p class="lead">{e(gross(voll))} verbraucht bei typischer Nutzung etwa <strong>{zahl(kwh)} kWh pro Jahr</strong>.
  Bei <span data-preis-anzeige>{preis_txt} €/kWh</span> sind das rund <strong>{euro_kwh(kwh)} im Jahr</strong> bzw. <strong>{euro_kwh(kwh, 12)} im Monat</strong>.{standby_html}</p>
</section>
{rechner_form(ctx, g)}
<div class="hinweis-karte">{icon('info')}<p><strong>Annahme:</strong> {e(g['hinweis'])} Passe die Regler an dein Gerät an.</p></div>
<section class="abschnitt">
  <div class="tipp-karte">
    <div class="tipp-kopf">{icon('bulb')}<h2>So sparst du Strom</h2></div>
    <p>{e(g['tipp'])}</p>
  </div>
</section>
{produkt_karte(ctx, p['label'], p['text'], p['query'], g['emoji'])}
<section class="abschnitt">
  <h2>{e(g['kategorie'])} im Vergleich</h2>
  <p class="unterzeile">Typische Jahreskosten aller Geräte dieses Bereichs</p>
  {rangliste(s, kategorie, markiert=g['slug'])}
</section>
<section class="abschnitt">
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
  <h1><span class="h1-emoji" aria-hidden="true">🏠</span>Mein Haushalt: Stromkosten aller Geräte</h1>
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
  <h1><span class="h1-emoji" aria-hidden="true">🧠</span>Stromfresser-Quiz: Was kostet mehr?</h1>
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
    return s, layout(s, titel, beschr, inhalt, "quiz")


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
  <h1><span class="h1-emoji" aria-hidden="true">☀️</span>Balkonkraftwerk-Rechner: Lohnt es sich für dich?</h1>
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
    return s, layout(s, titel, beschr, inhalt, "solar", faq_jsonld(fragen))


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


# ---------------------------------------------------------------- App-Dateien (PWA)

def daten_js(ctx, geraete):
    daten = {
        "preis": ctx["preis"],
        "kategorien": KATEGORIEN,
        "schnitt": HAUSHALT_SCHNITT,
        "vorlage": HAUSHALT_VORLAGE,
        "solar": SOLAR_MONATE,
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
            {"name": "Mein Haushalt", "short_name": "Haushalt", "url": "haushalt/", "icons": kurz},
            {"name": "Stromfresser-Quiz", "short_name": "Quiz", "url": "quiz/", "icons": kurz},
            {"name": "Balkonkraftwerk-Rechner", "short_name": "Solar", "url": "balkonkraftwerk/", "icons": kurz},
        ],
    }, ensure_ascii=False, indent=2)


def service_worker(version):
    vorab = ["./", "geraete/", "haushalt/", "quiz/", "balkonkraftwerk/", "manifest.webmanifest",
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


def baue(ziel, strict=False, heute=None):
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    fehlend = fehlende_pflichtangaben(cfg)
    if strict and fehlend:
        raise SystemExit(
            "Abbruch: In config.json fehlen Pflichtangaben fürs Impressum: " + ", ".join(fehlend) +
            ".\nOhne Impressum darf eine Website mit Werbe- oder Partnerlinks in Deutschland nicht online gehen.")
    heute = heute or datetime.date.today()
    geraete = lade_geraete()
    # Version aus allen Eingaben: ändert sich bei jeder inhaltlichen Änderung -> Browser und Service Worker laden neu
    h = hashlib.sha256()
    for datei in sorted([ROOT / "config.json", ROOT / "build.py", ROOT / "data" / "geraete.json", *(ROOT / "assets").iterdir()]):
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
        "impressum": cfg.get("impressum", {}),
        "fehlend": fehlend,
        "jahr": heute.year,
        "stand": f"{MONATE[heute.month - 1]} {heute.year}",
        "version": h.hexdigest()[:10],
    }

    ziel = Path(ziel)
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", ziel / "assets")

    seiten = [startseite(ctx, geraete), geraete_uebersicht(ctx, geraete), haushalt_seite(ctx, geraete),
              quiz_seite(ctx, geraete), balkonkraftwerk_seite(ctx)]
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
