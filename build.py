#!/usr/bin/env python3
"""Baut die statische Website "Stromfresser-Check" nach dist/.

Nur Python-Standardbibliothek, keine API, kein Server. Aufruf:
    python build.py            # lokale Vorschau (Platzhalter erlaubt)
    python build.py --strict   # Veröffentlichung: bricht ab, wenn das Impressum fehlt
"""
import argparse
import datetime
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


# ---------------------------------------------------------------- Rechnen

def nutzungsstunden(g):
    return min(g["stunden"] * g["nutzungen_woche"] * g.get("wochen_jahr", 52), STUNDEN_JAHR)


def jahresverbrauch_kwh(g):
    """Gleiche Formel wie in assets/app.js (rechneGeraet)."""
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


def produkt_box(ctx, label, text, query):
    stern = "*" if ctx["tag"] else ""
    rel = "sponsored nofollow noopener" if ctx["tag"] else "nofollow noopener"
    return f"""
<aside class="produkt">
  <div>
    <h3>{e(label)}</h3>
    <p>{e(text)}</p>
  </div>
  <a class="knopf" href="{e(amazon_link(ctx, query))}" rel="{rel}" target="_blank">Bei Amazon ansehen{stern}</a>
</aside>"""


def messgeraet_box(ctx):
    return produkt_box(ctx, "Echten Verbrauch messen statt schätzen",
                       "Ein Strommessgerät für die Steckdose zeigt dir Watt und kWh deines Geräts direkt an – "
                       "einfache Modelle kosten oft unter 20 €.",
                       "Strommessgerät Steckdose")


def faq_html(fragen):
    teile = "".join(f"<details><summary>{e(f)}</summary><p>{e(a)}</p></details>" for f, a in fragen)
    return f'<section class="faq"><h2>Häufige Fragen</h2>{teile}</section>'


def faq_jsonld(fragen):
    daten = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for f, a in fragen],
    }
    return '<script type="application/ld+json">' + json.dumps(daten, ensure_ascii=False) + "</script>"


def layout(seite, titel, beschreibung, inhalt, extra_head="", index=True):
    ctx = seite.ctx
    w = seite.wurzel
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
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="{e(beschreibung)}">
<link rel="canonical" href="{e(seite.kanonisch)}">
<meta property="og:title" content="{e(titel)}">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(seite.kanonisch)}">
<link rel="icon" href="{w}assets/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{w}assets/style.css">
{chr(10).join(meta)}
{extra_head}
</head>
<body>
{entwurf}
<header class="kopf">
  <div class="rahmen kopf-innen">
    <a class="logo" href="{w}"><span aria-hidden="true">⚡</span> {e(ctx['name'])}</a>
    <nav>
      <a href="{w}#geraete">Geräte</a>
      <a href="{w}balkonkraftwerk/">Balkonkraftwerk</a>
    </nav>
  </div>
</header>
<main class="rahmen">
{inhalt}
</main>
<footer class="fuss">
  <div class="rahmen">
    {partner}
    <p>Alle Werte sind typische Durchschnittswerte und ersetzen keine Messung. Stand: {e(ctx['stand'])}.</p>
    <p><a href="{w}impressum/">Impressum</a> · <a href="{w}datenschutz/">Datenschutz</a></p>
  </div>
</footer>
<script src="{w}assets/app.js" defer></script>
</body>
</html>
"""


def rechner_form(ctx, g=None):
    """Rechner-Formular. Ohne g: freier Rechner mit neutralen Startwerten."""
    g = g or {"leistung_w": 100, "stunden": 3, "nutzungen_woche": 7, "wochen_jahr": 52, "standby_w": 0}
    preis = ctx["preis"]
    kwh = jahresverbrauch_kwh(g)
    sb = standby_kwh(g)

    def feld(name, label, wert, einheit, schritt="any"):
        return f"""<label><span>{label}</span>
      <span class="eingabe"><input type="number" name="{name}" value="{wert:g}" min="0" step="{schritt}" inputmode="decimal"><em>{einheit}</em></span></label>"""

    return f"""
