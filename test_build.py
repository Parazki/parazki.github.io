#!/usr/bin/env python3
"""Tests für build.py – nur Standardbibliothek. Aufruf: python test_build.py"""
import datetime
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402


class Rechnen(unittest.TestCase):
    def test_dauerbetrieb(self):
        g = {"leistung_w": 18, "stunden": 24, "nutzungen_woche": 7}
        self.assertAlmostEqual(build.jahresverbrauch_kwh(g), 18 * 24 * 7 * 52 / 1000)

    def test_standby_fuellt_restliche_stunden(self):
        g = {"leistung_w": 100, "stunden": 1, "nutzungen_woche": 7, "standby_w": 1}
        nutz = 7 * 52
        self.assertAlmostEqual(build.jahresverbrauch_kwh(g), (100 * nutz + 1 * (8760 - nutz)) / 1000)
        self.assertAlmostEqual(build.standby_kwh(g), (8760 - nutz) / 1000)

    def test_saison(self):
        g = {"leistung_w": 2000, "stunden": 2, "nutzungen_woche": 7, "wochen_jahr": 20}
        self.assertAlmostEqual(build.jahresverbrauch_kwh(g), 2000 * 2 * 7 * 20 / 1000)

    def test_nie_mehr_als_ein_jahr(self):
        g = {"leistung_w": 10, "stunden": 24, "nutzungen_woche": 14, "standby_w": 5}
        self.assertAlmostEqual(build.jahresverbrauch_kwh(g), 10 * 8760 / 1000)

    def test_deutsche_zahlen(self):
        self.assertEqual(build.zahl(1234.5, 1), "1.234,5")
        self.assertEqual(build.euro(55.123), "55,12 €")
        self.assertEqual(build.euro(1234.4), "1.234 €")


class BasisUrl(unittest.TestCase):
    def setUp(self):
        self.alt = build.os.environ.pop("GITHUB_REPOSITORY", None)

    def tearDown(self):
        build.os.environ.pop("GITHUB_REPOSITORY", None)
        if self.alt is not None:
            build.os.environ["GITHUB_REPOSITORY"] = self.alt

    def test_projektseite(self):
        build.os.environ["GITHUB_REPOSITORY"] = "MaxMuster/stromfresser-check"
        self.assertEqual(build.basis_url({"base_url": "auto"}), "https://maxmuster.github.io/stromfresser-check")

    def test_nutzerseite(self):
        build.os.environ["GITHUB_REPOSITORY"] = "MaxMuster/maxmuster.github.io"
        self.assertEqual(build.basis_url({"base_url": "auto"}), "https://maxmuster.github.io")

    def test_eigene_domain(self):
        self.assertEqual(build.basis_url({"base_url": "https://example.de/"}), "https://example.de")


