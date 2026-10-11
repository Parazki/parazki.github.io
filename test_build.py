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
        self.assertEqual(xml.count("<url>"), len(self.geraete) + 5)
        self.assertNotIn("impressum", xml)

    def test_faq_jsonld_gueltig(self):
        text = (self.ziel / "geraet" / "kuehlschrank" / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        daten = json.loads(m.group(1))
        self.assertEqual(daten["@type"], "FAQPage")
        self.assertEqual(len(daten["mainEntity"]), 3)

    def test_relative_links_funktionieren(self):
        text = (self.ziel / "geraet" / "kuehlschrank" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="../../assets/style.css?v=', text)
        for ziel in re.findall(r'href="(\.\./\.\./geraet/[^"]+)"', text):
            self.assertTrue((self.ziel / "geraet" / "kuehlschrank" / ziel / "index.html").resolve().exists(), ziel)

    def test_navigation_markiert_aktive_seite(self):
        for pfad, ziel in (("index.html", "./"), ("quiz/index.html", "../quiz/"), ("geraet/kuehlschrank/index.html", "../../geraete/")):
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
        self.assertIn('data-domains="localhost:8000"', index)
        self.assertIn("Besucherstatistik (Umami)", (ziel_mit / "datenschutz" / "index.html").read_text(encoding="utf-8"))

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