<form class="rechner" data-rechner="geraet" onsubmit="return false">
  <div class="felder">
    {feld("leistung", "Leistung im Betrieb", g["leistung_w"], "Watt")}
    {feld("stunden", "Laufzeit pro Nutzung", g["stunden"], "Stunden")}
    {feld("nutzungen", "Nutzungen pro Woche", g["nutzungen_woche"], "× / Woche")}
    {feld("wochen", "Wochen pro Jahr", g.get("wochen_jahr", 52), "Wochen")}
    {feld("standby", "Standby-Leistung", g.get("standby_w", 0) or 0, "Watt")}
    {feld("preis", "Strompreis", preis, "€/kWh")}
  </div>
  <div class="ergebnis" aria-live="polite">
    <div><span>Pro Jahr</span><strong data-aus="euro_jahr">{euro(kwh * preis)}</strong><small data-aus="kwh_jahr">{zahl(kwh)} kWh</small></div>
    <div><span>Pro Monat</span><strong data-aus="euro_monat">{euro(kwh * preis / 12)}</strong><small data-aus="kwh_monat">{zahl(kwh / 12, 1)} kWh</small></div>
    <div><span>Davon Standby</span><strong data-aus="euro_standby">{euro(sb * preis)}</strong><small data-aus="kwh_standby">{zahl(sb, 1)} kWh</small></div>
  </div>
</form>"""


# ---------------------------------------------------------------- Seiten

def geraete_tabelle(seite, geraete):
    ctx = seite.ctx
    zeilen = []
    for g in sorted(geraete, key=jahresverbrauch_kwh, reverse=True):
        kwh = jahresverbrauch_kwh(g)
        zeilen.append(f"""<tr><td><a href="{seite.link('geraet/' + g['slug'] + '/')}">{e(gross(g['name']))}</a></td>
<td class="zahl">{zahl(kwh)} kWh</td><td class="zahl">{euro(kwh * ctx['preis'])}</td></tr>""")
    return f"""<div class="tabelle"><table>
<thead><tr><th>Gerät</th><th class="zahl">Verbrauch / Jahr</th><th class="zahl">Kosten / Jahr</th></tr></thead>
<tbody>{''.join(zeilen)}</tbody></table></div>"""


def startseite(ctx, geraete):
    s = Seite(ctx, "")
    preis_txt = zahl(ctx["preis"], 2)
    gruppen = []
    for kat in KATEGORIEN:
        liste = [g for g in geraete if g["kategorie"] == kat]
        if not liste:
            continue
        links = "".join(f'<li><a href="{s.link("geraet/" + g["slug"] + "/")}">{e(gross(g["name"]))}</a></li>' for g in liste)
        gruppen.append(f'<div class="gruppe"><h3>{e(kat)}</h3><ul>{links}</ul></div>')
    fragen = [
        ("Wie berechne ich die Stromkosten eines Geräts?",
         "Leistung in Watt × Betriebsstunden ÷ 1000 ergibt die Kilowattstunden (kWh). Multipliziert mit deinem Strompreis pro kWh erhältst du die Kosten. "
         "Beispiel: 100 W × 3 Stunden täglich × 365 Tage ÷ 1000 = 109,5 kWh im Jahr."),
        ("Welcher Strompreis ist voreingestellt?",
         f"Als Annahme {preis_txt} €/kWh. Trag am besten den Arbeitspreis aus deiner eigenen Stromrechnung ein – er steht dort in Cent pro kWh."),
        ("Was kostet Standby im Jahr?",
         f"Jedes Watt Dauer-Standby sind 8,76 kWh im Jahr – bei {preis_txt} €/kWh rund {euro(8.76 * ctx['preis'])}. "
         "Zehn Geräte mit je 2 W Standby kosten so schnell über 50 € im Jahr."),
        ("Wie finde ich die Leistung meines Geräts heraus?",
         "Auf dem Typenschild steht meist die maximale Leistung. Der tatsächliche Verbrauch liegt oft darunter. Am genauesten misst ein Strommessgerät für die Steckdose."),
    ]
    inhalt = f"""
<section class="held">
  <h1>Stromkosten-Rechner: Was kostet dein Gerät wirklich?</h1>
  <p class="lead">Gib Leistung und Nutzungsdauer ein und sieh sofort, was ein Gerät pro Jahr und pro Monat an Strom kostet – inklusive Standby. Kostenlos, ohne Anmeldung.</p>
</section>
{rechner_form(ctx)}
{messgeraet_box(ctx)}
<section id="geraete">
  <h2>Stromverbrauch typischer Haushaltsgeräte</h2>
  <p>Klick auf ein Gerät für den Rechner mit passenden Startwerten und konkrete Spartipps. Kosten bei {preis_txt} €/kWh.</p>
  <div class="gruppen">{''.join(gruppen)}</div>
  <h2>Die größten Stromfresser im Vergleich</h2>
  {geraete_tabelle(s, geraete)}