class Bauen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.ziel = Path(cls.tmp.name) / "dist"
        cls.ctx, cls.anzahl = build.baue(cls.ziel, heute=datetime.date(2026, 10, 11))
        cls.geraete = build.lade_geraete()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_jede_geraeteseite_existiert(self):
        for g in self.geraete:
            datei = self.ziel / "geraet" / g["slug"] / "index.html"
            self.assertTrue(datei.exists(), g["slug"])
            text = datei.read_text(encoding="utf-8")
            self.assertIn("Wie viel Strom verbraucht", text)
            self.assertIn("data-zum-haushalt", text)
            self.assertIn('data-rechner="geraet"', text)

    def test_grundseiten(self):
        for pfad in ("index.html", "geraete/index.html", "haushalt/index.html", "quiz/index.html",
                     "balkonkraftwerk/index.html", "impressum/index.html",
                     "datenschutz/index.html", "404.html", "sitemap.xml", "robots.txt",
                     "manifest.webmanifest", "sw.js", "assets/daten.js",
                     "assets/app.js", "assets/style.css", ".nojekyll"):
            self.assertTrue((self.ziel / pfad).exists(), pfad)

    def test_sitemap_vollstaendig(self):
        xml = (self.ziel / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(xml.count("<url>"), len(self.geraete) + 16 + len(build.ARTIKEL))
        self.assertNotIn("impressum", xml)

    def test_faq_jsonld_gueltig(self):
        text = (self.ziel / "geraet" / "kuehlschrank" / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        daten = json.loads(m.group(1))
        self.assertEqual(daten["@type"], "FAQPage")
        self.assertEqual(len(daten["mainEntity"]), 5)

    def test_relative_links_funktionieren(self):
        text = (self.ziel / "geraet" / "kuehlschrank" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="../../assets/style.css?v=', text)
        for ziel in re.findall(r'href="(\.\./\.\./geraet/[^"]+)"', text):
            self.assertTrue((self.ziel / "geraet" / "kuehlschrank" / ziel / "index.html").resolve().exists(), ziel)

    def test_navigation_markiert_aktive_seite(self):
        for pfad, ziel in (("index.html", "./"), ("quiz/index.html", "../werkzeuge/"), ("geraet/kuehlschrank/index.html", "../../geraete/"),
                            ("wissen/standby/index.html", "../../wissen/"), ("werkzeuge/zaehlerstand/index.html", "../../werkzeuge/")):
            text = (self.ziel / pfad).read_text(encoding="utf-8")
            self.assertIn(f'href="{ziel}" aria-current="page"', text, pfad)
            self.assertEqual(text.count('aria-current="page"'), 1, pfad)

    def test_manifest_installierbar(self):
        m = json.loads((self.ziel / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(m["display"], "standalone")
        self.assertEqual(m["start_url"], "./")
        groessen = {i["sizes"] for i in m["icons"]}
        self.assertTrue({"192x192", "512x512"} <= groessen)
        self.assertTrue(any(i["purpose"] == "maskable" for i in m["icons"]))
        for i in m["icons"] + [s["icons"][0] for s in m["shortcuts"]]:
            self.assertTrue((self.ziel / i["src"]).exists(), i["src"])
        for s in m["shortcuts"]:
            self.assertTrue((self.ziel / s["url"] / "index.html").exists(), s["url"])

    def test_icons_sind_png(self):
        for name in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
            self.assertEqual((self.ziel / "assets" / name).read_bytes()[:8], b"\x89PNG\r\n\x1a\n", name)

    def test_service_worker_vorab_dateien_existieren(self):
        sw = (self.ziel / "sw.js").read_text(encoding="utf-8")
        vorab = json.loads(re.search(r"const VORAB = (\[.*?\]);", sw).group(1))
        for pfad in vorab:
            datei = self.ziel / pfad.split("?")[0]
            if pfad.endswith("/") or pfad == "./":
                datei = datei / "index.html"
            self.assertTrue(datei.exists(), pfad)
        version = re.search(r'const VERSION = "sf-(\w+)"', sw).group(1)
        index = (self.ziel / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"assets/app.js?v={version}", index)

    def test_daten_js_vollstaendig(self):
        text = (self.ziel / "assets" / "daten.js").read_text(encoding="utf-8")
        daten = json.loads(text.removeprefix("window.SF=").strip().rstrip(";"))
        self.assertEqual(len(daten["geraete"]), len(self.geraete))
        slugs = {g["s"] for g in daten["geraete"]}
        for slug, _ in daten["vorlage"]:
            self.assertIn(slug, slugs)
        self.assertAlmostEqual(sum(daten["solar"]), 100)
        self.assertEqual(set(daten["schnitt"]), {"1", "2", "3", "4", "5"})

    def test_balkonkraftwerk_startwerte(self):
        ertrag, ersparnis, amort = build.bkw_rechnung()
        self.assertAlmostEqual(ertrag, 855)
        self.assertAlmostEqual(ersparnis, 855 * 0.4 * 0.35)
        self.assertAlmostEqual(amort, 400 / ersparnis)

    def test_statistik_nur_mit_website_id(self):
        cfg = json.loads((build.ROOT / "config.json").read_text(encoding="utf-8"))
        ohne = dict(cfg, umami_website_id="")
        mit = dict(cfg, umami_website_id="1234-abcd")
        ziel_ohne, ziel_mit = Path(self.tmp.name) / "ohne", Path(self.tmp.name) / "mit"
        build.baue(ziel_ohne, cfg=ohne, heute=datetime.date(2026, 10, 11))
        build.baue(ziel_mit, cfg=mit, heute=datetime.date(2026, 10, 11))
        self.assertNotIn("umami", (ziel_ohne / "index.html").read_text(encoding="utf-8"))
        self.assertNotIn("Umami", (ziel_ohne / "datenschutz" / "index.html").read_text(encoding="utf-8"))
        index = (ziel_mit / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-website-id="1234-abcd"', index)
        domain = build.basis_url(mit).split("://", 1)[-1].split("/", 1)[0]
        self.assertIn(f'data-domains="{domain}"', index)
        self.assertIn("Besucherstatistik (Umami)", (ziel_mit / "datenschutz" / "index.html").read_text(encoding="utf-8"))

    def test_wissen_artikel(self):
        self.assertGreaterEqual(len(build.ARTIKEL), 6)
        for a in build.ARTIKEL:
            text = (self.ziel / "wissen" / a["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertIn('"@type": "Article"', text)
            self.assertNotIn("{root}", text)
            self.assertNotIn("{preis}", text)
            for ziel in re.findall(r'href="(\.\./\.\./[^"#?]*/)"', text):
                self.assertTrue((self.ziel / "wissen" / a["slug"] / ziel / "index.html").resolve().exists(), (a["slug"], ziel))

    def test_werkzeuge_seiten(self):
        for pfad, typ in (("werkzeuge/standby/index.html", "standby"), ("werkzeuge/austausch/index.html", "austausch"),
                          ("werkzeuge/zaehlerstand/index.html", "zaehler"), ("balkonkraftwerk/index.html", "bkw")):
            self.assertIn(f'data-rechner="{typ}"', (self.ziel / pfad).read_text(encoding="utf-8"), pfad)
        self.assertIn("data-story", (self.ziel / "index.html").read_text(encoding="utf-8"))
        self.assertIn("data-story", (self.ziel / "balkonkraftwerk" / "index.html").read_text(encoding="utf-8"))

    def test_runde3_seiten(self):
        for pfad, merkmal in (("werkzeuge/spar-check/index.html", "data-spar-check"), ("werkzeuge/tarifvergleich/index.html", 'data-rechner="tarif"'),
                              ("werkzeuge/e-auto/index.html", 'data-rechner="eauto"'), ("werkzeuge/vergleich/index.html", "data-vergleich"),
                              ("wissen/lexikon/index.html", "DefinedTermSet")):
            self.assertIn(merkmal, (self.ziel / pfad).read_text(encoding="utf-8"), pfad)
        sc = (self.ziel / "werkzeuge" / "spar-check" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(sc.count('class="sc-frage"'), len(build.SPAR_FRAGEN))

    def test_lexikon_anker_eindeutig(self):
        slugs = [build.lexikon_slug(b) for b, _ in build.LEXIKON]
        self.assertEqual(len(slugs), len(set(slugs)))
        text = (self.ziel / "wissen" / "lexikon" / "index.html").read_text(encoding="utf-8")
        for slug in slugs:
            self.assertIn(f'id="{slug}"', text)

    def test_suchindex_ziele_existieren(self):
        text = (self.ziel / "assets" / "daten.js").read_text(encoding="utf-8")
        daten = json.loads(text.removeprefix("window.SF=").strip().rstrip(";"))
        self.assertGreater(len(daten["seiten"]), 40)
        for eintrag in daten["seiten"]:
            pfad = eintrag["u"].split("#")[0]
            self.assertTrue((self.ziel / pfad / "index.html").exists(), eintrag["u"])

    def test_spotlight_in_jeder_seite(self):
        for pfad in ("index.html", "geraet/kuehlschrank/index.html", "wissen/lexikon/index.html"):
            text = (self.ziel / pfad).read_text(encoding="utf-8")
            self.assertIn("data-spotlight-oeffnen", text)
            self.assertIn("data-spotlight-eingabe", text)

    def test_personalisierung_bausteine(self):
        start = (self.ziel / "index.html").read_text(encoding="utf-8")
        for merkmal in ("data-mein-bereich", "data-personalisieren", "data-ringe", "data-abzeichen", "data-mb-empfehlungen"):
            self.assertIn(merkmal, start)
        for pfad in ("index.html", "geraet/waschmaschine/index.html", "wissen/grundlast/index.html"):
            text = (self.ziel / pfad).read_text(encoding="utf-8")
            self.assertIn('id="profil-dialog"', text, pfad)
            self.assertIn("data-profil-oeffnen", text, pfad)
            self.assertNotIn("preis-dialog", text, pfad)
        self.assertIn("data-persoenlich", (self.ziel / "geraet" / "waschmaschine" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('data-artikel-slug="grundlast"', (self.ziel / "wissen" / "grundlast" / "index.html").read_text(encoding="utf-8"))

    def test_eigene_bilder_vollstaendig_und_gueltig(self):
        import xml.etree.ElementTree as ET
        ordner = self.ziel / "assets" / "bilder"
        for g in self.geraete:
            self.assertTrue((ordner / f"{g['slug']}.svg").is_file(), g["slug"])
        for datei in ordner.glob("*.svg"):
            ET.fromstring(datei.read_text(encoding="utf-8"))  # wirft bei kaputtem SVG
        # Jede Bild-Referenz auf jeder Seite zeigt auf eine vorhandene Datei
        for seite in self.ziel.rglob("index.html"):
            for ref in re.findall(r'(?:src|href)="([^"]*assets/bilder/[^"]+\.svg)"', seite.read_text(encoding="utf-8")):
                self.assertTrue((seite.parent / ref).resolve().is_file(), f"{seite}: {ref}")
        for key in ("messgeraet", "heizdecke", "leiste", "wallbox", "stromzaehler"):
            self.assertTrue((ordner / f"{key}.svg").is_file(), key)

    def test_produktbild_passt_zum_produkt(self):
        self.assertEqual(build.produkt_bild("Heizdecke"), "heizdecke")
        self.assertEqual(build.produkt_bild("Weinkühlschrank mit Effizienzklasse"), "weinkuehlschrank")
        self.assertEqual(build.produkt_bild("Kühlschrank-Thermometer"), "thermometer")
        self.assertEqual(build.produkt_bild("LED-Beamer"), "beamer")
        self.assertEqual(build.produkt_bild("Zeitschaltuhr für die Steckdose"), "zeitschaltuhr")
        self.assertEqual(build.produkt_bild("Steckdosen-Thermostat"), "thermostat")
        for g in self.geraete:
            self.assertIn(build.produkt_bild(g["produkt"]["label"]), build.BILDER, g["slug"])

    def test_startseite_apple_buehnen(self):
        start = (self.ziel / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="story story-mit-intro" data-story data-intro data-phase="intro"', start)
        self.assertLess(start.index('class="story-intro"'), start.index('class="story-bild"'), "Text muss vor dem Bild stehen")
        self.assertIn('class="bento"', start)
        self.assertIn("data-leuchttext", start)
        haus = start.split('class="hs-haus"')[1].split("</svg>")[0]
        self.assertEqual(haus.count('class="hs-geraet"'), 5)
        self.assertIn('data-story-zaehler="2500"', haus)
        self.assertEqual(start.count('class="hs-himmel"') + start.count('class="hs-fluss"'), 2)

    def test_google_eintrag(self):
        start = (self.ziel / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Stromfresser-Check: ", start)
        self.assertIn('<meta property="og:site_name" content="Stromfresser-Check">', start)
        self.assertIn("/assets/og-bild.png", start)
        self.assertIn('max-image-preview:large', start)
        self.assertNotIn('max-image-preview', (self.ziel / "impressum" / "index.html").read_text(encoding="utf-8"))
        graph = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', start, re.S)]
        website = next(x for b in graph for x in b.get("@graph", []) if x["@type"] == "WebSite")
        self.assertEqual(website["name"], "Stromfresser-Check")
        png = (self.ziel / "assets" / "og-bild.png").read_bytes()
        self.assertEqual((int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")), (1200, 630))
        ico = (self.ziel / "favicon.ico").read_bytes()
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00")
        self.assertEqual((self.ziel / f"{build.INDEXNOW_KEY}.txt").read_text(encoding="utf-8"), build.INDEXNOW_KEY)
        geraet = (self.ziel / "geraet" / "kuehlschrank" / "index.html").read_text(encoding="utf-8")
        self.assertIn('"BreadcrumbList"', geraet)
        self.assertIn('alt="Kühlschrank"', geraet)

    def test_umzug_alte_adressen_leiten_weiter(self):
        self.assertTrue(build.an_der_wurzel("https://parazki.github.io"))
        self.assertFalse(build.an_der_wurzel("https://parazki.github.io/stromfresser-check"))
        if not build.an_der_wurzel(self.ctx["base"]):
            # Noch als Projektseite unter /stromfresser-check/ veröffentlicht: keine Weiterleitungen nötig
            self.assertFalse((self.ziel / "stromfresser-check").exists())
            return
        # An der Wurzel (localhost oder parazki.github.io) -> jede alte Adresse zeigt auf die neue
        for seite in ("", "geraet/kuehlschrank/", "werkzeuge/vergleich/"):
            text = (self.ziel / "stromfresser-check" / seite / "index.html").read_text(encoding="utf-8")
            neu = f"{self.ctx['base']}/{seite}"
            self.assertIn(f'<link rel="canonical" href="{neu}">', text)
            self.assertIn(f'content="0; url={neu}"', text)
        self.assertIn("unregister", (self.ziel / "stromfresser-check" / "sw.js").read_text(encoding="utf-8"))
        self.assertNotIn("stromfresser-check/", (self.ziel / "sitemap.xml").read_text(encoding="utf-8"))

    def test_solar_szene(self):
        text = (self.ziel / "balkonkraftwerk" / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="story story-mit-intro"', text)
        self.assertLess(text.index('class="story-intro"'), text.index('class="solar-bild"'), "Text muss vor dem Bild stehen")
        self.assertEqual(text.count('class="ss-zelle"'), 60)
        self.assertEqual(text.count("data-story-zaehler="), 2)
        self.assertNotIn("solar-svg", text)

    def test_kein_html_injection_aus_daten(self):
        for g in self.geraete:
            for feld in ("name", "hinweis", "tipp"):
                self.assertNotIn("<", g[feld], f"{g['slug']}.{feld}")

    def test_strict_bricht_ohne_impressum_ab(self):
        cfg = json.loads((build.ROOT / "config.json").read_text(encoding="utf-8"))
        if build.fehlende_pflichtangaben(cfg):
            with self.assertRaises(SystemExit):
                build.baue(Path(self.tmp.name) / "strict", strict=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