</section>
<section class="hinweisbox">
  <h2>Lohnt sich ein Balkonkraftwerk?</h2>
  <p>Mit einem Steckersolargerät erzeugst du einen Teil deines Stroms selbst. <a href="{s.link('balkonkraftwerk/')}">Zum Balkonkraftwerk-Rechner →</a></p>
</section>
{faq_html(fragen)}
"""
    titel = f"Stromkosten-Rechner {ctx['jahr']}: Verbrauch & Kosten jedes Geräts berechnen"
    beschr = "Kostenloser Stromkosten-Rechner: Berechne Verbrauch und Kosten pro Jahr und Monat für Kühlschrank, Fernseher, Heizlüfter und über 30 weitere Geräte – mit Spartipps."
    return s, layout(s, titel, beschr, inhalt, faq_jsonld(fragen))


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
    aehnlich = [x for x in geraete if x["kategorie"] == g["kategorie"] and x["slug"] != g["slug"]][:6]
    aehnlich_html = "".join(
        f'<li><a href="{s.link("geraet/" + x["slug"] + "/")}">{e(gross(x["name"]))}</a> – ca. {euro(jahresverbrauch_kwh(x) * preis)} / Jahr</li>'
        for x in aehnlich)
    fragen = [
        (f"Wie viel Strom verbraucht {voll} im Jahr?",
         f"Bei typischer Nutzung etwa {zahl(kwh)} kWh im Jahr. Annahme: {g['hinweis']}"),
        (f"Was kostet {voll} im Monat?",
         f"Bei einem Strompreis von {preis_txt} €/kWh rund {euro(kosten / 12)} pro Monat bzw. {euro(kosten)} pro Jahr.{standby_satz}"),
        (f"{gross(name)}: Wie kann ich Strom sparen?", g["tipp"]),
    ]
    p = g["produkt"]
    inhalt = f"""
<nav class="krumen"><a href="{s.wurzel}">Start</a> › <a href="{s.wurzel}#geraete">{e(g['kategorie'])}</a> › {e(gross(name))}</nav>
<section class="held">
  <h1>Wie viel Strom verbraucht {e(voll)}?</h1>
  <p class="lead">{e(gross(voll))} verbraucht bei typischer Nutzung etwa <strong>{zahl(kwh)} kWh pro Jahr</strong>.
  Bei {preis_txt} €/kWh sind das rund <strong>{euro(kosten)} im Jahr</strong> bzw. <strong>{euro(kosten / 12)} im Monat</strong>.{e(standby_satz)}</p>
  <p class="annahme"><strong>Annahme:</strong> {e(g['hinweis'])} Passe die Werte unten an dein Gerät an.</p>
</section>
<h2>Stromkosten berechnen: {e(gross(name))}</h2>
{rechner_form(ctx, g)}
<section>
  <h2>So sparst du Strom</h2>
  <p>{e(g['tipp'])}</p>
</section>
{produkt_box(ctx, p['label'], p['text'], p['query'])}
{messgeraet_box(ctx)}
{f'<section><h2>Ähnliche Geräte</h2><ul class="liste">{aehnlich_html}</ul></section>' if aehnlich_html else ''}
{faq_html(fragen)}
"""
    titel = f"{gross(name)}: Stromverbrauch & Kosten pro Jahr berechnen ({ctx['jahr']})"
    beschr = (f"{gross(voll)} verbraucht ca. {zahl(kwh)} kWh im Jahr – rund {euro(kosten)}. "
              f"Mit Rechner für deine eigenen Werte und Spartipps.")
    return s, layout(s, titel, beschr, inhalt, faq_jsonld(fragen))


def balkonkraftwerk_seite(ctx):
    s = Seite(ctx, "balkonkraftwerk/")
    preis = ctx["preis"]
    # Startwerte, identisch mit den vorausgewählten Optionen unten und mit assets/app.js (rechneBkw)
    kwp = min(900, 800 * 1.15) / 1000
    ertrag = kwp * 950 * 1.0 * 1.0
    ersparnis = ertrag * 0.4 * preis
    amort = 400 / ersparnis
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
<nav class="krumen"><a href="{s.wurzel}">Start</a> › Balkonkraftwerk</nav>
<section class="held">
  <h1>Balkonkraftwerk-Rechner: Lohnt es sich für dich?</h1>
  <p class="lead">Berechne Ertrag, jährliche Ersparnis und Amortisationszeit deines Balkonkraftwerks – mit Ausrichtung, Region und Eigenverbrauch.</p>
</section>
<form class="rechner" data-rechner="bkw" onsubmit="return false">
  <div class="felder">
    <label><span>Modulleistung gesamt</span><span class="eingabe"><input type="number" name="modul" value="900" min="0" step="any" inputmode="decimal"><em>Wp</em></span></label>
    <label><span>Wechselrichter</span><span class="eingabe"><input type="number" name="wr" value="800" min="0" step="any" inputmode="decimal"><em>Watt</em></span></label>
    <label><span>Region</span><select name="region">
      <option value="900">Norddeutschland</option>
      <option value="950" selected>Mitte</option>
      <option value="1050">Süddeutschland</option></select></label>
    <label><span>Ausrichtung</span><select name="ausrichtung">
      <option value="1" selected>Süd</option>
      <option value="0.95">Südost / Südwest</option>
      <option value="0.8">Ost / West</option>
      <option value="0.6">Nord</option></select></label>
    <label><span>Montage</span><select name="montage">
      <option value="1" selected>Schräg (ca. 30°)</option>
      <option value="0.9">Flach (ca. 10°)</option>
      <option value="0.7">Senkrecht am Balkon</option></select></label>
    <label><span>Eigenverbrauch</span><span class="eingabe"><input type="number" name="eigen" value="40" min="0" max="100" step="any" inputmode="decimal"><em>%</em></span></label>
    <label><span>Strompreis</span><span class="eingabe"><input type="number" name="preis" value="{preis:g}" min="0" step="any" inputmode="decimal"><em>€/kWh</em></span></label>
    <label><span>Anschaffungskosten</span><span class="eingabe"><input type="number" name="kosten" value="400" min="0" step="any" inputmode="decimal"><em>€</em></span></label>
  </div>
  <div class="ergebnis" aria-live="polite">
    <div><span>Ertrag / Jahr</span><strong data-aus="ertrag">{zahl(ertrag)} kWh</strong><small>erzeugter Solarstrom</small></div>
    <div><span>Ersparnis / Jahr</span><strong data-aus="ersparnis">{euro(ersparnis)}</strong><small data-aus="eigen_kwh">{zahl(ertrag * 0.4)} kWh selbst genutzt</small></div>
    <div><span>Amortisation</span><strong data-aus="amort">{zahl(amort, 1)} Jahre</strong><small>bis sich das Gerät bezahlt hat</small></div>
  </div>
</form>
<p class="annahme">Grobe Schätzung mit Durchschnittswerten für Deutschland. Verschattung, Wetter und dein Verbrauchsprofil können das Ergebnis stark verändern. Liegt die Modulleistung deutlich über der Wechselrichterleistung, rechnet der Rechner mit einer Begrenzung.</p>
<section>
  <h2>So holst du mehr aus deinem Balkonkraftwerk</h2>
  <p>Lass Waschmaschine, Geschirrspüler und Ladegeräte mittags laufen, wenn die Sonne scheint – so steigt dein Eigenverbrauch und damit die Ersparnis. Eine schattenfreie Südausrichtung mit etwa 30° Neigung bringt den höchsten Ertrag.</p>
</section>
{produkt_box(ctx, "Balkonkraftwerk-Komplettsets", "Sets mit Modulen, Wechselrichter und Kabel – achte auf 800-W-Wechselrichter und passende Halterung für deinen Balkon.", "Balkonkraftwerk 800W Komplettset")}
{messgeraet_box(ctx)}
{faq_html(fragen)}
"""
    titel = f"Balkonkraftwerk-Rechner {ctx['jahr']}: Ertrag, Ersparnis & Amortisation"
    beschr = "Lohnt sich ein Balkonkraftwerk? Berechne kostenlos Ertrag, jährliche Ersparnis und Amortisationszeit – mit Ausrichtung, Region und Eigenverbrauch."
    return s, layout(s, titel, beschr, inhalt, faq_jsonld(fragen))


def impressum_seite(ctx):
    s = Seite(ctx, "impressum/")
    imp = ctx["impressum"]
    inhalt = f"""
<h1>Impressum</h1>
<p>Angaben gemäß § 5 DDG</p>
<p>{e(imp.get('name', ''))}<br>{e(imp.get('strasse', ''))}<br>{e(imp.get('plz_ort', ''))}</p>
<h2>Kontakt</h2>
<p>E-Mail: {e(imp.get('email', ''))}</p>
<h2>Verantwortlich für den Inhalt</h2>
<p>{e(imp.get('name', ''))}, Anschrift wie oben.</p>
<h2>Haftung für Inhalte</h2>
<p>Die Inhalte dieser Seite wurden mit Sorgfalt erstellt. Alle Verbrauchs- und Kostenangaben sind jedoch Durchschnittswerte und Schätzungen; für Richtigkeit, Vollständigkeit und Aktualität wird keine Gewähr übernommen.</p>
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
<h1>Datenschutzerklärung</h1>
<h2>Verantwortlicher</h2>
<p>{e(imp.get('name', ''))}, {e(imp.get('strasse', ''))}, {e(imp.get('plz_ort', ''))}, E-Mail: {e(imp.get('email', ''))}</p>
<h2>Hosting</h2>
<p>Diese Website wird bei GitHub Pages gehostet (GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). Beim Aufruf der Seiten verarbeitet GitHub technisch notwendige Daten wie deine IP-Adresse, um die Seite auszuliefern und die Sicherheit zu gewährleisten (berechtigtes Interesse, Art. 6 Abs. 1 lit. f DSGVO). Details: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement" rel="nofollow noopener">Datenschutzerklärung von GitHub</a>.</p>
<h2>Rechner</h2>
<p>Alle Berechnungen laufen ausschließlich in deinem Browser. Deine Eingaben werden nicht gespeichert und nicht übertragen. Diese Website setzt selbst keine Cookies.</p>
<h2>Amazon-Partnerprogramm</h2>
<p>Diese Website enthält Links zu Amazon.de. Als Teilnehmer des Amazon-Partnerprogramms (Amazon Europe Core S.à r.l. und weitere Amazon-Gesellschaften) erhalten wir für qualifizierte Käufe eine Provision. Erst wenn du einen solchen Link anklickst, gelangst du zu Amazon; Amazon kann dann Cookies setzen, um die Herkunft der Bestellung nachzuvollziehen. Es gelten die Datenschutzbestimmungen von Amazon.</p>
{werbung}
<h2>Deine Rechte</h2>
<p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht auf Beschwerde bei einer Datenschutz-Aufsichtsbehörde.</p>
"""
    return s, layout(s, "Datenschutzerklärung", "Datenschutzerklärung", inhalt, index=False)


def fehlerseite(ctx):
    # GitHub Pages liefert 404.html für alle Pfade aus – deshalb absolute Links.
    s = Seite(ctx, "")
    s.wurzel = ctx["base"] + "/"
    inhalt = f"""<section class="held"><h1>Seite nicht gefunden</h1>
<p class="lead">Diese Seite gibt es nicht (mehr). <a href="{s.wurzel}">Zum Stromkosten-Rechner →</a></p></section>"""
    return layout(s, "Seite nicht gefunden", "Seite nicht gefunden", inhalt, index=False)


# ---------------------------------------------------------------- Bauen

def lade_geraete():
    geraete = json.loads((ROOT / "data" / "geraete.json").read_text(encoding="utf-8"))
    slugs = set()
    for g in geraete:
        for feld in ("slug", "name", "artikel", "kategorie", "leistung_w", "stunden", "nutzungen_woche", "hinweis", "tipp", "produkt"):
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
    ctx = {
        "name": cfg.get("site_name", "Stromfresser-Check"),
        "base": basis_url(cfg),
        "preis": float(cfg.get("strompreis_eur_kwh", 0.35)),
        "tag": (cfg.get("amazon_partner_tag") or "").strip(),
        "verification": (cfg.get("google_site_verification") or "").strip(),
        "adsense": (cfg.get("adsense_client_id") or "").strip(),
        "impressum": cfg.get("impressum", {}),
        "fehlend": fehlend,
        "jahr": heute.year,
        "stand": f"{MONATE[heute.month - 1]} {heute.year}",
    }
    geraete = lade_geraete()

    ziel = Path(ziel)
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", ziel / "assets")

    seiten = [startseite(ctx, geraete), balkonkraftwerk_seite(ctx)]
    seiten += [geraeteseite(ctx, g, geraete) for g in geraete]
    seiten += [impressum_seite(ctx), datenschutz_seite(ctx)]
    for seite, inhalt in seiten:
        datei = ziel / seite.pfad / "index.html"
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(inhalt, encoding="utf-8")
    (ziel / "404.html").write_text(fehlerseite(ctx), encoding="utf-8")

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
    print(f"{n} Seiten gebaut nach {args.out} (Basis-URL {ctx['base']})")
    if ctx["fehlend"]:
        print("WARNUNG: Impressum unvollständig (" + ", ".join(ctx["fehlend"]) + ") – nur als Vorschau nutzen.", file=sys.stderr)
    if not ctx["tag"]:
        print("HINWEIS: Kein amazon_partner_tag gesetzt – Links bringen noch keine Provision.", file=sys.stderr)


if __name__ == "__main__":
    main()
